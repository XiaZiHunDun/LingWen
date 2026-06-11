"""Phase 9.42 F31: lazy per-volume graph load + query_impact cache integration."""
from __future__ import annotations

from infra.cross_volume import CrossVolumeReferenceGraph, ReferenceEdge, ReferenceNode
from infra.cross_volume.perf import load_volume_slice
from infra.cross_volume.storage import RippleStorage


class TestLazyVolumeLoad:
    def test_lazy_graph_starts_empty(self, tmp_path):
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage, lazy=True)
        assert len(graph) == 0
        assert graph.loaded_volumes == set()

    def test_load_volume_slice_hydrates_one_volume(self, tmp_path):
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        n_v1 = ReferenceNode(dimension="character", volume=1, chapter=1, title="V1", description="")
        n_v2 = ReferenceNode(dimension="character", volume=2, chapter=1, title="V2", description="")
        storage.append_node(n_v1)
        storage.append_node(n_v2)
        storage.append_edge(
            ReferenceEdge(from_node_id=n_v1.id, to_node_id=n_v2.id, relationship_type="mentions")
        )

        graph = CrossVolumeReferenceGraph(storage=storage, lazy=True)
        load_volume_slice(graph, volume=1)

        assert len(graph) == 2  # v1 node + v2 endpoint pulled in via edge
        assert 1 in graph.loaded_volumes
        assert graph.get_node(n_v1.id) is not None
        assert graph.get_node(n_v2.id) is not None

    def test_query_impact_filters_cross_volume_edges(self, tmp_path):
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)

        n_v1 = ReferenceNode(dimension="character", volume=1, chapter=1, title="Old", description="")
        n_v2 = ReferenceNode(dimension="character", volume=2, chapter=1, title="Mid", description="")
        n_v3 = ReferenceNode(dimension="character", volume=3, chapter=1, title="New", description="")
        for n in (n_v1, n_v2, n_v3):
            graph.add_node(n)
        e_old = ReferenceEdge(from_node_id=n_v1.id, to_node_id=n_v3.id, relationship_type="mentions")
        e_same = ReferenceEdge(from_node_id=n_v2.id, to_node_id=n_v3.id, relationship_type="evolves")
        graph.add_edge(e_old)
        graph.add_edge(e_same)

        impact = graph.query_impact(n_v3.id, from_volume=2)
        assert {e.id for e in impact} == {e_old.id}

    def test_query_impact_cache_hit_on_repeat(self, tmp_path):
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        n_a = ReferenceNode(dimension="character", volume=1, chapter=1, title="A", description="")
        n_b = ReferenceNode(dimension="character", volume=2, chapter=1, title="B", description="")
        graph.add_node(n_a)
        graph.add_node(n_b)
        graph.add_edge(ReferenceEdge(from_node_id=n_a.id, to_node_id=n_b.id))

        first = graph.query_impact(n_b.id, from_volume=2)
        second = graph.query_impact(n_b.id, from_volume=2)
        assert first == second
        stats = graph.impact_cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
