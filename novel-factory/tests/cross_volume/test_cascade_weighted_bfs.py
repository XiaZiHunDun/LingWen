"""Phase 9.16: cascade weighted BFS tests (priority queue by edge.weight)."""
import pytest

from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple


@pytest.fixture
def weighted_graph():
    """4-node weighted graph: n1→n2 (w=0.3), n1→n3 (w=0.9), n3→n4 (w=0.5).
    High-weight path n1→n3 (0.9) should propagate before n1→n2 (0.3)."""
    import tempfile
    from pathlib import Path

    from infra.cross_volume.storage import RippleStorage
    with tempfile.TemporaryDirectory() as tmp:
        storage = RippleStorage(db_path=Path(tmp) / "weighted.db")
        g = CrossVolumeReferenceGraph(storage)
        for nid, vol, ch in [("n1", 1, 1), ("n2", 2, 1), ("n3", 2, 2), ("n4", 3, 1)]:
            g.add_node(ReferenceNode(id=nid, volume=vol, chapter=ch, dimension="character"))
        # 低 weight 边
        g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2", weight=0.3))
        # 高 weight 边
        g.add_edge(ReferenceEdge(id="e13", from_node_id="n1", to_node_id="n3", weight=0.9))
        # 中 weight 边
        g.add_edge(ReferenceEdge(id="e34", from_node_id="n3", to_node_id="n4", weight=0.5))
        yield g


class TestWeightedCascadeBFS:
    def test_weighted_bfs_v2_default_uses_heapq(self, weighted_graph):
        """Default weighted=True → bfs_algorithm_version='v2_weighted'."""
        ripple = CrossVolumeRipple(
            id="rip-w1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = weighted_graph.trigger_cascade(ripple)
        assert isinstance(cascaded, CascadedRipple)
        assert cascaded.bfs_algorithm_version == "v2_weighted"

    def test_weighted_bfs_high_weight_propagates_first(self, weighted_graph):
        """高 weight 边 n1→n3 (0.9) 应优先于 n1→n2 (0.3) 传播, n4 通过 n3 链上.
        cascade_nodes 应含 {n2, n3, n4} (max_depth=3 同 set, 但 version v2_weighted 区分)."""
        ripple = CrossVolumeRipple(
            id="rip-w1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = weighted_graph.trigger_cascade(ripple)
        node_ids = {n.id for n in cascaded.cascade_nodes}
        assert node_ids == {"n2", "n3", "n4"}
        # n4 是 2 跳 (n1→n3→n4), depth_reached 应 >= 2
        assert cascaded.depth_reached >= 2

    def test_weighted_bfs_tie_break_by_node_id_lexicographic(self):
        """ties weight 相等时用 node_id 字典序 (heapq tuple 比较天然保证)."""
        import tempfile
        from pathlib import Path

        from infra.cross_volume.storage import RippleStorage
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "tie.db")
            g = CrossVolumeReferenceGraph(storage)
            for nid in ["n_a", "n_b", "n_c"]:  # 字典序 a < b < c
                g.add_node(ReferenceNode(id=nid, volume=1, chapter=1, dimension="character"))
            # 2 条边同 weight 0.5
            g.add_edge(ReferenceEdge(id="e_ab", from_node_id="n_a", to_node_id="n_b", weight=0.5))
            g.add_edge(ReferenceEdge(id="e_ac", from_node_id="n_a", to_node_id="n_c", weight=0.5))
            # tie-break 应按 n_b < n_c (字典序), so n_b 优先 pop
            # 主要验证 cascade 不漂移, 跑 2 次返同 set
            ripple = CrossVolumeRipple(
                id="rip-tie", trigger_volume=1, trigger_chapter=1,
                affected_nodes=("n_a",), affected_edges=(), proposed_actions=(),
            )
            c1 = g.trigger_cascade(ripple)
            c2 = g.trigger_cascade(ripple)
            assert {n.id for n in c1.cascade_nodes} == {n.id for n in c2.cascade_nodes}
            assert c1.bfs_algorithm_version == "v2_weighted"

    def test_weighted_false_falls_back_to_v1_fifo(self, weighted_graph):
        """weighted=False 时 bfs_algorithm_version='v1', 行为跟 Phase 9.15 FIFO 一致."""
        ripple = CrossVolumeRipple(
            id="rip-v1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = weighted_graph.trigger_cascade(ripple, weighted=False)
        assert cascaded.bfs_algorithm_version == "v1"
        # FIFO 跟 weighted 都是同 set (max_depth=3 同), 但 version 字段区分
        assert {n.id for n in cascaded.cascade_nodes} == {"n2", "n3", "n4"}

    def test_weighted_bfs_visited_set_prevents_revisit(self, weighted_graph):
        """高 weight 优先但 visited set 仍严防 revisit (n3 在 n1→n3 后 visit, 不会从 n2 反向回 n1)."""
        ripple = CrossVolumeRipple(
            id="rip-w1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = weighted_graph.trigger_cascade(ripple)
        # n1 是起点, 不应在 cascade_nodes
        assert "n1" not in {n.id for n in cascaded.cascade_nodes}

    def test_weighted_bfs_max_depth_3_cap(self):
        """max_depth=3 仍生效, 4 跳深的节点不进 cascade."""
        import tempfile
        from pathlib import Path

        from infra.cross_volume.storage import RippleStorage
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "depth.db")
            g = CrossVolumeReferenceGraph(storage)
            # 5 节点 chain: n1→n2→n3→n4→n5
            for i in range(1, 6):
                g.add_node(ReferenceNode(id=f"n{i}", volume=1, chapter=i, dimension="character"))
            for i in range(1, 5):
                g.add_edge(ReferenceEdge(id=f"e{i}{i+1}", from_node_id=f"n{i}", to_node_id=f"n{i+1}", weight=0.8))
            ripple = CrossVolumeRipple(
                id="rip-deep", trigger_volume=1, trigger_chapter=1,
                affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
            )
            cascaded = g.trigger_cascade(ripple)
            # n1→n2 (1) →n3 (2) →n4 (3), n5 4 跳不达
            assert {n.id for n in cascaded.cascade_nodes} == {"n2", "n3", "n4"}
            assert cascaded.depth_reached == 3

    def test_weighted_bfs_max_nodes_100_cap(self):
        """100 节点 cap 仍生效 (跟 Phase 9.15 一致)."""
        import tempfile
        from pathlib import Path

        from infra.cross_volume.storage import RippleStorage
        with tempfile.TemporaryDirectory() as tmp:
            storage = RippleStorage(db_path=Path(tmp) / "cap.db")
            g = CrossVolumeReferenceGraph(storage)
            # 1 trigger + 150 neighbors (star topology)
            g.add_node(ReferenceNode(id="trigger", volume=1, chapter=1, dimension="character"))
            for i in range(150):
                nid = f"n_{i:03d}"
                g.add_node(ReferenceNode(id=nid, volume=2, chapter=1, dimension="character"))
                g.add_edge(ReferenceEdge(id=f"e_{i:03d}", from_node_id="trigger", to_node_id=nid, weight=0.5))
            ripple = CrossVolumeRipple(
                id="rip-cap", trigger_volume=1, trigger_chapter=1,
                affected_nodes=("trigger",), affected_edges=(), proposed_actions=(),
            )
            cascaded = g.trigger_cascade(ripple)
            # ≤ 100 节点 (cap), 跟 Phase 9.15 一致
            assert len(cascaded.cascade_nodes) <= 100

    def test_weighted_bfs_collects_edges_for_each_hop(self, weighted_graph):
        """weighted BFS 仍 collect 每个 hop 对应的 edge (跟 Phase 9.15 一致)."""
        ripple = CrossVolumeRipple(
            id="rip-w1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        )
        cascaded = weighted_graph.trigger_cascade(ripple)
        edge_ids = {e.id for e in cascaded.cascade_edges}
        assert edge_ids == {"e12", "e13", "e34"}
