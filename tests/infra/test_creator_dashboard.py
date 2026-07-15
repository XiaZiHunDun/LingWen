"""Tests for infra.creator_dashboard."""
from __future__ import annotations

from infra.creator_dashboard import creator_overview
from infra.paths import ProjectPaths
from infra.studio_registry import get_project_by_slug


def test_creator_overview_anye_xinbiao():
    ProjectPaths.reset()
    project = get_project_by_slug("anye-xinbiao")
    assert project is not None
    data = creator_overview(project)
    assert data["slug"] == "anye-xinbiao"
    assert data["chapters_written"] == 10
    assert len(data["chapters"]) >= 10
    assert "creation_mode" in data
    assert data["companion_check_cmd"]
