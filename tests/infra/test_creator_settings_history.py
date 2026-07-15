"""Tests for infra.creator_settings_history."""
from __future__ import annotations

import pytest

from infra.creator_settings_docs import save_creator_settings_docs
from infra.creator_settings_history import (
    append_settings_snapshot,
    restore_settings_snapshot,
    settings_history_payload,
)
from infra.paths import ProjectPaths
from infra.project_init import init_minimal_short_project
from infra.studio_registry import StudioProject


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()


def test_snapshot_and_restore(factory_tmp):
    result = init_minimal_short_project(
        slug="settings-history",
        title="历史测试",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    ProjectPaths.reset()
    project = StudioProject(
        slug=result.slug,
        name=result.title,
        role="production",
        root=result.root,
        location="projects",
    )
    append_settings_snapshot(
        project,
        pillars_text="# 旧支柱\n",
        global_outline_text="# 旧大纲\n",
        label="seed",
    )
    save_creator_settings_docs(project, pillars_text="# 新支柱\n")
    history = settings_history_payload(project)
    assert history["count"] >= 2
    seed = next(s for s in history["snapshots"] if s["label"] == "seed")
    restored = restore_settings_snapshot(project, seed["id"])
    assert restored["pillars_text"].startswith("# 旧支柱")
