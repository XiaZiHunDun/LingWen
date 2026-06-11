"""Phase 9.23: RippleStorage.get_cascade_runs filter param tests (TDD).

覆盖 3 new filter params (min_depth, max_depth, algorithm) + 1 combined
跟 status. 既 status filter 跟 Phase 9.20 既有 test 重叠, 不重复测试.

注: record_cascade_run 实际签名是 (ripple_id, cascaded: CascadedRipple,
max_depth, status="completed"), 走 CascadedRipple.bfs_algorithm_version
控制写入的 algorithm column. fixture 用 CascadedRipple(algorithm_version=...)
构造, 跟既 record_cascade_run 1:1 pattern.
"""
import pytest

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
def storage_with_runs(tmp_path):
    """Create temp storage with 4 cascade_runs spanning depths/algorithms/statuses.

    Seed: ripple-1 with 4 runs (v2_weighted @ depth 2 completed, v1 @ depth 5 running,
    v2_weighted @ depth 8 completed, v1 @ depth 3 cancelled).
    """
    db_path = tmp_path / "test.db"
    storage = RippleStorage(db_path=db_path)
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
    # run #2: v1 @ depth 5, mark as running (open status)
    storage.record_cascade_run(
        "rip-1",
        _make_cascaded("rip-1", depth=5, algorithm_version="v1"),
        max_depth=5,
    )
    with storage._connect() as conn:
        # running status: completed_at placeholder (datetime.fromisoformat 需 valid ISO)
        conn.execute(
            "UPDATE cascade_runs SET status='running' WHERE max_depth=5"
        )
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
    return storage


class TestGetCascadeRunsFilters:
    def test_min_depth_filter_includes_specified_and_above(self, storage_with_runs):
        """min_depth=4 returns runs with max_depth >= 4 (run @5, run @8)."""
        runs = storage_with_runs.get_cascade_runs("rip-1", min_depth=4)
        depths = sorted(r.max_depth for r in runs)
        assert depths == [5, 8]

    def test_max_depth_filter_includes_specified_and_below(self, storage_with_runs):
        """max_depth=5 returns runs with max_depth <= 5 (run @2, run @3, run @5)."""
        runs = storage_with_runs.get_cascade_runs("rip-1", max_depth=5)
        depths = sorted(r.max_depth for r in runs)
        assert depths == [2, 3, 5]

    def test_algorithm_filter_exact_match(self, storage_with_runs):
        """algorithm='v1' returns only v1 runs (2 rows: max_depth=5 running, max_depth=3 cancelled)."""
        runs = storage_with_runs.get_cascade_runs("rip-1", algorithm="v1")
        algorithms = sorted({r.algorithm for r in runs})
        assert algorithms == ["v1"]
        assert len(runs) == 2

    def test_combined_status_and_min_depth(self, storage_with_runs):
        """status='cancelled' + min_depth=2 returns only cancelled runs with max_depth >= 2."""
        runs = storage_with_runs.get_cascade_runs("rip-1", status="cancelled", min_depth=2)
        assert len(runs) == 1
        assert runs[0].max_depth == 3
        assert runs[0].status == "cancelled"
