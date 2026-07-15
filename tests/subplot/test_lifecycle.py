"""Tests for subplot.lifecycle.

Phase 1.2.c — RED tests for state machine + 7-stage model.

设计约束 (per Doc 3 v1.0):
- 6 状态转换规则 (DRAFT→ACTIVE→PAUSED/CLOSING/ABANDONED, PAUSED→ACTIVE/ABANDONED, CLOSING→CLOSED/ABANDONED)
- 2 终态: CLOSED, ABANDONED
- CLOSING 必须持续 ≥ 2 章 (CLOSING_MIN_CHAPTERS)
- 7 阶段模型: seed/build/escalate/climax/resolve/close/echo
- 每阶段有典型章数范围
"""
from __future__ import annotations

import pytest

from infra.subplot.data_structures import (
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
from infra.subplot.lifecycle import (
    CLOSING_MIN_CHAPTERS,
    STAGE_TYPICAL_RANGES,
    STAGES,
    VALID_TRANSITIONS,
    can_transition,
    get_current_stage,
    get_stage_range,
    is_terminal,
)


def _plot(status: PlotStatus = PlotStatus.DRAFT, **kwargs) -> Plot:
    defaults = dict(plot_id="p1", type=PlotType.SUBPLOT, title="x", status=status)
    defaults.update(kwargs)
    return Plot(**defaults)


class TestValidTransitions:
    def test_all_6_transitions_present(self):
        """6 个非终态转换规则 (DRAFT/ACTIVE/PAUSED/CLOSING + 3 个 ACTIVE 出口)"""
        # 计数: DRAFT→ACTIVE, DRAFT→ABANDONED (1)
        #      ACTIVE→PAUSED, ACTIVE→CLOSING, ACTIVE→ABANDONED (3)
        #      PAUSED→ACTIVE, PAUSED→ABANDONED (2)
        #      CLOSING→CLOSED, CLOSING→ABANDONED (2)
        # = 8 总出口 (其中 ABANDONED 可从 3 态达)
        # 但 VALID_TRANSITIONS 是 dict[from -> set[to]],key 4 个非终态
        assert set(VALID_TRANSITIONS.keys()) == {
            PlotStatus.DRAFT, PlotStatus.ACTIVE,
            PlotStatus.PAUSED, PlotStatus.CLOSING,
        }
        # DRAFT 有 2 出口
        assert VALID_TRANSITIONS[PlotStatus.DRAFT] == {PlotStatus.ACTIVE, PlotStatus.ABANDONED}
        # ACTIVE 有 3 出口
        assert VALID_TRANSITIONS[PlotStatus.ACTIVE] == {
            PlotStatus.PAUSED, PlotStatus.CLOSING, PlotStatus.ABANDONED,
        }
        # PAUSED 有 2 出口
        assert VALID_TRANSITIONS[PlotStatus.PAUSED] == {PlotStatus.ACTIVE, PlotStatus.ABANDONED}
        # CLOSING 有 2 出口
        assert VALID_TRANSITIONS[PlotStatus.CLOSING] == {PlotStatus.CLOSED, PlotStatus.ABANDONED}

    def test_terminal_states_not_in_valid_transitions(self):
        """CLOSED / ABANDONED 是终态,不在 VALID_TRANSITIONS 中作为 key"""
        assert PlotStatus.CLOSED not in VALID_TRANSITIONS
        assert PlotStatus.ABANDONED not in VALID_TRANSITIONS


class TestCanTransition:
    @pytest.mark.parametrize("frm,to", [
        (PlotStatus.DRAFT, PlotStatus.ACTIVE),
        (PlotStatus.DRAFT, PlotStatus.ABANDONED),
        (PlotStatus.ACTIVE, PlotStatus.PAUSED),
        (PlotStatus.ACTIVE, PlotStatus.CLOSING),
        (PlotStatus.ACTIVE, PlotStatus.ABANDONED),
        (PlotStatus.PAUSED, PlotStatus.ACTIVE),
        (PlotStatus.PAUSED, PlotStatus.ABANDONED),
        (PlotStatus.CLOSING, PlotStatus.CLOSED),
        (PlotStatus.CLOSING, PlotStatus.ABANDONED),
    ])
    def test_valid_transitions_accepted(self, frm, to):
        assert can_transition(frm, to) is True

    @pytest.mark.parametrize("frm,to", [
        (PlotStatus.DRAFT, PlotStatus.PAUSED),  # 草稿不能直接暂停
        (PlotStatus.DRAFT, PlotStatus.CLOSING),
        (PlotStatus.DRAFT, PlotStatus.CLOSED),
        (PlotStatus.ACTIVE, PlotStatus.DRAFT),  # 不能回到草稿
        (PlotStatus.ACTIVE, PlotStatus.CLOSED),  # 必须经过 CLOSING
        (PlotStatus.PAUSED, PlotStatus.CLOSING),  # 暂停后必须先激活
        (PlotStatus.PAUSED, PlotStatus.CLOSED),
        (PlotStatus.CLOSING, PlotStatus.ACTIVE),  # CLOSING 不能回到 ACTIVE
        (PlotStatus.CLOSING, PlotStatus.PAUSED),
    ])
    def test_invalid_transitions_rejected(self, frm, to):
        assert can_transition(frm, to) is False

    def test_terminal_states_cannot_transition(self):
        """CLOSED / ABANDONED 不能再转换"""
        for terminal in (PlotStatus.CLOSED, PlotStatus.ABANDONED):
            for to in PlotStatus:
                assert can_transition(terminal, to) is False


class TestIsTerminal:
    def test_closed_is_terminal(self):
        assert is_terminal(PlotStatus.CLOSED) is True

    def test_abandoned_is_terminal(self):
        assert is_terminal(PlotStatus.ABANDONED) is True

    @pytest.mark.parametrize("s", [
        PlotStatus.DRAFT, PlotStatus.ACTIVE,
        PlotStatus.PAUSED, PlotStatus.CLOSING,
    ])
    def test_non_terminal_states(self, s):
        assert is_terminal(s) is False


class TestClosingMinChapters:
    def test_closing_min_chapters_is_2(self):
        """CLOSING 必须持续 ≥ 2 章"""
        assert CLOSING_MIN_CHAPTERS == 2


class TestStages:
    def test_7_stages_defined(self):
        assert len(STAGES) == 7
        assert set(STAGES) == {
            "seed", "build", "escalate", "climax", "resolve", "close", "echo",
        }

    def test_stage_typical_ranges_defined(self):
        """7 阶段都有典型章数范围 (min, max)"""
        assert set(STAGE_TYPICAL_RANGES.keys()) == set(STAGES)
        for stage in STAGES:
            mn, mx = STAGE_TYPICAL_RANGES[stage]
            assert mn >= 0
            assert mx >= mn

    def test_get_stage_range(self):
        mn, mx = get_stage_range("build")
        assert mn == 5
        assert mx == 15

    def test_get_stage_range_unknown_raises(self):
        with pytest.raises(ValueError, match="stage"):
            get_stage_range("nonexistent")


class TestGetCurrentStage:
    def _build_active_plot(self, birth_ch: int, close_ch: int) -> Plot:
        return Plot(
            plot_id="p1",
            type=PlotType.SUBPLOT,
            title="x",
            status=PlotStatus.ACTIVE,
            birth_ch=birth_ch,
            close_ch=close_ch,
            active_ch_range=(birth_ch, close_ch),
        )

    def test_seed_stage_at_birth(self):
        p = self._build_active_plot(birth_ch=10, close_ch=50)
        assert get_current_stage(p, current_ch=10) == "seed"

    def test_build_stage_after_seed(self):
        p = self._build_active_plot(birth_ch=10, close_ch=50)
        # seed 1-2 章后进入 build
        assert get_current_stage(p, current_ch=15) == "build"

    def test_climax_stage_just_before_close(self):
        p = self._build_active_plot(birth_ch=10, close_ch=50)
        # climax 在结束前 ~5 章 (resolve/close 各占 3-5 + 1-2)
        # 假设 escalate (5-10) + climax (2-5) 在 close 前
        # 40 章时应该接近 climax
        stage = get_current_stage(p, current_ch=40)
        assert stage in ("climax", "resolve")

    def test_echo_stage_after_close(self):
        p = self._build_active_plot(birth_ch=10, close_ch=50)
        # close_ch 之后是 echo
        assert get_current_stage(p, current_ch=60) == "echo"

    def test_close_stage_at_close_ch(self):
        p = self._build_active_plot(birth_ch=10, close_ch=50)
        # close_ch 应该是 close 阶段
        assert get_current_stage(p, current_ch=50) == "close"

    def test_unknown_plot_returns_echo(self):
        """未指定 birth_ch/close_ch 的 plot → echo (无信息)"""
        p = Plot(plot_id="p1", type=PlotType.SUBPLOT, title="x", status=PlotStatus.DRAFT)
        assert get_current_stage(p, current_ch=10) == "echo"
