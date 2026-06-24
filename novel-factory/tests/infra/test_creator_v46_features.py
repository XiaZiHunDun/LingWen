"""Tests for creator v4.6 recheck highlight, batch deviation scroll, outline read preview."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_companion_v46_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["recheck_issue_highlight"] is True


def test_advance_v46_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["batch_scroll_deviation_list"] is True
    assert profile["chapter_outline_read_preview"] is True
