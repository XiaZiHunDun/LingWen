"""Tests for PacingChecker.check_ripple_density (Phase 2.4).

Doc 1 §3.4 + Doc 4 联动:节奏检测器集成 Ripple wavefront。

核心方法:
- check_ripple_density(ripple_registry, current_ch, active_threshold=6) → list[Issue]
  - 活跃 ripple 数 > active_threshold → P2 issue (density 高)
  - wavefront 集中在单一章节 (> 3 ripple 同章节) → P1 issue (convergence)
  - 0 active → ()
  - 不修改现有 check() 签名

Protocol 抽象 ripple_registry (避免循环 import)
"""
from __future__ import annotations

from typing import Optional, Protocol

import pytest

from infra.consistency.checkers.pacing_checker import PacingChecker
from infra.consistency.engine.data_structures import (
    CheckerType,
    Issue,
    IssueSeverity,
)
from infra.world_model.data_structures import Ripple, RippleState
from infra.world_model.registry import RippleRegistry

# === Helpers ===

class _RippleRegistryLike(Protocol):
    """最小接口 — PacingChecker 实际需要 list_active + get_ripple"""

    def list_active(self) -> tuple[Ripple, ...]: ...
    def get_ripple(self, ripple_id: str) -> Optional[Ripple]: ...


def _ripple(ripple_id: str, state: RippleState = RippleState.OPEN, wavefront: tuple = (10,)) -> Ripple:
    return Ripple(
        ripple_id=ripple_id,
        origin_event="e",
        origin_ch=wavefront[0] if wavefront else 10,
        state=state,
        wavefront=wavefront,
    )


# === TestEmptyCases ===

class TestEmptyCases:
    """0 ripple 或全 RESOLVED → 无 issue"""

    def test_zero_active_ripples_no_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=200)
        assert issues == []

    def test_only_resolved_ripples_no_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(_ripple("r1", RippleState.RESOLVED))
        reg.add_ripple(_ripple("r2", RippleState.RESOLVED))
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=200)
        assert issues == []


# === TestDensityThreshold ===

class TestDensityThreshold:
    """活跃 ripple 数 > active_threshold → P2 issue"""

    def test_under_threshold_no_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # 5 active < 6 (default threshold),且每个 ripple wavefront 独立
        for i, ch in enumerate([50, 100, 150, 200, 250]):
            reg.add_ripple(_ripple(f"r{i}", wavefront=(ch,)))
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=300)
        assert issues == []

    def test_over_threshold_p2_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # 7 active > 6
        for i in range(7):
            reg.add_ripple(_ripple(f"r{i}", wavefront=(10,)))
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=200)
        # 应有至少 1 P2 issue (density)
        assert any(i.severity == IssueSeverity.P2 for i in issues)
        density_issues = [i for i in issues if "密度" in i.title or "density" in i.title.lower()]
        assert len(density_issues) >= 1

    def test_custom_threshold(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        for i in range(3):
            reg.add_ripple(_ripple(f"r{i}"))
        checker = PacingChecker()
        # 3 active > threshold=2 → P2
        issues = checker.check_ripple_density(reg, current_ch=200, active_threshold=2)
        assert any(i.severity == IssueSeverity.P2 for i in issues)


# === TestConvergence ===

class TestConvergence:
    """wavefront 集中在单一章节 → P1 issue (convergence)"""

    def test_no_convergence_when_spread(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # 4 个 ripple,wavefront 分散在不同章节
        for i, ch in enumerate([50, 100, 150, 200]):
            reg.add_ripple(_ripple(f"r{i}", wavefront=(ch,)))
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=200)
        # 无 P1 (convergence)
        assert not any(
            i.severity == IssueSeverity.P1 and ("集中" in i.title or "convergence" in i.title.lower())
            for i in issues
        )

    def test_convergence_p1_issue(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # 4 个 ripple wavefront 都含 ch100
        for i in range(4):
            reg.add_ripple(_ripple(f"r{i}", wavefront=(50, 100)))
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=100)
        # 至少 1 P1 (convergence)
        assert any(i.severity == IssueSeverity.P1 for i in issues)


# === TestMultipleIssues ===

class TestMultipleIssues:
    """密度高 + 集中 → 2 issues (1 P1 + 1 P2)"""

    def test_mixed_density_and_convergence(self, tmp_path):
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        # 4 个 ripple 集中在 ch100 + 3 个 ripple 分散 (= 7 active > threshold 6)
        for i in range(4):
            reg.add_ripple(_ripple(f"r_converge_{i}", wavefront=(50, 100)))
        for i, ch in enumerate([150, 200, 250]):
            reg.add_ripple(_ripple(f"r_spread_{i}", wavefront=(ch,)))
        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=300, active_threshold=6)
        # 7 active > 6 → P2 + 4 在 ch100 集中 (> 3 threshold) → P1
        severities = {i.severity for i in issues}
        assert IssueSeverity.P1 in severities
        assert IssueSeverity.P2 in severities


# === TestProtocolDecoupling ===

class TestProtocolDecoupling:
    """最小 stub registry 也能用"""

    def test_works_with_stub_registry(self, tmp_path):
        r1 = Ripple(ripple_id="r1", origin_event="e", origin_ch=10, wavefront=(10, 50, 100))
        r2 = Ripple(ripple_id="r2", origin_event="e", origin_ch=10, wavefront=(10, 50))
        ripples: dict[str, Ripple] = {"r1": r1, "r2": r2}

        class StubReg:
            def list_active(self) -> tuple[Ripple, ...]:
                return tuple(ripples.values())

            def get_ripple(self, ripple_id: str) -> Optional[Ripple]:
                return ripples.get(ripple_id)

        checker = PacingChecker()
        issues = checker.check_ripple_density(StubReg(), current_ch=100)
        # 2 active < 6 threshold → no issues
        assert issues == []
