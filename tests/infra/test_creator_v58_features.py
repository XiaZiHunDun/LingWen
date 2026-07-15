"""Tests for creator v5.8 diff change count, batch budget hint, studio badge tint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v58_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_change_count"] is True
    assert profile["batch_history_budget_hint"] is True


def test_studio_v58_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["studio_creation_mode_badge_tint"] is True


def test_companion_v58_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile.get("volume_plan_diff_change_count") is not True
    assert profile.get("studio_creation_mode_badge_tint") is not True
