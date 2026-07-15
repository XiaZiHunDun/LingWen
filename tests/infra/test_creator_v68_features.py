"""Tests for creator v6.8 zip export, duration distribution, undo hint."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v68_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_zip"] is True
    assert profile["batch_history_duration_distribution"] is True
    assert profile["creation_mode_switch_undo_hint"] is True


def test_companion_v68_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_undo_hint"] is True
    assert profile.get("volume_plan_diff_export_zip") is not True


def test_studio_v68_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_undo_hint"] is True
    assert profile.get("batch_history_duration_distribution") is not True
