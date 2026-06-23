"""Tests for creator v3.6 features."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from infra.creator_merge_preferences import (
    list_merge_preset_changelog,
    preflight_factory_merge_preset_pull,
    publish_merge_preset_to_factory,
    save_merge_preset_package,
    toposort_merge_preset_packages,
)
from infra.creator_onboarding_digest_schedule import (
    enqueue_digest_retry,
    load_digest_dead_letter,
    process_digest_retries,
    save_digest_schedule,
)
from infra.creator_onboarding_webhook import load_webhook_config, save_webhook_config
from infra.creator_template_approvals import (
    approve_template_approval,
    load_approval_chain_config,
    preview_template_approval_snapshot_diff,
    save_approval_chain_config,
    submit_template_version_approval,
    transfer_template_approval,
)
from infra.creator_volume_templates import save_custom_volume_template, set_custom_template_version_label
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


def _template_id(root) -> str:
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    set_custom_template_version_label(root, saved["id"], version_label="v1.0.0")
    return saved["id"]


def test_or_signing_and_transfer(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v36-approval",
        title="审批",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    tid = _template_id(root)
    save_approval_chain_config(
        root,
        required_steps=1,
        step_assignee_groups=[["alice", "bob"]],
    )
    cfg = load_approval_chain_config(root)
    assert cfg["step_assignee_groups"] == [["alice", "bob"]]
    row = submit_template_version_approval(root, tid, version_label="v1.1.0")
    assert row["or_signing"] is True
    approved = approve_template_approval(root, row["id"], assignee="bob")
    assert approved["status"] == "approved"
    row2 = submit_template_version_approval(root, tid, version_label="v1.2.0")
    transferred = transfer_template_approval(root, row2["id"], to_assignee="carol", note="休假")
    assert transferred["current_assignee"] == "carol"
    ProjectPaths.reset()


def test_approval_snapshot_diff(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v36-snapshot",
        title="快照",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    tid = _template_id(root)
    save_approval_chain_config(root, required_steps=1)
    row = submit_template_version_approval(root, tid, version_label="v1.1.0")
    diff = preview_template_approval_snapshot_diff(root, row["id"])
    assert diff["approval_id"] == row["id"]
    assert "diff_summary" in diff
    ProjectPaths.reset()


def test_digest_dead_letter_and_handle_quiet(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v36-digest",
        title="Digest",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_digest_schedule(
        root,
        enabled=True,
        interval_hours=1,
        handle_quiet_hours={"batch": {"start": 0, "end": 23}},
    )
    enqueue_digest_retry(root, channel="webhook", digest={"unread": 1}, error="fail")
    from infra.creator_onboarding_digest_schedule import _load_retry_queue, _save_retry_queue

    items = _load_retry_queue(root)
    items[0]["attempts"] = 4
    items[0]["next_retry_at"] = None
    _save_retry_queue(root, items)
    with patch(
        "infra.creator_onboarding_webhook.dispatch_digest_webhook",
        return_value={"dispatched": 0, "error": "fail"},
    ):
        processed = process_digest_retries(root)
    assert processed["dead_letter_count"] >= 1
    dead = load_digest_dead_letter(root)
    assert dead["item_count"] >= 1
    ProjectPaths.reset()


def test_webhook_signing_secret(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v36-webhook",
        title="Webhook",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    saved = save_webhook_config(
        root,
        url="https://example.com/hook",
        enabled=True,
        signing_secret="top-secret",
    )
    assert saved["signing_secret"] == "top-secret"
    loaded = load_webhook_config(root)
    assert loaded["signing_secret"] == "top-secret"
    ProjectPaths.reset()


def test_preset_changelog_and_factory_pull_preflight(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v36-preset",
        title="预设",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_merge_preset_package(
        root,
        package_id="pkg_a",
        name="A",
        description="",
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
    )
    save_merge_preset_package(
        root,
        package_id="pkg_a",
        name="A2",
        description="",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
    )
    changelog = list_merge_preset_changelog(root, package_id="pkg_a")
    assert changelog["entry_count"] >= 1
    publish_merge_preset_to_factory(root, package_id="pkg_a")
    from infra.creator_merge_preferences import _normalize_factory_preset_id

    fid = _normalize_factory_preset_id("pkg_a")
    preflight = preflight_factory_merge_preset_pull(root, package_ids=[fid])
    assert preflight["would_import"] == 1
    topo = toposort_merge_preset_packages(root)
    assert "edges" in topo
    ProjectPaths.reset()
