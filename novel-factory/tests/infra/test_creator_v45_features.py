"""Tests for creator v4.5 outline inline edit, recheck paragraph jump, batch pulse clear."""
from __future__ import annotations

import pytest

from infra.creator_dashboard import creator_chapter_preview, save_creator_chapter_outline
from infra.creator_logic_check import run_creator_logic_check
from infra.creator_ui_profile import resolve_creator_ui_profile
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


def test_companion_v45_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["chapter_outline_inline_edit"] is True
    assert profile["recheck_issue_paragraph_jump"] is True


def test_advance_v45_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["batch_clear_pulse_no_alert"] is True


def test_chapter_preview_full_outline(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v45-outline",
        title="大纲",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=3,
    )
    project = StudioProject(
        slug="v45-outline",
        name="大纲",
        role="production",
        root=result.root,
        location="projects",
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "正文。")
    preview = creator_chapter_preview(project, 1, include_full_outline=True)
    assert preview["has_outline"] is True
    assert "outline_text" in preview


def test_save_chapter_outline(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v45-save-outline",
        title="保存大纲",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=3,
    )
    project = StudioProject(
        slug="v45-save-outline",
        name="保存大纲",
        role="production",
        root=result.root,
        location="projects",
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "正文。")
    saved = save_creator_chapter_outline(project, 1, "更新后的分章大纲。")
    assert saved["outline_text"] == "更新后的分章大纲。\n"


def test_logic_check_issue_paragraph_field(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v45-logic",
        title="复查",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=3,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "第一段。\n\n第二段。")
    check = run_creator_logic_check(result.root, chapter_num=1)
    for issue in check.get("issues", []):
        assert "paragraph" in issue
        assert "line" in issue
