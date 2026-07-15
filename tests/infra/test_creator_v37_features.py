"""Tests for creator v3.7 features."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from infra.creator_merge_preferences import (
    list_merge_preset_changelog,
    preview_merge_preset_changelog_diff,
    publish_merge_preset_to_factory,
    pull_factory_merge_presets_to_project,
    save_merge_preset_package,
)
from infra.creator_onboarding_digest_schedule import (
    _append_dead_letter,
    enqueue_digest_retry,
    load_digest_dead_letter,
    load_digest_schedule,
    process_digest_retries,
    replay_digest_dead_letter,
    save_digest_schedule,
)
from infra.creator_template_approvals import (
    approve_template_approval,
    batch_approve_template_approvals,
    batch_reject_template_approvals,
    check_approval_snapshot_drift,
    save_approval_chain_config,
    submit_template_version_approval,
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


def test_approval_drift_blocks_and_batch(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v37-approval",
        title="审批",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    tid = _template_id(root)
    save_approval_chain_config(root, required_steps=1)
    row = submit_template_version_approval(root, tid, version_label="v1.1.0")
    drift = check_approval_snapshot_drift(root, row["id"])
    assert drift["drifted"] is False
    from infra.creator_volume_templates import _load_custom_store, _save_custom_store

    store = _load_custom_store(root)
    for item in store.get("templates", []):
        if item.get("id") == tid:
            item["volumes"][0]["end_chapter"] = 10
            break
    _save_custom_store(root, store)
    drift2 = check_approval_snapshot_drift(root, row["id"])
    assert drift2["drifted"] is True
    with pytest.raises(ValueError, match="drifted"):
        approve_template_approval(root, row["id"])
    approved = approve_template_approval(root, row["id"], force=True)
    assert approved["status"] == "approved"
    row2 = submit_template_version_approval(root, tid, version_label="v1.2.0")
    rejected = batch_reject_template_approvals(root, [row2["id"]], reason="no")
    assert rejected["rejected"] == 1
    row3 = submit_template_version_approval(root, tid, version_label="v1.3.0")
    batch = batch_approve_template_approvals(root, [row3["id"]], force=True)
    assert batch["approved"] == 1
    ProjectPaths.reset()


def test_digest_replay_and_channel_retry(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v37-digest",
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
        channel_retry_config={"webhook": {"max_attempts": 2, "base_backoff_sec": 30}},
    )
    schedule = load_digest_schedule(root)
    assert schedule["channel_retry_config"]["webhook"]["max_attempts"] == 2
    _append_dead_letter(
        root,
        {"channel": "webhook", "digest": {"unread": 1}, "error": "dead", "attempts": 5},
    )
    assert load_digest_dead_letter(root)["item_count"] == 1
    replayed = replay_digest_dead_letter(root, index=0)
    assert replayed["replayed"] is True
    assert load_digest_dead_letter(root)["item_count"] == 0
    enqueue_digest_retry(root, channel="webhook", digest={"unread": 1}, error="fail")
    from infra.creator_onboarding_digest_schedule import _load_retry_queue, _save_retry_queue

    items = _load_retry_queue(root)
    items[0]["attempts"] = 1
    items[0]["next_retry_at"] = None
    _save_retry_queue(root, items)
    with patch(
        "infra.creator_onboarding_webhook.dispatch_digest_webhook",
        return_value={"dispatched": 0, "error": "fail"},
    ):
        processed = process_digest_retries(root)
    assert processed["dead_letter_count"] >= 1
    ProjectPaths.reset()


def test_factory_pull_strategies_and_changelog_diff(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v37-preset",
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
    diff = preview_merge_preset_changelog_diff(root, package_id="pkg_a", entry_index=0)
    assert diff["change_count"] >= 1
    assert any(row["field"] == "name" for row in diff["changes"])
    publish_merge_preset_to_factory(root, package_id="pkg_a")
    from infra.creator_merge_preferences import _normalize_factory_preset_id

    fid = _normalize_factory_preset_id("pkg_a")
    save_merge_preset_package(
        root,
        package_id="pkg_a",
        name="Local",
        description="",
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
    )
    skipped = pull_factory_merge_presets_to_project(
        root,
        package_ids=[fid],
        conflict_strategies={"pkg_a": "prefer_project"},
    )
    assert skipped["skipped"] == 1
    pulled = pull_factory_merge_presets_to_project(
        root,
        package_ids=[fid],
        conflict_strategies={"pkg_a": "prefer_factory"},
    )
    assert pulled["imported"] == 1
    changelog = list_merge_preset_changelog(root, package_id="pkg_a")
    assert changelog["entry_count"] >= 1
    ProjectPaths.reset()
