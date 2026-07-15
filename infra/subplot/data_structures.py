"""灵文支线模型 · 核心数据结构

Phase 1.2 — Doc 3 (主线/支线模型 v1.0) 实施层。

核心模型:
- PlotType / PlotPurpose / PlotStatus: 3 个 str Enum
- Plot: 不可变 (frozen) 的支线/主线定义
- MAX_ACTIVE_SUBPLOTS = 5: 硬限制 (1 主线 + ≤4 支线)

设计原则 (per Doc 3):
- Plot 不可变 (frozen=True) — 定义后不应被原地修改,状态变化通过 Registry
- Plot 可 JSON 序列化 (to_dict / from_dict) — 持久化到 subplots.json
- 3 enums 全部 str Enum — JSON 友好
- protagonist_link 引用 world_model.NodeId — 跨包关联
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from infra.world_model import NodeId

# 硬限制: 1 主线 + ≤4 支线
MAX_ACTIVE_SUBPLOTS = 5


class PlotType(str, Enum):
    """支线类型"""

    MAIN = "main"  # 主线
    SUBPLOT = "subplot"  # 支线
    SIDE = "side"  # 副线 (占位,完整管理在后续阶段)


class PlotPurpose(str, Enum):
    """支线目的 — 8 个语义维度 (Doc 3 §3.1)"""

    GROWTH = "growth"  # 主角成长
    MYSTERY = "mystery"  # 悬疑/揭秘
    PAYOFF = "payoff"  # 伏笔回收
    FACTION = "faction"  # 势力博弈
    ROMANCE = "romance"  # 感情线
    PACING = "pacing"  # 节奏调节
    ARTIFACT = "artifact"  # 神器/法宝
    THEME = "theme"  # 主题表达


class PlotStatus(str, Enum):
    """支线状态 — 6 个状态,4 个非终态 + 2 个终态"""

    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 进行中
    PAUSED = "paused"  # 暂停 (资源让位)
    CLOSING = "closing"  # 收尾中 (≥2 章)
    CLOSED = "closed"  # 已收尾 (terminal)
    ABANDONED = "abandoned"  # 强切 (terminal)


@dataclass(frozen=True)
class Plot:
    """支线/主线定义 — 不可变,所有修改通过 Registry"""

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
