"""Tests for onboarding notification digest."""
from __future__ import annotations

import pytest

from infra.creator_onboarding_notifications import (
    build_notification_digest,
    record_mentions_from_notes,
)
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


def test_notification_digest_groups_by_handle(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="digest",
        title="摘要",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    record_mentions_from_notes(
        root,
        step_notes={
            "volume": "先锁卷纲 @batch",
            "pillars": "补支柱 @batch",
        },
        changed_step_ids={"volume", "pillars"},
    )
    digest = build_notification_digest(root)
    assert digest["unread"] == 2
    assert digest["group_count"] == 1
    assert digest["groups"][0]["handle"] == "batch"
    assert digest["groups"][0]["count"] == 2
    ProjectPaths.reset()
