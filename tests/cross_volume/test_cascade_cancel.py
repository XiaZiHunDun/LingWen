"""Phase 9.21 Task 1: cancel_cascade_run storage method.

Tests: cancel flips status to 'cancelled' + returns True /
2nd cancel idempotent returns False.
"""
import pytest

from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage_with_runs(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "cascade_cancel.db")
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
    yield storage, run_id


class TestCascadeCancel:
    def test_cancel_cascade_run_marks_status_and_returns_true(self, storage_with_runs):
        storage, run_id = storage_with_runs
        flipped = storage.cancel_cascade_run(run_id, reason="误触")
        assert flipped is True
        run = storage.get_cascade_run_by_id(run_id)
        assert run.status == "cancelled"

    def test_cancel_cascade_run_idempotent_returns_false_for_already_cancelled(self, storage_with_runs):
        storage, run_id = storage_with_runs
        assert storage.cancel_cascade_run(run_id) is True
        assert storage.cancel_cascade_run(run_id) is False
