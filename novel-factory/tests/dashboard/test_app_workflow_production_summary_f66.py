"""Phase 9.74 F66: GET /api/workflows/active exposes production_summary."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app
from dashboard.protocols import MasterControllerAdapter
from infra.agent_system import master_controller as mc_mod
from infra.got.data_structures import NodeExecution, NodeStatus


def _make_master_with_production_cache(tmp_path: Path):
    master = mc_mod.MasterController.__new__(mc_mod.MasterController)
    now = datetime.now(timezone.utc)

    class _StubGraph:
        def node_ids(self):
            return ["emit_chapter"]

        def has_execution(self, nid):
            return True

        def get_execution(self, nid):
            return NodeExecution(
                node_id=nid,
                status=NodeStatus.COMPLETED,
                started_at=now,
                finished_at=now,
                output={"chapter_num": 360},
            )

        def get_node(self, nid):
            return None

    class _StubSummary:
        steps = 7

    class _StubScheduler:
        _summary = _StubSummary()

    master._last_scheduler = _StubScheduler()
    master._last_graph = _StubGraph()
    master._last_workflow_name = "novel_writing"
    master._last_initial_inputs = {"chapter_num": 360}
    master._last_memory_context = {"source": "stub"}
    master._last_incremental_backfill = {"nodes_written": 2, "total_count": 2, "elapsed_s": 0.1}
    return master


class TestWorkflowProductionSummaryF66:
    def test_active_workflow_includes_production_summary(self, tmp_path: Path) -> None:
        master = _make_master_with_production_cache(tmp_path)
        adapter = MasterControllerAdapter(master)
        app = create_app(db_path=tmp_path / "rp.db", master_controller=adapter)
        client = TestClient(app)

        response = client.get("/api/workflows/active")
        assert response.status_code == 200
        body = response.json()
        assert body["production_summary"] is not None
        assert body["production_summary"]["chapter_num"] == 360
        assert body["production_summary"]["memory_context_source"] == "stub"
        assert body["production_summary"]["emit_chapter_completed"] is True
        assert body["incremental_backfill"]["nodes_written"] == 2
