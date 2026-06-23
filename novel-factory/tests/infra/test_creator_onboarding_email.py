"""Tests for creator onboarding mention email dispatch."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from infra.creator_onboarding_email import (
    dispatch_mention_email,
    load_email_config,
    save_email_config,
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


def test_save_and_load_email_config(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="email-cfg",
        title="邮件",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    saved = save_email_config(
        root,
        enabled=True,
        to_addresses=["writer@example.com"],
        mention_handles=["batch"],
        smtp_host="smtp.example.com",
        from_address="writer@example.com",
    )
    assert saved["enabled"] is True
    loaded = load_email_config(root)
    assert loaded["to_addresses"] == ["writer@example.com"]
    assert loaded["smtp_host"] == "smtp.example.com"
    ProjectPaths.reset()


def test_dispatch_email_filters_handles(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="email-dispatch",
        title="邮件发送",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_email_config(
        root,
        enabled=True,
        to_addresses=["writer@example.com"],
        mention_handles=["batch"],
        smtp_host="smtp.example.com",
        from_address="writer@example.com",
    )
    notifications = [
        {"id": "n1", "handle": "batch", "step_id": "volume", "note_excerpt": "x"},
        {"id": "n2", "handle": "reviewer", "step_id": "volume", "note_excerpt": "y"},
    ]
    smtp = MagicMock()
    smtp.__enter__ = MagicMock(return_value=smtp)
    smtp.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP", return_value=smtp):
        result_dispatch = dispatch_mention_email(root, notifications)
    assert result_dispatch["sent"] == 1
    smtp.send_message.assert_called_once()
    ProjectPaths.reset()
