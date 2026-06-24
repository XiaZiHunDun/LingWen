"""Tests for creator v6.4 diff markdown export, monthly summary, guide animation."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v64_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_markdown"] is True
    assert profile["batch_history_monthly_summary"] is True
    assert profile["creation_mode_switch_guide_animation"] is True


def test_companion_v64_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_guide_animation"] is True
    assert profile.get("volume_plan_diff_export_markdown") is not True
    assert profile.get("batch_history_monthly_summary") is not True


def test_studio_v64_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_guide_animation"] is True
    assert profile.get("volume_plan_diff_export_markdown") is not True
