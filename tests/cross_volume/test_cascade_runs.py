"""Phase 9.20 Task 1: cascade_runs table + 3 storage methods.

Tests: record_cascade_run (returns int>0) / get_cascade_runs (latest first +
status filter) / get_cascade_run_by_id (None for missing).
"""
import pytest

from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import CascadeRun, RippleStorage


@pytest.fixture
def storage_with_ripple(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "cascade_runs.db")
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
    yield storage


class TestCascadeRuns:
    def test_record_cascade_run_returns_run_id(self, storage_with_ripple):
        cascaded = storage_with_ripple.preview_cascade("rip-1", max_depth=2)
        run_id = storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=2)
        assert isinstance(run_id, int)
        assert run_id > 0

    def test_get_cascade_runs_returns_latest_first(self, storage_with_ripple):
        cascaded = storage_with_ripple.preview_cascade("rip-1", max_depth=2)
        id1 = storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=2)
        id2 = storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=3)
        id3 = storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=5)
        runs = storage_with_ripple.get_cascade_runs("rip-1")
        assert len(runs) == 3
        assert [r.id for r in runs] == [id3, id2, id1]

    def test_get_cascade_runs_filter_by_status(self, storage_with_ripple):
        cascaded = storage_with_ripple.preview_cascade("rip-1", max_depth=2)
        storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=2, status="completed")
        storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=3, status="completed")
        storage_with_ripple.record_cascade_run("rip-1", cascaded, max_depth=5, status="cancelled")
        completed = storage_with_ripple.get_cascade_runs("rip-1", status="completed")
        assert len(completed) == 2
        assert all(r.status == "completed" for r in completed)

    def test_get_cascade_run_by_id_returns_none_for_missing(self, storage_with_ripple):
        assert storage_with_ripple.get_cascade_run_by_id(999) is None
