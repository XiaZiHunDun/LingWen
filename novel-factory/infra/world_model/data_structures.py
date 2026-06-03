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

if TYPE_CHECKING:
    from infra.subplot.data_structures import Plot


class NodeType(str, Enum):
    LOCATION = "location"
    CHARACTER = "character"
    FACTION = "faction"
    ARTIFACT = "artifact"
    CONCEPT = "concept"


class PlotStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class NodeId:
    """关键点 ID = (type, name) 复合键"""

    type: NodeType
    name: str

    def __str__(self) -> str:
        return f"{self.type.value}:{self.name}"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("NodeId.name must be non-empty")

    @classmethod
    def from_string(cls, s: str) -> "NodeId":
        """从 "type:name" 字符串还原"""
        if ":" not in s:
            raise ValueError(f"NodeId string must contain ':' — got {s!r}")
        type_str, name = s.split(":", 1)
        return cls(NodeType(type_str), name)


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


class RippleState(str, Enum):
    """Ripple 4 状态 (Doc 1 §3.4):
    OPEN (挖坑) → PROPAGATING (扩散) → RESOLVING (平复中) → RESOLVED (终态)"""

    OPEN = "open"
    PROPAGATING = "propagating"
    RESOLVING = "resolving"
    RESOLVED = "resolved"


class ResolutionMode(str, Enum):
    """Ripple 解决方式 (Doc 1 §3.4):
    STRONG (100% 恢复, 伏笔回收) / WEAK (60-80% 恢复 + 新稳态) /
    UNRESOLVED (标记长期未平复, 接受但不关闭)"""

    STRONG = "strong"
    WEAK = "weak"
    UNRESOLVED = "unresolved"


# Doc 1 §3.4 硬限制:未平复 Ripple > 10 → 崩塌风险 > 0.7 → > 0.8 报警
# 计入:OPEN + PROPAGATING + RESOLVING (RESOLVED 终态不计入)
MAX_OPEN_RIPPLOTS = 10


@dataclass(frozen=True)
class Ripple:
    """剧情波浪 — 挖坑→扩散→平复 (Doc 1 §3.4)"""

    ripple_id: str
    origin_event: str
    origin_ch: int
    affected_nodes: tuple[NodeId, ...] = ()
    state: RippleState = RippleState.OPEN
    wavefront: tuple[int, ...] = ()  # 波浪推进的章节集合
    decay_rate: float = 0.2  # 衰减率 (Doc 1: 0.1-0.5)
    affected_relations: tuple[Relation, ...] = ()
    planned_resolve_ch: Optional[int] = None  # 计划平复章节 (注册时 enforce)
    resolved_ch: Optional[int] = None
    collapse_risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ripple_id": self.ripple_id,
            "origin_event": self.origin_event,
            "origin_ch": self.origin_ch,
            "affected_nodes": [str(n) for n in self.affected_nodes],
            "state": self.state.value,
            "wavefront": list(self.wavefront),
            "decay_rate": self.decay_rate,
            "affected_relations": [r.to_dict() for r in self.affected_relations],
            "planned_resolve_ch": self.planned_resolve_ch,
            "resolved_ch": self.resolved_ch,
            "collapse_risk": self.collapse_risk,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Ripple":
        # Backward compat: Phase 1.1 JSON 不含 state/wavefront/decay_rate/
        # affected_relations/planned_resolve_ch, 用 .get(key, default) 兜底
        return cls(
            ripple_id=d["ripple_id"],
            origin_event=d["origin_event"],
            origin_ch=d["origin_ch"],
            affected_nodes=tuple(NodeId.from_string(s) for s in d.get("affected_nodes", [])),
            state=RippleState(d["state"]) if "state" in d else RippleState.OPEN,
            wavefront=tuple(d.get("wavefront", ())),
            decay_rate=d.get("decay_rate", 0.2),
            affected_relations=tuple(Relation.from_dict(r) for r in d.get("affected_relations", [])),
            planned_resolve_ch=d.get("planned_resolve_ch"),
            resolved_ch=d.get("resolved_ch"),
            collapse_risk=d.get("collapse_risk", 0.0),
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
