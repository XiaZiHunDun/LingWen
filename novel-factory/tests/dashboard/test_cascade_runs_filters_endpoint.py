"""Phase 9.23: GET /api/ripples/cascade/{id}/runs filter query param tests (TDD).

覆盖 4 new Query() params: status (exposed from storage), min_depth, max_depth,
algorithm. 既 limit/offset 跟 Phase 9.20 既有 test 重叠, 不重复.

注: record_cascade_run 实际签名是 (ripple_id, cascaded: CascadedRipple,
max_depth, status="completed"), 走 CascadedRipple.bfs_algorithm_version
控制写入的 algorithm column. fixture 用 _make_cascaded helper 构造
(跟 tests/cross_volume/test_cascade_runs_filters.py 1:1 pattern).
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def _make_cascaded(ripple_id: str, depth: int, algorithm_version: str) -> CascadedRipple:
    """Build a CascadedRipple with given depth/algorithm (empty nodes/edges/actions)."""
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
def client_with_runs(tmp_path, monkeypatch):
    """Create FastAPI test client with seeded cascade_runs for rip-1.

    Seed: 4 runs spanning depths/algorithms/statuses
    (v2_weighted @ depth 2 completed, v1 @ depth 5 running, v2_weighted @ depth 8 completed, v1 @ depth 3 cancelled).
    """
    storage = RippleStorage(db_path=tmp_path / "test_endpoint.db")
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

    # run #1: v2_weighted @ depth 2, status=completed (default)
    storage.record_cascade_run(
        "rip-1",
        _make_cascaded("rip-1", depth=2, algorithm_version="v2_weighted"),
        max_depth=2,
    )
    # run #2: v1 @ depth 5, mark as running
    storage.record_cascade_run(
        "rip-1",
        _make_cascaded("rip-1", depth=5, algorithm_version="v1"),
        max_depth=5,
    )
    with storage._connect() as conn:
        conn.execute("UPDATE cascade_runs SET status='running' WHERE max_depth=5")
        conn.commit()
    # run #3: v2_weighted @ depth 8
    storage.record_cascade_run(
        "rip-1",
        _make_cascaded("rip-1", depth=3, algorithm_version="v2_weighted"),
        max_depth=8,
    )
    # run #4: v1 @ depth 3, mark as cancelled
    storage.record_cascade_run(
        "rip-1",
        _make_cascaded("rip-1", depth=0, algorithm_version="v1"),
        max_depth=3,
    )
    with storage._connect() as conn:
        conn.execute(
            "UPDATE cascade_runs SET status='cancelled', completed_at='2026-06-11T00:00:00Z' WHERE max_depth=3"
        )
        conn.commit()

    from dashboard import app as app_module
    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    return TestClient(create_app())


class TestGetCascadeRunsFiltersEndpoint:
    def test_status_filter_returns_only_matching(self, client_with_runs):
        """/runs?status=cancelled returns only cancelled runs."""
        response = client_with_runs.get("/api/ripples/cascade/rip-1/runs?status=cancelled")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 1
        assert runs[0]["status"] == "cancelled"
        assert runs[0]["max_depth"] == 3

    def test_min_depth_filter_returns_inclusive(self, client_with_runs):
        """/runs?min_depth=4 returns runs with max_depth >= 4."""
        response = client_with_runs.get("/api/ripples/cascade/rip-1/runs?min_depth=4")
        assert response.status_code == 200
        depths = sorted(r["max_depth"] for r in response.json())
        assert depths == [5, 8]

    def test_max_depth_filter_returns_inclusive(self, client_with_runs):
        """/runs?max_depth=5 returns runs with max_depth <= 5."""
        response = client_with_runs.get("/api/ripples/cascade/rip-1/runs?max_depth=5")
        assert response.status_code == 200
        depths = sorted(r["max_depth"] for r in response.json())
        assert depths == [2, 3, 5]

    def test_algorithm_filter_exact_match(self, client_with_runs):
        """/runs?algorithm=v1 returns only v1 runs."""
        response = client_with_runs.get("/api/ripples/cascade/rip-1/runs?algorithm=v1")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 2
        assert all(r["algorithm"] == "v1" for r in runs)

    def test_combined_status_min_max_depth_algorithm(self, client_with_runs):
        """/runs?status=cancelled&min_depth=2&max_depth=5&algorithm=v1 returns 1 row."""
        response = client_with_runs.get(
            "/api/ripples/cascade/rip-1/runs?status=cancelled&min_depth=2&max_depth=5&algorithm=v1"
        )
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 1
        assert runs[0]["status"] == "cancelled"
        assert runs[0]["max_depth"] == 3
        assert runs[0]["algorithm"] == "v1"
