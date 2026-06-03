"""Tests for world_model.links (Phase 2.3 — Ripple ↔ Subplot 联动).

Doc 1 §3.4 + Doc 3 联动:
- link_subplot_to_ripple: 把 ripple_id 加入 Plot.related_ripples (idempotent)
- apply_ripple_resolution: ripple RESOLVED 时联动相关 subplot
  - ACTIVE → CLOSING (per Phase 1.2 状态机, 需 ≥2 章)
  - auto_close=True (default): 自动转换
  - auto_close=False: dry-run, 只记录
- LinkAction: frozen dataclass 记录每次状态转换

关键约束:
- Protocol `_SubplotRegistryLike` 解耦,接受最小接口
- ripple 不存在 → RippleNotFoundError
- subplot 已 CLOSED/ABANDONED → 跳过 (幂等)
- CLOSING_MIN_CHAPTERS = 2: apply 时需 current_ch + 2 <= close_ch
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional, Protocol

import pytest

from infra.subplot.data_structures import (
    Plot,
    PlotStatus,
    PlotType,
)
from infra.subplot.registry import PlotRegistry
from infra.world_model.data_structures import Ripple, RippleState
from infra.world_model.links import (
    LinkAction,
    apply_ripple_resolution,
    link_subplot_to_ripple,
)
from infra.world_model.registry import RippleNotFoundError, RippleRegistry

# === Helpers ===

def _plot(
    plot_id: str,
    status: PlotStatus = PlotStatus.ACTIVE,
    related: tuple[str, ...] = (),
    birth_ch: int = 10,
    close_ch: Optional[int] = None,
) -> Plot:
    return Plot(
        plot_id=plot_id,
        type=PlotType.SUBPLOT,
        title=f"plot_{plot_id}",
        status=status,
        birth_ch=birth_ch,
        active_ch_range=(birth_ch, 200),
        close_ch=close_ch,
        related_ripples=related,
    )


def _ripple(ripple_id: str, state: RippleState = RippleState.RESOLVED) -> Ripple:
    return Ripple(
        ripple_id=ripple_id,
        origin_event="e",
        origin_ch=10,
        state=state,
    )


# === TestLinkSubplotToRipple ===

class TestLinkSubplotToRipple:
    """link_subplot_to_ripple: 加入 ripple_id 到 related_ripples (idempotent)"""

    def test_adds_ripple_id_to_empty(self):
        plot = _plot("p1")
        new = link_subplot_to_ripple(plot, _ripple("r1"))
        assert "r1" in new.related_ripples
        assert len(new.related_ripples) == 1
        # 原 plot 不变 (不可变)
        assert plot.related_ripples == ()

    def test_idempotent_duplicate(self):
        plot = _plot("p1", related=("r1",))
        new = link_subplot_to_ripple(plot, _ripple("r1"))
        # 重复 link 不应添加第二个
        assert new.related_ripples == ("r1",)

    def test_appends_preserves_order(self):
        plot = _plot("p1", related=("r1", "r2"))
        new = link_subplot_to_ripple(plot, _ripple("r3"))
        assert new.related_ripples == ("r1", "r2", "r3")

    def test_returns_new_plot_object(self):
        plot = _plot("p1")
        new = link_subplot_to_ripple(plot, _ripple("r1"))
        assert new is not plot
        assert isinstance(new, Plot)


# === TestApplyRippleResolution ===

class TestApplyRippleResolution:
    """apply_ripple_resolution: 涟漪 RESOLVED 时联动 subplot (ACTIVE → CLOSING)"""

    def test_active_plot_transitions_to_closing(self, tmp_path):
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        rreg.add_ripple(_ripple("r1", RippleState.RESOLVED))
        sreg.add_plot(_plot("p1", status=PlotStatus.ACTIVE, related=("r1",)))

        actions = apply_ripple_resolution(
            rreg, sreg, "r1", current_ch=100, auto_close=True
        )
        assert len(actions) == 1
        a = actions[0]
        assert a.plot_id == "p1"
        assert a.from_status == PlotStatus.ACTIVE
        assert a.to_status == PlotStatus.CLOSING

        # 状态机真正更新
        p1 = sreg.get_plot("p1")
        assert p1 is not None
        assert p1.status == PlotStatus.CLOSING
        assert p1.close_ch == 102  # 100 + CLOSING_MIN_CHAPTERS

    def test_closed_plot_skipped(self, tmp_path):
        """已 CLOSED 的 plot 跳过 (幂等)"""
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        rreg.add_ripple(_ripple("r1", RippleState.RESOLVED))
        sreg.add_plot(_plot("p1", status=PlotStatus.CLOSED, related=("r1",)))

        actions = apply_ripple_resolution(
            rreg, sreg, "r1", current_ch=200, auto_close=True
        )
        assert actions == ()  # 无 LinkAction
        # 状态不变
        p1 = sreg.get_plot("p1")
        assert p1 is not None
        assert p1.status == PlotStatus.CLOSED

    def test_auto_close_false_dry_run(self, tmp_path):
        """auto_close=False: dry-run, 不改 status"""
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        rreg.add_ripple(_ripple("r1", RippleState.RESOLVED))
        sreg.add_plot(_plot("p1", status=PlotStatus.ACTIVE, related=("r1",)))

        actions = apply_ripple_resolution(
            rreg, sreg, "r1", current_ch=100, auto_close=False
        )
        # 仍返回 1 个 LinkAction (记录会改),但 registry 不动
        assert len(actions) == 1
        assert actions[0].to_status == PlotStatus.CLOSING

        p1 = sreg.get_plot("p1")
        assert p1 is not None
        assert p1.status == PlotStatus.ACTIVE  # 未变

    def test_unregistered_ripple_raises(self, tmp_path):
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        # r1 未注册
        with pytest.raises(RippleNotFoundError):
            apply_ripple_resolution(
                rreg, sreg, "ghost", current_ch=100, auto_close=True
            )

    def test_multiple_subplots_for_one_ripple(self, tmp_path):
        """1 个 ripple 关联 3 subplot → 3 个 LinkAction"""
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        rreg.add_ripple(_ripple("r1", RippleState.RESOLVED))
        sreg.add_plot(_plot("p1", related=("r1",)))
        sreg.add_plot(_plot("p2", related=("r1",)))
        sreg.add_plot(_plot("p3", related=("r1",)))
        # p4 不关联 r1
        sreg.add_plot(_plot("p4", related=("r_other",)))

        actions = apply_ripple_resolution(
            rreg, sreg, "r1", current_ch=100, auto_close=True
        )
        assert len(actions) == 3
        plot_ids = {a.plot_id for a in actions}
        assert plot_ids == {"p1", "p2", "p3"}

    def test_paused_plot_not_auto_closed(self, tmp_path):
        """PAUSED plot 不在 ACTIVE→CLOSING 范围,保持 PAUSED"""
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        sreg = PlotRegistry(base_dir=tmp_path / "subplots")
        rreg.add_ripple(_ripple("r1", RippleState.RESOLVED))
        sreg.add_plot(_plot("p1", status=PlotStatus.PAUSED, related=("r1",)))

        actions = apply_ripple_resolution(
            rreg, sreg, "r1", current_ch=100, auto_close=True
        )
        # PAUSED → CLOSING 不是合法转换
        # 应返回空 actions (跳过非法转换)
        assert actions == ()
        p1 = sreg.get_plot("p1")
        assert p1 is not None
        assert p1.status == PlotStatus.PAUSED


# === TestLinkActionDataclass ===

class TestLinkActionDataclass:
    """LinkAction 不可变 + 字段语义"""

    def test_frozen_immutable(self):
        a = LinkAction(
            plot_id="p1",
            from_status=PlotStatus.ACTIVE,
            to_status=PlotStatus.CLOSING,
            reason="ripple r1 resolved",
        )
        with pytest.raises((AttributeError, Exception)):
            a.plot_id = "p2"  # type: ignore[misc]

    def test_fields_accessible(self):
        a = LinkAction(
            plot_id="p1",
            from_status=PlotStatus.ACTIVE,
            to_status=PlotStatus.CLOSING,
            reason="test",
        )
        assert a.plot_id == "p1"
        assert a.from_status == PlotStatus.ACTIVE
        assert a.to_status == PlotStatus.CLOSING
        assert a.reason == "test"


# === TestProtocolDecoupling ===

class TestProtocolDecoupling:
    """apply_ripple_resolution 接受 Protocol (不是具体类型)"""

    def test_works_with_stub_subplot_registry(self, tmp_path):
        """最小 stub:只需 list_all + get_plot + update_status"""
        rreg = RippleRegistry(base_dir=tmp_path / "ripples")
        rreg.add_ripple(_ripple("r1", RippleState.RESOLVED))

        p1 = _plot("p1", status=PlotStatus.ACTIVE, related=("r1",))
        plots: dict[str, Plot] = {"p1": p1}

        class StubSubplotReg:
            def list_all(self) -> tuple[Plot, ...]:
                return tuple(plots.values())

            def get_plot(self, plot_id: str) -> Optional[Plot]:
                return plots.get(plot_id)

            def update_status(self, plot_id, new_status, current_ch, close_ch=None):
                old = plots[plot_id]
                plots[plot_id] = replace(old, status=new_status, close_ch=close_ch)
                return plots[plot_id]

        stub = StubSubplotReg()
        actions = apply_ripple_resolution(
            rreg, stub, "r1", current_ch=100, auto_close=True
        )
        assert len(actions) == 1
        assert actions[0].to_status == PlotStatus.CLOSING
        # 状态机更新反映在 stub
        assert stub.get_plot("p1").status == PlotStatus.CLOSING


# === TestImportContract ===

class TestImportContract:
    """Public API 完整性:所有 2.3 符号从顶层可导入"""

    def test_top_level_imports(self):
        from infra.world_model import (
            LinkAction,
            apply_ripple_resolution,
            link_subplot_to_ripple,
        )
        assert LinkAction is not None
        assert callable(link_subplot_to_ripple)
        assert callable(apply_ripple_resolution)
