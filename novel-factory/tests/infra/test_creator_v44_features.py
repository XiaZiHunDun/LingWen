"""Tests for creator v4.4 batch summary auto-open, inline recheck, deviation prompt."""
from __future__ import annotations

from infra.creator_ui_profile import resolve_creator_ui_profile


def test_companion_v44_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["chapter_recheck_inline"] is True


def test_advance_v44_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["batch_auto_open_summary"] is True
    assert profile["batch_deviation_prompt"] is True
