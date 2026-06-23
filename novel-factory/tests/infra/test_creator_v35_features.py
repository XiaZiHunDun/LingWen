"""Tests for creator v3.5: assignees, digest routing/stats, preset topo/diff."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from infra.creator_merge_preferences import (
    apply_toposort_merge_preset_order,
    detect_factory_merge_preset_conflicts,
    preview_merge_preset_import_diff,
    publish_merge_preset_to_factory,
    save_merge_preset_package,
    toposort_merge_preset_packages,
)
from infra.creator_onboarding_digest_schedule import (
    enqueue_digest_retry,
    load_digest_dispatch_stats,
    load_digest_schedule,
    process_digest_retries,
    save_digest_schedule,
)
from infra.creator_template_approvals import (
    _approvals_path,
    _load_store,
    approve_template_approval,
    notify_overdue_template_approvals,
    save_approval_chain_config,
    save_approval_sla_config,
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


def _save_template(root, name: str = "结构") -> str:
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name=name, volumes=volumes, max_chapter=12)
    set_custom_template_version_label(root, saved["id"], version_label="v1.0.0")
    return saved["id"]


def test_approval_step_assignees_and_notes(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v35-approval",
        title="审批",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    tid = _save_template(root)
    save_approval_chain_config(root, required_steps=1, step_assignees=["alice"])
    row = submit_template_version_approval(
        root,
        tid,
        version_label="v1.1.0",
        submit_note="请审阅",
    )
    assert row["submit_note"] == "请审阅"
    assert row["current_assignee"] == "alice"
    approved = approve_template_approval(root, row["id"], assignee="alice", resolve_note="LGTM")
    assert approved["resolve_note"] == "LGTM"
    ProjectPaths.reset()


def test_notify_overdue_once(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v35-overdue",
        title="超时",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    tid = _save_template(root, "超时卷")
    save_approval_sla_config(root, timeout_hours=1, email_on_overdue=True)
    save_approval_chain_config(root, required_steps=1)
    submit_template_version_approval(root, tid, version_label="v1.1.0")
    store = _load_store(root)
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    store["approvals"][0]["submitted_at"] = past
    _approvals_path(root).write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with patch("infra.creator_onboarding_email.dispatch_approval_email", return_value={"sent": True}) as mail:
        first = notify_overdue_template_approvals(root)
        second = notify_overdue_template_approvals(root)
    assert first["notified"] == 1
    assert second["notified"] == 0
    assert mail.call_count == 1
    ProjectPaths.reset()


def test_digest_handle_channels_and_stats(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v35-digest",
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
        channels=["webhook"],
        handle_channels={"batch": ["webhook"], "*": ["email"]},
    )
    loaded = load_digest_schedule(root)
    assert loaded["handle_channels"]["batch"] == ["webhook"]
    enqueue_digest_retry(root, channel="webhook", digest={"unread": 1}, error="fail")
    stats = load_digest_dispatch_stats(root)
    assert stats["failed_total"] >= 1
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    from infra.creator_onboarding_digest_schedule import _load_retry_queue, _save_retry_queue

    items = _load_retry_queue(root)
    items[0]["next_retry_at"] = future
    _save_retry_queue(root, items)
    processed = process_digest_retries(root)
    assert processed["retried"] == 0
    assert processed["remaining"] == 1
    ProjectPaths.reset()


def test_merge_preset_toposort_and_diff(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v35-preset",
        title="预设",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_merge_preset_package(
        root,
        package_id="pkg_b",
        name="B",
        description="",
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
        depends_on=["pkg_a"],
    )
    save_merge_preset_package(
        root,
        package_id="pkg_a",
        name="A",
        description="",
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
    )
    topo = toposort_merge_preset_packages(root)
    assert topo["order"].index("pkg_a") < topo["order"].index("pkg_b")
    apply_toposort_merge_preset_order(root)
    diff = preview_merge_preset_import_diff(
        root,
        {
            "packages": [
                {
                    "id": "pkg_a",
                    "name": "A2",
                    "pillars_merge_source": "editor",
                    "global_outline_merge_source": "editor",
                },
            ],
        },
    )
    assert diff["updated"]
    save_merge_preset_package(
        root,
        package_id="factory_clash",
        name="本地",
        description="",
        pillars_merge_source="editor",
        global_outline_merge_source="editor",
        version_label="v1.0.0",
    )
    publish_merge_preset_to_factory(root, package_id="factory_clash")
    save_merge_preset_package(
        root,
        package_id="factory_clash",
        name="本地改",
        description="",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
        version_label="v1.0.0",
    )
    conflicts = detect_factory_merge_preset_conflicts(root)
    assert conflicts["conflict_count"] >= 1
    ProjectPaths.reset()
