"""Tests for creator v5.1 diff save confirm, batch history replay, studio entry hint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v51_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_save_confirm"] is True
    assert profile["batch_history_replay_range"] is True


def test_studio_v51_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["studio_creation_entry_hint"] is True
    assert profile.get("volume_plan_diff_save_confirm") is not True
    assert profile.get("batch_history_replay_range") is not True


def test_companion_v51_ui_profile_defaults() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile.get("volume_plan_diff_save_confirm") is not True
    assert profile.get("batch_history_replay_range") is not True
    assert profile.get("studio_creation_entry_hint") is not True
