"""灵文核心 · Domain — Subplot/Plot 实体

Phase 19+ Sub1 — 从 infra/subplot/data_structures.py 迁移到 lingwen-core/domain。

主支线/支线定义 + 3 个 str Enum。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from lingwen_core.domain.common import NodeId

MAX_ACTIVE_SUBPLOTS = 5


class PlotType(str, Enum):
    """支线类型"""

    MAIN = "main"
    SUBPLOT = "subplot"
    SIDE = "side"


class PlotPurpose(str, Enum):
    """支线目的 — 8 个语义维度"""

    GROWTH = "growth"
    MYSTERY = "mystery"
    PAYOFF = "payoff"
    FACTION = "faction"
    ROMANCE = "romance"
    PACING = "pacing"
    ARTIFACT = "artifact"
    THEME = "theme"


class PlotStatus(str, Enum):
    """支线状态 — 6 个状态"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class Plot:
    """支线/主线定义 — 不可变"""

    plot_id: str
    type: PlotType
    title: str
    status: PlotStatus
    purpose: PlotPurpose = PlotPurpose.GROWTH
    protagonist_link: Optional[NodeId] = None
    birth_ch: int = 0
    active_ch_range: tuple[int, int] = (0, 0)
    close_ch: Optional[int] = None
    constraints_generated: tuple[str, ...] = ()
    related_ripples: tuple[str, ...] = ()
    parent_plot: Optional[str] = None
    key_chapters: tuple[int, ...] = ()
    next_constraint_ch: int = 0

    def __post_init__(self) -> None:
        if not self.plot_id or not self.plot_id.strip():
            raise ValueError("plot_id must be non-empty")
        if not self.title or not self.title.strip():
            raise ValueError("title must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plot_id": self.plot_id,
            "type": self.type.value,
            "title": self.title,
            "status": self.status.value,
            "purpose": self.purpose.value,
            "protagonist_link": str(self.protagonist_link) if self.protagonist_link else None,
            "birth_ch": self.birth_ch,
            "active_ch_range": list(self.active_ch_range),
            "close_ch": self.close_ch,
            "constraints_generated": list(self.constraints_generated),
            "related_ripples": list(self.related_ripples),
            "parent_plot": self.parent_plot,
            "key_chapters": list(self.key_chapters),
            "next_constraint_ch": self.next_constraint_ch,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Plot":
        protagonist = d.get("protagonist_link")
        protagonist_link = NodeId.from_string(protagonist) if protagonist else None
        return cls(
            plot_id=d["plot_id"],
            type=PlotType(d["type"]),
            title=d["title"],
            status=PlotStatus(d["status"]),
            purpose=PlotPurpose(d.get("purpose", PlotPurpose.GROWTH.value)),
            protagonist_link=protagonist_link,
            birth_ch=d.get("birth_ch", 0),
            active_ch_range=tuple(d.get("active_ch_range", [0, 0])),
            close_ch=d.get("close_ch"),
            constraints_generated=tuple(d.get("constraints_generated", [])),
            related_ripples=tuple(d.get("related_ripples", [])),
            parent_plot=d.get("parent_plot"),
            key_chapters=tuple(d.get("key_chapters", [])),
            next_constraint_ch=d.get("next_constraint_ch", 0),
        )


__all__ = [
    "MAX_ACTIVE_SUBPLOTS",
    "Plot",
    "PlotPurpose",
    "PlotStatus",
    "PlotType",
]
