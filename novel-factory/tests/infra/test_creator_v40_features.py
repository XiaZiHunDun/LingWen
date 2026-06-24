"""Tests for creator v4.0 companion edit + advance batch summary + wizard expand."""
from __future__ import annotations

import pytest

from infra.creator_dashboard import creator_chapter_preview, save_creator_chapter_body
from infra.creator_onboarding_progress import dismiss_wizard_panel, load_onboarding_progress
from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_summary import write_volume_summary
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


def test_companion_v40_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["chapter_inline_edit"] is True
    assert profile["wizard_expand_if_incomplete"] is True


def test_save_chapter_body_and_full_preview(factory_tmp) -> None:
    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="v40-companion",
        title="陪伴",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    project = StudioProject(
        slug="v40-companion",
        name="陪伴",
        role="production",
        root=result.root,
        location="projects",
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "# 旧正文\n")

    saved = save_creator_chapter_body(project, 1, "新正文段落。")
    assert saved["has_body"] is True
    assert saved["body_text"] == "新正文段落。\n"
    assert paths.read_chapter(1).strip() == "新正文段落。"

    preview = creator_chapter_preview(project, 1, include_full_body=True)
    assert preview["body_text"] == "新正文段落。\n"


def test_dismiss_wizard_panel_persists(factory_tmp) -> None:
    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="v40-wizard",
        title="向导",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    saved = dismiss_wizard_panel(result.root)
    assert saved["wizard_panel_dismissed"] is True
    loaded = load_onboarding_progress(result.root)
    assert loaded["wizard_panel_dismissed"] is True


def test_write_volume_summary_for_batch_range(factory_tmp) -> None:
    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="v40-advance",
        title="推进",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=10,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "第一章内容。")
    paths.write_chapter(2, "第二章内容。")
    out = write_volume_summary(result.root, start_chapter=1, end_chapter=2)
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "ch001" in text
    assert "ch002" in text
