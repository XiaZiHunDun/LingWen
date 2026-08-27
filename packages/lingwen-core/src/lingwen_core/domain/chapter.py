"""灵文核心 · Domain — Chapter 实体

Phase 18.1 — 章节域实体与章节事件。

包含:
- Chapter — 单章正文（frozen dataclass）
- PhysicalLine / MentalLine — 章节内的物理/心理线
- ChapterWrittenEvent / ChapterReviewedEvent — 章节事件
"""
from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass(frozen=True)
class MentalLine:
    """心理线 — 角色在想什么/感受到什么"""

    ch: int
    thoughts: list[str] = field(default_factory=list)
    emotions: dict[NodeId, str] = field(default_factory=dict)
    arc_progress: dict[NodeId, float] = field(default_factory=dict)
    growth_signals: list[str] = field(default_factory=list)


class ChapterWrittenEvent(DomainEvent):
    """章节写完事件"""

    type: str = "ChapterWritten"


class ChapterReviewedEvent(DomainEvent):
    """章节审核完成事件"""

    type: str = "ChapterReviewed"
