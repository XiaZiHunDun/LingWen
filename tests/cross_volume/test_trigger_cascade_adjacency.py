# tests/cross_volume/test_trigger_cascade_adjacency.py
"""Phase 14.0 T1: Cascade 邻接表 O(1) 查找 RED→GREEN 测试.

新增字段 `_adjacency_by_node: dict[str, dict[str, str]]` (Phase 14.0 T1) 提供
`trigger_cascade` 第 326-334 行 O(1) 边查找替代 O(degree) 线性扫。

测试覆盖:
1. `ingest_edge(e)` 后 `_adjacency_by_node[e.from][e.to] == e.id`
2. 双向索引 (A→B 与 B→A 同时可达)
3. `trigger_cascade` 优先用 `_adjacency_by_node`, 不走旧 `_index_by_node_edges` 线性扫
4. `_register_edge_in_indexes(edge)` helper 原子写双索引
"""
from __future__ import annotations

import pytest

from infra.cross_volume import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.reference_graph import ReferenceEdge as _RawEdge  # noqa: F401  # type-hint alias
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "ripple.db")


@pytest.fixture
def graph(storage):
    g = CrossVolumeReferenceGraph(storage=storage)
    return g


def _node(volume: int, chapter: int = 0, *, title: str = "") -> ReferenceNode:
    return ReferenceNode(
        dimension="character",
        volume=volume,
        chapter=chapter,
        title=title,
        description="",
        payload={},
    )


def _edge(from_id: str, to_id: str, weight: float = 1.0) -> ReferenceEdge:
    return ReferenceEdge(
        from_node_id=from_id,
        to_node_id=to_id,
        relationship_type="mentions",
        weight=weight,
        payload={},
    )


class TestAdjacencyIndex:
    def test_adjacency_index_built_on_ingest_edge(self, graph):
        """ingest_edge(e) 后, _adjacency_by_node[e.from][e.to] == e.id"""
        a = _node(volume=1)
        b = _node(volume=2)
        graph.ingest_node(a)
        graph.ingest_node(b)
        e = _edge(a.id, b.id)
        graph.ingest_edge(e)
        # Phase 14.0 新字段断言
        assert hasattr(graph, "_adjacency_by_node"), "graph must expose _adjacency_by_node"
        assert graph._adjacency_by_node.get(a.id, {}).get(b.id) == e.id

    def test_adjacency_index_bidirectional(self, graph):
        """双向索引: A→B 之后 B→A 也在反向查询里"""
        a = _node(volume=1)
        b = _node(volume=2)
        graph.ingest_node(a)
        graph.ingest_node(b)
        e = _edge(a.id, b.id)
        graph.ingest_edge(e)
        # 反向查询也命中 (新 dict 存两份)
        assert graph._adjacency_by_node[b.id][a.id] == e.id

    def test_adjacency_lookup_used_by_trigger_cascade(self, graph):
        """trigger_cascade 优先用 _adjacency_by_node, 不走 _index_by_node_edges 线性扫"""
        from infra.cross_volume.ripple import CrossVolumeRipple

        class SpyDict(dict):
            """记录所有 .get() 调用。dict 实例的 .get 是 read-only 属性, 用子类记录。"""

            def __init__(self, *a, **kw) -> None:
                super().__init__(*a, **kw)
                self.get_calls: list[tuple] = []

            def get(self, key, default=None):  # type: ignore[override]
                self.get_calls.append((key, default))
                return super().get(key, default)

        a = _node(volume=1, title="A")
        b = _node(volume=2, title="B")
        c = _node(volume=3, title="C")

        # 安装 spy dict 在 ingest 之前 (so writes go to spy)
        graph._adjacency_by_node = SpyDict()
        graph.ingest_node(a)
        graph.ingest_node(b)
        graph.ingest_node(c)
        e_ab = _edge(a.id, b.id, weight=0.9)
        e_bc = _edge(b.id, c.id, weight=0.7)
        graph.ingest_edge(e_ab)
        graph.ingest_edge(e_bc)
        spy: SpyDict = graph._adjacency_by_node  # type: ignore[assignment]

        ripple = CrossVolumeRipple(
            id="ripple-1",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=(a.id,),
            payload={"desc": "trigger"},
        )

        cascade = graph.trigger_cascade(ripple, max_depth=2, weighted=False)

        assert len(spy.get_calls) >= 1, (
            f"trigger_cascade should query _adjacency_by_node.get at least once; "
            f"got {len(spy.get_calls)} calls"
        )
        # B 邻居发现
        assert any(n.id == b.id for n in cascade.cascade_nodes), "B should be discovered via adjacency"
        # C 间接可达
        assert any(n.id == c.id for n in cascade.cascade_nodes), "C should be reachable via adjacency"

    def test_register_edge_in_indexes_helper_atomic(self, graph):
        """_register_edge_in_indexes(edge) 原子写双索引, 旧 set 索引仍正确"""
        a = _node(volume=1)
        b = _node(volume=2)
        graph.ingest_node(a)
        graph.ingest_node(b)
        e = _edge(a.id, b.id)
        # 直接调 helper
        graph._register_edge_in_indexes(e)
        # 新索引
        assert graph._adjacency_by_node[a.id][b.id] == e.id
        assert graph._adjacency_by_node[b.id][a.id] == e.id
        # 旧 set 索引也写
        assert e.id in graph._index_by_node_edges[a.id]
        assert e.id in graph._index_by_node_edges[b.id]
