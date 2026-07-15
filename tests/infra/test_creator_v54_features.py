"""Tests for creator v5.4 outline row highlight, batch date groups, mode badge hint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_plan import build_outline_highlight_lines


def test_advance_v54_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_outline_row_highlight"] is True
    assert profile["batch_history_date_group"] is True


def test_companion_v54_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_badge_hint"] is True


def test_build_outline_highlight_lines_marks_volume_row() -> None:
    outline = "| 卷 | 章范围 | 核心冲突 | 锁定 |\n| 一 | 1-5 | 开篇 | 是 |\n| 二 | 6-10 | 发展 | 否 |"
    lines = build_outline_highlight_lines(outline, ["一"])
    highlighted = [row for row in lines if row["highlighted"]]
    assert highlighted
    assert "一" in highlighted[0]["text"]
