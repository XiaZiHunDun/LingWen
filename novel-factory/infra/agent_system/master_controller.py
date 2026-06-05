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
import math
import re
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
from .decision_queue import (
    DecisionKind,
    HumanDecision,
    HumanDecisionQueue,
    create_decision,
)
from .orchestration.task_orchestrator import TaskOrchestrator
from .registry.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)

# Phase 7.5: S1-S8 8 维评分维度 — 用于 polish_merge LLM 评分
_S1_S8_KEYS: tuple[str, ...] = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")

# Phase 8.1: Static LLM robustness helpers
_NON_SAFE_LABEL_CHARS = re.compile(r"[^a-zA-Z0-9_]")


def _coerce_score(value: Any, *, default: int = 5) -> int:
    """Phase 8.1: 把 LLM 返回的 score coerce + clamp 到 [0, 10] int 范围.

    Why: HAIKU 真实输出常给 float (7.5), str ("7"), 或越界 (15, -3).
    当前 int() 强转: float 截断丢精度, str raise, 越界未 clamp.
    This helper handles all cases + 给缺失/无效回退 (默认 5 = 中性).

    Args:
        value: 任意 LLM 输出 (int/float/str/None/list)
        default: coerce 失败时的回退 (默认 5)

    Returns:
        int in [0, 10], 越界 clamp, 非数回 default
    """
    if value is None:
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(n):
        return default
    return max(0, min(10, round(n)))


def _safe_label(label: str) -> str:
    """Phase 8.1: 把 label 规范成 JSON key 安全的 [a-zA-Z0-9_]+.

    Why: f"scores_{label}" 当 JSON key 时, 如果 label 含特殊字符 (., -, 空格, 中文),
    LLM 输出可能错位. 防御性 normalize 两端 — prompt 用 sanitized 当 JSON key,
    winner 仍用原始 (dashboard 显示期望原始).

    Args:
        label: 原始 label (默认是 upstream node id)

    Returns:
        sanitized label, 非 [a-zA-Z0-9_] 字符替换为 _
    """
    return _NON_SAFE_LABEL_CHARS.sub("_", label)


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

        # ==================== 决策队列 (Phase 4.2/4.3) ====================
        self._decision_queue = HumanDecisionQueue(state_dir=self._config.state_dir)

        # ==================== 活跃工作流缓存 (Phase 5) ====================
        # run_workflow() 调用后填充,resume_workflow() 用它来"接着跑"
        # 注:仅支持单一活跃工作流;若需多工作流,应改为 dict[workflow_name, ...]
        self._last_scheduler: Optional[Any] = None
        self._last_graph: Optional[Any] = None
        self._last_workflow_name: Optional[str] = None
        self._last_start_nodes: List[str] = []

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
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """用 GoT 调度器运行工作流 (Doc 4 Phase 3 + 4)

        这是 MasterController 的新入口,GoT 替代 22 步状态机。
        保留 advance_step/dispatch_task 等老方法,GoT 失败时可回退。

        Args:
            workflow_name: workflow YAML 名 (如 'novel_writing')
            start_nodes: 起点节点 ID 列表 (None = 自动找无依赖节点)
            initial_inputs: 起点节点的 seed inputs (e.g. chapter_num=1, characters=[...])
            max_backtracks: 软回溯预算 (默认 2)
            base_dir: workflow YAML 目录 (None = 默认 infra/got/workflows/)

        Returns:
            {
                "summary": ExecutionSummary (completed, failed, steps, ...),
                "graph": ThoughtGraph (含 mermaid 导出),
                "executions": dict[node_id, NodeExecution] 全部执行记录,
                "pending_decisions": list[dict] 本次 run 扫描到的 DECISION 节点
                                  生成的 HumanDecision 序列化,
            }

        Raises:
            WorkflowError: 加载失败
            HumanInterventionRequired: 回溯超限
            MaxStepsExceeded: 步数超限
        """
        # 延迟 import 避免 got ↔ agent_system 循环
        from infra.got.workflow_loader import WorkflowError

        from .got_bridge import build_got_scheduler

        bd_path: Optional[Any] = None
        if base_dir is not None:
            from pathlib import Path
            bd_path = Path(base_dir)

        try:
            scheduler, graph = build_got_scheduler(
                master=self,
                workflow_name=workflow_name,
                base_dir=str(bd_path) if bd_path else None,
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

        # 扫描 DECISION 节点 → 创建 HumanDecision (Phase 4.3)
        pending_decisions = self._harvest_decision_specs(graph)

        summary = scheduler.run(
            start_nodes=start_nodes,
            initial_inputs=initial_inputs or {},
        )

        # 收集全部 executions
        executions: Dict[str, Any] = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)

        # 缓存活跃工作流状态 (Phase 5) — resume_workflow() 用它
        self._last_scheduler = scheduler
        self._last_graph = graph
        self._last_workflow_name = workflow_name
        self._last_start_nodes = list(start_nodes)

        return {
            "summary": summary,
            "graph": graph,
            "executions": executions,
            "pending_decisions": pending_decisions,
        }

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> HumanDecision:
        """解决决策 (delegates to HumanDecisionQueue.resolve)

        Args:
            decision_id: 决策 ID
            option: 选定的选项
            resolved_by: 解决者标识 (默认 'human')

        Returns:
            更新后的 HumanDecision

        Raises:
            RuntimeError: decision queue 未初始化
            KeyError / ValueError: 见 HumanDecisionQueue.resolve
        """
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        # Phase 6.5: with_lock() 拿 fcntl 排他锁 + 重新读 + 写回,
        # 防止 CLI 与 dashboard 跨进程写 decisions.json 时的 race condition
        with queue.with_lock():
            resolved = queue.resolve(decision_id, option, resolved_by=resolved_by)
        return resolved

    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Dict[str, Any]:
        """恢复 DECISION 暂停的工作流 (Phase 5)

        三步合一:
        1. 标记 HumanDecision 为 RESOLVED (PENDING → RESOLVED)
        2. 把对应 GoT DECISION 节点从 WAITING → COMPLETED,写入 option
        3. 重新调用 scheduler.run() 让下游节点继续执行

        用法:
            result1 = controller.run_workflow("novel_writing")
            # summary.paused=True (DECISION 节点等待)
            for d in result1["pending_decisions"]:
                controller.resume_workflow(d["decision_id"], "approve")
            # 最终一次调用后,summary.paused=False (全部 COMPLETED)

        Args:
            decision_id: HumanDecision ID (从 list_pending_decisions / pending_decisions 取)
            option: 选定的选项
            resolved_by: 解决者标识

        Returns:
            同 run_workflow() 结构 + 额外 resolved_decision 字段:
            {
                "summary": ExecutionSummary,
                "graph": ThoughtGraph,
                "executions": dict[node_id, NodeExecution],
                "pending_decisions": list[dict] (本轮扫描的新决策),
                "resolved_decision": HumanDecision (本轮已解决),
            }

        Raises:
            RuntimeError: 无活跃工作流 (从未 run_workflow)
            KeyError: decision_id 不存在
            ValueError: 决策已 RESOLVED / option 不在 options 中 / node 非 WAITING
        """
        # 1. 检查有活跃工作流
        scheduler = getattr(self, "_last_scheduler", None)
        graph = getattr(self, "_last_graph", None)
        if scheduler is None or graph is None:
            raise RuntimeError(
                "no active workflow; call run_workflow() first before resume_workflow()"
            )

        # 2. 查决策 → 拿 node_id
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        decision = queue.get(decision_id)  # 抛 KeyError if missing

        # 3. 标 RESOLVED (PENDING → RESOLVED)
        resolved = self.resolve_decision(decision_id, option, resolved_by=resolved_by)

        # 4. 标 DECISION 节点 WAITING → COMPLETED,写入 option
        scheduler.resume(
            decision_node_id=decision.node_id,
            option=option,
            resolved_by=resolved_by,
        )

        # 5. 扫描新 DECISION 节点 (下游可能有)
        pending_decisions = self._harvest_decision_specs(graph)

        # 6. 继续执行 — 用上次缓存的 start_nodes
        start_nodes = self._last_start_nodes
        if not start_nodes:
            start_nodes = [
                nid for nid in graph.node_ids()
                if not graph.get_node(nid).depends_on
            ]

        summary = scheduler.run(start_nodes=start_nodes)

        # 7. 收集 executions
        executions: Dict[str, Any] = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)

        return {
            "summary": summary,
            "graph": graph,
            "executions": executions,
            "pending_decisions": pending_decisions,
            "resolved_decision": resolved,
        }

    def list_pending_decisions(self) -> list[dict[str, Any]]:
        """列出 PENDING 决策 (按 priority desc + due_at asc 排序)

        Returns:
            list of HumanDecision.to_dict() 序列化结果
        """
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            return []
        return [d.to_dict() for d in queue.pending()]

    def get_decision_queue(self) -> HumanDecisionQueue:
        """返回底层 HumanDecisionQueue (供高级操作:defer/cancel/save)"""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        return queue

    def _harvest_decision_specs(self, graph: Any) -> list[dict[str, Any]]:
        """扫描图中的 DECISION 节点 → 创建 HumanDecision → 返回序列化列表

        Phase 4.3: run_workflow 自动从工作流图中识别 DECISION 类型节点,
        包装为 HumanDecision 放入决策队列,供人工介入。
        """
        from infra.got.data_structures import NodeType

        # 防御:__new__ 构造的测试 stub 可能没有 _decision_queue
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            return []

        harvested: list[dict[str, Any]] = []
        for nid in graph.node_ids():
            node = graph.get_node(nid)
            if node.type != NodeType.DECISION:
                continue
            kind = _infer_decision_kind(nid)
            decision = create_decision(
                decision_kind=kind,
                node_id=nid,
                prompt=node.description or f"决策点: {node.name or nid}",
                options=_default_options_for(kind),
                priority=_default_priority_for(kind),
            )
            # Phase 6.5: with_lock() 让 add 也是原子的
            with queue.with_lock():
                queue.add(decision)
            harvested.append(decision.to_dict())
        return harvested

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
                llm_report = self.auditor.audit_chapter(
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
        """润色章节（委托给polisher, LLM 化路径 Phase 7.2）"""
        result = self.polisher.polish_chapter(chapter_num=0, content=content)
        return result["content"]

    def polish_emotional_pacing(self, content: str) -> str:
        """情绪节奏 variant — 对话自然化 + 节奏调整 (Phase 7.4)

        跳过 remove_ai_gloss 规则, 留给 ai_trace_removal 节点处理
        (两个 variant 是正交优化维度)

        韧性契约 (Phase 7.2 模式, fixup M1): 每个 LLM 调 try/except 兜底,
        失败不致命 — logger.warning 后 content 继续流转. 防止单 LLM 失败
        → AgentComputeFn fail=True → 节点 FAILED → backtrack.
        """
        polished = content
        try:
            polished = self.polisher.optimize_dialogue_llm(polished)
        except Exception as e:
            logger.warning("polish_emotional_pacing: dialogue_llm failed: %s", e)
        try:
            polished = self.polisher.adjust_pacing_llm(polished)
        except Exception as e:
            logger.warning("polish_emotional_pacing: pacing_llm failed: %s", e)
        return polished

    def polish_ai_trace_removal(self, content: str) -> str:
        """AI 痕迹 variant — 规则去 AI 痕迹 + 对话自然化 (Phase 7.4)

        跳过 adjust_pacing_llm, 留给 emotional_pacing 节点处理

        韧性契约 (fixup M1): remove_ai_gloss 是纯规则从不出错, 不兜底;
        optimize_dialogue_llm try/except 兜底 (失败 → logger.warning +
        保留规则去 AI 痕迹结果).
        """
        polished = self.polisher.remove_ai_gloss(content)
        try:
            polished = self.polisher.optimize_dialogue_llm(polished)
        except Exception as e:
            logger.warning("polish_ai_trace_removal: dialogue_llm failed: %s", e)
        return polished

    def polish_merge_synthesis(
        self,
        content_a: str,
        content_b: str,
        *,
        labels: tuple[str, str] = ("A", "B"),
    ) -> Dict[str, Any]:
        """Phase 7.5: LLM S1-S8 8 维加权评分, 选高者 (polish_merge 节点)

        调 polisher.chat() (HAIKU tier, 4000 tokens) 评分 2 个 variant, 加权
        (等权 0.125 each) 求总分, winner = 高者。韧性契约: LLM 失败 → 走
        max(len) 兜底, reason="llm_fail"。

        Args:
            content_a: variant A 内容
            content_b: variant B 内容
            labels: 2 个 label (默认 ("A", "B")), 也可用上游节点 id
                    (e.g. ("polish_emotional_pacing", "polish_ai_trace_removal"))

        Returns:
            {
                "content": str,             # winner 内容
                "winner": str,              # labels[0] or labels[1]
                "scores_a": dict[str, int], # {S1: 8, ..., S8: 7}
                "scores_b": dict[str, int],
                "scores_total_a": float,    # 0-10 平均
                "scores_total_b": float,
                "scores_delta": float,      # total_a - total_b
                "fallback": str | None,     # 兜底原因 (None=走 LLM)
                "_labels": list[str],       # Phase 7.6: 透传 labels (dashboard 雷达图消费)
            }
        """
        empty = self._merge_synthesis_len_fallback
        if not content_a or not content_b:
            result: Dict[str, Any] = empty(content_a, content_b, labels, reason="empty_content")
        elif content_a == content_b:
            result = {
                "content": content_a,
                "winner": labels[0],
                "scores_a": {},
                "scores_b": {},
                "scores_total_a": 0.0,
                "scores_total_b": 0.0,
                "scores_delta": 0.0,
                "fallback": "identical",
            }
        else:
            try:
                result = self._merge_synthesis_llm(content_a, content_b, labels)
            except self._MergeParseError as e:
                logger.warning("polish_merge_synthesis: JSON parse failed, len fallback: %s", e)
                result = empty(content_a, content_b, labels, reason="json_parse_failed")
            except Exception as e:
                logger.warning("polish_merge_synthesis: LLM failed, len fallback: %s", e)
                result = empty(content_a, content_b, labels, reason="llm_fail")
        # Phase 7.6: 透传 labels 给 dashboard 雷达图抽 label_a/b
        result["_labels"] = list(labels)
        return result

    class _MergeParseError(Exception):
        """Phase 8.1: polish_merge LLM 响应 parse 失败 (非 JSON / 缺 scores 字段 / 类型错)."""

    def _parse_merge_response(self, response: str) -> dict:
        """解析 LLM JSON 响应, 失败抛 _MergeParseError (根因清晰).

        Why: base.py parse_response 失败兜底返 {raw: response}, 之前 master_controller
        读 parsed["scores_X"] KeyError 被外层通用 try/except 吞, 走 llm_fail 兜底,
        日志看不到根因. 这个方法显式抛 _MergeParseError → 外层 catch → fallback
        设为 "json_parse_failed" 更具体.
        """
        parsed = self.polisher.parse_response(response, format_type="json")
        # base.py:178-181 失败兜底返 {"raw": response}, 检测这个
        if not isinstance(parsed, dict) or "raw" in parsed:
            raise self._MergeParseError(
                f"JSON parse failed (raw response, first 200 chars): {response[:200]}"
            )
        return parsed

    def _merge_synthesis_llm(
        self,
        content_a: str,
        content_b: str,
        labels: tuple[str, str],
    ) -> Dict[str, Any]:
        """Phase 7.5: 调 polisher LLM 评分 2 variant, 等权求总分选高者"""
        from .agents.polisher.prompts import (
            build_merge_synthesis_prompt,
            get_merge_synthesis_system_prompt,
        )

        prompt = build_merge_synthesis_prompt(content_a, content_b, labels=labels)
        system = get_merge_synthesis_system_prompt()
        response = self.polisher.chat(
            prompt=prompt, system=system, temperature=0.2, max_tokens=2000
        )
        parsed = self._parse_merge_response(response)

        label_a, label_b = labels
        safe_a, safe_b = _safe_label(label_a), _safe_label(label_b)
        # 防御性: scores_X 字段是 dict (HAIKU 可能给 int)
        scores_a_raw = parsed.get(f"scores_{safe_a}")
        scores_b_raw = parsed.get(f"scores_{safe_b}")
        if not isinstance(scores_a_raw, dict) or not isinstance(scores_b_raw, dict):
            raise self._MergeParseError(
                f"scores field not dict (scores_{safe_a}={type(scores_a_raw).__name__}, "
                f"scores_{safe_b}={type(scores_b_raw).__name__})"
            )
        scores_a = {k: _coerce_score(scores_a_raw.get(k, 5)) for k in _S1_S8_KEYS}
        scores_b = {k: _coerce_score(scores_b_raw.get(k, 5)) for k in _S1_S8_KEYS}
        total_a = sum(scores_a.values()) / 8.0
        total_b = sum(scores_b.values()) / 8.0
        winner = label_a if total_a >= total_b else label_b  # 原始 label, dashboard 友好
        content = content_a if winner == label_a else content_b
        return {
            "content": content,
            "winner": winner,
            "scores_a": scores_a,
            "scores_b": scores_b,
            "scores_total_a": total_a,
            "scores_total_b": total_b,
            "scores_delta": total_a - total_b,
        }

    def _merge_synthesis_len_fallback(
        self,
        content_a: str,
        content_b: str,
        labels: tuple[str, str],
        *,
        reason: str,
    ) -> Dict[str, Any]:
        """Phase 7.5: max(len) 兜底 (LLM 失败 / 空 content 时)"""
        if not content_a and not content_b:
            return {
                "content": "",
                "winner": "",
                "scores_a": {},
                "scores_b": {},
                "scores_total_a": 0.0,
                "scores_total_b": 0.0,
                "scores_delta": 0.0,
                "fallback": reason,
            }
        if not content_a:
            return {
                "content": content_b,
                "winner": labels[1],
                "scores_a": {},
                "scores_b": {},
                "scores_total_a": 0.0,
                "scores_total_b": 0.0,
                "scores_delta": 0.0,
                "fallback": reason,
            }
        if not content_b:
            return {
                "content": content_a,
                "winner": labels[0],
                "scores_a": {},
                "scores_b": {},
                "scores_total_a": 0.0,
                "scores_total_b": 0.0,
                "scores_delta": 0.0,
                "fallback": reason,
            }
        winner = labels[0] if len(content_a) >= len(content_b) else labels[1]
        content = content_a if winner == labels[0] else content_b
        return {
            "content": content,
            "winner": winner,
            "scores_a": {},
            "scores_b": {},
            "scores_total_a": 0.0,
            "scores_total_b": 0.0,
            "scores_delta": 0.0,
            "fallback": reason,
        }

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


# === Decision helpers (Phase 4.3) ===

_DEFAULT_DECISION_OPTIONS: dict[str, tuple[str, ...]] = {
    DecisionKind.OUTLINE_JUDGMENT.value: ("approve", "revise", "abandon"),
    DecisionKind.VOLUME_JUDGMENT.value: ("approve", "minor_fix", "major_revise"),
    DecisionKind.CHAPTER_ITERATION_JUDGMENT.value: (
        "next_batch",
        "iterate",
        "human_review",
    ),
    DecisionKind.PUBLISH_JUDGMENT.value: ("S_publish", "A_publish", "B_revise", "reject"),
    DecisionKind.SUBPLOT_OPEN.value: ("open", "defer", "abandon"),
    DecisionKind.SUBPLOT_CLOSE.value: ("close", "extend", "abandon"),
    DecisionKind.STYLE_PICK.value: ("燃系", "细腻", "冷峻", "幽默"),
}

_DEFAULT_DECISION_PRIORITY: dict[str, int] = {
    DecisionKind.PUBLISH_JUDGMENT.value: 10,
    DecisionKind.OUTLINE_JUDGMENT.value: 8,
    DecisionKind.VOLUME_JUDGMENT.value: 7,
    DecisionKind.CHAPTER_ITERATION_JUDGMENT.value: 6,
    DecisionKind.STYLE_PICK.value: 4,
    DecisionKind.SUBPLOT_OPEN.value: 3,
    DecisionKind.SUBPLOT_CLOSE.value: 3,
}


def _infer_decision_kind(node_id: str) -> DecisionKind:
    """从 node_id 推断 DecisionKind

    规则:子串匹配 (顺序敏感)
    - "publish" → PUBLISH_JUDGMENT
    - "outline" → OUTLINE_JUDGMENT
    - "volume" → VOLUME_JUDGMENT
    - "iteration" / "iter" → CHAPTER_ITERATION_JUDGMENT
    - "style" → STYLE_PICK
    - "subplot_close" → SUBPLOT_CLOSE
    - "subplot" → SUBPLOT_OPEN (兜底)
    - 其他 → OUTLINE_JUDGMENT 兜底
    """
    nid = node_id.lower()
    if "publish" in nid:
        return DecisionKind.PUBLISH_JUDGMENT
    if "outline" in nid:
        return DecisionKind.OUTLINE_JUDGMENT
    if "volume" in nid:
        return DecisionKind.VOLUME_JUDGMENT
    if "iteration" in nid or "iter" in nid:
        return DecisionKind.CHAPTER_ITERATION_JUDGMENT
    if "style" in nid:
        return DecisionKind.STYLE_PICK
    if "subplot_close" in nid:
        return DecisionKind.SUBPLOT_CLOSE
    if "subplot" in nid:
        return DecisionKind.SUBPLOT_OPEN
    return DecisionKind.OUTLINE_JUDGMENT


def _default_options_for(kind: DecisionKind) -> tuple[str, ...]:
    return _DEFAULT_DECISION_OPTIONS.get(kind.value, ("approve", "reject"))


def _default_priority_for(kind: DecisionKind) -> int:
    return _DEFAULT_DECISION_PRIORITY.get(kind.value, 5)


def _collect_decision_specs_from_graph(graph: Any) -> list[dict[str, Any]]:
    """从图中扫描 DECISION 节点 → 返回 spec 列表 (供单元测试 / 上层 UI 使用)

    注:实际创建 HumanDecision 由 MasterController._harvest_decision_specs 完成。
    本函数仅返回元数据 (node_id, kind),不创建 HumanDecision。
    """
    from infra.got.data_structures import NodeType

    specs: list[dict[str, Any]] = []
    for nid in graph.node_ids():
        node = graph.get_node(nid)
        if node.type != NodeType.DECISION:
            continue
        kind = _infer_decision_kind(nid)
        specs.append({
            "node_id": nid,
            "decision_kind": kind,
            "prompt": node.description or f"决策点: {node.name or nid}",
            "options": list(_default_options_for(kind)),
            "priority": _default_priority_for(kind),
        })
    return specs


__all__ = [
    "MasterController",
    "_infer_decision_kind",
    "_collect_decision_specs_from_graph",
]
