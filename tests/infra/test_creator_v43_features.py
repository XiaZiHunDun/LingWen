"""Tests for creator v4.3 batch highlight, chapter P0 recheck, pulse summary generate."""
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


def test_companion_v43_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["chapter_save_p0_recheck"] is True


def test_advance_v43_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["batch_highlight_alert_volumes"] is True
    assert profile["volume_pulse_summary_generate"] is True


def test_logic_check_single_chapter(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v43-companion",
        title="陪伴",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=5,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(2, "第二章测试。")
    check = run_creator_logic_check(result.root, chapter_num=2)
    assert check["chapter"] == 2
    assert check["chapters_checked"] == 1
