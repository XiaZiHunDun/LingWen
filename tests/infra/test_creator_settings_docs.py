"""Tests for infra.creator_settings_docs."""
from __future__ import annotations

import pytest

from infra.creator_revision import CreatorDocConflictError
from infra.creator_settings_docs import (
    assert_settings_revisions,
    creator_settings_docs_payload,
    preview_settings_docs_diff,
    preview_settings_merge_strategy,
    preview_settings_three_way,
    resolve_merged_settings,
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


def test_settings_revision_conflict(factory_tmp):
    result = init_minimal_short_project(
        slug="settings-conflict",
        title="设定冲突",
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
    save_creator_settings_docs(project, pillars_text="# 旧\n")
    docs = creator_settings_docs_payload(project)
    save_creator_settings_docs(project, pillars_text="# 新\n")
    with pytest.raises(CreatorDocConflictError):
        save_creator_settings_docs(
            project,
            pillars_text="# 本地编辑\n",
            expected_pillars_revision=docs["pillars_revision"],
        )


def test_three_way_preview(factory_tmp):
    result = init_minimal_short_project(
        slug="three-way",
        title="三路对比",
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
    save_creator_settings_docs(project, pillars_text="# 磁盘\n")
    from infra.creator_settings_history import append_settings_snapshot

    append_settings_snapshot(
        project,
        pillars_text="# 历史\n",
        global_outline_text="# 大纲\n",
        label="seed",
    )
    preview = preview_settings_three_way(
        project,
        pillars_text="# 编辑器\n",
        global_outline_text="# 大纲\n",
    )
    assert preview["has_history"] is True
    assert preview["editor_vs_history"]["pillars"]["changed"] is True


def test_resolve_merged_settings_from_history(factory_tmp):
    result = init_minimal_short_project(
        slug="merge-history",
        title="合并历史",
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
    save_creator_settings_docs(project, pillars_text="# 磁盘\n", global_outline_text="# 大纲\n")
    from infra.creator_settings_history import append_settings_snapshot

    snap = append_settings_snapshot(
        project,
        pillars_text="# 历史支柱\n",
        global_outline_text="# 历史大纲\n",
        label="merge-seed",
    )
    pillars, outline = resolve_merged_settings(
        project,
        pillars_source="history",
        outline_source="disk",
        editor_pillars="# 编辑器\n",
        editor_outline="# 编辑器大纲\n",
        snapshot_id=snap["id"],
    )
    assert pillars == "# 历史支柱\n"
    assert outline == "# 大纲\n"


def test_save_with_merge_sources(factory_tmp):
    result = init_minimal_short_project(
        slug="merge-save",
        title="合并保存",
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
    current = creator_settings_docs_payload(project)
    save_creator_settings_docs(
        project,
        pillars_text="# 编辑器\n",
        global_outline_text=current["global_outline_text"],
        expected_pillars_revision=current["pillars_revision"],
        expected_global_outline_revision=current["global_outline_revision"],
        pillars_merge_source="disk",
    )
    reloaded = creator_settings_docs_payload(project)
    assert reloaded["pillars_text"] == current["pillars_text"]


def test_merge_strategy_preview(factory_tmp):
    result = init_minimal_short_project(
        slug="merge-preview",
        title="合并预览",
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
    save_creator_settings_docs(project, pillars_text="# 磁盘\n", global_outline_text="# 大纲\n")
    preview = preview_settings_merge_strategy(
        project,
        pillars_text="# 编辑器\n",
        global_outline_text="# 大纲\n",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
    )
    assert preview["pillars"]["source"] == "disk"
    assert preview["pillars"]["vs_editor"]["changed"] is True
    assert preview["pillars"]["vs_disk"]["changed"] is False
