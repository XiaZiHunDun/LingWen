"""Phase 27 P2-WFRUNNER — MasterController 工作流运行 service.

从 WorkflowMixin.run_workflow / resume_workflow (181 行) 拆出,
自含 budget + scheduler + state 生命周期管理. Mixin.run_workflow()
变 1 行 delegate: return self._get_runner().run(...).
"""
from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from lingwen_pipeline.master_controller import MasterController

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """MasterController 工作流运行 service (Phase 27 P2-WFRUNNER).

    封装 run_workflow / resume_workflow + 4 internal helpers.
    读 / 写 controller._state (WorkflowState) 直传 — 不持独立 state.
    """

    def __init__(self, controller: "MasterController") -> None:
        self._controller = controller

    def run(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """运行工作流 (Phase 27 P2-WFRUNNER).

        Returns:
            {summary, graph, executions, pending_decisions, incremental_backfill, memory_context}
        """
        controller = self._controller

        # Phase 8.8: 先写 budget, AgentComputeFn 才读得到
        controller._current_budget_usd = cost_budget_usd
        # Phase 8.12: run_id (uuid4 hex) + 持久化到 budget_service
        run_id = uuid.uuid4().hex
        controller._current_run_id = run_id
        # getattr 兜底 __new__ 构造的 test stub
        budget_service = getattr(controller, "budget_service", None)
        if budget_service is not None and cost_budget_usd is not None:
            budget_service.set(scope="run", usd=cost_budget_usd, run_id=run_id)
        try:
            raise NotImplementedError("Phase 27 Task 2-5: implementation in progress")
        finally:
            # Phase 8.8 / 8.12: reset 防跨 run leak
            controller._current_budget_usd = None
            controller._current_run_id = None
