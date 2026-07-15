"""Tests for subplot.queries.

Phase 1.2.g — RED tests for 3 query functions.

设计约束 (per Doc 3 v1.0):
- can_open_new_subplot(registry): 当前 active subplot 数 < 5 → True
- suggest_subplot_to_close(registry): 返回最早 active 的 subplot_id (None if 没有)
- detect_constraint_saturation(registry, current_ch): 返回 ≥3 个 constraint
  在未来 5 章内触发的 plot_id
"""
from __future__ import annotations

import pytest

from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
from infra.subplot.queries import (
    can_open_new_subplot,
    detect_constraint_saturation,
    suggest_subplot_to_close,
)
from infra.subplot.registry import PlotRegistry


def _subplot(
    plot_id: str,
    status: PlotStatus = PlotStatus.ACTIVE,
    birth_ch: int = 0,
    next_constraint_ch: int = 0,
    active_ch_range: tuple[int, int] = (0, 100),
) -> Plot:
    return Plot(
        plot_id=plot_id,
        type=PlotType.SUBPLOT,
        title=plot_id,
        status=status,
        purpose=PlotPurpose.GROWTH,
        birth_ch=birth_ch,
        active_ch_range=active_ch_range,
        next_constraint_ch=next_constraint_ch,
    )


class TestCanOpenNewSubplot:
    def test_empty_registry_can_open(self):
        r = PlotRegistry()
        assert can_open_new_subplot(r) is True

    def test_4_active_can_open(self):
        r = PlotRegistry()
        for i in range(4):
            r.add_plot(_subplot(f"sub-{i}"))
        assert r.count_active_subplots() == 4
        assert can_open_new_subplot(r) is True

    def test_5_active_cannot_open(self):
        r = PlotRegistry()
        for i in range(5):
            r.add_plot(_subplot(f"sub-{i}"))
        assert r.count_active_subplots() == 5
        assert can_open_new_subplot(r) is False

    def test_5_active_plus_paused_cannot_open(self):
        """PAUSED 不计入 5 限制,所以 paused 后仍满 5 active"""
        r = PlotRegistry()
        for i in range(5):
            r.add_plot(_subplot(f"sub-{i}"))
        r.add_plot(_subplot("paused-1", status=PlotStatus.PAUSED))
        assert can_open_new_subplot(r) is False

    def test_main_does_not_block_opening(self):
        """MAIN 类型不占 subplot 名额"""
        r = PlotRegistry()
        r.add_plot(Plot(
            plot_id="main-001", type=PlotType.MAIN,
            title="主线", status=PlotStatus.ACTIVE,
        ))
        for i in range(5):
            r.add_plot(_subplot(f"sub-{i}"))
        # 5 subplot 满了,即使有 1 main 也不能开
        assert can_open_new_subplot(r) is False


class TestSuggestSubplotToClose:
    def test_empty_returns_none(self):
        r = PlotRegistry()
        assert suggest_subplot_to_close(r) is None

    def test_returns_oldest_active_subplot(self):
        """最早 active 的 subplot (按 birth_ch 最小)"""
        r = PlotRegistry()
        r.add_plot(_subplot("new", birth_ch=20, active_ch_range=(20, 100)))
        r.add_plot(_subplot("old", birth_ch=5, active_ch_range=(5, 100)))
        r.add_plot(_subplot("mid", birth_ch=10, active_ch_range=(10, 100)))
        # 最早的 (birth_ch 最小) 是 old
        assert suggest_subplot_to_close(r) == "old"

    def test_skips_main_type(self):
        """MAIN 不在候选范围"""
        r = PlotRegistry()
        r.add_plot(Plot(
            plot_id="main-001", type=PlotType.MAIN,
            title="主线", status=PlotStatus.ACTIVE, birth_ch=1,
        ))
        r.add_plot(_subplot("sub-1", birth_ch=10))
        assert suggest_subplot_to_close(r) == "sub-1"

    def test_skips_non_active(self):
        """非 ACTIVE 状态 (PAUSED/CLOSING/CLOSED) 不在候选"""
        r = PlotRegistry()
        r.add_plot(_subplot("paused", status=PlotStatus.PAUSED, birth_ch=1))
        r.add_plot(_subplot("closing", status=PlotStatus.CLOSING, birth_ch=2))
        r.add_plot(_subplot("active", birth_ch=3))
        assert suggest_subplot_to_close(r) == "active"


class TestDetectConstraintSaturation:
    def test_no_saturation_no_active(self):
        r = PlotRegistry()
        assert detect_constraint_saturation(r, current_ch=50) is None

    def test_3_constraints_within_5_chapters_is_saturation(self):
        """未来 5 章内 ≥ 3 个 constraint 触发 → saturation"""
        r = PlotRegistry()
        p = Plot(
            plot_id="busy", type=PlotType.SUBPLOT, title="busy",
            status=PlotStatus.ACTIVE, purpose=PlotPurpose.MYSTERY,
            constraints_generated=("ch52: 神秘人", "ch53: 线索", "ch54: 真相"),
        )
        r.add_plot(p)
        # current_ch=50,未来 5 章 (50-55) 触发 3 个 constraint
        assert detect_constraint_saturation(r, current_ch=50) == "busy"

    def test_2_constraints_within_5_chapters_not_saturation(self):
        """只有 2 个 constraint → 不算 saturation"""
        r = PlotRegistry()
        p = Plot(
            plot_id="moderate", type=PlotType.SUBPLOT, title="m",
            status=PlotStatus.ACTIVE, purpose=PlotPurpose.MYSTERY,
            constraints_generated=("ch51: 线索", "ch52: 真相"),
        )
        r.add_plot(p)
        assert detect_constraint_saturation(r, current_ch=50) is None

    def test_3_constraints_outside_5_chapters_not_saturation(self):
        """3 个 constraint 但都在 5 章外 → 不算"""
        r = PlotRegistry()
        p = Plot(
            plot_id="slow", type=PlotType.SUBPLOT, title="s",
            status=PlotStatus.ACTIVE, purpose=PlotPurpose.MYSTERY,
            constraints_generated=("ch60: 线索", "ch70: 真相", "ch80: 结局"),
        )
        r.add_plot(p)
        assert detect_constraint_saturation(r, current_ch=50) is None

    def test_constraint_format_chXX(self):
        """constraint 格式: 'chXX: 描述' — 解析 ch 后的数字"""
        r = PlotRegistry()
        p = Plot(
            plot_id="p1", type=PlotType.SUBPLOT, title="p",
            status=PlotStatus.ACTIVE, purpose=PlotPurpose.MYSTERY,
            constraints_generated=("ch55: 事件A", "ch56: 事件B", "ch57: 事件C"),
        )
        r.add_plot(p)
        assert detect_constraint_saturation(r, current_ch=52) == "p1"

    def test_constraint_format_flexible(self):
        """constraint 格式宽松:只要有数字就算"""
        r = PlotRegistry()
        p = Plot(
            plot_id="p1", type=PlotType.SUBPLOT, title="p",
            status=PlotStatus.ACTIVE, purpose=PlotPurpose.MYSTERY,
            constraints_generated=("第55章: A", "第56章: B", "第57章: C"),
        )
        r.add_plot(p)
        assert detect_constraint_saturation(r, current_ch=52) == "p1"

    def test_inactive_subplot_ignored(self):
        """非 active subplot 不计入 saturation"""
        r = PlotRegistry()
        p = Plot(
            plot_id="p1", type=PlotType.SUBPLOT, title="p",
            status=PlotStatus.PAUSED, purpose=PlotPurpose.MYSTERY,
            constraints_generated=("ch52: A", "ch53: B", "ch54: C"),
        )
        r.add_plot(p)
        assert detect_constraint_saturation(r, current_ch=50) is None
