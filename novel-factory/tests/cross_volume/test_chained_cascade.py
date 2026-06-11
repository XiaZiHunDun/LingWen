"""Phase 9.64 F55: chained cascade + parent_ripple_id tests."""
from __future__ import annotations

import pytest

from infra.cross_volume.chained_cascade import spawn_child_ripples
from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def chain_graph(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "chain.db")
    graph = CrossVolumeReferenceGraph(storage)
    for spec in [
        ("n1", 1, 1),
        ("n2", 2, 1),
        ("n3", 3, 1),
        ("n4", 3, 2),
    ]:
        graph.add_node(
            ReferenceNode(
                id=spec[0],
                volume=spec[1],
                chapter=spec[2],
                dimension="character",
            )
        )
    graph.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    graph.add_edge(ReferenceEdge(id="e23", from_node_id="n2", to_node_id="n3"))
    graph.add_edge(ReferenceEdge(id="e34", from_node_id="n3", to_node_id="n4"))
    storage._graph = graph
    return storage, graph


class TestChainedCascadeSpawn:
    def test_spawn_child_ripples_at_depth_2(self, chain_graph):
        storage, graph = chain_graph
        parent = CrossVolumeRipple(
            id="rip-parent",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
        cascaded = graph.trigger_cascade(parent, max_depth=3)
        assert cascaded.depth_reached >= 2

        child_ids = spawn_child_ripples(storage, graph, parent, cascaded)
        assert len(child_ids) >= 1
        for cid in child_ids:
            child = storage.get_ripple_by_id(cid)
            assert child is not None
            assert child.parent_ripple_id == "rip-parent"
            assert child.status == "pending"

    def test_spawn_skips_when_parent_is_already_child(self, chain_graph):
        storage, graph = chain_graph
        parent = CrossVolumeRipple(
            id="rip-child",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            parent_ripple_id="rip-root",
        )
        cascaded = graph.trigger_cascade(parent, max_depth=3)
        assert spawn_child_ripples(storage, graph, parent, cascaded) == []

    def test_append_ripple_integrated_spawn(self, chain_graph):
        storage, graph = chain_graph
        parent = CrossVolumeRipple(
            id="rip-integrated",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
        storage.append_ripple(parent)
        children = storage.get_child_ripples("rip-integrated")
        assert len(children) >= 1
        assert storage.count_child_ripples("rip-integrated") == len(children)

    def test_parent_ripple_id_column_migrated(self, tmp_path):
        db = tmp_path / "legacy.db"
        storage = RippleStorage(db_path=db)
        ripple = CrossVolumeRipple(
            id="rip-col",
            trigger_volume=1,
            trigger_chapter=5,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            parent_ripple_id="rip-parent-id",
        )
        storage.append_ripple(ripple)
        loaded = storage.get_ripple_by_id("rip-col")
        assert loaded.parent_ripple_id == "rip-parent-id"


class TestChainedCascadeAPIFields:
    def test_list_item_includes_parent_and_child_count(self, tmp_path):
        from dashboard.app import _ripple_to_list_item

        storage = RippleStorage(db_path=tmp_path / "api.db")
        parent = CrossVolumeRipple(
            id="rip-api-parent",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
        )
        child = CrossVolumeRipple(
            id="rip-api-child",
            trigger_volume=2,
            trigger_chapter=1,
            affected_nodes=("n2",),
            affected_edges=(),
            proposed_actions=(),
            parent_ripple_id="rip-api-parent",
        )
        storage.append_ripple(parent)
        storage.append_ripple(child)
        item = _ripple_to_list_item(parent, storage)
        assert item.child_count == 1
        child_item = _ripple_to_list_item(child, storage)
        assert child_item.parent_ripple_id == "rip-api-parent"
