"""Tests for background digest polling tick."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from infra.creator_onboarding_digest_background import tick_digest_for_active_project
from infra.creator_onboarding_digest_schedule import save_digest_schedule
from infra.creator_onboarding_notifications import record_mentions_from_notes
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


def test_tick_digest_for_active_project(factory_tmp, monkeypatch) -> None:
    result = init_minimal_short_project(
        slug="digest-bg",
        title="后台 digest",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    mock_project = MagicMock()
    mock_project.root = root
    monkeypatch.setattr("infra.studio_registry.active_project", lambda: mock_project)
    record_mentions_from_notes(
        root,
        step_notes={"volume": "先锁卷纲 @batch"},
        changed_step_ids={"volume"},
    )
    save_digest_schedule(root, enabled=True, interval_hours=24, channels=["webhook"])
    result_tick = tick_digest_for_active_project()
    assert result_tick.get("skipped") is True or result_tick.get("sent") is True
    ProjectPaths.reset()
