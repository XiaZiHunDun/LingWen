"""Tests for template approval SLA and email hooks."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from infra.creator_template_approvals import (
    _load_store,
    _save_store,
    list_overdue_template_approvals,
    save_approval_sla_config,
    submit_template_version_approval,
)
from infra.creator_volume_templates import save_custom_volume_template
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


def test_overdue_template_approvals(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="tmpl-sla",
        title="SLA",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_approval_sla_config(root, timeout_hours=24)
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    with patch("infra.creator_onboarding_webhook.dispatch_approval_webhook"):
        with patch("infra.creator_onboarding_email.dispatch_approval_email") as mock_email:
            pending = submit_template_version_approval(root, saved["id"], version_label="v1.0.0")
            mock_email.assert_called()
    store = _load_store(root)
    for row in store.get("approvals") or []:
        if row.get("id") == pending["id"]:
            row["submitted_at"] = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    _save_store(root, store)
    overdue = list_overdue_template_approvals(root)
    assert len(overdue) == 1
    assert overdue[0]["hours_pending"] >= 48
    ProjectPaths.reset()
