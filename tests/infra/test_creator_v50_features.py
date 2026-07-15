"""Tests for creator v5.0 mode switch hint, volume plan diff, batch history."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_plan import preview_volume_plan_diff


def test_companion_v50_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_hint"] is True
    assert profile.get("volume_plan_diff_preview") is not True
    assert profile.get("batch_history_panel") is not True


def test_advance_v50_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_preview"] is True
    assert profile["batch_history_panel"] is True
    assert profile["creation_mode_switch_hint"] is True


def test_studio_v50_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["volume_plan_diff_preview"] is False
    assert profile["batch_history_panel"] is False
    assert profile["creation_mode_switch_hint"] is False


def test_preview_volume_plan_diff_detects_conflict_change() -> None:
    baseline = [
        {
            "label": "一",
            "start_chapter": 1,
            "end_chapter": 5,
            "core_conflict": "开篇",
            "locked": True,
        },
    ]
    draft = [
        {
            "label": "一",
            "start_chapter": 1,
            "end_chapter": 5,
            "core_conflict": "改写冲突",
            "locked": True,
        },
    ]
    result = preview_volume_plan_diff(baseline, draft)
    assert result["has_changes"] is True
    assert any(row["type"] == "changed" and row["label"] == "一" for row in result["changes"])


def test_preview_volume_plan_diff_no_change() -> None:
    row = {
        "label": "一",
        "start_chapter": 1,
        "end_chapter": 5,
        "core_conflict": "开篇",
        "locked": True,
    }
    result = preview_volume_plan_diff([row], [dict(row)])
    assert result["has_changes"] is False
    assert result["changes"] == []
