"""Tests for creator v5.9 diff type filter, batch duration, badge legend."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v59_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_type_filter"] is True
    assert profile["batch_history_duration"] is True
    assert profile["creation_mode_badge_legend"] is True


def test_companion_v59_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_badge_legend"] is True
    assert profile.get("volume_plan_diff_type_filter") is not True


def test_studio_v59_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_badge_legend"] is True
