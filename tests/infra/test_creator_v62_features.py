"""Tests for creator v6.2 diff export outline, failure trend, doc open."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v62_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_outline"] is True
    assert profile["batch_history_failure_trend"] is True
    assert profile["creation_mode_switch_doc_open"] is True


def test_companion_v62_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_doc_open"] is True
    assert profile.get("volume_plan_diff_export_outline") is not True


def test_studio_v62_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["creation_mode_switch_doc_open"] is True
