"""Tests for creator v6.5 diff email share, success rate chart, onboarding step link."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v65_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_email_share"] is True
    assert profile["batch_history_success_rate_chart"] is True
    assert profile["creation_mode_onboarding_step_link"] is True


def test_companion_v65_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_onboarding_step_link"] is True
    assert profile.get("volume_plan_diff_export_email_share") is not True
    assert profile.get("batch_history_success_rate_chart") is not True


def test_studio_v65_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_onboarding_step_link"] is True
    assert profile.get("volume_plan_diff_export_email_share") is not True
