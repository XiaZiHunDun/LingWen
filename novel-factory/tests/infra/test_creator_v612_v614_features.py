"""Tests for creator v6.12–v6.14 batch features."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v612_v614_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_share_link_apply_confirm"] is True
    assert profile["batch_history_cost_efficiency_chart"] is True
    assert profile["creation_mode_switch_reduced_motion"] is True
    assert profile["volume_plan_diff_share_token_validation"] is True
    assert profile["batch_history_retry_rate_stack"] is True
    assert profile["creation_mode_switch_aria_live"] is True
    assert profile["volume_plan_diff_share_link_merge"] is True
    assert profile["batch_history_chapter_failure_heatmap"] is True
    assert profile["creation_mode_preview_pinned_sidebar"] is True


def test_companion_v612_v614_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_reduced_motion"] is True
    assert profile["creation_mode_switch_aria_live"] is True
    assert profile["creation_mode_preview_pinned_sidebar"] is True
    assert profile.get("volume_plan_diff_share_link_apply_confirm") is not True


def test_studio_v612_v614_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_preview_pinned_sidebar"] is True
    assert profile.get("batch_history_cost_efficiency_chart") is not True
