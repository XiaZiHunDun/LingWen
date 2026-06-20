"""Tests for infra/studio_registry.py (Phase 10.04)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.paths import ProjectPaths
from infra.studio_registry import (
    activate_project,
    active_state_path,
    get_project_by_slug,
    list_projects,
    production_preflight,
    project_summary,
    quality_summary,
)


@pytest.fixture(autouse=True)
def _reset_paths():
    ProjectPaths.reset()
    yield
    ProjectPaths.reset()


def test_list_projects_includes_root_and_anye_xinbiao():
    projects = list_projects()
    slugs = {p.slug for p in projects}
    assert "xingyun-jiyuan" in slugs
    assert "anye-xinbiao" in slugs


def test_activate_project_persists_and_sets_env(monkeypatch, tmp_path: Path):
    state = tmp_path / "studio_active.json"
    monkeypatch.setattr("infra.studio_registry.active_state_path", lambda: state)

    project = activate_project("anye-xinbiao")
    assert project.slug == "anye-xinbiao"
    assert state.is_file()
    data = json.loads(state.read_text(encoding="utf-8"))
    assert data["slug"] == "anye-xinbiao"
    assert get_project_by_slug("anye-xinbiao") is not None


def test_project_summary_anye_xinbiao():
    project = get_project_by_slug("anye-xinbiao")
    assert project is not None
    summary = project_summary(project)
    assert summary["chapter_count"] == 10
    assert summary["has_golden_set"] is True
    assert summary["pillars_ok"] is True


def test_quality_summary_anye_xinbiao():
    project = get_project_by_slug("anye-xinbiao")
    assert project is not None
    quality = quality_summary(project)
    assert quality["chapters_written"] == 10
    assert quality["coverage_pct"] == 100.0
    assert quality["golden_set_status"] == "ready"


def test_production_preflight_canon_range():
    project = get_project_by_slug("anye-xinbiao")
    assert project is not None
    result = production_preflight(
        project,
        start_chapter=1,
        end_chapter=2,
        mode="canon",
    )
    assert result["all_ok"] is True
    assert len(result["chapters"]) == 2
