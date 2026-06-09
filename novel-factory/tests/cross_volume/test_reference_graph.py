# tests/cross_volume/test_reference_graph.py
"""Phase 9.10: CrossVolumeReferenceGraph + ReferenceNode + ReferenceEdge tests.

TDD: 这些测试在 step 1 阶段会全部 FAIL (ImportError), 在 Task 3 (CVG impl) 后通过.
"""
import pytest

from infra.cross_volume import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "ripple.db")


@pytest.fixture
def graph(storage):
    return CrossVolumeReferenceGraph(storage=storage)


class TestReferenceGraph:
    def test_add_and_get_node(self, graph):
        node = ReferenceNode(dimension="character", volume=1, chapter=3,
                             title="李青云", description="主角",
                             payload={"name": "李青云", "role": "主角"})
        graph.add_node(node)
        got = graph.get_node(node.id)
        assert got is not None
        assert got.id == node.id
        assert got.dimension == "character"
        assert got.title == "李青云"

    def test_add_node_rejects_duplicate_id(self, graph):
        node = ReferenceNode(dimension="character", volume=1, chapter=1,
                             title="A", description="")
        graph.add_node(node)
        with pytest.raises(ValueError, match="duplicate node id"):
            graph.add_node(node)  # same id → raise

    def test_add_edge_validates_fk(self, graph):
        node_a = ReferenceNode(dimension="character", volume=1, chapter=1,
                                title="A", description="")
        node_b = ReferenceNode(dimension="foreshadow", volume=2, chapter=5,
                                title="B", description="")
        graph.add_node(node_a)
        graph.add_node(node_b)
        # Missing FK
        with pytest.raises(ValueError, match="from_node_id not found"):
            graph.add_edge(ReferenceEdge(from_node_id="nonexistent", to_node_id=node_b.id))

    def test_get_nodes_by_volume_filter(self, graph):
        n1 = ReferenceNode(dimension="character", volume=1, chapter=1, title="C1", description="")
        n2 = ReferenceNode(dimension="character", volume=1, chapter=2, title="C2", description="")
        n3 = ReferenceNode(dimension="character", volume=2, chapter=1, title="C3", description="")
        for n in (n1, n2, n3):
            graph.add_node(n)
        vol1_nodes = graph.get_nodes_by_volume(1)
        assert len(vol1_nodes) == 2
        assert {n.id for n in vol1_nodes} == {n1.id, n2.id}

    def test_get_nodes_by_dimension_filter(self, graph):
        n_char = ReferenceNode(dimension="character", volume=1, chapter=1, title="C", description="")
        n_fore = ReferenceNode(dimension="foreshadow", volume=1, chapter=2, title="F", description="")
        n_set = ReferenceNode(dimension="setting", volume=1, chapter=3, title="S", description="")
        n_plot = ReferenceNode(dimension="plot_point", volume=1, chapter=4, title="P", description="")
        for n in (n_char, n_fore, n_set, n_plot):
            graph.add_node(n)
        char_nodes = graph.get_nodes_by_dimension("character")
        assert len(char_nodes) == 1
        assert char_nodes[0].id == n_char.id

    def test_get_neighbors_returns_connected(self, graph):
        n_a = ReferenceNode(dimension="character", volume=1, chapter=1, title="A", description="")
        n_b = ReferenceNode(dimension="foreshadow", volume=1, chapter=2, title="B", description="")
        n_c = ReferenceNode(dimension="setting", volume=1, chapter=3, title="C", description="")
        for n in (n_a, n_b, n_c):
            graph.add_node(n)
        graph.add_edge(ReferenceEdge(from_node_id=n_a.id, to_node_id=n_b.id, relationship_type="mentions"))
        graph.add_edge(ReferenceEdge(from_node_id=n_a.id, to_node_id=n_c.id, relationship_type="appears_with"))
        neighbors = graph.get_neighbors(n_a.id)
        assert len(neighbors) == 2
        assert {n.id for n in neighbors} == {n_b.id, n_c.id}
