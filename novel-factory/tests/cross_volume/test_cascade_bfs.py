"""Phase 9.15: cascade BFS tests (depth 3 + visited set)."""
import pytest

from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple


@pytest.fixture
def graph_with_chain():
    """3-volume chain: V1c1 → V2c1 → V3c1 (linear, 3 hops max)."""
    import tempfile
    from pathlib import Path

    from infra.cross_volume.storage import RippleStorage
    with tempfile.TemporaryDirectory() as tmp:
        storage = RippleStorage(db_path=Path(tmp) / "cascade.db")
        g = CrossVolumeReferenceGraph(storage)
        # Nodes
        n1 = ReferenceNode(id="n1", volume=1, chapter=1, dimension="character")
        n2 = ReferenceNode(id="n2", volume=2, chapter=1, dimension="character")
        n3 = ReferenceNode(id="n3", volume=3, chapter=1, dimension="character")
        n4 = ReferenceNode(id="n4", volume=3, chapter=2, dimension="foreshadow")
        for n in [n1, n2, n3, n4]:
            g.add_node(n)
        # Edges (chain: n1-n2-n3, branch: n3-n4)
        g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
        g.add_edge(ReferenceEdge(id="e23", from_node_id="n2", to_node_id="n3"))
        g.add_edge(ReferenceEdge(id="e34", from_node_id="n3", to_node_id="n4"))
        yield g


class TestTriggerCascadeBFS:
    def test_cascade_bfs_depth_1_returns_direct_neighbors(self, graph_with_chain):
        """Ripple starts at n1 → BFS returns [n2] (1-hop)."""
        ripple = CrossVolumeRipple(
            id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple, max_depth=1)
        assert isinstance(cascaded, CascadedRipple)
        assert cascaded.trigger_ripple_id == "rip-1"
        assert {n.id for n in cascaded.cascade_nodes} == {"n2"}
        assert cascaded.depth_reached == 1

    def test_cascade_bfs_depth_2_returns_2_hop(self, graph_with_chain):
        """Ripple starts at n1 → BFS returns [n2, n3] (1+2 hops)."""
        ripple = CrossVolumeRipple(
            id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple, max_depth=2)
        assert {n.id for n in cascaded.cascade_nodes} == {"n2", "n3"}
        assert cascaded.depth_reached == 2

    def test_cascade_bfs_depth_3_returns_3_hop_max(self, graph_with_chain):
        """Ripple starts at n1 → BFS returns [n2, n3, n4] (1+2+3 hops, n4 is 3rd hop from n1)."""
        ripple = CrossVolumeRipple(
            id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple, max_depth=3)
        assert {n.id for n in cascaded.cascade_nodes} == {"n2", "n3", "n4"}
        assert cascaded.depth_reached == 3

    def test_cascade_bfs_cycle_safe_no_infinite_loop(self):
        """Cycle n1→n2→n3→n1: BFS must not loop infinitely (visited set)."""
        import tempfile
        from pathlib import Path

        from infra.cross_volume.storage import RippleStorage
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "cycle.db")
            g = CrossVolumeReferenceGraph(storage)
            for nid in ["n1", "n2", "n3"]:
                g.add_node(ReferenceNode(id=nid, volume=1, chapter=1, dimension="character"))
            g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
            g.add_edge(ReferenceEdge(id="e23", from_node_id="n2", to_node_id="n3"))
            g.add_edge(ReferenceEdge(id="e31", from_node_id="n3", to_node_id="n1"))  # cycle back
            ripple = CrossVolumeRipple(
                id="rip-cycle", trigger_volume=1, trigger_chapter=1,
                affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
            )
            cascaded = g.trigger_cascade(ripple)  # must terminate fast
            assert {n.id for n in cascaded.cascade_nodes} == {"n2", "n3"}
            assert cascaded.depth_reached == 2  # n3 reachable, n1 already visited

    def test_cascade_bfs_isolated_ripple_returns_empty(self, graph_with_chain):
        """Ripple on node n4 with max_depth=0 → 0 cascade, depth=0."""
        ripple = CrossVolumeRipple(
            id="rip-iso", trigger_volume=3, trigger_chapter=2,
            affected_nodes=("n4",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple, max_depth=0)
        assert cascaded.cascade_nodes == ()
        assert cascaded.cascade_edges == ()
        assert cascaded.cascade_actions == ()
        assert cascaded.depth_reached == 0

    def test_cascade_bfs_visited_set_skips_revisit(self, graph_with_chain):
        """Starting node visited, no revisit (n1 is in visited from start)."""
        ripple = CrossVolumeRipple(
            id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple)
        # n1 is starting node, NOT in cascade_nodes
        assert "n1" not in {n.id for n in cascaded.cascade_nodes}

    def test_cascade_bfs_collects_edges_for_each_hop(self, graph_with_chain):
        """Each BFS hop collects the corresponding edge."""
        ripple = CrossVolumeRipple(
            id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple)
        edge_ids = {e.id for e in cascaded.cascade_edges}
        assert edge_ids == {"e12", "e23", "e34"}

    def test_cascade_bfs_generates_proposed_actions_per_hop(self, graph_with_chain):
        """1 proposed_action per BFS hop (3 hops = 3 actions)."""
        ripple = CrossVolumeRipple(
            id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = graph_with_chain.trigger_cascade(ripple)
        assert len(cascaded.cascade_actions) == 3
        for i, action in enumerate(cascaded.cascade_actions, start=1):
            assert action["action"] == "propagate"
            assert action["depth"] == i
            assert "from" in action and "to" in action
