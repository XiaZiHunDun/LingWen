"""Phase 9.68 F60: incremental_backfill field in workflow API responses."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi.testclient import TestClient

from dashboard.app import create_app
from dashboard.protocols import MasterControllerAdapter, _workflow_result_to_dict
from infra.agent_system.decision_queue import HumanDecisionQueue
from infra.cross_volume.backfill import BackfillStats


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


class _BackfillStubController:
    """Minimal MC stub returning incremental_backfill stats."""

    def __init__(self, state_dir: str) -> None:
        self._queue = HumanDecisionQueue(state_dir=state_dir)
        self._last_workflow_status: Optional[dict] = None

    def list_pending_decisions(self) -> list[dict]:
        return [d.to_dict() for d in self._queue.pending()]

    def get_decision_queue(self) -> HumanDecisionQueue:
        return self._queue

    def resolve_decision(self, decision_id: str, option: str, resolved_by: str = "human"):
        d = self._queue.resolve(decision_id, option, resolved_by=resolved_by)
        self._queue.save()
        return d

    def defer_decision(self, decision_id: str, reason: str = ""):
        d = self._queue.defer(decision_id, reason=reason)
        self._queue.save()
        return d

    def cancel_decision(self, decision_id: str, reason: str = ""):
        d = self._queue.cancel(decision_id)
        self._queue.save()
        return d

    def run_workflow(self, workflow_name: str, **kwargs) -> dict[str, Any]:
        summary = _FakeSummary(completed=3, steps=3, node_count=3, paused=False)
        stats = BackfillStats(
            character_count=1,
            foreshadow_count=0,
            setting_count=0,
            plot_point_count=0,
            total_count=1,
            elapsed_s=0.1,
            dry_run=False,
            nodes_written=1,
            nodes_skipped=0,
        )
        self._last_workflow_status = {
            "is_active": True,
            "workflow_name": workflow_name,
            "completed": summary.completed,
            "failed": summary.failed,
            "paused": summary.paused,
            "paused_nodes": [],
            "node_count": summary.node_count,
            "steps": summary.steps,
            "pending_decisions": [],
        }
        return {
            "summary": summary,
            "graph": None,
            "executions": {},
            "pending_decisions": [],
            "workflow_name": workflow_name,
            "incremental_backfill": stats,
        }

    def resume_workflow(self, decision_id: str, option: str, resolved_by: str = "human"):
        raise RuntimeError("not used in this test")

    def get_active_workflow_status(self, since=None) -> dict:
        if self._last_workflow_status is None:
            return {"is_active": False, "workflow_name": None, "pending_decisions": []}
        return self._last_workflow_status


class TestWorkflowResultSerialization:
    def test_workflow_result_to_dict_includes_backfill(self):
        stats = BackfillStats(
            character_count=0,
            foreshadow_count=0,
            setting_count=0,
            plot_point_count=0,
            total_count=0,
            elapsed_s=0.0,
            dry_run=True,
            nodes_written=0,
            nodes_skipped=0,
        )
        payload = _workflow_result_to_dict(
            {"summary": None, "executions": {}, "incremental_backfill": stats}
        )
        assert payload["incremental_backfill"]["dry_run"] is True
        assert payload["incremental_backfill"]["nodes_written"] == 0

    def test_workflow_result_to_dict_null_backfill(self):
        payload = _workflow_result_to_dict({"summary": None, "executions": {}})
        assert payload["incremental_backfill"] is None


class TestWorkflowIncrementalBackfillApi:
    def test_run_workflow_exposes_incremental_backfill(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        stub = _BackfillStubController(state_dir=str(state_dir))
        adapter = MasterControllerAdapter(stub)
        app = create_app(db_path=tmp_path / "rp.db", master_controller=adapter)
        client = TestClient(app)

        response = client.post(
            "/api/workflows/run",
            json={"workflow_name": "novel_writing", "initial_inputs": {"chapter_num": 5}},
        )
        assert response.status_code == 200
        body = response.json()
        assert "incremental_backfill" in body
        bf = body["incremental_backfill"]
        assert bf is not None
        assert bf["nodes_written"] == 1
        assert bf["total_count"] == 1
        assert bf["dry_run"] is False
