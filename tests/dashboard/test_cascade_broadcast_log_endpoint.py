"""Phase 9.44 F33: GET /api/ripples/cascade/{id}/broadcast-log endpoint tests."""
from __future__ import annotations

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
    storage = RippleStorage(db_path=tmp_path / "broadcast_log_api.db")
    graph = CrossVolumeReferenceGraph(storage)
    graph.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    graph.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    graph.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = graph
    ripple = CrossVolumeRipple(
        id="rip-1",
        trigger_volume=1,
        trigger_chapter=1,
        affected_nodes=("n1",),
        affected_edges=(),
        proposed_actions=(),
        status="pending",
    )
    storage.append_ripple(ripple)

    from dashboard import app as app_module
    from dashboard.app import create_app

    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    yield TestClient(create_app()), storage


class TestCascadeBroadcastLogEndpoint:
    def test_get_broadcast_log_returns_history(self, client_with_storage):
        client, storage = client_with_storage
        storage.append_cascade_broadcast_log("rip-1", latency_ms=21)
        storage.append_cascade_broadcast_log("rip-1", latency_ms=42)
        resp = client.get("/api/ripples/cascade/rip-1/broadcast-log")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        assert data[0]["latency_ms"] == 42
        assert data[0]["ripple_id"] == "rip-1"
        assert "created_at" in data[0]

    def test_get_broadcast_log_respects_limit_offset(self, client_with_storage):
        client, storage = client_with_storage
        for ms in (11, 22, 33):
            storage.append_cascade_broadcast_log("rip-1", latency_ms=ms)
        resp = client.get("/api/ripples/cascade/rip-1/broadcast-log?limit=1&offset=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_get_broadcast_log_empty_for_unknown_ripple(self, client_with_storage):
        client, _ = client_with_storage
        resp = client.get("/api/ripples/cascade/unknown/broadcast-log")
        assert resp.status_code == 200
        assert resp.json() == []
