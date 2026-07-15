"""Tests for infra.creator_onboarding_autodetect."""
from __future__ import annotations

import pytest

from infra.creator_onboarding_autodetect import infer_auto_completed_steps
from infra.creator_volume_plan import save_volume_plan
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
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


def test_infer_pillars_and_volume(factory_tmp):
    result = init_minimal_short_project(
        slug="auto-steps",
        title="自动勾选",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=10,
    )
    ProjectPaths.reset()
    project = StudioProject(
        slug=result.slug,
        name=result.title,
        role="production",
        root=result.root,
        location="projects",
    )
    paths = ProjectPaths.get(result.root)
    cfg = ProjectConfig.load(paths)
    cfg.pillars_path.write_text("# 支柱\n" + ("x" * 80) + "\n", encoding="utf-8")
    save_volume_plan(
        result.root,
        [
            {
                "label": "一",
                "start_chapter": 1,
                "end_chapter": 10,
                "core_conflict": "主线",
                "locked": True,
            },
        ],
    )
    inferred = infer_auto_completed_steps(project)
    assert "init" in inferred
    assert "pillars" in inferred
    assert "volume" in inferred
    ProjectPaths.reset()
