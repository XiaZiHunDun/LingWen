"""Phase 9.21 Task 2: POST cascade cancel endpoint."""
import pytest
from fastapi.testclient import TestClient

from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def client_with_runs(tmp_path, monkeypatch):
    """TestClient + storage with 1 persisted cascade run for rip-1."""
    storage = RippleStorage(db_path=tmp_path / "cascade_cancel_endpoint.db")
    g = CrossVolumeReferenceGraph(storage)
    g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = g
    ripple = CrossVolumeRipple(
        id="rip-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=("n1",), affected_edges=(), proposed_actions=(), status="pending",
    )
    storage.append_ripple(ripple)
    cascaded = storage.preview_cascade("rip-1", max_depth=2)
    run_id = storage.record_cascade_run("rip-1", cascaded, max_depth=2)

    from dashboard import app as app_module
    from dashboard.app import create_app

    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    yield TestClient(create_app()), storage, run_id


class TestCascadeCancelEndpoint:
    def test_post_cancel_endpoint_returns_cancelled_run(self, client_with_runs):
        """POST /cancel → 200 + CascadeRunResponse(status='cancelled')."""
        client, storage, run_id = client_with_runs
        resp = client.post(
            f"/api/ripples/cascade/rip-1/runs/{run_id}/cancel",
            json={"reason": "误触"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["id"] == run_id

    def test_post_cancel_endpoint_returns_404_for_missing_run(self, client_with_runs):
        """POST /cancel on unknown run_id → 404."""
        client, _, _ = client_with_runs
        resp = client.post(
            "/api/ripples/cascade/rip-1/runs/999/cancel", json={}
        )
        assert resp.status_code == 404
