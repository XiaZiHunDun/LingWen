"""Tests for creator v6.6 diff pdf export, failure reason, mode switch confirm."""
from __future__ import annotations

from infra.creator_batch_history import derive_batch_failure_reason, enrich_batch_history_job
from infra.creator_ui_profile import resolve_creator_ui_profile


def test_advance_v66_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_export_pdf"] is True
    assert profile["batch_history_failure_reason_label"] is True
    assert profile["creation_mode_switch_confirm_dialog"] is True


def test_companion_v66_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile["creation_mode_switch_confirm_dialog"] is True
    assert profile.get("volume_plan_diff_export_pdf") is not True


def test_derive_batch_failure_reason() -> None:
    assert derive_batch_failure_reason({"status": "completed"}) is None
    assert derive_batch_failure_reason({"status": "failed", "error": "preflight blocked"}) == "preflight blocked"
    assert derive_batch_failure_reason({"status": "failed", "exit_code": 2}) == "进程退出码 2"
    enriched = enrich_batch_history_job({"status": "failed", "error": "chapter_failed"})
    assert enriched["failure_reason"] == "chapter_failed"
