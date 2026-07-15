"""Tests for creator v7.0 milestone: share e2e, ops summary, a11y checklist."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v7_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_share_link_e2e"] is True
    assert profile["batch_history_ops_summary"] is True
    assert profile["creation_mode_accessibility_checklist"] is True


def test_companion_v7_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_accessibility_checklist"] is True
    assert profile.get("volume_plan_diff_share_link_e2e") is not True


def test_studio_v7_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_accessibility_checklist"] is True
    assert profile.get("batch_history_ops_summary") is not True
