"""Tests for creator v3.9 UX refinements."""
from __future__ import annotations

import pytest

from infra.creator_dashboard import creator_overview
from infra.creator_ui_profile import filter_deviations_by_min_severity, resolve_creator_ui_profile
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


def test_companion_wizard_collapsed_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["wizard_default_collapsed"] is True
    assert profile["wizard_expand_if_incomplete"] is True
    assert profile["chapter_inline_edit"] is True
    assert profile["deviation_min_severity"] is None


def test_advance_alerts_only_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["deviation_min_severity"] == "alert"
    assert profile["wizard_default_collapsed"] is False


def test_filter_deviations_alert_only() -> None:
    rows = [
        {"severity": "warn", "message": "a"},
        {"severity": "alert", "message": "b"},
    ]
    filtered = filter_deviations_by_min_severity(rows, "alert")
    assert len(filtered) == 1
    assert filtered[0]["severity"] == "alert"


def test_advance_overview_filters_deviations_and_pulse(factory_tmp) -> None:
    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="v39-advance",
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
    project = StudioProject(
        slug="v39-advance",
        name="推进",
        role="production",
        root=root,
        location="projects",
    )
    overview = creator_overview(project)
    assert overview["ui_profile"]["deviation_min_severity"] == "alert"
    assert overview["deviation_total_count"] >= overview["deviation_count"]
    pulse = overview["volume_pulse"]
    assert pulse is not None
    assert pulse["alerts_only"] is True
    assert all(row["status"] == "alert" for row in pulse["volumes"])
    ProjectPaths.reset()


def test_volume_pulse_alerts_only_flag(factory_tmp) -> None:
    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="v39-pulse",
        title="Pulse",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=6,
    )
    root = result.root
    from infra.creator_volume_plan import save_volume_plan

    save_volume_plan(
        root,
        volumes=[
            {"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a", "locked": False},
        ],
    )
    full = build_volume_pulse(root, alerts_only=False)
    alerts = build_volume_pulse(root, alerts_only=True)
    assert full["volume_count"] >= alerts["volume_count"]
    assert "alerts_only" in alerts
    ProjectPaths.reset()
