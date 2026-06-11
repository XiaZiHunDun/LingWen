"""Phase 9.19 Task 2: max_depth query param for cascade endpoints."""
import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from infra.cross_volume.reference_graph import ReferenceEdge, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def cvg_storage(tmp_path):
    """Storage with ripple + multi-hop graph + persisted cascade."""
    storage = RippleStorage(db_path=tmp_path / "cvg.db")
    from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph
    g = CrossVolumeReferenceGraph(storage)
    # Chain: n1 → n2 → n3 (n3 is 2-hop from n1)
    g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n3", volume=3, chapter=1, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    g.add_edge(ReferenceEdge(id="e23", from_node_id="n2", to_node_id="n3"))
    storage._graph = g
    # Append ripple → fires cascade hook → persists cascade at depth=3
    ripple = CrossVolumeRipple(
        id="rip-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        status="pending",
    )
    storage.append_ripple(ripple)
    yield storage


@pytest.fixture
def client(cvg_storage, monkeypatch):
    """TestClient with _default_storage overridden to use cvg_storage."""
    from dashboard import app as app_module
    monkeypatch.setattr(app_module, "_default_storage", lambda: cvg_storage)
    app = create_app()
    return TestClient(app)


class TestCascadeEndpointMaxDepth:
    def test_max_depth_absent_returns_persisted(self, client):
        """No max_depth param → returns persisted cascade (backward compat)."""
        resp = client.get("/api/cvg/ripples/rip-1/cascade")
        assert resp.status_code == 200
        data = resp.json()
        assert data["depth_reached"] == 3  # persisted (append_ripple used default max_depth=3)

    def test_max_depth_0_returns_persisted(self, client):
        """max_depth=0 → returns persisted cascade."""
        resp = client.get("/api/cvg/ripples/rip-1/cascade?max_depth=0")
        assert resp.status_code == 200
        assert resp.json()["depth_reached"] == 3

    def test_max_depth_2_returns_2_hop(self, client):
        """max_depth=2 → re-run BFS, returns 2-hop nodes (n2 + n3)."""
        resp = client.get("/api/cvg/ripples/rip-1/cascade?max_depth=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["depth_reached"] == 2
        assert len(data["cascade_nodes"]) == 2

    def test_max_depth_11_rejected(self, client):
        """max_depth>10 → 400."""
        resp = client.get("/api/cvg/ripples/rip-1/cascade?max_depth=11")
        assert resp.status_code == 400

    def test_max_depth_neg_rejected(self, client):
        """max_depth<0 → 400."""
        resp = client.get("/api/cvg/ripples/rip-1/cascade?max_depth=-1")
        assert resp.status_code == 400
