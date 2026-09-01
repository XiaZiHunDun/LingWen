"""infra/subplot/helpers.py — Phase 1.2 application services on WorldSnapshot

Behavior helpers that operate on ``WorldSnapshot.active_subplots``. Moved
out of ``infra.world_model.__init__`` as part of Phase 19+ Sub1 (Task 5).

Implementation unchanged from when it lived in
``infra/world_model/__init__``; only the import location moved.

Future Phase: these functions target ``lingwen_core.use_cases``
(use-case layer), not domain entities.
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from lingwen_core.domain.subplot import PlotStatus

if TYPE_CHECKING:
    from lingwen_core.domain.ripple import WorldSnapshot
    from lingwen_core.domain.subplot import Plot


def subplots_count(snapshot: "WorldSnapshot") -> int:
    """统计 WorldSnapshot 中 active subplot 数 (Phase 1.2 工具方法)"""
    return len(snapshot.active_subplots)


def add_subplot(snapshot: "WorldSnapshot", plot: "Plot") -> "WorldSnapshot":
    """向 WorldSnapshot 添加一个 subplot,返回新快照 (不可变)

    Args:
        snapshot: 原快照
        plot: Plot 对象 (来自 lingwen_core.domain.subplot)

    Returns:
        含新 subplot 的新 WorldSnapshot
    """
    return replace(snapshot, active_subplots=(*snapshot.active_subplots, plot))


def get_active_subplots(snapshot: "WorldSnapshot") -> tuple["Plot", ...]:
    """返回 WorldSnapshot 中所有 status == ACTIVE 的 subplot (Phase 1.2 工具方法)"""
    return tuple(p for p in snapshot.active_subplots if p.status == PlotStatus.ACTIVE)


__all__ = [
    "add_subplot",
    "get_active_subplots",
    "subplots_count",
]
