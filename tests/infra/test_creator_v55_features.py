"""Tests for creator v5.5 outline jump, batch status color, studio badge hint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v55_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_jump_outline_edit"] is True
    assert profile["batch_history_status_color"] is True


def test_studio_v55_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["studio_creation_mode_badge_hint"] is True


def test_companion_v55_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile.get("volume_plan_diff_jump_outline_edit") is not True
    assert profile.get("studio_creation_mode_badge_hint") is not True
