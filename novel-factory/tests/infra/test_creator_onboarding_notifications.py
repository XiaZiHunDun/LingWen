"""Tests for wizard @mention notifications."""
from __future__ import annotations

import pytest

from infra.creator_onboarding_notifications import (
    ack_onboarding_notifications,
    list_onboarding_notifications,
    unread_mention_count,
)
from infra.creator_onboarding_progress import save_onboarding_progress
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


def test_mention_notifications_created_and_acked(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="wiz-notify",
        title="通知",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_onboarding_progress(
        root,
        completed_step_ids=["init"],
        step_notes={"volume": "请 @reviewer 协助"},
    )
    assert unread_mention_count(root) == 1
    rows = list_onboarding_notifications(root, unread_only=True)
    assert rows[0]["handle"] == "reviewer"
    ack = ack_onboarding_notifications(root, all_notifications=True)
    assert ack["acked"] == 1
    assert unread_mention_count(root) == 0
    ProjectPaths.reset()


def test_notifications_filter_by_handle(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="wiz-filter",
        title="过滤",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_onboarding_progress(
        root,
        completed_step_ids=["init"],
        step_notes={"volume": "请 @batch 和 @reviewer 协助"},
    )
    batch_only = list_onboarding_notifications(root, handle="batch")
    assert len(batch_only) == 1
    assert batch_only[0]["handle"] == "batch"
    ProjectPaths.reset()
