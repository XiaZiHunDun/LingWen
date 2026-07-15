"""Tests for world_model.lifecycle (Phase 1.5 — RippleEngine state machine).

Doc 1 §3.4 — Ripple 4 状态机 + 平复模式校验。

4 状态:
  OPEN → PROPAGATING / RESOLVING / RESOLVED
  PROPAGATING → RESOLVING / RESOLVED
  RESOLVING → RESOLVED
  RESOLVED → terminal (set())

3 平复模式:STRONG (100% 恢复) / WEAK (60-80% + 新稳态) / UNRESOLVED (接受但不关闭)
"""
from __future__ import annotations

import pytest

from infra.world_model.data_structures import (
    ResolutionMode,
    Ripple,
    RippleState,
)
from infra.world_model.lifecycle import (
    COLLAPSE_RISK_THRESHOLD,
    MAX_OPEN_RIPPLOTS,
    RESOLUTION_GRACE_CH,
    VALID_TRANSITIONS,
    can_transition,
    is_terminal,
)

# === Helpers ===

def _ripple(state: RippleState = RippleState.OPEN) -> Ripple:
    return Ripple(
        ripple_id="r1",
        origin_event="e",
        origin_ch=10,
        state=state,
        planned_resolve_ch=200,
    )


# === TestRippleStateMachine ===

class TestRippleStateMachine:
    def test_valid_transitions_is_frozen_mapping(self):
        # 4 状态都有定义 (RESOLVED terminal = 空 set)
        assert RippleState.OPEN in VALID_TRANSITIONS
        assert RippleState.PROPAGATING in VALID_TRANSITIONS
        assert RippleState.RESOLVING in VALID_TRANSITIONS
        assert RippleState.RESOLVED in VALID_TRANSITIONS

    def test_open_can_transition_to_propagating_resolving_resolved(self):
        r = _ripple(RippleState.OPEN)
        assert can_transition(r, RippleState.PROPAGATING) is True
        assert can_transition(r, RippleState.RESOLVING) is True
        assert can_transition(r, RippleState.RESOLVED) is True

    def test_propagating_can_transition_to_resolving_resolved(self):
        r = _ripple(RippleState.PROPAGATING)
        assert can_transition(r, RippleState.RESOLVING) is True
        assert can_transition(r, RippleState.RESOLVED) is True
        # PROPAGATING 不能回 OPEN
        assert can_transition(r, RippleState.OPEN) is False

    def test_resolving_can_only_transition_to_resolved(self):
        r = _ripple(RippleState.RESOLVING)
        assert can_transition(r, RippleState.RESOLVED) is True
        # RESOLVING 不能回 PROPAGATING/OPEN
        assert can_transition(r, RippleState.OPEN) is False
        assert can_transition(r, RippleState.PROPAGATING) is False

    def test_resolved_is_terminal(self):
        r = _ripple(RippleState.RESOLVED)
        assert is_terminal(r.state) is True
        # RESOLVED 任何转换都 False
        for s in RippleState:
            assert can_transition(r, s) is False, f"RESOLVED → {s} 应禁止"

    def test_self_transition_is_invalid(self):
        # 同状态自转 = false (必须显式 transition)
        for s in RippleState:
            r = _ripple(s)
            assert can_transition(r, s) is False, f"self-transition {s}→{s} 应禁止"


# === TestRippleConstants ===

class TestRippleConstants:
    def test_max_open_ripplots_is_10(self):
        # Doc 1 §3.4: 累计未平复 Ripple > 10 → 崩塌风险 > 0.7
        assert MAX_OPEN_RIPPLOTS == 10

    def test_resolution_grace_ch_is_5(self):
        # 计划平复可超 current_ch + grace = 5
        assert RESOLUTION_GRACE_CH == 5

    def test_collapse_risk_threshold_is_0_8(self):
        # Doc 1: 崩塌风险 > 0.8 系统报警
        assert COLLAPSE_RISK_THRESHOLD == pytest.approx(0.8)


# === TestResolutionMode ===

class TestResolutionMode:
    def test_three_modes_defined(self):
        # 3 个平复模式
        assert ResolutionMode.STRONG.value == "strong"
        assert ResolutionMode.WEAK.value == "weak"
        assert ResolutionMode.UNRESOLVED.value == "unresolved"

    def test_resolution_mode_str_enum(self):
        # str Enum pattern
        for m in ResolutionMode:
            assert isinstance(m.value, str)
            assert m.name == m.value.upper()
