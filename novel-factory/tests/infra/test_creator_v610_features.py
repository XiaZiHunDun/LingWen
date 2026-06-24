"""Tests for creator v6.10 share preview, queue depth, speech."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v610_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_share_link_preview"] is True
    assert profile["batch_history_queue_depth_chart"] is True
    assert profile["creation_mode_switch_speech"] is True


def test_companion_v610_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_speech"] is True
    assert profile.get("volume_plan_diff_share_link_preview") is not True


def test_studio_v610_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_speech"] is True
    assert profile.get("batch_history_queue_depth_chart") is not True
