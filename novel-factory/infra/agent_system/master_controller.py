# novel-factory/agent_system/master_controller.py
"""主控调度器（Facade模式）

只负责协调，不做具体逻辑。

委托关系：
- 配置加载 → self._config (由 agent_config.load_default_config 构建)
- AI Router → self._router (由 agent_factory.build_router 构建)
- 任务编排 → self._orchestrator (由 agent_factory.build_orchestrator 构建)
- 角色池 → self._skill_registry (由 agent_factory.build_skill_registry 构建)
- 5个Agent工具 → self.outline_master / self.content_writer / ...
- 社交引擎 → self.relationship_tracker / self.conflict_alert / ...
"""

import logging
from typing import Any, Dict, List, Optional

from ..ai_service.router import AIRouter
from .agent_config import MasterControllerConfig, load_default_config
from .agent_factory import (
    build_agent_tools,
    build_orchestrator,
    build_router,
    build_skill_registry,
    build_social_engine,
)
from .orchestration.task_orchestrator import TaskOrchestrator
from .registry.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)


class MasterController:
    """主控调度器（Facade模式）

    只负责协调，不做具体逻辑。
    """

    def __init__(
        self,
        state_dir: Optional[str] = None,
        router: Optional[AIRouter] = None,
        config: Optional[MasterControllerConfig] = None,
    ):
        """初始化主控调度器

        Args:
            state_dir: 状态目录（None = 使用 agent_config 中的默认值，cwd-无关）
            router: 显式传入的 AIRouter（None = 从 config 构造）
            config: 显式传入的配置（None = 从 env vars 加载）
        """
        # ==================== 配置层 ====================
        self._config = config or load_default_config(state_dir=state_dir)

        # ==================== AI Router ====================
        self._router = router if router is not None else build_router(self._config)

        # ==================== 基础设施 ====================
        # 共享 StateManager 实例：避免 TaskOrchestrator / 社交引擎 各持一份
        from ..state.state_manager import StateManager
        self._state_manager = StateManager()
        self._orchestrator = build_orchestrator(state_manager=self._state_manager)
        self._skill_registry = build_skill_registry()

        # ==================== 5个核心Agent工具 ====================
        tools = build_agent_tools(self._router)
        self.outline_master = tools.outline_master
        self.character_designer = tools.character_designer
        self.content_writer = tools.content_writer
        self.auditor = tools.auditor
        self.polisher = tools.polisher

        # ==================== 社交引擎 ====================
        social = build_social_engine(self._config.state_dir)
        self.relationship_tracker = social.relationship_tracker
        self.event_calculator = social.event_calculator
        self.conflict_alert = social.conflict_alert
        self.writing_suggestion = social.writing_suggestion
        self.context_builder = social.context_builder

    def get_router(self) -> AIRouter:
        """获取AIRouter实例

        Returns:
            AIRouter实例
        """
        return self._router

    def get_orchestrator(self) -> TaskOrchestrator:
        """获取任务编排器实例

        Returns:
            TaskOrchestrator实例
        """
        return self._orchestrator

    def get_skill_registry(self) -> SkillRegistry:
        """获取技能注册表实例

        Returns:
            SkillRegistry实例
        """
        return self._skill_registry

    # ==================== 工作流方法 ====================

    def advance_step(self, target_step: str, context: Optional[Dict] = None) -> tuple[bool, str]:
        """推进工作流步骤（委托给Orchestrator）

        Args:
            target_step: 目标步骤
            context: 可选的上下文信息

        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        return self._orchestrator.advance_step(target_step, context)

    def dispatch_task(
        self,
        task_name: str,
        agent: str,
        context: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """分发任务（委托给Orchestrator）

        Args:
            task_name: 任务名称
            agent: Agent类型
            context: 任务上下文
            priority: 优先级

        Returns:
            str: 任务ID
        """
        return self._orchestrator.dispatch_task(task_name, agent, context, priority)

    def verify_task(self, task_id: str, result: Dict[str, Any]) -> tuple[bool, str]:
        """验证任务完成（委托给Orchestrator）

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            tuple[bool, str]: (是否验证通过, 错误信息)
        """
        return self._orchestrator.verify_task(task_id, result)

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态（委托给Orchestrator）"""
        return self._orchestrator.get_workflow_status()

    # ==================== 角色池方法 ====================

    def run_workflow(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        max_backtracks: int = 2,
    ) -> Dict[str, Any]:
        """用 GoT 调度器运行工作流 (Doc 4 Phase 3)

        这是 MasterController 的新入口,GoT 替代 22 步状态机。
        保留 advance_step/dispatch_task 等老方法,GoT 失败时可回退。

        Args:
            workflow_name: workflow YAML 名 (如 'novel_writing')
            start_nodes: 起点节点 ID 列表 (None = 自动找无依赖节点)
            initial_inputs: 起点节点的 seed inputs (e.g. chapter_num=1, characters=[...])
            max_backtracks: 软回溯预算 (默认 2)

        Returns:
            {
                "summary": ExecutionSummary (completed, failed, steps, ...),
                "graph": ThoughtGraph (含 mermaid 导出),
                "executions": dict[node_id, NodeExecution] 全部执行记录,
            }

        Raises:
            WorkflowError: 加载失败
            HumanInterventionRequired: 回溯超限
            MaxStepsExceeded: 步数超限
        """
        # 延迟 import 避免 got ↔ agent_system 循环
        from infra.got.workflow_loader import WorkflowError

        from .got_bridge import build_got_scheduler

        try:
            scheduler, graph = build_got_scheduler(
                master=self,
                workflow_name=workflow_name,
                max_backtracks=max_backtracks,
            )
        except WorkflowError:
            raise

        # 默认起点:无依赖的节点
        if start_nodes is None:
            start_nodes = [
                nid for nid in graph.node_ids()
                if not graph.get_node(nid).depends_on
            ]

        summary = scheduler.run(
            start_nodes=start_nodes,
            initial_inputs=initial_inputs or {},
        )

        # 收集全部 executions
        executions: Dict[str, Any] = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)

        return {
            "summary": summary,
            "graph": graph,
            "executions": executions,
        }

    def switch_agent_role(self, agent_name: str, role_id: str) -> bool:
        """切换Agent角色

        Args:
            agent_name: Agent名称（如'content_writer', 'auditor'）
            role_id: 角色ID（如'writer-a', 'auditor-c'）

        Returns:
            bool: 是否切换成功
        """
        config = self._skill_registry.query_by_role_id(role_id)
        if config:
            # 角色配置存在，实际切换逻辑在Agent工具中处理
            return True
        return False

    def get_agent_role_config(self, role_id: str) -> Optional[Dict[str, Any]]:
        """获取角色配置

        Args:
            role_id: 角色ID

        Returns:
            角色配置字典或None
        """
        return self._skill_registry.query_by_role_id(role_id)

    # ==================== 创作相关方法（委托给Agent工具） ====================

    def generate_outline(self, settings: Dict, requirements: Dict) -> Dict:
        """生成大纲"""
        return self.outline_master.generate_outline(settings, requirements)

    def generate_characters(self, outline: Dict, character_requirements: List[Dict]) -> List[Dict]:
        """生成角色卡片"""
        characters = []
        for req in character_requirements:
            card = self.character_designer.generate_character_card(req)
            characters.append(card)
        return characters

    def write_chapter(
        self,
        chapter_num: int,
        outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        style_guide: Dict,
        use_llm: bool = True
    ) -> Dict:
        """写章节流程（委托给content_writer）

        Args:
            chapter_num: 章节编号
            outline: 章节大纲
            characters: 角色列表
            memory_context: 记忆上下文
            style_guide: 风格指南
            use_llm: 是否使用LLM生成（默认True）

        Returns:
            包含content、prompt、suggestions的字典
        """
        # 获取章节大纲
        chapter_outline = self.outline_master.schema.get_chapter_outline(outline, chapter_num)

        # 构建上下文
        context = self.context_builder.build_writing_context(
            chapter_outline=chapter_outline,
            characters=characters,
            memory_context=memory_context,
            relationship_network=self.relationship_tracker.get_network(),
            style_guide=style_guide
        )

        # 获取写作建议
        suggestions = self.writing_suggestion.generate_suggestions(
            self.relationship_tracker, chapter_num
        )

        if use_llm:
            # 使用LLM生成章节
            result = self.content_writer.generate_chapter(chapter_num, context)
            return {
                "content": result["content"],
                "word_count": result.get("word_count", len(result["content"])),
                "suggestions": suggestions,
                "context": context
            }
        else:
            # 仅返回prompt（用于调试）
            prompt = self.content_writer.build_writing_prompt(context)
            return {
                "prompt": prompt,
                "suggestions": suggestions,
                "context": context
            }

    def audit_chapter(
        self,
        chapter_num: int,
        content: str,
        characters: List[Dict],
        timeline: List[Dict],
        use_llm: bool = True
    ) -> Dict:
        """审核章节（委托给auditor）

        Args:
            chapter_num: 章节编号
            content: 章节内容
            characters: 角色列表
            timeline: 时间线
            use_llm: 是否使用LLM深度审核（默认True）

        Returns:
            审核报告
        """
        # 角色一致性检查
        char_issues = self.auditor.check_character_consistency(content, characters)

        # AI痕迹检测
        ai_issues = self.auditor.detect_ai_gloss(content)

        # 生成报告
        all_issues = char_issues + ai_issues

        if use_llm:
            # 使用LLM进行深度审核
            try:
                llm_report = self.auditor.llm_audit(
                    chapter_num=chapter_num,
                    content=content,
                    characters=characters,
                    context={"timeline": timeline}
                )
                # 合并LLM报告中的issues
                if "issues" in llm_report:
                    all_issues.extend(llm_report["issues"])
                if "scores" in llm_report:
                    return self.auditor.generate_audit_report(chapter_num, all_issues, llm_report["scores"])
            except Exception as e:
                # LLM审核失败不影响规则检查结果，但记录 traceback 便于排查
                logger.warning(
                    f"LLM审核失败 (chapter {chapter_num}): {e}",
                    exc_info=True,
                )

        return self.auditor.generate_audit_report(chapter_num, all_issues, scores={})

    def polish_chapter(self, content: str) -> str:
        """润色章节（委托给polisher）"""
        result = self.polisher.remove_ai_gloss(content)
        result = self.polisher.optimize_dialogue(result)
        return result

    # ==================== 社交引擎方法 ====================

    def apply_event(self, event_type: str, from_char: str, to_char: str, chapter: int):
        """应用事件并更新关系"""
        self.event_calculator.apply_event(event_type, from_char, to_char, self.relationship_tracker)
        self.relationship_tracker.record_event(from_char, to_char, event_type, chapter)

    def check_alerts(self, chapter: int) -> List[Dict]:
        """检查预警"""
        return self.conflict_alert.check_alerts(self.relationship_tracker, chapter)

    def get_writing_suggestions(self, chapter: int) -> List[str]:
        """获取写作建议"""
        return self.writing_suggestion.generate_suggestions(self.relationship_tracker, chapter)
