"""Tests for template approval audit export and webhook events."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from infra.creator_template_approvals import (
    export_template_approval_audit,
    list_template_approval_history,
    save_approval_chain_config,
    submit_template_version_approval,
    approve_template_approval,
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


def test_export_approval_audit_includes_chain_log(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="tmpl-audit",
        title="审计",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_approval_chain_config(root, required_steps=1)
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    with patch("infra.creator_onboarding_webhook.dispatch_approval_webhook") as mock_hook:
        pending = submit_template_version_approval(root, saved["id"], version_label="v1.0.0")
        approve_template_approval(root, pending["id"])
        assert mock_hook.call_count >= 2
    audit = export_template_approval_audit(root)
    assert audit["count"] >= 1
    approved = next(row for row in audit["approvals"] if row["id"] == pending["id"])
    assert approved["status"] == "approved"
    assert approved["chain_log"]
    history = list_template_approval_history(root)
    assert history[0]["chain_log"]
    ProjectPaths.reset()
