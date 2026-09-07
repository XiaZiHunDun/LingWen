"""MasterController Orchestrator 薄代理 Mixin (Phase 31 ARCHDEBT-MINI).

Consolidates the 4 (formerly "5") 1-line forwarders to TaskOrchestrator.
Pure passthrough — zero added logic. Each method's signature stays identical
to TaskOrchestrator.<method> to preserve type contracts.

Required host attributes:
- self._orchestrator: TaskOrchestrator (injected by MasterController.__init__)

History:
- Phase 15.0 P3-SPLIT: orchestrator proxies bundled in WorkflowMixin.
- Phase 27 P2-WFRUNNER: count reduced from 5 to 4 when WorkflowRunner.run_workflow
  / resume_workflow split off (those became runner delegates, not orchestrator
  proxies). Docstring "5 薄代理" became stale; corrected to "4" in Phase 31.
- Phase 31 ARCHDEBT-MINI: extracted to dedicated mixin for single-responsibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from lingwen_core.agents.orchestration.task_orchestrator import TaskOrchestrator


class OrchestratorProxyMixin:
    """4 thin orchestrator proxies (Phase 31).

    Each method delegates 1:1 to self._orchestrator.<method>(...). Signatures
    must match TaskOrchestrator.<method> exactly. Add new proxies here only
    if they are 1-line forwarders with no added logic.
    """

    def advance_step(
        self, target_step: str, context: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """推进工作流步骤 (thin proxy → TaskOrchestrator.advance_step)."""
        return self._orchestrator.advance_step(target_step, context)

    def dispatch_task(
        self,
        task_name: str,
        agent: str,
        context: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """分发任务 (thin proxy → TaskOrchestrator.dispatch_task)."""
        return self._orchestrator.dispatch_task(task_name, agent, context, priority)

    def verify_task(
        self, task_id: str, result: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """验证任务完成 (thin proxy → TaskOrchestrator.verify_task)."""
        return self._orchestrator.verify_task(task_id, result)

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态 (thin proxy → TaskOrchestrator.get_workflow_status)."""
        return self._orchestrator.get_workflow_status()
