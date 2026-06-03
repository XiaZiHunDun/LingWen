"""KeyPointGraph — N² 矛盾检测

Phase 1.1 — Doc 1 实施层。

核心算法: 对单章节 Snapshot 做 O(N²) 扫描,N≤100 时单次扫描 < 10ms。

检测的"硬矛盾"(1.1 MVP 范围):
1. active 角色 located_in destroyed 地点
2. destroyed 节点出现在 weight>0 的 active 关系中
3. (留扩展位) 后续加角色属性冲突/装备归属矛盾等

不检测的(留给后续阶段):
- 跨章节时间线矛盾(需 RippleEngine)
- 角色属性值冲突(同字段不同值, 需 attrs 语义模型)
- 关系权重语义矛盾(需关系类型注册表)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Optional

from .data_structures import KeyPoint, NodeId, Relation, WorldSnapshot


class ContradictionKind(str, Enum):
    """矛盾类型 — 跟 IssueSeverity 不同,这里只标"有矛盾",严重度由调用方决定"""

    LOCATED_IN_DESTROYED = "located_in_destroyed"  # active 节点 located_in destroyed 节点
    DESTROYED_NODE_HAS_ACTIVE_RELATION = "destroyed_node_has_active_relation"  # destroyed 节点还有 active 关系


@dataclass(frozen=True)
class Contradiction:
    kind: ContradictionKind
    node_a: NodeId
    node_b: NodeId
    relation: Optional[Relation] = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.description:
            object.__setattr__(
                self,
                "description",
                f"{self.kind.value}: {self.node_a} <-> {self.node_b}",
            )

    def __str__(self) -> str:
        return f"[{self.kind.value}] {self.node_a} <-> {self.node_b}"


class KeyPointGraph:
    """关键点图 — 一章内 N² 矛盾扫描

    不可变视角:add_node/add_relation 返回新实例,避免就地变更。
    实际上为了易用,这里用可变 dict + list 存储(类似 dict.setdefault
    风格的增量构建),但节点对象本身是不可变的 KeyPoint。
    """

    def __init__(
        self,
        nodes: Optional[dict[NodeId, KeyPoint]] = None,
        relations: Optional[list[Relation]] = None,
    ) -> None:
        self._nodes: dict[NodeId, KeyPoint] = dict(nodes or {})
        self._relations: list[Relation] = list(relations or [])

    @classmethod
    def from_snapshot(cls, snap: WorldSnapshot) -> "KeyPointGraph":
        return cls(nodes=snap.nodes, relations=list(snap.relations))

    # ---------- mutators ----------

    def add_node(self, kp: KeyPoint) -> None:
        if kp.id in self._nodes:
            raise ValueError(f"Node {kp.id} already exists; use update_node")
        self._nodes[kp.id] = kp

    def update_node(self, kp: KeyPoint) -> None:
        self._nodes[kp.id] = kp

    def add_relation(self, rel: Relation) -> None:
        if rel.src not in self._nodes:
            raise KeyError(f"src node {rel.src} not in graph")
        if rel.dst not in self._nodes:
            raise KeyError(f"dst node {rel.dst} not in graph")
        self._relations.append(rel)

    # ---------- accessors ----------

    def get_node(self, nid: NodeId) -> Optional[KeyPoint]:
        return self._nodes.get(nid)

    def relations_of(self, nid: NodeId) -> list[Relation]:
        """返回与 nid 相关的所有关系 (作为 src 或 dst)"""
        return [r for r in self._relations if r.src == nid or r.dst == nid]

    def node_count(self) -> int:
        return len(self._nodes)

    def relation_count(self) -> int:
        return len(self._relations)

    def all_nodes(self) -> list[KeyPoint]:
        return list(self._nodes.values())

    # ---------- contradiction detection ----------

    def detect_contradictions(self) -> Iterator[Contradiction]:
        """N² 扫描, yield 矛盾"""
        # 1) LOCATED_IN_DESTROYED — 检查所有 located_in 关系
        for rel in self._relations:
            if rel.type != "located_in":
                continue
            dst = self._nodes.get(rel.dst)
            if dst is None:
                continue
            if dst.status == "destroyed":
                src = self._nodes.get(rel.src)
                if src is not None and src.status == "active":
                    yield Contradiction(
                        kind=ContradictionKind.LOCATED_IN_DESTROYED,
                        node_a=rel.src,
                        node_b=rel.dst,
                        relation=rel,
                    )

        # 2) DESTROYED_NODE_HAS_ACTIVE_RELATION — destroyed 节点参与 weight>0 关系
        # 注意 1) 已经覆盖了 located_in,这里跳过重复
        for rel in self._relations:
            if rel.type == "located_in" or rel.weight <= 0:
                continue
            for endpoint in (rel.src, rel.dst):
                kp = self._nodes.get(endpoint)
                if kp is None:
                    continue
                if kp.status == "destroyed":
                    other = rel.dst if endpoint == rel.src else rel.src
                    yield Contradiction(
                        kind=ContradictionKind.DESTROYED_NODE_HAS_ACTIVE_RELATION,
                        node_a=endpoint,
                        node_b=other,
                        relation=rel,
                    )
