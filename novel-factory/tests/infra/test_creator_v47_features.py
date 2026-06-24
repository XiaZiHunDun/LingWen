"""Tests for creator v4.7 deviation highlight, batch open deviation, logic check highlight."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_companion_v47_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["logic_check_issue_highlight"] is True


def test_advance_v47_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["deviation_list_highlight"] is True
    assert profile["batch_open_first_deviation"] is True
