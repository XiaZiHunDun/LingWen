"""Tests for creator v4.2 deviation jump, P0-only logic check, summary pulse sync."""
from __future__ import annotations

import pytest

from infra.creator_dashboard import _build_volume_summaries, creator_overview
from infra.creator_logic_check import run_creator_logic_check
from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_plan import save_volume_plan
from infra.creator_volume_pulse import build_volume_pulse
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


def test_companion_v42_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["logic_check_p0_only"] is True
    assert profile["deviation_chapter_jump"] is True


def test_advance_v42_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["deviation_chapter_jump"] is True
    assert profile["logic_check_p0_only"] is False


def test_logic_check_p0_only_flag(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v42-companion",
        title="陪伴",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=3,
    )
    check = run_creator_logic_check(result.root)
    assert check["p0_only"] is True
    for row in check["issues"]:
        assert row["severity"] == "P0"


def test_volume_summary_pulse_status_sync(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v42-advance",
        title="推进",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=10,
    )
    root = result.root
    save_volume_plan(
        root,
        volumes=[
            {"label": "一", "start_chapter": 1, "end_chapter": 5, "core_conflict": "a", "locked": True},
        ],
    )
    paths = ProjectPaths.get(root)
    paths.write_chapter(8, "越界章。")
    write_volume_summary(root, start_chapter=1, end_chapter=5)
    pulse = build_volume_pulse(root, alerts_only=False)
    summaries = _build_volume_summaries(root, pulse)
    assert summaries
    assert summaries[0]["pulse_status"] in {"ok", "warn", "alert"}
    assert summaries[0]["volume_label"] == "一"

    project = StudioProject(
        slug="v42-advance",
        name="推进",
        role="production",
        root=root,
        location="projects",
    )
    overview = creator_overview(project)
    assert overview["volume_summaries"][0].get("pulse_status") is not None
