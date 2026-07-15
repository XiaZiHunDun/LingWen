"""Tests for creator v5.6 diff refresh on save, batch running pulse, companion badge tint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v56_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_refresh_on_save"] is True
    assert profile["batch_history_running_pulse"] is True


def test_companion_v56_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["companion_creation_mode_badge_tint"] is True


def test_studio_v56_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile.get("volume_plan_diff_refresh_on_save") is not True
    assert profile.get("companion_creation_mode_badge_tint") is not True
