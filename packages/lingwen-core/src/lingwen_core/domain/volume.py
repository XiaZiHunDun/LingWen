"""灵文核心 · Domain — Volume 实体

Phase 18.1 — 卷域实体。
"""
from __future__ import annotations

from dataclasses import dataclass

from lingwen_core.ports.storage import DomainEvent


@dataclass(frozen=True)
class Volume:
    """卷 = 章节的连续范围

    Invariants:
    - volume > 0
    - title 非空
    - chapter_range[0] <= chapter_range[1]
    """

    volume: int
    title: str
    chapter_range: tuple[int, int]

    def __post_init__(self) -> None:
        if self.volume <= 0:
            raise ValueError(f"Volume.volume must be positive — got {self.volume}")
        if not self.title or not self.title.strip():
            raise ValueError("Volume.title must be non-empty")
        start, end = self.chapter_range
        if start <= 0 or end <= 0:
            raise ValueError("Volume.chapter_range values must be positive")
        if start > end:
            raise ValueError(
                f"Volume.chapter_range start ({start}) must be <= end ({end})"
            )


class VolumeCreatedEvent(DomainEvent):
    """卷创建事件"""

    type: str = "VolumeCreated"
