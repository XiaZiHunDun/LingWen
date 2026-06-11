"""Phase 9.46 F35: global cascade_runs list storage + API tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def _make_cascaded(ripple_id: str, depth: int, algorithm_version: str) -> CascadedRipple:
    from datetime import datetime, timezone

    return CascadedRipple(
        trigger_ripple_id=ripple_id,
        cascade_nodes=(),
        cascade_edges=(),
        cascade_actions=(),
        depth_reached=depth,
        generated_at=datetime.now(timezone.utc).isoformat(),
        bfs_algorithm_version=algorithm_version,
    )


@pytest.fixture
def storage_with_multi_ripple_runs(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "global_runs.db")
    graph = CrossVolumeReferenceGraph(storage)
    graph.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    graph.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    graph.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = graph
    for ripple_id in ("rip-a", "rip-b"):
        storage.append_ripple(
            CrossVolumeRipple(
                id=ripple_id,
                trigger_volume=1,
                trigger_chapter=1,
                affected_nodes=("n1",),
                affected_edges=(),
                proposed_actions=(),
                status="pending",
            )
        )
        storage.record_cascade_run(
            ripple_id,
            _make_cascaded(ripple_id, depth=2, algorithm_version="v2_weighted"),
            max_depth=2,
        )
        storage.record_cascade_run(
            ripple_id,
            _make_cascaded(ripple_id, depth=3, algorithm_version="v1"),
            max_depth=5,
        )
    return storage


class TestListAllCascadeRunsStorage:
    def test_list_all_returns_cross_ripple_rows(self, storage_with_multi_ripple_runs):
        runs = storage_with_multi_ripple_runs.list_all_cascade_runs()
        assert len(runs) == 4
        ripple_ids = {r.ripple_id for r in runs}
        assert ripple_ids == {"rip-a", "rip-b"}

    def test_list_all_filter_by_ripple_id(self, storage_with_multi_ripple_runs):
        runs = storage_with_multi_ripple_runs.list_all_cascade_runs(ripple_id="rip-a")
        assert len(runs) == 2
        assert all(r.ripple_id == "rip-a" for r in runs)

    def test_list_all_filter_by_algorithm(self, storage_with_multi_ripple_runs):
        runs = storage_with_multi_ripple_runs.list_all_cascade_runs(algorithm="v1")
        assert len(runs) == 2
        assert all(r.algorithm == "v1" for r in runs)


@pytest.fixture
def client_with_storage(storage_with_multi_ripple_runs, monkeypatch):
    from dashboard import app as app_module
    from dashboard.app import create_app

    monkeypatch.setattr(app_module, "_default_storage", lambda: storage_with_multi_ripple_runs)
    yield TestClient(create_app()), storage_with_multi_ripple_runs


class TestGlobalCascadeRunsEndpoint:
    def test_get_all_cascade_runs_endpoint(self, client_with_storage):
        client, _ = client_with_storage
        resp = client.get("/api/cascade/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4

    def test_get_all_cascade_runs_filter_ripple_id(self, client_with_storage):
        client, _ = client_with_storage
        resp = client.get("/api/cascade/runs?ripple_id=rip-b")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(row["ripple_id"] == "rip-b" for row in data)

    def test_get_all_cascade_runs_respects_limit(self, client_with_storage):
        client, _ = client_with_storage
        resp = client.get("/api/cascade/runs?limit=1")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
