"""Tests for infra.creator_merge_preferences."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import load_merge_preferences, save_merge_preferences
from infra.paths import ProjectPaths
from infra.project_init import init_minimal_short_project


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()


def test_merge_preferences_roundtrip(factory_tmp):
    result = init_minimal_short_project(
        slug="merge-prefs",
        title="合并偏好",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    save_merge_preferences(
        result.root,
        pillars_merge_source="disk",
        global_outline_merge_source="history",
    )
    loaded = load_merge_preferences(result.root)
    assert loaded["pillars_merge_source"] == "disk"
    assert loaded["global_outline_merge_source"] == "history"
    ProjectPaths.reset()


def test_merge_preferences_remember_snapshot(factory_tmp):
    result = init_minimal_short_project(
        slug="merge-snap",
        title="快照记忆",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    save_merge_preferences(
        result.root,
        pillars_merge_source="history",
        global_outline_merge_source="editor",
        merge_snapshot_id="snap-abc",
    )
    loaded = load_merge_preferences(result.root)
    assert loaded["merge_snapshot_id"] == "snap-abc"
    ProjectPaths.reset()


def test_merge_preferences_global_fallback(factory_tmp, monkeypatch):
    import infra.creator_merge_preferences as cmp

    monkeypatch.setattr("infra.studio_registry.factory_root", lambda: factory_tmp)
    monkeypatch.setattr(
        cmp,
        "_global_prefs_path",
        lambda: factory_tmp / "infra" / ".state" / "creator_merge_preferences_global.json",
    )

    from infra.creator_merge_preferences import (
        load_global_merge_preferences,
        load_merge_preferences,
        save_global_merge_preferences,
        save_merge_preferences,
    )

    save_global_merge_preferences(
        pillars_merge_source="disk",
        global_outline_merge_source="history",
        merge_snapshot_id="global-snap",
    )
    result = init_minimal_short_project(
        slug="global-merge",
        title="全局合并",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    loaded = load_merge_preferences(result.root)
    assert loaded["uses_global_default"] is True
    assert loaded["pillars_merge_source"] == "disk"
    save_merge_preferences(
        result.root,
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
    )
    loaded = load_merge_preferences(result.root)
    assert loaded["uses_global_default"] is False
    assert load_global_merge_preferences()["pillars_merge_source"] == "editor"
    ProjectPaths.reset()
