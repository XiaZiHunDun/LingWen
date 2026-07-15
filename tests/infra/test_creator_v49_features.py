"""Tests for creator v4.9 inline dismiss, deviation-summary link, issue keyboard nav."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_companion_v49_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["issue_keyboard_navigation"] is True


def test_advance_v49_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["batch_deviation_inline_dismiss"] is True
    assert profile["batch_deviation_summary_link"] is True
