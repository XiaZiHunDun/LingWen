"""Phase 2.1-2.6 端到端集成测试。

完整流水线:
1. LLM extraction: 解析 mock LLM 输出 (ripple_extraction 模板)
2. RippleEngine: register / propagate / resolve
3. SnapshotDiff: 比较两章的世界快照
4. PacingChecker.check_ripple_density: 密度检测
5. CoreForeshadowChecker.check_ripple_alignment: 状态机对齐
6. apply_ripple_resolution: 联动 subplot 状态

镜像 Phase 1.5 test_ripple_integration 风格。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
from infra.consistency.checkers.pacing_checker import PacingChecker
from infra.consistency.engine.data_structures import IssueSeverity
from infra.prompt_engineering import (
    ExtractedResolution,
    ExtractedRipple,
    RippleExtractionResult,
    parse_ripple_extraction,
)
from infra.prompt_engineering.templates import load_template, render_template
from infra.subplot.data_structures import Plot, PlotStatus, PlotType
from infra.subplot.registry import PlotRegistry
from infra.world_model import (
    LinkAction,
    ResolutionMode,
    Ripple,
    RippleEngine,
    RippleRegistry,
    RippleState,
    apply_ripple_resolution,
    diff_snapshots,
    link_subplot_to_ripple,
    predict_collapse_risk,
)
from infra.world_model.snapshot_diff import ChangeKind, EntityKind

# === Helpers ===

def _ripple(ripple_id: str, state: RippleState = RippleState.OPEN) -> Ripple:
    return Ripple(ripple_id=ripple_id, origin_event="e", origin_ch=10, state=state)


def _plot(plot_id: str, status: PlotStatus = PlotStatus.ACTIVE, related=()) -> Plot:
    return Plot(
        plot_id=plot_id,
        type=PlotType.SUBPLOT,
        title=f"plot_{plot_id}",
        status=status,
        birth_ch=10,
        active_ch_range=(10, 200),
        related_ripples=related,
    )


# === TestE2E_LLMToRippleLifecycle ===

class TestE2E_LLMToRippleLifecycle:
    """完整: 模板加载 → 解析 LLM 输出 → register → propagate → resolve"""

    def test_template_loads_and_parses(self):
        """ripple_extraction 模板加载成功"""
        template = load_template("ripple_extraction", version=1)
        assert template.scenario == "ripple_extraction"
        assert template.version == 1
        assert "{chapter_num}" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt
        assert "{active_ripples}" in template.user_prompt

    def test_template_renders(self):
        template = load_template("ripple_extraction", version=1)
        ctx = {
            "chapter_num": 100,
            "chapter_content": "林尘觉醒...",
            "active_ripples": "r1 (open)",
        }
        rendered = render_template(template, ctx)
        assert "100" in rendered.user_prompt
        assert "林尘觉醒" in rendered.user_prompt

    def test_parse_to_engine_pipeline(self, tmp_path):
        """解析 → register → propagate → resolve 全链路"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        eng = RippleEngine()

        # 1. 解析 mock LLM 输出
        raw = '''{
            "new_ripples": [
                {"ripple_id": "r1", "origin_event": "林尘身世", "origin_ch": 10, "planned_resolve_ch": 200}
            ],
            "resolved_ripples": []
        }'''
        result = parse_ripple_extraction(raw)
        assert len(result.new_ripples) == 1
        ext = result.new_ripples[0]
        assert ext.ripple_id == "r1"
        assert ext.planned_resolve_ch == 200

        # 2. register
        r = eng.register(reg, ext.ripple_id, ext.origin_event, ext.origin_ch,
                         planned_resolve_ch=ext.planned_resolve_ch)
        assert r.state == RippleState.OPEN

        # 3. propagate
        r = eng.propagate(reg, "r1", 50)
        assert r.state == RippleState.PROPAGATING

        # 4. resolve
        r = eng.resolve(reg, "r1", 200, ResolutionMode.STRONG)
        assert r.state == RippleState.RESOLVED

    def test_resolved_extraction_triggers_resolve(self, tmp_path):
        """LLM 输出 resolved_ripples → 实际 resolve"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        eng = RippleEngine()
        eng.register(reg, "r1", "e", 10, planned_resolve_ch=200)

        raw = '''{
            "new_ripples": [],
            "resolved_ripples": [
                {"ripple_id": "r1", "resolution_ch": 150, "mode": "weak"}
            ]
        }'''
        result = parse_ripple_extraction(raw)
        assert len(result.resolved_ripples) == 1
        ext_res: ExtractedResolution = result.resolved_ripples[0]
        assert ext_res.ripple_id == "r1"
        assert ext_res.mode == "weak"

        # 用 mode 解析为 ResolutionMode
        mode = ResolutionMode(ext_res.mode)
        r = eng.resolve(reg, "r1", ext_res.resolution_ch, mode)
        assert r.resolved_ch == 150
        assert r.state == RippleState.RESOLVED


# === TestE2E_SnapshotDiff ===

class TestE2E_SnapshotDiff:
    """SnapshotDiff 检测两章世界状态变化"""

    def test_diff_ripple_state_change(self, tmp_path):
        from infra.world_model.data_structures import MentalLine, PhysicalLine, WorldSnapshot

        prev = WorldSnapshot(
            snapshot_id="s1",
            chapter=100,
            timestamp=datetime(2026, 6, 4),
            active_ripples=(_ripple("r1", RippleState.OPEN),),
        )
        curr = WorldSnapshot(
            snapshot_id="s2",
            chapter=200,
            timestamp=datetime(2026, 6, 4),
            active_ripples=(_ripple("r1", RippleState.RESOLVED),),
        )
        changes = diff_snapshots(prev, curr)
        ripple_changes = [c for c in changes if c.entity == EntityKind.RIPPLE]
        assert len(ripple_changes) == 1
        c = ripple_changes[0]
        assert c.kind == ChangeKind.MODIFIED
        # state 字段变化
        state_fc = next(fc for fc in c.field_changes if fc[0] == "state")
        assert state_fc[1] == RippleState.OPEN
        assert state_fc[2] == RippleState.RESOLVED

    def test_diff_add_new_ripple(self, tmp_path):
        from infra.world_model.data_structures import MentalLine, PhysicalLine, WorldSnapshot

        prev = WorldSnapshot(
            snapshot_id="s1", chapter=100, timestamp=datetime(2026, 6, 4),
        )
        curr = WorldSnapshot(
            snapshot_id="s2", chapter=200, timestamp=datetime(2026, 6, 4),
            active_ripples=(_ripple("r1", RippleState.OPEN),),
        )
        changes = diff_snapshots(prev, curr)
        ripple_changes = [c for c in changes if c.entity == EntityKind.RIPPLE]
        assert len(ripple_changes) == 1
        assert ripple_changes[0].kind == ChangeKind.ADDED


# === TestE2E_CheckerIntegration ===

class TestE2E_CheckerIntegration:
    """两个 checker 集成到完整流水线"""

    def test_pacing_density_detects_overload(self, tmp_path):
        """register 8 个 active ripple → PacingChecker 检测 P2 density"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        for i in range(8):
            reg.add_ripple(Ripple(
                ripple_id=f"r{i}", origin_event="e", origin_ch=10,
                state=RippleState.OPEN, wavefront=(10, 50),
            ))

        checker = PacingChecker()
        issues = checker.check_ripple_density(reg, current_ch=100, active_threshold=6)
        # 8 active > 6 → P2
        assert any(i.severity == IssueSeverity.P2 for i in issues)

    def test_foreshadow_detects_overdue(self, tmp_path):
        """register 1 overdue ripple → CoreForeshadowChecker 检测 P1"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        reg.add_ripple(Ripple(
            ripple_id="r1", origin_event="e", origin_ch=10,
            state=RippleState.OPEN, planned_resolve_ch=10,
        ))

        checker = CoreForeshadowChecker(chapters_dir=tmp_path)
        issues = checker.check_ripple_alignment(reg, current_ch=100)
        # current=100, planned=10, 差 90 > 5 → P1
        assert any(i.severity == IssueSeverity.P1 for i in issues)

    def test_collapse_risk_after_resolution_drops(self, tmp_path):
        """resolve 几个 ripple → collapse_risk 降低"""
        reg = RippleRegistry(base_dir=tmp_path / "ripples")
        eng = RippleEngine()
        for i in range(8):
            eng.register(reg, f"r{i}", "e", 1, planned_resolve_ch=10)

        before = predict_collapse_risk(reg, current_ch=100)
        # 平复 4 个
        for i in range(4):
            eng.resolve(reg, f"r{i}", 100, ResolutionMode.STRONG)
        after = predict_collapse_risk(reg, current_ch=100)
        assert before > after


# === TestE2E_RippleSubplotLink ===

class TestE2E_RippleSubplotLink:
    """Ripple ↔ Subplot 联动"""

    def test_link_subplot_to_ripple_then_resolve(self, tmp_path):
        """link → register → resolve 触发 ACTIVE → CLOSING"""
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        eng = RippleEngine()

        # 1. 创建 subplot
        plot = _plot("p1", PlotStatus.ACTIVE)
        sreg.add_plot(plot)

        # 2. register ripple
        r = eng.register(rreg, "r1", "e", 10, planned_resolve_ch=200)
        # 3. link ripple → subplot
        new_plot = link_subplot_to_ripple(plot, r)
        sreg._plots["p1"] = new_plot  # 手动更新 registry

        # 4. resolve ripple → 触发 ACTIVE → CLOSING
        eng.resolve(rreg, "r1", 200, ResolutionMode.STRONG)
        actions = apply_ripple_resolution(rreg, sreg, "r1", current_ch=200, auto_close=True)

        assert len(actions) == 1
        a: LinkAction = actions[0]
        assert a.plot_id == "p1"
        assert a.from_status == PlotStatus.ACTIVE
        assert a.to_status == PlotStatus.CLOSING

        # subplot 状态已更新
        p1 = sreg.get_plot("p1")
        assert p1.status == PlotStatus.CLOSING
        assert p1.close_ch == 202  # current_ch + 2

    def test_idempotent_link(self):
        """重复 link 同一 ripple → 幂等"""
        plot = _plot("p1", related=("r1",))
        r = _ripple("r1")

        new1 = link_subplot_to_ripple(plot, r)
        new2 = link_subplot_to_ripple(new1, r)
        # 不应重复
        assert new2.related_ripples == ("r1",)
