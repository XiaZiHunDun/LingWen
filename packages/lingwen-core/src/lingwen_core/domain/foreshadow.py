"""灵文核心 · Domain — Foreshadow 实体

Phase 18.1 — 伏笔域实体。

伏笔 = 提前埋设的故事元素, 计划在后续章节回收。
"""

from __future__ import annotations

from dataclasses import dataclass

from lingwen_core.ports.storage import DomainEvent


@dataclass(frozen=True)
class Foreshadow:
    """伏笔实体

    Invariants:
    - foreshadow_id 非空
    - description 非空
    - planted_ch > 0
    - planned_resolve_ch >= planted_ch
    """

    foreshadow_id: str
    description: str
    planted_ch: int
    planned_resolve_ch: int | None
    resolved_ch: int | None = None

    def __post_init__(self) -> None:
        if not self.foreshadow_id or not self.foreshadow_id.strip():
            raise ValueError("Foreshadow.foreshadow_id must be non-empty")
        if not self.description or not self.description.strip():
            raise ValueError("Foreshadow.description must be non-empty")
        if self.planted_ch <= 0:
            raise ValueError(f"Foreshadow.planted_ch must be positive — got {self.planted_ch}")
        if self.planned_resolve_ch is not None:
            if self.planned_resolve_ch <= self.planted_ch:
                raise ValueError(
                    f"Foreshadow.planned_resolve_ch ({self.planned_resolve_ch}) must be "
                    f"> planted_ch ({self.planted_ch})"
                )
        if self.resolved_ch is not None and self.resolved_ch < self.planted_ch:
            raise ValueError(
                f"Foreshadow.resolved_ch ({self.resolved_ch}) must be >= planted_ch ({self.planted_ch})"
            )


class ForeshadowPlantedEvent(DomainEvent):
    """伏笔埋设事件"""

    type: str = "ForeshadowPlanted"


class ForeshadowResolvedEvent(DomainEvent):
    """伏笔回收事件"""

    type: str = "ForeshadowResolved"
