"""Tests for creator v4.1 read preview, inline logic issues, pulse jump fields."""
from __future__ import annotations

import pytest

from infra.creator_logic_check import run_creator_logic_check
from infra.creator_ui_profile import resolve_creator_ui_profile
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


def test_companion_v41_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["logic_check_inline_issues"] is True
    assert profile["chapter_full_preview"] is False


def test_advance_v41_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["chapter_full_preview"] is True
    assert profile["logic_check_inline_issues"] is False


def test_logic_check_returns_issue_list(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v41-companion",
        title="陪伴",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=3,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "第一章测试正文。")
    check = run_creator_logic_check(result.root)
    assert "issues" in check
    assert isinstance(check["issues"], list)
    for row in check["issues"]:
        assert "severity" in row
        assert "chapter" in row
        assert "title" in row
