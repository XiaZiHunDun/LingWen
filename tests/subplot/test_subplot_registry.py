"""Tests for subplot.registry.

Phase 1.2.e — RED tests for PlotRegistry CRUD + 5-subplot limit + JSON persistence.

设计约束 (per Doc 3 v1.0):
- 1 主线 + ≤4 支线 典型 (但 MAX_ACTIVE_SUBPLOTS = 5 允许仅支线)
- 5 限制: 添加第 6 个 active subplot → raise SubplotLimitExceeded
- add_plot(plot): 校验状态合法 + 5 限制
- update_status: 校验状态转换 + CLOSING≥2ch
- JSON 持久化到 {base_dir}/subplots.json
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)
from infra.subplot.registry import (
    DuplicatePlotIdError,
    PlotNotFoundError,
    PlotRegistry,
    SubplotLimitExceeded,
)


def _plot(
    plot_id: str = "p1",
    type_: PlotType = PlotType.SUBPLOT,
    status: PlotStatus = PlotStatus.DRAFT,
    purpose: PlotPurpose = PlotPurpose.GROWTH,
    **kwargs,
) -> Plot:
    defaults = dict(
        plot_id=plot_id,
        type=type_,
        title=plot_id,
        status=status,
        purpose=purpose,
    )
    defaults.update(kwargs)
    return Plot(**defaults)


class TestPlotRegistryBasic:
    def test_empty_registry(self):
        r = PlotRegistry()
        assert r.list_all() == ()
        assert r.list_active() == ()
        assert r.count() == 0

    def test_add_plot_basic(self):
        r = PlotRegistry()
        p = _plot(plot_id="p1", status=PlotStatus.DRAFT)
        r.add_plot(p)
        assert r.get_plot("p1") == p
        assert r.count() == 1

    def test_add_duplicate_id_raises(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1"))
        with pytest.raises(DuplicatePlotIdError, match="p1"):
            r.add_plot(_plot(plot_id="p1"))

    def test_get_plot_missing_returns_none(self):
        r = PlotRegistry()
        assert r.get_plot("nonexistent") is None

    def test_get_plot_raises_for_lookup(self):
        r = PlotRegistry()
        with pytest.raises(PlotNotFoundError):
            r.require_plot("nonexistent")

    def test_list_all_returns_tuple(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1"))
        r.add_plot(_plot(plot_id="p2"))
        all_plots = r.list_all()
        assert isinstance(all_plots, tuple)
        assert {p.plot_id for p in all_plots} == {"p1", "p2"}


class TestListActive:
    def test_list_active_filters(self):
        """list_active 只返回 status == ACTIVE 的 plot"""
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="p2", status=PlotStatus.DRAFT))
        r.add_plot(_plot(plot_id="p3", status=PlotStatus.PAUSED))
        r.add_plot(_plot(plot_id="p4", status=PlotStatus.CLOSING))
        r.add_plot(_plot(plot_id="p5", status=PlotStatus.CLOSED))

        active = r.list_active()
        assert {p.plot_id for p in active} == {"p1"}

    def test_count_active(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="p2", status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="p3", status=PlotStatus.DRAFT))
        assert r.count_active() == 2

    def test_count_active_subplots(self):
        """count_active_subplots 只数 SUBPLOT 类型 (非 MAIN)"""
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="main-001", type_=PlotType.MAIN, status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="sub-1", type_=PlotType.SUBPLOT, status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="sub-2", type_=PlotType.SUBPLOT, status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="sub-3", type_=PlotType.SUBPLOT, status=PlotStatus.ACTIVE))
        # main 不算,3 个 subplot 算
        assert r.count_active_subplots() == 3


class TestSubplotLimit:
    def test_subplot_limit_constant(self):
        assert MAX_ACTIVE_SUBPLOTS == 5

    def test_5_active_subplots_allowed(self):
        """正好 5 个 active subplot → 允许"""
        r = PlotRegistry()
        for i in range(5):
            r.add_plot(_plot(plot_id=f"sub-{i}", status=PlotStatus.ACTIVE))
        assert r.count_active_subplots() == 5

    def test_6th_active_subplot_raises(self):
        """第 6 个 active subplot → SubplotLimitExceeded"""
        r = PlotRegistry()
        for i in range(5):
            r.add_plot(_plot(plot_id=f"sub-{i}", status=PlotStatus.ACTIVE))
        with pytest.raises(SubplotLimitExceeded, match="5"):
            r.add_plot(_plot(plot_id="sub-5", status=PlotStatus.ACTIVE))

    def test_main_plot_does_not_count_toward_limit(self):
        """MAIN 类型不计入 5 限制"""
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="main-001", type_=PlotType.MAIN, status=PlotStatus.ACTIVE))
        for i in range(5):
            r.add_plot(_plot(plot_id=f"sub-{i}", status=PlotStatus.ACTIVE))
        # 1 main + 5 subplot OK
        assert r.count() == 6
        assert r.count_active_subplots() == 5

    def test_draft_subplot_does_not_count_toward_limit(self):
        """DRAFT 状态不计入 5 限制"""
        r = PlotRegistry()
        for i in range(5):
            r.add_plot(_plot(plot_id=f"sub-{i}", status=PlotStatus.ACTIVE))
        # 第 6 个 DRAFT 状态可加
        r.add_plot(_plot(plot_id="sub-draft", status=PlotStatus.DRAFT))
        assert r.count() == 6

    def test_paused_does_not_count_toward_limit(self):
        """PAUSED 状态不计入 5 限制 (资源让位)"""
        r = PlotRegistry()
        for i in range(5):
            r.add_plot(_plot(plot_id=f"sub-{i}", status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="sub-paused", status=PlotStatus.PAUSED))
        assert r.count() == 6
        assert r.count_active_subplots() == 5


class TestListByPurpose:
    def test_list_by_purpose(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="m1", purpose=PlotPurpose.MYSTERY, status=PlotStatus.ACTIVE))
        r.add_plot(_plot(plot_id="m2", purpose=PlotPurpose.MYSTERY, status=PlotStatus.DRAFT))
        r.add_plot(_plot(plot_id="g1", purpose=PlotPurpose.GROWTH, status=PlotStatus.ACTIVE))

        mysteries = r.list_by_purpose(PlotPurpose.MYSTERY)
        assert {p.plot_id for p in mysteries} == {"m1", "m2"}

        growths = r.list_by_purpose(PlotPurpose.GROWTH)
        assert {p.plot_id for p in growths} == {"g1"}


class TestUpdateStatus:
    def test_update_status_valid_transition(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.DRAFT))
        r.update_status("p1", PlotStatus.ACTIVE, current_ch=1)
        assert r.get_plot("p1").status == PlotStatus.ACTIVE

    def test_update_status_invalid_transition_raises(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.DRAFT))
        # DRAFT → CLOSING 不合法
        with pytest.raises(ValueError, match="DRAFT"):
            r.update_status("p1", PlotStatus.CLOSING, current_ch=1)

    def test_update_status_terminal_raises(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE, close_ch=10))
        r.update_status("p1", PlotStatus.CLOSING, current_ch=1, close_ch=10)
        r.update_status("p1", PlotStatus.CLOSED, current_ch=10)
        # CLOSED → ACTIVE 不可
        with pytest.raises(ValueError, match="CLOSED"):
            r.update_status("p1", PlotStatus.ACTIVE, current_ch=11)

    def test_update_status_unknown_plot_raises(self):
        r = PlotRegistry()
        with pytest.raises(PlotNotFoundError):
            r.update_status("nonexistent", PlotStatus.ACTIVE, current_ch=1)

    def test_update_status_to_closing_after_only_1_chapter_raises(self):
        """CLOSING 必须持续 ≥ 2 章 — 进入 CLOSING 时,需要预留 ≥2 章"""
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE))
        # 假设当前章 = 50,close_ch = 51 → 只有 1 章 (< 2)
        with pytest.raises(ValueError, match="(?i)must last"):
            r.update_status("p1", PlotStatus.CLOSING, current_ch=50, close_ch=51)

    def test_update_status_to_closing_with_2_chapters_ok(self):
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE))
        # close_ch=52 → 50,51,52 共 3 章
        r.update_status("p1", PlotStatus.CLOSING, current_ch=50, close_ch=52)
        assert r.get_plot("p1").status == PlotStatus.CLOSING

    def test_update_status_to_closing_no_close_ch_raises(self):
        """未指定 close_ch → 拒绝进入 CLOSING"""
        r = PlotRegistry()
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE))
        with pytest.raises(ValueError, match="close_ch"):
            r.update_status("p1", PlotStatus.CLOSING, current_ch=50)


class TestRegistryPersistence:
    def test_save_and_load_roundtrip(self, tmp_path: Path):
        r = PlotRegistry(tmp_path)
        r.add_plot(_plot(plot_id="main-001", type_=PlotType.MAIN, status=PlotStatus.ACTIVE,
                         purpose=PlotPurpose.GROWTH))
        r.add_plot(_plot(plot_id="sub-1", status=PlotStatus.ACTIVE,
                         purpose=PlotPurpose.MYSTERY))
        r.save()

        # 文件应该存在
        assert (tmp_path / "subplots.json").exists()

        # Load 到新 registry
        r2 = PlotRegistry(tmp_path)
        r2.load()
        assert r2.count() == 2
        assert r2.get_plot("main-001") is not None
        assert r2.get_plot("sub-1") is not None

    def test_save_creates_dir(self, tmp_path: Path):
        nested = tmp_path / "deep" / "state"
        r = PlotRegistry(nested)
        r.add_plot(_plot(plot_id="p1"))
        r.save()
        assert nested.exists()
        assert (nested / "subplots.json").exists()

    def test_load_missing_file_raises(self, tmp_path: Path):
        r = PlotRegistry(tmp_path)
        with pytest.raises(FileNotFoundError):
            r.load()

    def test_persistence_preserves_active_count(self, tmp_path: Path):
        r = PlotRegistry(tmp_path)
        for i in range(3):
            r.add_plot(_plot(plot_id=f"sub-{i}", status=PlotStatus.ACTIVE))
        r.save()

        r2 = PlotRegistry(tmp_path)
        r2.load()
        assert r2.count_active_subplots() == 3

    def test_save_load_preserves_close_ch(self, tmp_path: Path):
        r = PlotRegistry(tmp_path)
        r.add_plot(_plot(plot_id="p1", status=PlotStatus.ACTIVE, close_ch=100))
        r.save()

        r2 = PlotRegistry(tmp_path)
        r2.load()
        assert r2.get_plot("p1").close_ch == 100


class TestRegistryDefaultLocation:
    def test_default_base_dir(self, tmp_path, monkeypatch):
        """无参时使用 .state/subplots/ 默认目录"""
        monkeypatch.setenv("LINGWEN_STATE_DIR", str(tmp_path))
        r = PlotRegistry()
        # 应当指向 .state/subplots 子目录
        assert "subplots" in str(r.base_dir)
