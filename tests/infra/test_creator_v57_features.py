"""Tests for creator v5.7 diff auto collapse, batch failed retry, advance badge tint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v57_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_auto_collapse"] is True
    assert profile["batch_history_failed_retry"] is True
    assert profile["advance_creation_mode_badge_tint"] is True


def test_companion_v57_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile.get("volume_plan_diff_auto_collapse") is not True
    assert profile.get("batch_history_failed_retry") is not True


def test_studio_v57_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile.get("advance_creation_mode_badge_tint") is not True
