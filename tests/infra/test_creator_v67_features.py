"""Tests for creator v6.7 print preview, status stack chart, switch history."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v67_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_print_preview"] is True
    assert profile["batch_history_status_stack_chart"] is True
    assert profile["creation_mode_switch_history"] is True


def test_companion_v67_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_history"] is True
    assert profile.get("volume_plan_diff_export_print_preview") is not True


def test_studio_v67_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_history"] is True
    assert profile.get("batch_history_status_stack_chart") is not True
