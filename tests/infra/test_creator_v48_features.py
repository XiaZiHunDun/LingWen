"""Tests for creator v4.8 deviation click highlight, batch inline summary, unified issue highlight."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_companion_v48_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["issue_paragraph_highlight_unified"] is True


def test_advance_v48_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["deviation_click_highlight"] is True
    assert profile["batch_deviation_inline_summary"] is True
