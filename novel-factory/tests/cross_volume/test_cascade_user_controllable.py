"""Phase 9.19: user-controllable cascade depth tests."""
from __future__ import annotations

import pytest

from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def cvg_storage(tmp_path):
    """Storage with 1 ripple + graph that has 2-hop reachable nodes.
    Chain: n1 → n2 → n3 (n3 is 2-hop from n1).
    """
    storage = RippleStorage(db_path=tmp_path / "cvg.db")
    g = CrossVolumeReferenceGraph(storage)
    g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n3", volume=3, chapter=1, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    g.add_edge(ReferenceEdge(id="e23", from_node_id="n2", to_node_id="n3"))
    storage._graph = g
    ripple = CrossVolumeRipple(
        id="rip-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        status="pending",
    )
    storage.append_ripple(ripple)
    yield storage


class TestPreviewCascade:
    def test_preview_cascade_depth_1_returns_direct_neighbors(self, cvg_storage):
        """max_depth=1 → only n2 (1-hop from n1, not n3)."""
        cascaded = cvg_storage.preview_cascade("rip-1", max_depth=1)
        assert {n.id for n in cascaded.cascade_nodes} == {"n2"}
        assert cascaded.depth_reached == 1

    def test_preview_cascade_no_persist(self, cvg_storage):
        """Calling preview_cascade does NOT write to ripple_cascade table."""
        import sqlite3
        cvg_storage.preview_cascade("rip-1", max_depth=1)
        with cvg_storage._connect() as conn:
            rows = conn.execute("SELECT COUNT(*) FROM ripple_cascade").fetchone()[0]
        # append_ripple wrote 1 cascade row (depth=3 default); preview must NOT add more
        assert rows == 1
