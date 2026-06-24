"""Tests for creator v3.8 mode-aware UX features."""
from __future__ import annotations

import pytest

from infra.creator_dashboard import creator_overview
from infra.creator_logic_check import run_creator_logic_check
from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_pulse import build_volume_pulse
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


def test_ui_profile_companion_hides_studio_ops() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["show_studio_workflow"] is False
    assert profile["show_digest_ops"] is False
    assert profile["primary_action"] == "logic_check"
    assert profile["volume_pulse_enabled"] is False


def test_ui_profile_advance_enables_volume_pulse() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["show_studio_workflow"] is False
    assert profile["volume_pulse_enabled"] is True
    assert profile["primary_action"] == "volume_pulse"


def test_ui_profile_studio_shows_ops() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["show_studio_workflow"] is True
    assert profile["show_digest_ops"] is True


def test_logic_check_and_overview_ui_profile(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v38-companion",
        title="陪伴",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=6,
    )
    root = result.root
    project = StudioProject(
        slug="v38-companion",
        name="陪伴",
        role="production",
        root=root,
        location="projects",
    )
    overview = creator_overview(project)
    assert overview["ui_profile"]["primary_action"] == "logic_check"
    assert overview["volume_pulse"] is None
    check = run_creator_logic_check(root)
    assert "passed" in check
    assert check["creation_mode"] == "companion"
    assert check["chapters_checked"] == 6
    ProjectPaths.reset()


def test_volume_pulse_for_advance(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v38-advance",
        title="推进",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    from infra.creator_volume_plan import save_volume_plan

    save_volume_plan(
        root,
        volumes=[
            {"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a", "locked": True},
            {"label": "二", "start_chapter": 7, "end_chapter": 12, "core_conflict": "b", "locked": False},
        ],
    )
    pulse = build_volume_pulse(root)
    assert pulse["volume_count"] == 2
    assert len(pulse["volumes"]) == 2
    assert pulse["volumes"][0]["label"] == "一"
    project = StudioProject(
        slug="v38-advance",
        name="推进",
        role="production",
        root=root,
        location="projects",
    )
    overview = creator_overview(project)
    assert overview["volume_pulse"]["volume_count"] == 2
    ProjectPaths.reset()
