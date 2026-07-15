"""Tests for creator v5.2 diff expand detail, batch history filter, mode doc links."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_plan import preview_volume_plan_diff


def test_advance_v52_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_expand_detail"] is True
    assert profile["batch_history_status_filter"] is True


def test_companion_v52_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_doc_link"] is True
    assert profile.get("volume_plan_diff_expand_detail") is not True


def test_preview_volume_plan_diff_includes_details() -> None:
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
    changed = result["changes"][0]
    assert changed["details"]
    assert any("核心冲突" in line for line in changed["details"])
