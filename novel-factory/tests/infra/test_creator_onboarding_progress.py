"""Tests for infra.creator_onboarding_progress."""
from __future__ import annotations

import pytest

from infra.creator_onboarding_progress import (
    load_onboarding_progress,
    progress_pct,
    save_onboarding_progress,
)
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


def test_save_and_load_progress(factory_tmp):
    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="wiz-progress",
        title="向导进度",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    root = result.root
    saved = save_onboarding_progress(root, completed_step_ids=["init", "pillars", "init"])
    assert saved["completed_step_ids"] == ["init", "pillars"]
    loaded = load_onboarding_progress(root)
    assert loaded["completed_step_ids"] == ["init", "pillars"]
    assert progress_pct(["init", "pillars"], 4) == 50
    ProjectPaths.reset()


def test_progress_pct_empty():
    assert progress_pct([], 6) == 0
    assert progress_pct(["a", "b", "c"], 3) == 100
