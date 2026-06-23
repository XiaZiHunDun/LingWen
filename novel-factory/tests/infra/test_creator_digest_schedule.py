"""Tests for scheduled onboarding notification digest dispatch."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from infra.creator_onboarding_digest_schedule import (
    dispatch_scheduled_digest,
    save_digest_schedule,
)
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


def test_dispatch_scheduled_digest_when_forced(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="digest-sched",
        title="定时 digest",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    record_mentions_from_notes(
        root,
        step_notes={"volume": "先锁卷纲 @batch"},
        changed_step_ids={"volume"},
    )
    save_digest_schedule(root, enabled=True, interval_hours=24, channels=["webhook"])
    with patch(
        "infra.creator_onboarding_webhook.dispatch_digest_webhook",
        return_value={"sent": True},
    ) as mock_webhook:
        sent = dispatch_scheduled_digest(root, force=True)
    assert sent["sent"] is True
    mock_webhook.assert_called_once()
    ProjectPaths.reset()


def test_dispatch_skips_when_not_due(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="digest-skip",
        title="跳过 digest",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_digest_schedule(root, enabled=True, interval_hours=24)
    skipped = dispatch_scheduled_digest(root, force=False)
    assert skipped["skipped"] is True
    assert skipped["reason"] == "no unread notifications"
    ProjectPaths.reset()
