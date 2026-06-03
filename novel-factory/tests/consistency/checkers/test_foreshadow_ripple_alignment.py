"""Tests for CoreForeshadowChecker.check_ripple_alignment (Phase 2.5).

Doc 1 §3.4 + Doc 4 联动:伏笔检测器对齐 Ripple 状态机。

核心方法:
- check_ripple_alignment(ripple_registry, current_ch) → list[Issue]
  - OPEN/PROPAGATING/RESOLVING 状态 + planned_resolve_ch < current_ch - 5 → P1 (overdue)
  - OPEN 状态 + planned_resolve_ch is None → P3 (warning)
  - RESOLVED 状态 + resolved_ch 在 current_ch-5..current_ch 范围 → 无 issue
  - 不修改现有 check() / check_chapter() 签名

Protocol 抽象 ripple_registry
"""
from __future__ import annotations

from typing import Optional, Protocol

import pytest

from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
from infra.consistency.engine.data_structures import (
    CheckerType,
    Issue,
    IssueSeverity,
)
from infra.world_model.data_structures import Ripple, RippleState
from infra.world_model.registry import RippleRegistry
from infra.world_model.lifecycle import RESOLUTION_GRACE_CH


# === Helpers ===

class _RippleRegistryLike(Protocol):
    def list_all(self) -> tuple[Ripple, ...]: ...
    def get_ripple(self, ripple_id: str) -> Optional[Ripple]: ...


def _ripple(
    ripple_id: str,
    state: RippleState = RippleState.OPEN,
    origin_ch: int = 10,
    planned_resolve_ch: Optional[int] = None,
    resolved_ch: Optional[int] = None,
) -> Ripple:
    return Ripple(
        ripple_id=ripple_id,
        origin_event="e",
        origin_ch=origin_ch,
        state=state,
        planned_resolve_ch=planned_resolve_ch,
        resolved_ch=resolved_ch,
    )


# === TestEmptyCases ===

class TestEmptyCases:
    """0 ripple → 无 issue"""

    def test_zero_ripples_no_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=200)
        assert issues == []

    def test_only_resolved_no_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.RESOLVED, resolved_ch=200))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=200)
        assert issues == []


# === TestOverdueDetection ===

class TestOverdueDetection:
    """OPEN/PROPAGATING/RESOLVING + planned 超期 → P1"""

    def test_open_overdue_p1_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # planned_resolve_ch=10, current_ch=100 → overdue (100 - 10 > 5)
        reg.add_ripple(_ripple("r1", RippleState.OPEN, planned_resolve_ch=10))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        assert any(i.severity == IssueSeverity.P1 for i in issues)

    def test_propagating_overdue_p1_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.PROPAGATING, planned_resolve_ch=10))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        assert any(i.severity == IssueSeverity.P1 for i in issues)

    def test_resolving_overdue_p1_issue(self, tmp_path):
        """正在平复但已超 planned_resolve_ch → P1"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.RESOLVING, planned_resolve_ch=10))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        assert any(i.severity == IssueSeverity.P1 for i in issues)

    def test_open_within_grace_no_issue(self, tmp_path):
        """planned_resolve_ch 在 grace 范围内 → 无 issue"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # current_ch=100, planned=98, 差 2 ≤ grace=5
        reg.add_ripple(_ripple("r1", RippleState.OPEN, planned_resolve_ch=98))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        assert issues == []


# === TestPlannedMissing ===

class TestPlannedMissing:
    """OPEN 状态 + planned_resolve_ch is None → P3 (warning)"""

    def test_open_no_planned_p3_warning(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.OPEN, planned_resolve_ch=None))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        # 至少 1 P3 (warning)
        assert any(i.severity == IssueSeverity.P3 for i in issues)

    def test_propagating_no_planned_p3_warning(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.PROPAGATING, planned_resolve_ch=None))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        assert any(i.severity == IssueSeverity.P3 for i in issues)


# === TestResolvedRecent ===

class TestResolvedRecent:
    """RESOLVED 状态 + resolved_ch 在范围 → 无 issue"""

    def test_resolved_at_current_no_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.RESOLVED, resolved_ch=200))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=200)
        assert issues == []

    def test_resolved_recent_no_issue(self, tmp_path):
        """resolved_ch = current_ch - 3, 在 5 章内 → 无 issue"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.RESOLVED, resolved_ch=197))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=200)
        assert issues == []


# === TestMultipleIssues ===

class TestMultipleIssues:
    """混合场景"""

    def test_resolved_plus_open_overdue(self, tmp_path):
        """1 RESOLVED + 1 OPEN overdue → 1 P1"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r_resolved", RippleState.RESOLVED, resolved_ch=200))
        reg.add_ripple(_ripple("r_overdue", RippleState.OPEN, planned_resolve_ch=10))
        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=200)
        # 1 P1 (overdue)
        p1_issues = [i for i in issues if i.severity == IssueSeverity.P1]
        assert len(p1_issues) == 1
        assert "r_overdue" in p1_issues[0].evidence or "r_overdue" in p1_issues[0].id


# === TestProtocolDecoupling ===

class TestProtocolDecoupling:
    """最小 stub registry 也能用"""

    def test_works_with_stub_registry(self, tmp_path):
        r1 = _ripple("r1", RippleState.OPEN, planned_resolve_ch=10)
        ripples = {"r1": r1}

        class StubReg:
            def list_all(self) -> tuple[Ripple, ...]:
                return tuple(ripples.values())

            def get_ripple(self, ripple_id: str) -> Optional[Ripple]:
                return ripples.get(ripple_id)

        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(StubReg(), current_ch=100)
        assert any(i.severity == IssueSeverity.P1 for i in issues)


# === TestConstants ===

class TestConstants:
    """验证 grace 常量正确"""

    def test_grace_constant(self):
        assert RESOLUTION_GRACE_CH == 5
