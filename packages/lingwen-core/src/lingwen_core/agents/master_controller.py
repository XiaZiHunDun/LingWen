# novel-factory/agent_system/master_controller.py
"""主控调度器（Facade模式）

Phase 15.0 P3-SPLIT: 已拆分为多个子模块，保持向后兼容。

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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..ai_service.router import AIRouter

if TYPE_CHECKING:
    from ..ai_service.cost_tracker import CostTracker
    from .budget_persistence import BudgetService
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
from .mc_social import SocialEngineMixin
from .mc_writing import WritingMixin
from .mc_editing import EditingMixin
from .mc_workflow import WorkflowMixin
from .orchestration.task_orchestrator import TaskOrchestrator
from .registry.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)


class MasterController(WorkflowMixin, WritingMixin, EditingMixin, SocialEngineMixin):
    """主控调度器（Facade模式）

    只负责协调，不做具体逻辑。
    """

    def __init__(
        self,
        state_dir: Optional[str] = None,
        router: Optional[AIRouter] = None,
        config: Optional[MasterControllerConfig] = None,
        cost_tracker: Optional["CostTracker"] = None,
        budget_service: Optional["BudgetService"] = None,
        budget_service_by_tier: Optional["BudgetService"] = None,
    ):
        """初始化主控调度器

        Args:
            state_dir: 状态目录
            router: 显式传入的 AIRouter
            config: 显式传入的配置
            cost_tracker: 显式传入的 CostTracker
            budget_service: 显式传入的 BudgetService
            budget_service_by_tier: 显式传入的 BudgetService
        """
        self._config = config or load_default_config(state_dir=state_dir)

        self._router = router if router is not None else build_router(self._config)

        self.cost_tracker = cost_tracker

        self.budget_service = budget_service

        self.budget_service_by_tier = budget_service_by_tier

        self._current_budget_usd: Optional[float] = None

        self._current_run_id: Optional[str] = None

        from ..state.state_manager import StateManager

        self._state_manager = StateManager()
        self._orchestrator = build_orchestrator(state_manager=self._state_manager)
        self._skill_registry = build_skill_registry()

        tools = build_agent_tools(self._router)
        self.outline_master = tools.outline_master
        self.character_designer = tools.character_designer
        self.content_writer = tools.content_writer
        self.auditor = tools.auditor
        self.polisher = tools.polisher

        social = build_social_engine(self._config.state_dir)
        self.relationship_tracker = social.relationship_tracker
        self.event_calculator = social.event_calculator
        self.conflict_alert = social.conflict_alert
        self.writing_suggestion = social.writing_suggestion
        self.context_builder = social.context_builder

        self._decision_queue = HumanDecisionQueue(state_dir=self._config.state_dir)

        self._last_scheduler: Optional[Any] = None
        self._last_graph: Optional[Any] = None
        self._last_workflow_name: Optional[str] = None
        self._last_start_nodes: List[str] = []
        self._last_initial_inputs: Dict[str, Any] = {}
        self._last_incremental_backfill: Any = None
        self._last_memory_context: Optional[Dict[str, Any]] = None

    def get_router(self) -> AIRouter:
        """获取AIRouter实例"""
        return self._router

    def get_orchestrator(self) -> TaskOrchestrator:
        """获取任务编排器实例"""
        return self._orchestrator

    def get_skill_registry(self) -> SkillRegistry:
        """获取技能注册表实例"""
        return self._skill_registry

    def switch_agent_role(self, agent_name: str, role_id: str) -> bool:
        """切换Agent角色"""
        return self._skill_registry.switch_role(agent_name, role_id)

    def get_agent_role_config(self, role_id: str) -> Optional[Dict[str, Any]]:
        """获取角色配置"""
        return self._skill_registry.query_by_role_id(role_id)

    class _MergeParseError(Exception):
        """Merge parsing error"""

        pass


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
    """从 node_id 推断 DecisionKind"""
    if "publish" in node_id.lower():
        return DecisionKind.PUBLISH_JUDGMENT
    if "outline" in node_id.lower():
        return DecisionKind.OUTLINE_JUDGMENT
    if "volume" in node_id.lower():
        return DecisionKind.VOLUME_JUDGMENT
    if "chapter" in node_id.lower() and "iteration" in node_id.lower():
        return DecisionKind.CHAPTER_ITERATION_JUDGMENT
    if "subplot" in node_id.lower() and "open" in node_id.lower():
        return DecisionKind.SUBPLOT_OPEN
    if "subplot" in node_id.lower() and "close" in node_id.lower():
        return DecisionKind.SUBPLOT_CLOSE
    if "style" in node_id.lower() or "pick" in node_id.lower():
        return DecisionKind.STYLE_PICK
    return DecisionKind.OUTLINE_JUDGMENT