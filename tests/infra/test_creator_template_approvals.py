"""Tests for template version approval workflow."""
from __future__ import annotations

import pytest

from infra.creator_template_approvals import (
    approve_template_approval,
    list_template_approvals,
    reject_template_approval,
    save_approval_chain_config,
    submit_template_version_approval,
)
from infra.creator_volume_templates import (
    save_custom_volume_template,
    set_custom_template_version_label,
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


def test_submit_and_approve_template_version(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="tmpl-approval",
        title="审批",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    set_custom_template_version_label(root, saved["id"], version_label="v1.0.0")
    save_approval_chain_config(root, required_steps=1)
    pending = submit_template_version_approval(root, saved["id"], version_label="v2.0.0")
    assert pending["status"] == "pending"
    rows = list_template_approvals(root, status="pending")
    assert len(rows) == 1
    approved = approve_template_approval(root, pending["id"])
    assert approved["status"] == "approved"
    ProjectPaths.reset()


def test_reject_template_version_approval(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="tmpl-reject",
        title="驳回",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    save_approval_chain_config(root, required_steps=1)
    pending = submit_template_version_approval(root, saved["id"], version_label="v1.0.0")
    rejected = reject_template_approval(root, pending["id"], reason="semver 不合规")
    assert rejected["status"] == "rejected"
    assert rejected["reject_reason"] == "semver 不合规"
    ProjectPaths.reset()
