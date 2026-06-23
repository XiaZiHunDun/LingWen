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
