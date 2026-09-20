"""Phase 102: pipeline.merge_chapter_settings — per-chapter subset override."""
from __future__ import annotations

from lingwen_illustrations.pipeline import merge_chapter_settings


def test_chapter_in_overrides_merges() -> None:
    """chapter_num in chapter_overrides → settings overridden for that key."""
    settings = {"max_assets": 20, "auto_generate": False, "chapter_overrides": {5: {"max_assets": 8}}}
    effective = merge_chapter_settings(settings, 5)
    assert effective["max_assets"] == 8
    assert effective["auto_generate"] is False
    assert effective["chapter_overrides"] == {5: {"max_assets": 8}}


def test_chapter_not_in_overrides_unchanged() -> None:
    """chapter_num not in chapter_overrides → settings unchanged (no copy needed)."""
    settings = {"max_assets": 20, "chapter_overrides": {5: {"max_assets": 8}}}
    effective = merge_chapter_settings(settings, 7)
    assert effective == settings
    assert effective is settings  # fast path: identity


def test_chapter_num_none_unchanged() -> None:
    """chapter_num=None (cover asset) → no merge."""
    settings = {"max_assets": 20, "chapter_overrides": {5: {"max_assets": 8}}}
    effective = merge_chapter_settings(settings, None)
    assert effective is settings


def test_chapter_overrides_empty_unchanged() -> None:
    """chapter_overrides={} → no merge (fast path)."""
    settings = {"max_assets": 20, "chapter_overrides": {}}
    effective = merge_chapter_settings(settings, 5)
    assert effective is settings


def test_chapter_overrides_missing_unchanged() -> None:
    """chapter_overrides key absent → no merge."""
    settings = {"max_assets": 20}  # no chapter_overrides key
    effective = merge_chapter_settings(settings, 5)
    assert effective is settings


def test_override_wins_on_conflict() -> None:
    """When override has same key as project setting, override value wins."""
    settings = {"max_assets": 20, "confirm_before_generate": False,
                "chapter_overrides": {5: {"max_assets": 8, "confirm_before_generate": True}}}
    effective = merge_chapter_settings(settings, 5)
    assert effective["max_assets"] == 8
    assert effective["confirm_before_generate"] is True


def test_override_subset_empty_dict() -> None:
    """override value is {} → no override applied but a fresh dict IS allocated (copy semantics)."""
    settings = {"max_assets": 20, "chapter_overrides": {5: {}}}
    effective = merge_chapter_settings(settings, 5)
    # Empty subset triggers merge path; a fresh dict should be allocated
    # (verified by identity inequality) even though values are unchanged
    assert effective is not settings
    assert effective == settings
    assert effective["max_assets"] == 20


def test_immutable_does_not_mutate_input() -> None:
    """merge_chapter_settings MUST NOT mutate input dict."""
    settings = {"max_assets": 20, "chapter_overrides": {5: {"max_assets": 8}}}
    snapshot = dict(settings)
    snapshot_overrides = dict(settings["chapter_overrides"])
    snapshot_subset = dict(settings["chapter_overrides"][5])
    merge_chapter_settings(settings, 5)
    assert settings == snapshot
    assert settings["chapter_overrides"] == snapshot_overrides
    assert settings["chapter_overrides"][5] == snapshot_subset
