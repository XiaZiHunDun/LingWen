"""Tests for creator onboarding mention webhooks."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from infra.creator_onboarding_webhook import (
    dispatch_mention_webhook,
    load_webhook_config,
    save_webhook_config,
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


def test_save_and_load_webhook_config(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="webhook-cfg",
        title="Webhook",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    saved = save_webhook_config(
        root,
        url="https://example.com/hooks/mentions",
        enabled=True,
        mention_handles=["batch"],
    )
    assert saved["enabled"] is True
    loaded = load_webhook_config(root)
    assert loaded["url"] == "https://example.com/hooks/mentions"
    assert loaded["mention_handles"] == ["batch"]
    ProjectPaths.reset()


def test_dispatch_webhook_filters_handles(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="webhook-dispatch",
        title="Webhook 发送",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_webhook_config(
        root,
        url="https://example.com/hooks/mentions",
        enabled=True,
        mention_handles=["batch"],
    )
    notifications = [
        {"id": "n1", "handle": "batch", "step_id": "volume", "note_excerpt": "x"},
        {"id": "n2", "handle": "reviewer", "step_id": "volume", "note_excerpt": "y"},
    ]
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.status = 200
        result_dispatch = dispatch_mention_webhook(root, notifications)
    assert result_dispatch["dispatched"] == 1
    ProjectPaths.reset()
