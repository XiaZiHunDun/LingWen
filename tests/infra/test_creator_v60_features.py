"""Tests for creator v6.0 mode preview, diff export, batch success rate."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v60_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export"] is True
    assert profile["batch_history_success_rate"] is True
    assert profile["creation_mode_switch_preview"] is True


def test_companion_v60_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_preview"] is True
    assert profile.get("volume_plan_diff_export") is not True


def test_studio_v60_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_preview"] is True
    assert profile.get("batch_history_success_rate") is not True
