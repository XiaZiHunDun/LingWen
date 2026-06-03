"""Tests for world_model.engine (Phase 1.5 — RippleEngine).

Doc 1 §3.4 — Ripple 传播/衰减/平复 6 方法:
  1. register(registry, ripple_id, origin_event, origin_ch, planned_resolve_ch)
  2. propagate(registry, ripple_id, current_ch, affected_nodes, affected_relations)
  3. start_resolution(registry, ripple_id)
  4. resolve(registry, ripple_id, current_ch, mode)
  5. compute_collapse_risk(registry, current_ch)
  6. get_active_wavefront(ripple, current_ch)

状态变更通过 dataclasses.replace,无 mutation。

测试用 _StubRegistry (in-memory dict) 解耦 RippleRegistry (1.5.g/h 才实施),
确保 engine 逻辑独立可测。
"""
from __future__ import annotations

import pytest

from infra.world_model.data_structures import (
    NodeId,
    NodeType,
    ResolutionMode,
    Ripple,
    RippleState,
)
from infra.world_model.engine import RippleEngine

# === Stub registry (解耦 RippleRegistry) ===

class _StubRegistry:
    """最小 registry 接口,供 engine 测试独立使用"""

    def __init__(self) -> None:
        self._ripples: dict[str, Ripple] = {}

    def add_ripple(self, ripple: Ripple) -> None:
        if ripple.ripple_id in self._ripples:
            raise ValueError(f"duplicate ripple_id: {ripple.ripple_id}")
        self._ripples[ripple.ripple_id] = ripple

    def get_ripple(self, ripple_id: str) -> Ripple | None:
        return self._ripples.get(ripple_id)

    def update_ripple(self, ripple: Ripple) -> None:
        self._ripples[ripple.ripple_id] = ripple

    def list_active(self) -> tuple[Ripple, ...]:
        return tuple(self._ripples.values())


@pytest.fixture
def engine() -> RippleEngine:
    return RippleEngine()


@pytest.fixture
def registry() -> _StubRegistry:
    return _StubRegistry()


# === TestRegister ===

class TestRegister:
    def test_register_creates_open_ripple(self, engine, registry):
        r = engine.register(registry, "r1", "星月之子身世", 10, planned_resolve_ch=200)
        assert r.state == RippleState.OPEN
        assert r.ripple_id == "r1"
        assert r.origin_event == "星月之子身世"
        assert r.origin_ch == 10
        assert r.planned_resolve_ch == 200
        # wavefront 初始包含 origin_ch (ensure origin chapter 算 active)
        assert r.wavefront == (10,)
        assert r.affected_nodes == ()

    def test_register_stores_in_registry(self, engine, registry):
        r = engine.register(registry, "r1", "e", 1, planned_resolve_ch=10)
        assert registry.get_ripple("r1") == r

    def test_register_rejects_planned_resolve_le_origin_ch(self, engine, registry):
        with pytest.raises(ValueError, match="(?i)planned_resolve_ch"):
            engine.register(registry, "r1", "e", 100, planned_resolve_ch=50)

    def test_register_with_affected_nodes(self, engine, registry):
        nodes = (NodeId(NodeType.CHARACTER, "林尘"), NodeId(NodeType.CHARACTER, "暗皇"))
        r = engine.register(registry, "r1", "e", 1, planned_resolve_ch=10,
                            affected_nodes=nodes)
        assert r.affected_nodes == nodes


# === TestPropagate ===

class TestPropagate:
    def test_propagate_appends_to_wavefront(self, engine, registry):
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.propagate(registry, "r1", 50)
        assert r.state == RippleState.PROPAGATING
        assert 50 in r.wavefront

    def test_propagate_dedupes_wavefront(self, engine, registry):
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        engine.propagate(registry, "r1", 50)
        r = engine.propagate(registry, "r1", 50)  # same chapter
        assert r.wavefront.count(50) == 1

    def test_propagate_with_affected_nodes(self, engine, registry):
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        nodes = (NodeId(NodeType.CHARACTER, "暗皇"),)
        r = engine.propagate(registry, "r1", 50, affected_nodes=nodes)
        assert r.affected_nodes == nodes

    def test_propagate_keeps_origin_ch_in_wavefront(self, engine, registry):
        # 初始 wavefront 应包含 origin_ch (ensure first 章节也算 active)
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.propagate(registry, "r1", 50)
        assert 10 in r.wavefront  # origin_ch
        assert 50 in r.wavefront  # current


# === TestStartResolution ===

class TestStartResolution:
    def test_start_resolution_from_open(self, engine, registry):
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.start_resolution(registry, "r1")
        assert r.state == RippleState.RESOLVING

    def test_start_resolution_from_propagating(self, engine, registry):
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        engine.propagate(registry, "r1", 50)
        r = engine.start_resolution(registry, "r1")
        assert r.state == RippleState.RESOLVING

    def test_start_resolution_unknown_ripple_raises(self, engine, registry):
        with pytest.raises(ValueError, match="(?i)not found"):
            engine.start_resolution(registry, "nonexistent")


# === TestResolve ===

class TestResolve:
    def test_resolve_strong_sets_resolved_ch(self, engine, registry):
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.resolve(registry, "r1", 200, ResolutionMode.STRONG)
        assert r.state == RippleState.RESOLVED
        assert r.resolved_ch == 200

    def test_resolve_weak_allows_60_80_pct(self, engine, registry):
        # WEAK = 60-80% 恢复 + 新稳态;resolved_ch 仍记录,但 state 终态
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.resolve(registry, "r1", 200, ResolutionMode.WEAK)
        assert r.state == RippleState.RESOLVED
        assert r.resolved_ch == 200

    def test_resolve_from_open_directly(self, engine, registry):
        # OPEN → RESOLVED (one-step 平复) 合法
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.resolve(registry, "r1", 200, ResolutionMode.STRONG)
        assert r.state == RippleState.RESOLVED

    def test_resolve_unresolved_marks_terminal(self, engine, registry):
        # UNRESOLVED 模式 = 接受但不关闭;但 state 仍 → RESOLVED
        # (因为"标记长期未平复"也是终态,只是没回收)
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        r = engine.resolve(registry, "r1", 500, ResolutionMode.UNRESOLVED)
        assert r.state == RippleState.RESOLVED
        assert r.resolved_ch == 500


# === TestComputeCollapseRisk ===

class TestComputeCollapseRisk:
    def test_empty_registry_zero_risk(self, engine, registry):
        assert engine.compute_collapse_risk(registry, current_ch=100) == 0.0

    def test_no_stale_ripples_zero_risk(self, engine, registry):
        # ripple 还未超 planned_resolve_ch + grace
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=200)
        assert engine.compute_collapse_risk(registry, current_ch=50) == 0.0

    def test_stale_ripples_elevate_risk(self, engine, registry):
        # 1 个 stale ripple,1/10 = 0.1
        engine.register(registry, "r1", "e", 10, planned_resolve_ch=20)
        # current_ch=50, planned_resolve_ch + grace = 25, stale
        risk = engine.compute_collapse_risk(registry, current_ch=50)
        assert risk > 0.0

    def test_collapse_risk_clamped_to_1(self, engine, registry):
        # 15 stale / 10 limit → clamp 1.0
        for i in range(15):
            engine.register(registry, f"r{i}", "e", i, planned_resolve_ch=i + 1)
        risk = engine.compute_collapse_risk(registry, current_ch=100)
        assert risk <= 1.0


# === TestGetActiveWavefront ===

class TestGetActiveWavefront:
    def test_wavefront_before_origin_ch_empty(self, engine):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=10, wavefront=())
        assert engine.get_active_wavefront(r, current_ch=5) == ()

    def test_wavefront_includes_origin_and_propagation(self, engine):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=10, wavefront=(10, 50, 100))
        assert engine.get_active_wavefront(r, current_ch=50) == (10, 50)

    def test_wavefront_clamped_to_current_ch(self, engine):
        r = Ripple(ripple_id="r1", origin_event="e", origin_ch=10, wavefront=(10, 50, 100, 200))
        assert engine.get_active_wavefront(r, current_ch=75) == (10, 50)


# === TestIntegration: ch010→ch050→ch200 worked example ===

class TestRippleWorkedExample:
    """Doc 1 §3.4 worked example: ch010 林尘身份 → ch050 涟漪扩散 → ch200 强平复"""

    def test_full_lifecycle(self, engine, registry):
        # ch010: 挖坑
        r = engine.register(registry, "ripple_identity", "林尘是星月之子",
                            10, planned_resolve_ch=200)
        assert r.state == RippleState.OPEN

        # ch050: 涟漪扩散 (暗皇追踪)
        r = engine.propagate(registry, r.ripple_id, 50,
                             affected_nodes=(NodeId(NodeType.CHARACTER, "暗皇"),))
        assert r.state == RippleState.PROPAGATING
        assert 50 in r.wavefront

        # ch200: 强平复
        r = engine.resolve(registry, r.ripple_id, 200, ResolutionMode.STRONG)
        assert r.state == RippleState.RESOLVED
        assert r.resolved_ch == 200
