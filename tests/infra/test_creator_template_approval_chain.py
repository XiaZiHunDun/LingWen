"""Tests for multi-step template version approval chain."""
from __future__ import annotations

import pytest

from infra.creator_template_approvals import (
    approve_template_approval,
    list_template_approvals,
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


def test_approval_chain_requires_multiple_steps(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="tmpl-chain",
        title="审批链",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_approval_chain_config(root, required_steps=2)
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    set_custom_template_version_label(root, saved["id"], version_label="v1.0.0")
    pending = submit_template_version_approval(root, saved["id"], version_label="v2.0.0")
    assert pending["chain_progress"] == "1/2"
    first = approve_template_approval(root, pending["id"])
    assert first["chain_advanced"] is True
    assert first["status"] == "pending"
    assert first["chain_progress"] == "2/2"
    second = approve_template_approval(root, pending["id"])
    assert second["chain_advanced"] is False
    assert second["status"] == "approved"
    rows = list_template_approvals(root, status="pending")
    assert rows == []
    ProjectPaths.reset()
