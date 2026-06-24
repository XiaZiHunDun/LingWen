"""Tests for creator v6.3 diff highlight export, weekly summary, capability matrix."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v63_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_highlight"] is True
    assert profile["batch_history_weekly_summary"] is True
    assert profile["creation_mode_capability_matrix"] is True


def test_companion_v63_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_capability_matrix"] is True
    assert profile.get("volume_plan_diff_export_highlight") is not True
    assert profile.get("batch_history_weekly_summary") is not True


def test_studio_v63_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_capability_matrix"] is True
    assert profile.get("volume_plan_diff_export_highlight") is not True
