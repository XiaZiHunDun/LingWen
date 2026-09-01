"""灵文世界模型 · 核心数据结构

Phase 1.1 — Doc 1 (灵文理论框架 v1.0) 实施层。

核心模型:
- NodeId/NodeType: 关键点标识
- KeyPoint: 关键点状态
- Relation: 关键点之间的关系
- PhysicalLine/MentalLine: 物理线/心理线
- Ripple: 剧情波浪 (挖坑→扩散→平复)
- WorldSnapshot: 一章一个版本的世界快照

Phase 1.2 (Doc 3): 加 active_subplots 字段 (lazy import 避免循环依赖)

Phase 1.5 (Doc 1 §3.4): Ripple 扩展 — 加 state / wavefront / decay_rate /
affected_relations / planned_resolve_ch 5 字段,backward-compatible with Phase 1.1
JSON (from_dict 用 .get(key, default) 兜底)。

设计原则:
- 不可变 (frozen=True) 优先,便于 reasoning 和缓存
- to_dict / from_dict 用于 JSON 持久化
- NodeId 用 type+name 复合,避免 id 冲突
- 跨包引用用 TYPE_CHECKING + 字符串注解,运行时 lazy import
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

# Phase 19+ Sub1: NodeId/NodeType canonical alignment.
# Re-export from lingwen_core.domain.common so consumers via
# `infra.world_model.data_structures.NodeId` and via `lingwen_core.domain.common.NodeId`
# resolve to the SAME class object. This unblocks `infra.subplot.data_structures`
# shim conversion (canonical Plot uses lingwen_core.domain.common.NodeId).
from lingwen_core.domain.common import NodeId, NodeType

# Phase 19+ Sub1 Task T19.2: Ripple/RippleState/ResolutionMode canonical alignment.
# Re-export from lingwen_core.domain.ripple so consumers via
# `infra.world_model.data_structures.Ripple` and via `lingwen_core.domain.ripple.Ripple`
# resolve to the SAME class object. Closes class-identity divergence that Phase 18 v18
# handoff explicitly flagged as deferred carryover. Same pattern as NodeId/NodeType.
from lingwen_core.domain.ripple import MAX_OPEN_RIPPLOTS, ResolutionMode, Ripple, RippleState

if TYPE_CHECKING:
    from infra.subplot.data_structures import Plot


class PlotStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


@dataclass
class KeyPoint:
    """关键点 = 世界中一个稳定存在的对象"""

    id: NodeId
    attrs: dict[str, Any] = field(default_factory=dict)
    status: str = "active"  # active/destroyed/hidden/transformed
    first_ch: int = 0
    last_ch: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.id.type.value,
            "name": self.id.name,
            "attrs": self.attrs,
            "status": self.status,
            "first_ch": self.first_ch,
            "last_ch": self.last_ch,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "KeyPoint":
        nid = NodeId.from_string(d["id"])
        return cls(
            id=nid,
            attrs=d.get("attrs", {}),
            status=d.get("status", "active"),
            first_ch=d.get("first_ch", 0),
            last_ch=d.get("last_ch", 0),
        )


@dataclass(frozen=True)
class Relation:
    """关系 = 关键点之间的边"""

    src: NodeId
    dst: NodeId
    type: str  # knows/owns/located_in/allied_to/opposed_to/...
    weight: float = 1.0
    first_ch: int = 0
    last_ch: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "src": str(self.src),
            "dst": str(self.dst),
            "type": self.type,
            "weight": self.weight,
            "first_ch": self.first_ch,
            "last_ch": self.last_ch,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Relation":
        return cls(
            src=NodeId.from_string(d["src"]),
            dst=NodeId.from_string(d["dst"]),
            type=d["type"],
            weight=d.get("weight", 1.0),
            first_ch=d.get("first_ch", 0),
            last_ch=d.get("last_ch", 0),
        )


@dataclass
class PhysicalLine:
    """物理线 — 客观世界发生的事"""

    ch: int
    actions: list[str] = field(default_factory=list)
    locations: list[NodeId] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ch": self.ch,
            "actions": list(self.actions),
            "locations": [str(n) for n in self.locations],
            "events": list(self.events),
            "constraints": list(self.constraints),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PhysicalLine":
        return cls(
            ch=d["ch"],
            actions=d.get("actions", []),
            locations=[NodeId.from_string(s) for s in d.get("locations", [])],
            events=d.get("events", []),
            constraints=d.get("constraints", []),
        )


@dataclass
class MentalLine:
    """心理线 — 角色在想什么/感受到什么"""

    ch: int
    thoughts: list[str] = field(default_factory=list)
    emotions: dict[NodeId, str] = field(default_factory=dict)
    arc_progress: dict[NodeId, float] = field(default_factory=dict)
    growth_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ch": self.ch,
            "thoughts": list(self.thoughts),
            "emotions": {str(k): v for k, v in self.emotions.items()},
            "arc_progress": {str(k): v for k, v in self.arc_progress.items()},
            "growth_signals": list(self.growth_signals),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MentalLine":
        return cls(
            ch=d["ch"],
            thoughts=d.get("thoughts", []),
            emotions={NodeId.from_string(k): v for k, v in d.get("emotions", {}).items()},
            arc_progress={NodeId.from_string(k): v for k, v in d.get("arc_progress", {}).items()},
            growth_signals=d.get("growth_signals", []),
        )


@dataclass(frozen=True)
class WorldSnapshot:
    """世界快照 — 一章结束时,世界处于一个确定状态"""

    snapshot_id: str
    chapter: int
    timestamp: datetime
    nodes: dict[NodeId, KeyPoint] = field(default_factory=dict)
    relations: tuple[Relation, ...] = ()
    physical: PhysicalLine = field(default_factory=lambda: PhysicalLine(ch=0))
    mental: MentalLine = field(default_factory=lambda: MentalLine(ch=0))
    active_ripples: tuple[Ripple, ...] = ()
    active_subplots: tuple["Plot", ...] = ()  # Phase 1.2 (Doc 3)
    world_mood: str = "neutral"
    consistency_hash: str = ""

    def __post_init__(self) -> None:
        # 始终重新计算 hash — 每次 new / dataclasses.replace 都是新快照,hash 必须反映当前内容
        # (旧的 `if not self.consistency_hash` 写法会让 dataclasses.replace 继承旧 hash,导致不一致)
        object.__setattr__(self, "consistency_hash", self.compute_consistency_hash())

    def compute_consistency_hash(self) -> str:
        """基于 nodes + relations + lines + subplots 计算一致性 hash"""
        payload = {
            "nodes": {str(k): v.to_dict() for k, v in sorted(self.nodes.items(), key=lambda x: str(x[0]))},
            "relations": [r.to_dict() for r in sorted(self.relations, key=lambda r: (str(r.src), str(r.dst)))],
            "physical": self.physical.to_dict(),
            "mental": self.mental.to_dict(),
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "active_subplots": [self._plot_to_dict(p) for p in self.active_subplots],
            "world_mood": self.world_mood,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _plot_to_dict(p: Any) -> dict[str, Any]:
        """Plot → dict (duck typing: 调用 p.to_dict())"""
        return p.to_dict() if hasattr(p, "to_dict") else p

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "chapter": self.chapter,
            "timestamp": self.timestamp.isoformat(),
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "relations": [r.to_dict() for r in self.relations],
            "physical": self.physical.to_dict(),
            "mental": self.mental.to_dict(),
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "active_subplots": [self._plot_to_dict(p) for p in self.active_subplots],
            "world_mood": self.world_mood,
            "consistency_hash": self.consistency_hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorldSnapshot":
        # Lazy import to avoid circular dependency (subplot → world_model)
        from infra.subplot.data_structures import Plot

        nodes = {NodeId.from_string(s): KeyPoint.from_dict(kd) for s, kd in d.get("nodes", {}).items()}
        subplots = tuple(Plot.from_dict(pd) for pd in d.get("active_subplots", []))
        return cls(
            snapshot_id=d["snapshot_id"],
            chapter=d["chapter"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            nodes=nodes,
            relations=tuple(Relation.from_dict(rd) for rd in d.get("relations", [])),
            physical=PhysicalLine.from_dict(d.get("physical", {"ch": 0})),
            mental=MentalLine.from_dict(d.get("mental", {"ch": 0})),
            active_ripples=tuple(Ripple.from_dict(rd) for rd in d.get("active_ripples", [])),
            active_subplots=subplots,
            world_mood=d.get("world_mood", "neutral"),
            consistency_hash=d.get("consistency_hash", ""),
        )
