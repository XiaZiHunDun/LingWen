"""Tests for infra.creator_settings_docs."""
from __future__ import annotations

import pytest

from infra.creator_settings_docs import (
    creator_settings_docs_payload,
    preview_settings_docs_diff,
    save_creator_settings_docs,
    text_diff_summary,
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


def test_save_settings_docs(factory_tmp):
    result = init_minimal_short_project(
        slug="settings-docs",
        title="设定测试",
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
    payload = save_creator_settings_docs(
        project,
        pillars_text="# 新支柱\n",
        global_outline_text="# 新大纲\n",
    )
    assert "新支柱" in payload["pillars_text"]
    assert "新大纲" in payload["global_outline_text"]
    reloaded = creator_settings_docs_payload(project)
    assert reloaded["pillars_text"].startswith("# 新支柱")


def test_text_diff_summary():
    unchanged = text_diff_summary("a\nb", "a\nb")
    assert unchanged["changed"] is False
    assert unchanged["lines_added"] == 0

    changed = text_diff_summary("a\nb", "a\nc\n")
    assert changed["changed"] is True
    assert changed["lines_added"] >= 1
    assert changed["lines_removed"] >= 1


def test_preview_settings_docs_diff(factory_tmp):
    result = init_minimal_short_project(
        slug="settings-preview",
        title="预览测试",
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
    save_creator_settings_docs(project, pillars_text="# 旧\n", global_outline_text="# 大纲\n")
    preview = preview_settings_docs_diff(
        project,
        pillars_text="# 新\n",
        global_outline_text="# 大纲\n",
    )
    assert preview["has_changes"] is True
    assert preview["pillars"]["changed"] is True
    assert preview["global_outline"]["changed"] is False
