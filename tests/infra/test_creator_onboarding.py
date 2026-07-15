"""Tests for infra.creator_onboarding."""
from __future__ import annotations

import pytest

from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
)
from infra.creator_onboarding import onboarding_wizard_payload
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


def _project(factory_tmp, *, slug: str, mode: str):
    chapter_count = 10 if mode == CREATION_MODE_STUDIO else 12
    result = init_minimal_short_project(
        slug=slug,
        title=slug,
        factory_root=factory_tmp,
        creation_mode=mode,
        chapter_count=chapter_count,
    )
    ProjectPaths.reset()
    return StudioProject(
        slug=result.slug,
        name=result.title,
        role="production",
        root=result.root,
        location="projects",
    )


@pytest.mark.parametrize(
    ("mode", "checklist"),
    [
        (CREATION_MODE_COMPANION, "docs/companion-walkthrough-checklist.md"),
        (CREATION_MODE_ADVANCE, "docs/advance-walkthrough-checklist.md"),
        (CREATION_MODE_STUDIO, "docs/studio-creator-hybrid-checklist.md"),
    ],
)
def test_onboarding_payload_by_mode(factory_tmp, mode, checklist):
    project = _project(factory_tmp, slug=f"onboard-{mode}", mode=mode)
    payload = onboarding_wizard_payload(project)
    assert payload["creation_mode"] == mode
    assert payload["checklist_doc"] == checklist
    assert payload["onboarding_doc"] == "docs/creator-onboarding-wizard.md"
    assert len(payload["steps"]) >= 4
    assert "completed_step_ids" in payload
    assert "progress_pct" in payload
    step_ids = {step["id"] for step in payload["steps"]}
    assert "pillars" in step_ids
    assert "dashboard" in step_ids
