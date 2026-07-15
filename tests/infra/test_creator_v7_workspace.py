"""Phase C creator workspace ui_profile flags."""
from __future__ import annotations

from infra.creator_mode import CREATION_MODE_ADVANCE, CREATION_MODE_COMPANION, CREATION_MODE_STUDIO
from infra.creator_ui_profile import resolve_creator_ui_profile


def test_companion_simplified_mode_ops_enabled() -> None:
    profile = resolve_creator_ui_profile(creation_mode=CREATION_MODE_COMPANION)
    assert profile["creator_simplified_mode_ops"] is True
    assert profile["creator_mode_guide_default_collapsed"] is True
    assert profile["creator_workspace_tabs"] is True


def test_advance_workspace_tabs_enabled() -> None:
    profile = resolve_creator_ui_profile(creation_mode=CREATION_MODE_ADVANCE)
    assert profile["creator_workspace_tabs"] is True


def test_studio_keeps_three_column_layout() -> None:
    profile = resolve_creator_ui_profile(creation_mode=CREATION_MODE_STUDIO)
    assert profile["creator_workspace_tabs"] is False
