"""Tests for digest quiet hours and retry queue."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from infra.creator_onboarding_digest_schedule import (
    dispatch_scheduled_digest,
    enqueue_digest_retry,
    load_digest_retry_queue,
    process_digest_retries,
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


def test_quiet_hours_skip_dispatch(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="digest-quiet",
        title="静默",
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
    save_digest_schedule(
        root,
        enabled=True,
        interval_hours=1,
        channels=["webhook"],
        quiet_hours_start=0,
        quiet_hours_end=23,
    )
    skipped = dispatch_scheduled_digest(root, force=False)
    assert skipped.get("reason") == "quiet hours"
    ProjectPaths.reset()


def test_digest_retry_queue(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="digest-retry",
        title="重试",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    enqueue_digest_retry(
        root,
        channel="webhook",
        digest={"unread": 1, "group_count": 1, "groups": []},
        error="timeout",
    )
    queue = load_digest_retry_queue(root)
    assert queue["item_count"] == 1
    with patch(
        "infra.creator_onboarding_webhook.dispatch_digest_webhook",
        return_value={"dispatched": 1},
    ):
        processed = process_digest_retries(root)
    assert processed["retried"] == 1
    assert processed["remaining"] == 0
    ProjectPaths.reset()
