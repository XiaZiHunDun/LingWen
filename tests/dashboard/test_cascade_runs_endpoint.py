"""Phase 9.20 Task 2: cascade runs endpoint + ?persist=true query param."""
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
def client_with_storage(tmp_path, monkeypatch):
    """TestClient with _default_storage overridden to use fresh storage."""
    storage = RippleStorage(db_path=tmp_path / "cascade_runs_endpoint.db")
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

    from dashboard import app as app_module
    from dashboard.app import create_app

    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    yield TestClient(create_app()), storage


class TestCascadeRunsEndpoint:
    def test_get_cascade_runs_endpoint_returns_history(self, client_with_storage):
        """GET /api/ripples/cascade/{id}/runs → list."""
        client, storage = client_with_storage
        cascaded = storage.preview_cascade("rip-1", max_depth=2)
        storage.record_cascade_run("rip-1", cascaded, max_depth=2)
        storage.record_cascade_run("rip-1", cascaded, max_depth=3)
        resp = client.get("/api/ripples/cascade/rip-1/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_cascade_runs_endpoint_respects_limit_offset(self, client_with_storage):
        """limit=1 offset=1 → 1 row (the 2nd newest)."""
        client, storage = client_with_storage
        cascaded = storage.preview_cascade("rip-1", max_depth=2)
        storage.record_cascade_run("rip-1", cascaded, max_depth=2)
        storage.record_cascade_run("rip-1", cascaded, max_depth=3)
        storage.record_cascade_run("rip-1", cascaded, max_depth=5)
        resp = client.get("/api/ripples/cascade/rip-1/runs?limit=1&offset=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_persist_true_creates_run_and_returns_cascade_run(self, client_with_storage):
        """GET ?persist=true&max_depth=2 → CascadeRunResponse with id."""
        client, _ = client_with_storage
        resp = client.get("/api/ripples/cascade/rip-1?persist=true&max_depth=2")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["ripple_id"] == "rip-1"
        assert data["max_depth"] == 2
        assert data["status"] == "completed"

    def test_persist_false_returns_existing_preview_path(self, client_with_storage):
        """Phase 9.19 path, persist default False, behavior unchanged.

        既 path returns CascadeResponse (trigger_ripple_id, no 'id' / 'ripple_id' / 'status').
        """
        client, _ = client_with_storage
        resp = client.get("/api/ripples/cascade/rip-1?max_depth=2")
        assert resp.status_code == 200
        # CascadeResponse has trigger_ripple_id not ripple_id, no id, no status
        data = resp.json()
        assert "id" not in data
        assert "ripple_id" not in data
        assert "status" not in data
        assert "trigger_ripple_id" in data

    def test_persist_true_for_missing_ripple_returns_404(self, client_with_storage):
        """GET ?persist=true on unknown ripple → 404."""
        client, _ = client_with_storage
        resp = client.get("/api/ripples/cascade/unknown?persist=true&max_depth=2")
        assert resp.status_code == 404
