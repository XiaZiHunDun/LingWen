"""Phase 9.41 F30: GET /api/cvg/reference-graph for ImpactGraph.vue."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph, ReferenceEdge, ReferenceNode
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def cvg_storage(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "cvg.db")
    graph = CrossVolumeReferenceGraph(storage)
    graph.add_node(
        ReferenceNode(
            id="n-char",
            dimension="character",
            volume=1,
            chapter=3,
            title="Hero",
            description="protagonist",
        )
    )
    graph.add_node(
        ReferenceNode(
            id="n-plot",
            dimension="plot_point",
            volume=2,
            chapter=5,
            title="Battle",
        )
    )
    graph.add_edge(
        ReferenceEdge(
            id="e1",
            from_node_id="n-char",
            to_node_id="n-plot",
            relationship_type="causes",
            weight=0.8,
        )
    )
    yield storage


@pytest.fixture
def client(cvg_storage, monkeypatch):
    from dashboard import app as app_module

    monkeypatch.setattr(app_module, "_default_storage", lambda: cvg_storage)
    return TestClient(create_app())


class TestReferenceGraphEndpoint:
    def test_returns_nodes_and_edges(self, client):
        resp = client.get("/api/cvg/reference-graph")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert data["total_node_count"] == 2
        assert data["total_edge_count"] == 1
        assert data["truncated"] is False
        assert data["nodes"][0]["dimension"] in ("character", "plot_point")

    def test_volume_filter(self, client):
        resp = client.get("/api/cvg/reference-graph?volume=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["volume"] == 1
        assert data["edges"] == []

    def test_dimension_filter(self, client):
        resp = client.get("/api/cvg/reference-graph?dimension=character")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["dimension"] == "character"

    def test_limit_truncates_nodes(self, client, cvg_storage):
        graph = CrossVolumeReferenceGraph(cvg_storage)
        for i in range(5):
            graph.add_node(
                ReferenceNode(
                    id=f"extra-{i}",
                    dimension="setting",
                    volume=1,
                    chapter=i,
                    title=f"S{i}",
                )
            )
        resp = client.get("/api/cvg/reference-graph?limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["nodes"]) == 3
        assert data["truncated"] is True
        assert data["total_node_count"] >= 3

    def test_empty_graph(self, client, tmp_path, monkeypatch):
        from dashboard import app as app_module

        empty = RippleStorage(db_path=tmp_path / "empty.db")
        monkeypatch.setattr(app_module, "_default_storage", lambda: empty)
        empty_client = TestClient(create_app())
        resp = empty_client.get("/api/cvg/reference-graph")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert data["total_node_count"] == 0
