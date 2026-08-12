"""Phase 9.65 F56: lightweight MasterControllerLike stub for Playwright e2e.

Avoids real MasterController / API keys; decisions API reads the same
infra/.state/decisions.json that e2e_seed writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from infra.agent_system.decision_queue import HumanDecision, HumanDecisionQueue


@dataclass
class _FakeSummary:
    completed: int = 0
    failed: int = 0
    total_cost_tokens: int = 0
    backtrack_count: int = 0
    steps: int = 0
    node_count: int = 0
    paused: bool = False
    paused_nodes: tuple = ()


class E2EStubController:
    """Minimal MasterControllerLike for live-backend Playwright e2e."""

    def __init__(self, state_dir: str) -> None:
        self._queue = HumanDecisionQueue(state_dir=state_dir)
        self._last_workflow_status: Optional[dict[str, Any]] = None

    def _sync_queue_from_disk(self) -> None:
        """Reload decisions.json so CLI e2e_seed reset/ensure is visible without restart."""
        if self._queue._state_path is not None:
            self._queue._load()

    def list_pending_decisions(self) -> list[dict]:
        self._sync_queue_from_disk()
        return [d.to_dict() for d in self._queue.pending()]

    def get_decision_queue(self) -> HumanDecisionQueue:
        self._sync_queue_from_disk()
        return self._queue

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> HumanDecision:
        d = self._queue.resolve(decision_id, option, resolved_by=resolved_by)
        self._queue.save()
        return d

    def defer_decision(self, decision_id: str, reason: str = "") -> HumanDecision:
        d = self._queue.defer(decision_id, reason=reason)
        self._queue.save()
        return d

    def cancel_decision(self, decision_id: str, reason: str = "") -> HumanDecision:
        d = self._queue.cancel(decision_id)
        self._queue.save()
        return d

    def run_workflow(self, workflow_name: str, **kwargs: Any) -> dict:
        summary = _FakeSummary(completed=1, steps=1, node_count=1)
        self._last_workflow_status = {
            "is_active": True,
            "workflow_name": workflow_name,
            "completed": summary.completed,
            "failed": summary.failed,
            "paused": summary.paused,
            "paused_nodes": list(summary.paused_nodes),
            "node_count": summary.node_count,
            "steps": summary.steps,
            "pending_decisions": [],
        }
        return {"summary": summary, "graph": None, "executions": {}, "pending_decisions": []}

    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> dict:
        if self._last_workflow_status is None:
            raise RuntimeError("no active workflow")
        d = self.resolve_decision(decision_id, option, resolved_by=resolved_by)
        return {"summary": _FakeSummary(), "graph": None, "executions": {}, "pending_decisions": [], "resolved_decision": d}

    def get_active_workflow_status(self, since=None) -> dict:
        if self._last_workflow_status is None:
            return {"is_active": False, "workflow_name": None, "pending_decisions": []}
        return self._last_workflow_status
