"""Phase 19+ Sub1 — Plot entity guard tests."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest


def test_plot_importable():
    from lingwen_core.domain.subplot import Plot
    assert Plot is not None


def test_plot_frozen():
    from lingwen_core.domain.subplot import Plot, PlotStatus, PlotType

    p = Plot(
        plot_id="p:1",
        type=PlotType.SUBPLOT,
        title="test",
        status=PlotStatus.ACTIVE,
    )
    assert is_dataclass(p)
    assert p.__dataclass_params__.frozen  # type: ignore[attr-defined]
    with pytest.raises(FrozenInstanceError):
        p.plot_id = "x"  # type: ignore[misc]


def test_plot_rejects_empty_plot_id():
    from lingwen_core.domain.subplot import Plot, PlotStatus, PlotType

    with pytest.raises(ValueError, match="non-empty"):
        Plot(plot_id="", type=PlotType.SUBPLOT, title="t", status=PlotStatus.ACTIVE)


def test_plot_to_dict_from_dict_roundtrip():
    from lingwen_core.domain.common import NodeId, NodeType
    from lingwen_core.domain.subplot import Plot, PlotPurpose, PlotStatus, PlotType

    p = Plot(
        plot_id="p:1",
        type=PlotType.SUBPLOT,
        title="mystery",
        status=PlotStatus.ACTIVE,
        purpose=PlotPurpose.MYSTERY,
        protagonist_link=NodeId(NodeType.CHARACTER, "alice"),
        birth_ch=10,
        active_ch_range=(10, 50),
    )
    d = p.to_dict()
    p2 = Plot.from_dict(d)
    assert p == p2


def test_plot_state_machine_enums():
    from lingwen_core.domain.subplot import PlotPurpose, PlotStatus, PlotType

    assert PlotType.MAIN.value == "main"
    assert PlotType.SUBPLOT.value == "subplot"
    assert PlotStatus.DRAFT.value == "draft"
    assert PlotStatus.CLOSED.value == "closed"
    assert PlotPurpose.GROWTH.value == "growth"
    assert PlotPurpose.MYSTERY.value == "mystery"
