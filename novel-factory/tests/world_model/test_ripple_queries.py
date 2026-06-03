"""Tests for world_model.queries (Phase 1.5 — 3 query helpers).

Doc 1 §3.4 核心 query:
- detect_unresolved_ripples: state != RESOLVED and current_ch > planned_resolve_ch + grace
- predict_collapse_risk: len(stale) / MAX_OPEN_RIPPLOTS
- suggest_resolution_chapter: origin_ch + int(1.0 / max(decay_rate, 0.1))
"""
from __future__ import annotations

import pytest

from infra.world_model.data_structures import (
    Ripple,
    RippleState,
)
from infra.world_model.lifecycle import (
    MAX_OPEN_RIPPLOTS,
    RESOLUTION_GRACE_CH,
)
from infra.world_model.queries import (
    detect_unresolved_ripples,
    predict_collapse_risk,
    suggest_resolution_chapter,
)

# === Stub registry ===

class _StubRegistry:
    def __init__(self, ripples: tuple[Ripple, ...] = ()) -> None:
        self._ripples = {r.ripple_id: r for r in ripples}

    def list_active(self) -> tuple[Ripple, ...]:
        return tuple(self._ripples.values())


def _ripple(ripple_id: str, state: RippleState = RippleState.OPEN,
            planned_resolve_ch: int = 10, decay_rate: float = 0.2) -> Ripple:
    return Ripple(
        ripple_id=ripple_id,
        origin_event="e",
        origin_ch=1,
        state=state,
        decay_rate=decay_rate,
        planned_resolve_ch=planned_resolve_ch,
    )


# === TestDetectUnresolvedRipples ===

class TestDetectUnresolvedRipples:
    def test_empty_registry_returns_empty(self):
        reg = _StubRegistry()
        assert detect_unresolved_ripples(reg, current_ch=100) == ()

    def test_resolved_excluded(self):
        reg = _StubRegistry((_ripple("r1", state=RippleState.RESOLVED, planned_resolve_ch=1),))
        assert detect_unresolved_ripples(reg, current_ch=100) == ()

    def test_unresolved_within_grace_excluded(self):
        # current_ch=10, planned=20, grace=5 → 20+5=25 > 10,不在 stale
        reg = _StubRegistry((_ripple("r1", planned_resolve_ch=20),))
        assert detect_unresolved_ripples(reg, current_ch=10) == ()

    def test_unresolved_beyond_grace_included(self):
        # current_ch=50, planned=20, grace=5 → 20+5=25 < 50,stale
        reg = _StubRegistry((_ripple("r1", planned_resolve_ch=20),))
        stale = detect_unresolved_ripples(reg, current_ch=50)
        assert len(stale) == 1
        assert stale[0].ripple_id == "r1"

    def test_propagating_and_resolving_count_as_unresolved(self):
        # 任意非 RESOLVED 状态都计 unresolved
        reg = _StubRegistry((
            _ripple("r_open", state=RippleState.OPEN, planned_resolve_ch=1),
            _ripple("r_prop", state=RippleState.PROPAGATING, planned_resolve_ch=1),
            _ripple("r_resv", state=RippleState.RESOLVING, planned_resolve_ch=1),
        ))
        stale = detect_unresolved_ripples(reg, current_ch=100)
        assert len(stale) == 3

    def test_custom_grace(self):
        # grace=10 时,planned=20+10=30,current=25 → not stale
        reg = _StubRegistry((_ripple("r1", planned_resolve_ch=20),))
        assert detect_unresolved_ripples(reg, current_ch=25, grace=10) == ()

    def test_no_planned_resolve_ch_excluded(self):
        # 没 planned_resolve_ch 的 ripple 不参与 stale 检测
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=1)
        reg = _StubRegistry((r,))
        assert detect_unresolved_ripples(reg, current_ch=100) == ()


# === TestPredictCollapseRisk ===

class TestPredictCollapseRisk:
    def test_zero_stale_zero_risk(self):
        reg = _StubRegistry()
        assert predict_collapse_risk(reg, current_ch=100) == 0.0

    def test_one_stale_elevated(self):
        reg = _StubRegistry((_ripple("r1", planned_resolve_ch=1),))
        risk = predict_collapse_risk(reg, current_ch=100)
        assert risk == pytest.approx(1 / MAX_OPEN_RIPPLOTS)

    def test_clamped_to_one(self):
        # 15 stale / 10 = 1.5 → clamp 1.0
        reg = _StubRegistry(tuple(_ripple(f"r{i}", planned_resolve_ch=1) for i in range(15)))
        assert predict_collapse_risk(reg, current_ch=100) == 1.0

    def test_doc1_threshold_above_0_7(self):
        # 8 stale / 10 = 0.8 → Doc 1 报警
        reg = _StubRegistry(tuple(_ripple(f"r{i}", planned_resolve_ch=1) for i in range(8)))
        risk = predict_collapse_risk(reg, current_ch=100)
        assert risk == pytest.approx(0.8)
        assert risk >= 0.7  # Doc 1 threshold


# === TestSuggestResolutionChapter ===

class TestSuggestResolutionChapter:
    def test_default_decay_rate_0_2_suggests_5_ch(self):
        # origin=1, decay=0.2 → 1 + int(1/0.2) = 1 + 5 = 6
        r = _ripple("r1", decay_rate=0.2)
        assert suggest_resolution_chapter(r) == 6

    def test_decay_rate_0_5_suggests_2_ch(self):
        # decay=0.5 → 1 + int(1/0.5) = 1 + 2 = 3
        r = _ripple("r1", decay_rate=0.5)
        assert suggest_resolution_chapter(r) == 3

    def test_decay_rate_0_1_suggests_10_ch(self):
        # decay=0.1 → 1 + int(1/0.1) = 1 + 10 = 11
        r = _ripple("r1", decay_rate=0.1)
        assert suggest_resolution_chapter(r) == 11

    def test_decay_rate_clamped_to_min_0_1(self):
        # decay=0.05 → max(0.05, 0.1) = 0.1 → 1 + 10 = 11
        r = _ripple("r1", decay_rate=0.05)
        assert suggest_resolution_chapter(r) == 11
