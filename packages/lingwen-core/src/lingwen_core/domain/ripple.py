"""灵文核心 · Domain — Ripple 实体

Phase 18.1 — 涟漪/剧情波浪域实体。

Ripple = 剧情波浪（挖坑→扩散→平复），与 Foreshadow 关系密切
但 Ripple 是因果链，Foreshadow 是单一提示点。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from lingwen_core.domain.common import KeyPoint, NodeId, Relation
from lingwen_core.ports.storage import DomainEvent


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


MAX_OPEN_RIPPLOTS = 10  # Doc 1 §3.4 硬限制
RESOLUTION_GRACE_CH = 5  # planned_resolve_ch 可超 current_ch 最多 5 章（Doc 1 §3.4）
COLLAPSE_RISK_THRESHOLD = 0.8  # > 0.8 系统报警


@dataclass(frozen=True)
class Ripple:
    """剧情波浪 — 挖坑→扩散→平复 (Doc 1 §3.4)

    Invariants:
    - ripple_id 非空
    - origin_ch > 0
    - decay_rate ∈ [0, 1]
    - collapse_risk ∈ [0, 1]
    - planned_resolve_ch >= origin_ch (如果设置)
    """

    ripple_id: str
    origin_event: str
    origin_ch: int
    affected_nodes: tuple[NodeId, ...] = ()
    state: RippleState = RippleState.OPEN
    wavefront: tuple[int, ...] = ()
    decay_rate: float = 0.2
    affected_relations: tuple[Relation, ...] = ()
    planned_resolve_ch: int | None = None
    resolved_ch: int | None = None
    collapse_risk: float = 0.0
    resolution_mode: ResolutionMode | None = None

    def __post_init__(self) -> None:
        if not self.ripple_id or not self.ripple_id.strip():
            raise ValueError("Ripple.ripple_id must be non-empty")
        if not self.origin_event or not self.origin_event.strip():
            raise ValueError("Ripple.origin_event must be non-empty")
        if self.origin_ch <= 0:
            raise ValueError(f"Ripple.origin_ch must be positive — got {self.origin_ch}")
        if not 0.0 <= self.decay_rate <= 1.0:
            raise ValueError(
                f"Ripple.decay_rate must be in [0, 1] — got {self.decay_rate}"
            )
        if not 0.0 <= self.collapse_risk <= 1.0:
            raise ValueError(
                f"Ripple.collapse_risk must be in [0, 1] — got {self.collapse_risk}"
            )
        if self.planned_resolve_ch is not None and self.planned_resolve_ch < self.origin_ch:
            raise ValueError(
                f"Ripple.planned_resolve_ch ({self.planned_resolve_ch}) must be "
                f">= origin_ch ({self.origin_ch})"
            )

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
            "resolution_mode": self.resolution_mode.value if self.resolution_mode else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Ripple":
        return cls(
            ripple_id=str(d["ripple_id"]),
            origin_event=str(d["origin_event"]),
            origin_ch=int(d["origin_ch"]),
            affected_nodes=tuple(
                NodeId.from_string(s) for s in d.get("affected_nodes", [])
            ),
            state=RippleState(d["state"]) if "state" in d else RippleState.OPEN,
            wavefront=tuple(d.get("wavefront", ())),
            decay_rate=float(d.get("decay_rate", 0.2)),
            affected_relations=tuple(
                Relation.from_dict(r) for r in d.get("affected_relations", [])
            ),
            planned_resolve_ch=d.get("planned_resolve_ch"),
            resolved_ch=d.get("resolved_ch"),
            collapse_risk=float(d.get("collapse_risk", 0.0)),
            resolution_mode=(
                ResolutionMode(d["resolution_mode"])
                if d.get("resolution_mode")
                else None
            ),
        )


@dataclass(frozen=True)
class WorldSnapshot:
    """世界快照 — 一章结束时世界处于一个确定状态

    Invariants:
    - snapshot_id 非空
    - chapter > 0
    - consistency_hash 总是反映当前内容（__post_init__ 自动重算）
    """

    snapshot_id: str
    chapter: int
    timestamp: datetime
    nodes: dict[NodeId, KeyPoint] = field(default_factory=dict)
    relations: tuple[Relation, ...] = ()
    active_ripples: tuple[Ripple, ...] = ()
    world_mood: str = "neutral"
    consistency_hash: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id or not self.snapshot_id.strip():
            raise ValueError("WorldSnapshot.snapshot_id must be non-empty")
        if self.chapter <= 0:
            raise ValueError(f"WorldSnapshot.chapter must be positive — got {self.chapter}")
        # 始终重新计算 hash — 每次 new / dataclasses.replace 都是新快照
        object.__setattr__(self, "consistency_hash", self.compute_consistency_hash())

    def compute_consistency_hash(self) -> str:
        """基于 nodes + relations + ripples 计算一致性 hash"""
        payload = {
            "nodes": {str(k): v.to_dict() for k, v in sorted(self.nodes.items(), key=lambda x: str(x[0]))},
            "relations": [r.to_dict() for r in sorted(self.relations, key=lambda r: (str(r.src), str(r.dst)))],
            "active_ripples": [r.to_dict() for r in self.active_ripples],
            "world_mood": self.world_mood,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


class RippleOpenedEvent(DomainEvent):
    """涟漪开启事件"""

    type: str = "RippleOpened"


class RippleStateChangedEvent(DomainEvent):
    """涟漪状态变化事件"""

    type: str = "RippleStateChanged"


class RippleResolvedEvent(DomainEvent):
    """涟漪平复事件"""

    type: str = "RippleResolved"