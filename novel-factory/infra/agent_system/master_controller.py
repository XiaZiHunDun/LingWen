# novel-factory/agent_system/master_controller.py
"""主控调度器（Facade模式）

协调各子模块，不做具体逻辑实现。
职责：
- 依赖注入（Router、Orchestrator、Registry）
- 工作流方法委托给Agent工具
- 社交引擎协调
"""

from typing import Dict, List, Optional, Any

from .agents.outline_master.tools import OutlineMasterTools
from .agents.character_designer.tools import CharacterDesignerTools
from .agents.content_writer.tools import ContentWriterTools
from .agents.auditor.tools import AuditorTools
from .agents.polisher.tools import PolisherTools
from .social_engine.relationship_tracker import RelationshipTracker
from .social_engine.event_effect_calculator import EventEffectCalculator
from .social_engine.conflict_alert import ConflictAlert
from .social_engine.writing_suggestion import WritingSuggestion
from .shared.context_builder import ContextBuilder

# 导入AI Service
from ..ai_service import ProviderConfig
from ..ai_service.router import AIRouter

# 导入TaskOrchestrator
from .task_orchestrator import TaskOrchestrator

# 导入SkillRegistry
from .skill_registry import SkillRegistry


class MasterController:
    """主控调度器（Facade模式）

    只负责协调，不做具体逻辑。

    委托关系：
    - AI Router管理 → self._router
    - 任务编排 → self._orchestrator
    - 角色池 → self._skill_registry
    - 5个Agent工具保持不变
    - 社交引擎保持不变
    """

    def __init__(
        self,
        state_dir: str = "novel-factory/agent_system",
        router: Optional[AIRouter] = None
    ):
        """初始化主控调度器

        Args:
            state_dir: 状态目录
            router: AIRouter实例，如果为None则创建默认实例
        """
        # ==================== 基础设施 ====================

        # AI Router
        if router is None:
            self._router = self._create_default_router()
        else:
            self._router = router

        # TaskOrchestrator（任务编排器）
        self._orchestrator = TaskOrchestrator(
            state_file=f"{state_dir}/workflow_state.json"
        )

        # SkillRegistry（技能注册表）
        self._skill_registry = SkillRegistry()

        # ==================== 5个核心Agent工具 ====================

        self.outline_master = OutlineMasterTools()
        self.character_designer = CharacterDesignerTools()
        self.content_writer = ContentWriterTools(router=self._router)
        self.auditor = AuditorTools(router=self._router)
        self.polisher = PolisherTools()

        # ==================== 社交引擎 ====================

        self.relationship_tracker = RelationshipTracker(f"{state_dir}/social_engine/relationship_network.json")
        self.event_calculator = EventEffectCalculator()
        self.conflict_alert = ConflictAlert()
        self.writing_suggestion = WritingSuggestion()
        self.context_builder = ContextBuilder()

    def _create_default_router(self) -> AIRouter:
        """创建默认的AIRouter实例

        从环境变量读取配置

        Returns:
            AIRouter实例
        """
        import os

        # 从环境变量获取API密钥
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        minimax_key = os.getenv("MINIMAX_API_KEY", "")

        config = {}
        if openai_key:
            config["openai"] = ProviderConfig(api_key=openai_key, model="gpt-4")
        if anthropic_key:
            config["anthropic"] = ProviderConfig(api_key=anthropic_key, model="claude-3-5-sonnet-20241022")
        if minimax_key:
            config["minimax"] = ProviderConfig(api_key=minimax_key, model="MiniMax-M2.7")

        if not config:
            raise RuntimeError(
                "No AI provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or MINIMAX_API_KEY environment variable."
            )

        # 默认使用minimax（成本最低），启用故障转移
        return AIRouter(
            config=config,
            primary_provider="minimax" if "minimax" in config else ("anthropic" if "anthropic" in config else "openai"),
            enable_failover=True
        )

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
                # LLM审核失败不影响规则检查结果
                pass

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