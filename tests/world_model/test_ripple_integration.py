"""Tests for world_model Ripple end-to-end integration (Phase 1.5).

Doc 1 §3.4 worked example + 紧急工况验证:
1. ch010 挖坑 → ch050 涟漪扩散 → ch200 强平复 → ch350 终态保留
2. 8+ 个未平复 → 崩塌风险 > 0.7 → 11 个 → 报警 (> 0.8) clamp
3. Engine + Registry + Queries 全链路:Wavefront 过滤 + stale 检测 + 状态机
4. JSON 持久化 → 重新加载 → ripple 状态保持
5. 1 个 ripple 完整生命周期 + 多种平复模式 (STRONG / WEAK / UNRESOLVED) 串联

镜像 Phase 1.2 `test_subplot_integration.py` 风格。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.world_model import (
    MAX_OPEN_RIPPLOTS,
    NodeId,
    NodeType,
    ResolutionMode,
    Ripple,
    RippleEngine,
    RippleRegistry,
    RippleState,
    detect_unresolved_ripples,
    predict_collapse_risk,
    suggest_resolution_chapter,
)
from infra.world_model.queries import detect_unresolved_ripples as detect_unresolved_ripples_q
from infra.world_model.queries import predict_collapse_risk as predict_collapse_risk_q

# === Helpers ===

def _tmp_registry(tmp_path: Path) -> RippleRegistry:
    """创建使用 tmp_path 的 RippleRegistry (避免污染 .state/ripples/)"""
    return RippleRegistry(base_dir=tmp_path / "ripples")


# === TestEndToEndWorkedExample ===

class TestEndToEndWorkedExample:
    """Doc 1 §3.4 worked example: ch010 林尘身份 → ch200 强平复"""

    def test_full_lifecycle_ch010_to_ch200(self, tmp_path: Path):
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()

        # ch010: 挖坑 (林尘是星月之子)
        ripple = eng.register(
            reg, "ripple_identity_001", "林尘是星月之子", 10, planned_resolve_ch=200
        )
        assert ripple.state == RippleState.OPEN
        assert ripple.wavefront == (10,)
        assert reg.count_open() == 1

        # ch050: 涟漪扩散 (暗皇追踪)
        ripple = eng.propagate(
            reg, "ripple_identity_001", 50,
            affected_nodes=(NodeId(NodeType.CHARACTER, "暗皇"),),
        )
        assert ripple.state == RippleState.PROPAGATING
        assert 50 in ripple.wavefront
        assert ripple.wavefront == (10, 50)

        # ch100: 二次扩散 (星月议会介入)
        ripple = eng.propagate(reg, "ripple_identity_001", 100)
        assert ripple.state == RippleState.PROPAGATING
        assert 100 in ripple.wavefront

        # ch200: 平复开始 → 强平复 (100% 恢复,伏笔回收)
        ripple = eng.start_resolution(reg, "ripple_identity_001")
        assert ripple.state == RippleState.RESOLVING

        ripple = eng.resolve(reg, "ripple_identity_001", 200, ResolutionMode.STRONG)
        assert ripple.state == RippleState.RESOLVED
        assert ripple.resolved_ch == 200
        assert reg.count_open() == 0  # RESOLVED 不计入 open
        assert reg.count_resolved() == 1

    def test_wavefront_tracks_active_chapters(self, tmp_path: Path):
        """Doc 1 §3.4:波前随章节推进,过滤掉 future 章节"""
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        eng.register(reg, "r1", "e", 10, planned_resolve_ch=200)
        eng.propagate(reg, "r1", 50)
        eng.propagate(reg, "r1", 100)
        eng.propagate(reg, "r1", 200)

        # ch75: 看 active wavefront → 只含 ≤ 75 的章节
        r_final = reg.get_ripple("r1")
        active = eng.get_active_wavefront(r_final, current_ch=75)
        assert active == (10, 50)

        # ch200: 全展开
        active = eng.get_active_wavefront(r_final, current_ch=200)
        assert active == (10, 50, 100, 200)


# === TestCollapseAlarm ===

class TestCollapseAlarm:
    """Doc 1 §3.4: 累计未平复 > 10 → 崩塌风险 > 0.7 → > 0.8 报警"""

    def test_eight_stale_ripples_high_risk(self, tmp_path: Path):
        """8/10 = 0.8 → 触发阈值"""
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        # 注册 8 个 ripple,planned_resolve_ch=10 (10+grace=15 < 100 = stale)
        for i in range(8):
            eng.register(reg, f"r{i}", f"event_{i}", 1, planned_resolve_ch=10)

        risk = eng.compute_collapse_risk(reg, current_ch=100)
        assert risk == pytest.approx(0.8)
        assert risk >= 0.7  # Doc 1 报警阈值

    def test_eleven_stale_clamped_to_one(self, tmp_path: Path):
        """11 stale / 10 → clamp 1.0"""
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        # 11 > MAX_OPEN_RIPPLOTS,先注册 10,resolve 1 个腾位置再注册 1 个
        for i in range(MAX_OPEN_RIPPLOTS):
            eng.register(reg, f"r{i}", f"event_{i}", 1, planned_resolve_ch=10)
        # 解决 r0 → 释放 slot → 再注册 r10
        eng.resolve(reg, "r0", 50, ResolutionMode.STRONG)
        eng.register(reg, "r10", "event_10", 1, planned_resolve_ch=10)

        risk = eng.compute_collapse_risk(reg, current_ch=100)
        assert risk == pytest.approx(1.0)

    def test_open_ripple_limit_enforced(self, tmp_path: Path):
        """注册 10 个就拒绝第 11 个 (registry.add_ripple 校验)"""
        from infra.world_model.registry import OpenRippleLimitExceeded

        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        for i in range(MAX_OPEN_RIPPLOTS):
            eng.register(reg, f"r{i}", f"event_{i}", 1, planned_resolve_ch=100)
        with pytest.raises(OpenRippleLimitExceeded):
            eng.register(reg, "r_overflow", "boom", 1, planned_resolve_ch=100)

    def test_resolved_ripple_does_not_count_against_limit(self, tmp_path: Path):
        """RESOLVED 终态释放 slot,允许新增"""
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        # 占满 10 slot
        for i in range(MAX_OPEN_RIPPLOTS):
            eng.register(reg, f"r{i}", f"event_{i}", 1, planned_resolve_ch=100)
        # 解决 1 个 → 释放 slot
        eng.resolve(reg, "r0", 50, ResolutionMode.STRONG)
        # 新增成功
        eng.register(reg, "r_new", "new", 1, planned_resolve_ch=100)
        assert reg.count_open() == MAX_OPEN_RIPPLOTS

    def test_risk_drops_after_resolution(self, tmp_path: Path):
        """平复 ripple → 不再 stale → risk 降低"""
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        for i in range(8):
            eng.register(reg, f"r{i}", f"event_{i}", 1, planned_resolve_ch=10)

        before = eng.compute_collapse_risk(reg, current_ch=100)
        assert before == pytest.approx(0.8)

        # 平复 4 个
        for i in range(4):
            eng.resolve(reg, f"r{i}", 100, ResolutionMode.STRONG)
        after = eng.compute_collapse_risk(reg, current_ch=100)
        assert after == pytest.approx(0.4)


# === TestEngineRegistryQueriesIntegration ===

class TestEngineRegistryQueriesIntegration:
    """全链路:Engine 操作 → Registry 状态 → Queries 反馈"""

    def test_detect_unresolved_reflects_engine_state(self, tmp_path: Path):
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        # 1 fresh + 2 stale
        eng.register(reg, "r_fresh", "e1", 10, planned_resolve_ch=200)
        eng.register(reg, "r_stale1", "e2", 1, planned_resolve_ch=10)
        eng.register(reg, "r_stale2", "e3", 1, planned_resolve_ch=10)

        # ch50: stale1/stale2 应被检测 (10 + grace=5 < 50)
        stale = detect_unresolved_ripples(reg, current_ch=50)
        stale_ids = {r.ripple_id for r in stale}
        assert stale_ids == {"r_stale1", "r_stale2"}

        # 平复 stale1 → 不再 stale
        eng.resolve(reg, "r_stale1", 50, ResolutionMode.WEAK)
        stale = detect_unresolved_ripples(reg, current_ch=50)
        assert {r.ripple_id for r in stale} == {"r_stale2"}

    def test_predict_collapse_via_query_matches_engine(self, tmp_path: Path):
        """queries.predict_collapse_risk 应与 engine.compute_collapse_risk 一致"""
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        for i in range(7):
            eng.register(reg, f"r{i}", f"e{i}", 1, planned_resolve_ch=10)

        # 两种调用方式结果应一致
        risk_engine = eng.compute_collapse_risk(reg, current_ch=100)
        risk_query = predict_collapse_risk(reg, current_ch=100)
        assert risk_engine == risk_query
        assert risk_engine == pytest.approx(7 / MAX_OPEN_RIPPLOTS)

    def test_suggest_resolution_chapter_matches_decay(self, tmp_path: Path):
        """decay_rate=0.2 → origin + 5ch;0.5 → +2ch;0.1 → +10ch"""
        # decay=0.2 → origin=10 + 5 = 15
        r1 = Ripple(ripple_id="r1", origin_event="e", origin_ch=10, decay_rate=0.2)
        assert suggest_resolution_chapter(r1) == 15

        # decay=0.5 → origin=10 + 2 = 12
        r2 = Ripple(ripple_id="r2", origin_event="e", origin_ch=10, decay_rate=0.5)
        assert suggest_resolution_chapter(r2) == 12

        # decay=0.1 → origin=10 + 10 = 20
        r3 = Ripple(ripple_id="r3", origin_event="e", origin_ch=10, decay_rate=0.1)
        assert suggest_resolution_chapter(r3) == 20


# === TestJSONPersistence ===

class TestJSONPersistence:
    """registry.save() → JSON → registry.load() → ripple 状态保持"""

    def test_save_and_load_preserves_state(self, tmp_path: Path):
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        # 2 ripples: 1 OPEN + 1 RESOLVED
        eng.register(reg, "r_open", "e1", 10, planned_resolve_ch=200)
        eng.register(reg, "r_resolved", "e2", 20, planned_resolve_ch=100)
        eng.resolve(reg, "r_resolved", 100, ResolutionMode.STRONG)
        reg.save()

        # 重新加载
        reg2 = RippleRegistry(base_dir=tmp_path / "ripples")
        reg2.load()
        assert reg2.count() == 2
        r1 = reg2.get_ripple("r_open")
        assert r1 is not None
        assert r1.state == RippleState.OPEN
        assert r1.planned_resolve_ch == 200
        r2 = reg2.get_ripple("r_resolved")
        assert r2 is not None
        assert r2.state == RippleState.RESOLVED
        assert r2.resolved_ch == 100

    def test_save_creates_directory_if_missing(self, tmp_path: Path):
        reg = _tmp_registry(tmp_path / "new_subdir" / "deep")
        eng = RippleEngine()
        eng.register(reg, "r1", "e", 10, planned_resolve_ch=100)
        reg.save()  # 不应抛 FileNotFoundError
        assert (tmp_path / "new_subdir" / "deep" / "ripples" / "registry.json").exists()

    def test_loaded_json_is_human_readable(self, tmp_path: Path):
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        eng.register(reg, "r1", "e", 10, planned_resolve_ch=100)
        reg.save()
        raw = (tmp_path / "ripples" / "registry.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert "ripples" in data
        assert "r1" in data["ripples"]
        assert data["ripples"]["r1"]["state"] == "open"
        assert data["ripples"]["r1"]["planned_resolve_ch"] == 100


# === TestMultipleResolutionModes ===

class TestMultipleResolutionModes:
    """3 种平复模式 (STRONG/WEAK/UNRESOLVED) 都能完成生命周期"""

    @pytest.mark.parametrize("mode", [
        ResolutionMode.STRONG,
        ResolutionMode.WEAK,
        ResolutionMode.UNRESOLVED,
    ])
    def test_all_modes_lead_to_resolved(self, tmp_path: Path, mode):
        reg = _tmp_registry(tmp_path)
        eng = RippleEngine()
        eng.register(reg, f"r_{mode.value}", "e", 10, planned_resolve_ch=100)
        r = eng.resolve(reg, f"r_{mode.value}", 100, mode)
        assert r.state == RippleState.RESOLVED
        assert r.resolved_ch == 100
        # 不论模式,RESOLVED 都不计入 open
        assert reg.count_open() == 0
        assert reg.count_resolved() == 1


# === TestImportContract ===

class TestImportContract:
    """Public API 完整性:所有 1.5 符号从顶层可导入"""

    def test_top_level_imports(self):
        from infra.world_model import (
            MAX_OPEN_RIPPLOTS,
            RESOLUTION_GRACE_CH,
            ResolutionMode,
            Ripple,
            RippleEngine,
            RippleRegistry,
            RippleState,
            detect_unresolved_ripples,
            predict_collapse_risk,
            suggest_resolution_chapter,
        )
        # 全部可绑定 + 类型断言
        assert RippleEngine is not None
        assert RippleRegistry is not None
        assert MAX_OPEN_RIPPLOTS == 10
        assert RESOLUTION_GRACE_CH == 5
        assert RippleState.OPEN.value == "open"
        assert ResolutionMode.STRONG.value == "strong"
        assert callable(detect_unresolved_ripples)
        assert callable(predict_collapse_risk)
        assert callable(suggest_resolution_chapter)

    def test_queries_module_path_consistent(self):
        """queries.predict_collapse_risk 应与 __init__ 导出的一致"""
        from infra.world_model import predict_collapse_risk as top
        assert top is predict_collapse_risk_q
        from infra.world_model import detect_unresolved_ripples as top_d
        assert top_d is detect_unresolved_ripples_q
