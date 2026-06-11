"""Phase 9.32 F16: configurable max_nodes_cap for cascade BFS."""
import tempfile
from pathlib import Path

import pytest

from infra.cross_volume.reference_graph import (
    DEFAULT_MAX_NODES_CAP,
    MAX_NODES_CAP_UPPER,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def _star_graph(storage: RippleStorage, neighbor_count: int = 150) -> CrossVolumeReferenceGraph:
    g = CrossVolumeReferenceGraph(storage)
    g.add_node(ReferenceNode(id="trigger", volume=1, chapter=1, dimension="character"))
    for i in range(neighbor_count):
        nid = f"n_{i:03d}"
        g.add_node(ReferenceNode(id=nid, volume=2, chapter=1, dimension="character"))
        g.add_edge(
            ReferenceEdge(id=f"e_{i:03d}", from_node_id="trigger", to_node_id=nid, weight=0.5)
        )
    return g


def _star_ripple() -> CrossVolumeRipple:
    return CrossVolumeRipple(
        id="rip-cap",
        trigger_volume=1,
        trigger_chapter=1,
        affected_nodes=("trigger",),
        affected_edges=(),
        proposed_actions=(),
    )


class TestTriggerCascadeMaxNodesCap:
    def test_default_cap_still_100(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "cap.db")
            g = _star_graph(storage)
            cascaded = g.trigger_cascade(_star_ripple())
            assert len(cascaded.cascade_nodes) <= DEFAULT_MAX_NODES_CAP

    def test_custom_cap_200_collects_all_150_neighbors(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "cap.db")
            g = _star_graph(storage, neighbor_count=150)
            cascaded = g.trigger_cascade(_star_ripple(), max_depth=1, max_nodes_cap=200)
            assert len(cascaded.cascade_nodes) == 150

    def test_invalid_max_nodes_cap_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "cap.db")
            g = _star_graph(storage, neighbor_count=5)
            with pytest.raises(ValueError, match="max_nodes_cap"):
                g.trigger_cascade(_star_ripple(), max_nodes_cap=0)
            with pytest.raises(ValueError, match="max_nodes_cap"):
                g.trigger_cascade(_star_ripple(), max_nodes_cap=MAX_NODES_CAP_UPPER + 1)


class TestPreviewCascadeMaxNodesCap:
    def test_preview_cascade_forwards_max_nodes_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "cap.db")
            g = _star_graph(storage, neighbor_count=120)
            storage._graph = g
            storage.append_ripple(_star_ripple())
            cascaded = storage.preview_cascade("rip-cap", max_depth=1, max_nodes_cap=200)
            assert len(cascaded.cascade_nodes) == 120
