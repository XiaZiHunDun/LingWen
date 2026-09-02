"""灵文核心 · Domain — Chapter 实体

Phase 18.1 — 章节域实体与章节事件。

包含:
- Chapter — 单章正文（frozen dataclass）
- PhysicalLine / MentalLine — 章节内的物理/心理线
- ChapterWrittenEvent / ChapterReviewedEvent — 章节事件

Phase 19+ Sub1 — PhysicalLine / MentalLine 加 to_dict / from_dict
（WorldSnapshot.consistency_hash 需要序列化 lines；序列化输出与
infra/world_model/data_structures.py:154-201 等价,以便 shim 替换时
无需迁移消费者代码）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lingwen_core.domain.common import NodeId
from lingwen_core.ports.storage import DomainEvent


@dataclass(frozen=True)
class Chapter:
    """单章正文 — 不可变

    Invariants:
    - chapter > 0
    - title 非空
    - outline_ref 非空
    """

    chapter: int
    title: str
    text: str
    outline_ref: str  # 关联的大纲 ID

    def __post_init__(self) -> None:
        if self.chapter <= 0:
            raise ValueError(f"Chapter.chapter must be positive — got {self.chapter}")
        if not self.title or not self.title.strip():
            raise ValueError("Chapter.title must be non-empty")
        if not self.outline_ref or not self.outline_ref.strip():
            raise ValueError("Chapter.outline_ref must be non-empty")


@dataclass(frozen=True)
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


@dataclass(frozen=True)
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


class ChapterWrittenEvent(DomainEvent):
    """章节写完事件"""

    type: str = "ChapterWritten"


class ChapterReviewedEvent(DomainEvent):
    """章节审核完成事件"""

    type: str = "ChapterReviewed"
