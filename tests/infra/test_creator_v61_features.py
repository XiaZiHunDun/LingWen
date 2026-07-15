"""Tests for creator v6.1 volume filter, avg duration, yaml snippet."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v61_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_volume_filter"] is True
    assert profile["batch_history_avg_duration"] is True
    assert profile["creation_mode_yaml_snippet"] is True


def test_companion_v61_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_yaml_snippet"] is True
    assert profile.get("volume_plan_diff_volume_filter") is not True


def test_studio_v61_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_yaml_snippet"] is True
