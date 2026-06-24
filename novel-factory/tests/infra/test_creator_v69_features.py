"""Tests for creator v6.9 share link, concurrency chart, hotkey."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v69_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_share_link"] is True
    assert profile["batch_history_concurrency_chart"] is True
    assert profile["creation_mode_switch_hotkey"] is True


def test_companion_v69_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_hotkey"] is True
    assert profile.get("volume_plan_diff_export_share_link") is not True


def test_studio_v69_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_hotkey"] is True
    assert profile.get("batch_history_concurrency_chart") is not True
