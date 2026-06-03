"""Tests for subplot.data_structures.

Phase 1.2.a — RED tests for Plot dataclass + 3 enums + MAX_ACTIVE_SUBPLOTS.

设计约束 (per Doc 3 v1.0):
- Plot 不可变 (frozen=True) — plot 定义后不应被原地修改
- Plot 可 JSON 序列化 (to_dict / from_dict) — 持久化到 subplots.json
- 3 enums 全部 str Enum — JSON 友好,值即名称
- PlotType (3) / PlotPurpose (8) / PlotStatus (6) — 数量固定
- MAX_ACTIVE_SUBPLOTS = 5 — 1 主线 + ≤4 支线
"""
from __future__ import annotations

import dataclasses

import pytest

from infra.subplot.data_structures import (
    MAX_ACTIVE_SUBPLOTS,
    Plot,
    PlotPurpose,
    PlotStatus,
    PlotType,
)


def _lin_chen_id():
    """复用 world_model.NodeId 构造 protagonist_link"""
    from infra.world_model import NodeId, NodeType
    return NodeId(NodeType.CHARACTER, "林尘")


class TestEnums:
    def test_plot_type_has_3_values(self):
        assert len(PlotType) == 3
        assert {t.value for t in PlotType} == {"main", "subplot", "side"}

    def test_plot_purpose_has_8_values(self):
        assert len(PlotPurpose) == 8
        # 8 个语义维度 (Doc 3 §3.1)
        assert {p.value for p in PlotPurpose} == {
            "growth", "mystery", "payoff", "faction",
            "romance", "pacing", "artifact", "theme",
        }

    def test_plot_status_has_6_values(self):
        assert len(PlotStatus) == 6
        assert {s.value for s in PlotStatus} == {
            "draft", "active", "paused", "closing", "closed", "abandoned",
        }

    def test_enums_are_str_enum(self):
        """str Enum — JSON 序列化时直接用 value"""
        assert PlotType.MAIN == "main"
        assert PlotPurpose.GROWTH == "growth"
        assert PlotStatus.ACTIVE == "active"


class TestMaxActiveSubplots:
    def test_max_active_subplots_is_5(self):
        """硬限制: 1 主线 + ≤4 支线"""
        assert MAX_ACTIVE_SUBPLOTS == 5


class TestPlotDataclass:
    def test_create_minimal_plot(self):
        """最小 Plot 只需 plot_id + type + title + status"""
        p = Plot(
            plot_id="main-001",
            type=PlotType.MAIN,
            title="主角成长",
            status=PlotStatus.DRAFT,
        )
        assert p.plot_id == "main-001"
        assert p.type == PlotType.MAIN
        assert p.title == "主角成长"
        assert p.status == PlotStatus.DRAFT
        # 默认字段
        assert p.purpose == PlotPurpose.GROWTH  # 默认值
        assert p.protagonist_link is None
        assert p.birth_ch == 0
        assert p.active_ch_range == (0, 0)
        assert p.close_ch is None
        assert p.constraints_generated == ()
        assert p.related_ripples == ()
        assert p.parent_plot is None
        assert p.key_chapters == ()
        assert p.next_constraint_ch == 0

    def test_plot_is_frozen(self):
        """Plot 不可变 — frozen=True"""
        p = Plot(plot_id="p1", type=PlotType.SUBPLOT, title="x", status=PlotStatus.DRAFT)
        with pytest.raises(dataclasses.FrozenInstanceError):
            p.title = "改"  # type: ignore[misc]

    def test_plot_equality_by_field_values(self):
        """相同字段值 → 相等 (dataclass 默认行为)"""
        args = dict(plot_id="p1", type=PlotType.MAIN, title="x", status=PlotStatus.DRAFT)
        p1 = Plot(**args)
        p2 = Plot(**args)
        assert p1 == p2

    def test_plot_full_construction(self):
        """完整构造: 所有字段都设"""
        p = Plot(
            plot_id="subplot-mystery-001",
            type=PlotType.SUBPLOT,
            title="身世之谜",
            purpose=PlotPurpose.MYSTERY,
            protagonist_link=_lin_chen_id(),
            birth_ch=10,
            active_ch_range=(10, 50),
            close_ch=50,
            status=PlotStatus.ACTIVE,
            constraints_generated=("ch20: 神秘人出现", "ch35: 真相初露"),
            related_ripples=("ripple-001", "ripple-002"),
            parent_plot="main-001",
            key_chapters=(10, 20, 35, 50),
            next_constraint_ch=20,
        )
        assert p.purpose == PlotPurpose.MYSTERY
        assert p.birth_ch == 10
        assert p.active_ch_range == (10, 50)
        assert p.close_ch == 50
        assert len(p.constraints_generated) == 2
        assert p.parent_plot == "main-001"
        assert p.key_chapters == (10, 20, 35, 50)


class TestPlotValidation:
    def test_empty_plot_id_rejected(self):
        """plot_id 不能为空 — 标识必须明确"""
        with pytest.raises(ValueError, match="plot_id"):
            Plot(plot_id="", type=PlotType.MAIN, title="x", status=PlotStatus.DRAFT)

    def test_whitespace_plot_id_rejected(self):
        with pytest.raises(ValueError, match="plot_id"):
            Plot(plot_id="   ", type=PlotType.MAIN, title="x", status=PlotStatus.DRAFT)

    def test_empty_title_rejected(self):
        with pytest.raises(ValueError, match="title"):
            Plot(plot_id="p1", type=PlotType.MAIN, title="", status=PlotStatus.DRAFT)


class TestPlotSerialization:
    def _build_full_plot(self) -> Plot:
        return Plot(
            plot_id="subplot-mystery-001",
            type=PlotType.SUBPLOT,
            title="身世之谜",
            purpose=PlotPurpose.MYSTERY,
            protagonist_link=_lin_chen_id(),
            birth_ch=10,
            active_ch_range=(10, 50),
            close_ch=50,
            status=PlotStatus.ACTIVE,
            constraints_generated=("ch20: 神秘人出现", "ch35: 真相初露"),
            related_ripples=("ripple-001",),
            parent_plot="main-001",
            key_chapters=(10, 20, 50),
            next_constraint_ch=20,
        )

    def test_to_dict_roundtrip(self):
        p = self._build_full_plot()
        d = p.to_dict()
        p2 = Plot.from_dict(d)
        assert p2 == p

    def test_to_dict_minimal_roundtrip(self):
        """最小 plot 也能 roundtrip"""
        p = Plot(plot_id="p1", type=PlotType.MAIN, title="x", status=PlotStatus.DRAFT)
        d = p.to_dict()
        p2 = Plot.from_dict(d)
        assert p2 == p

    def test_to_dict_uses_enum_values(self):
        """to_dict 中 enum 用 value (str) — JSON 友好"""
        p = self._build_full_plot()
        d = p.to_dict()
        assert d["type"] == "subplot"
        assert d["purpose"] == "mystery"
        assert d["status"] == "active"

    def test_to_dict_serializes_nodestatus_as_string(self):
        """protagonist_link (NodeId) 序列化为 'character:林尘' 字符串"""
        p = self._build_full_plot()
        d = p.to_dict()
        assert d["protagonist_link"] == "character:林尘"

    def test_to_dict_serializes_tuples_as_lists(self):
        """tuple 字段 (constraints_generated 等) JSON 序列化为 list"""
        p = self._build_full_plot()
        d = p.to_dict()
        assert isinstance(d["constraints_generated"], list)
        assert isinstance(d["key_chapters"], list)
        assert isinstance(d["related_ripples"], list)

    def test_from_dict_restores_tuples(self):
        """from_dict 后 tuple 字段恢复为 tuple (而非 list)"""
        p = self._build_full_plot()
        d = p.to_dict()
        p2 = Plot.from_dict(d)
        assert isinstance(p2.constraints_generated, tuple)
        assert isinstance(p2.key_chapters, tuple)
        assert isinstance(p2.related_ripples, tuple)

    def test_from_dict_handles_optional_fields(self):
        """from_dict 兼容 None / 缺失字段"""
        d = {
            "plot_id": "p1",
            "type": "main",
            "title": "x",
            "status": "draft",
        }
        p = Plot.from_dict(d)
        assert p.protagonist_link is None
        assert p.close_ch is None
        assert p.parent_plot is None
        assert p.constraints_generated == ()
        assert p.key_chapters == ()
