"""Tests for creator v6.11 share apply, throughput chart, haptic."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v611_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_share_link_apply"] is True
    assert profile["batch_history_throughput_chart"] is True
    assert profile["creation_mode_switch_haptic"] is True


def test_companion_v611_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_haptic"] is True
    assert profile.get("volume_plan_diff_share_link_apply") is not True


def test_studio_v611_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_haptic"] is True
    assert profile.get("batch_history_throughput_chart") is not True
