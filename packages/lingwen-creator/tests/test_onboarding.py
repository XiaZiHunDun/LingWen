"""Phase 126 v16.2.3 T1a: tests for onboarding/ subdomain (7 small modules).

Tests cover:
- Package importability
- Per-module public function imports
- Shim back-compat for 7 infra modules
"""
from __future__ import annotations


def test_onboarding_package_imports() -> None:
    """lingwen_creator.onboarding package is importable."""
    import lingwen_creator.onboarding
    assert lingwen_creator.onboarding.__name__ == "lingwen_creator.onboarding"


def test_onboarding_star_imports_all_nine_submodules() -> None:
    """onboarding package __init__.py exposes all 9 submodules via star-imports."""
    import lingwen_creator.onboarding as pkg
    expected = {
        "onboarding",
        "autodetect",
        "digest_background",
        "digest_schedule",
        "email",
        "notifications",
        "progress",
        "webhook",
        "diff_collab",
    }
    for name in expected:
        assert hasattr(pkg, name), f"missing submodule {name}"


def test_onboarding_submodule_count() -> None:
    """Verify all 9 onboarding source modules are present in the package directory."""
    from pathlib import Path

    import lingwen_creator.onboarding

    pkg_dir = Path(lingwen_creator.onboarding.__file__).parent
    py_files = {p.stem for p in pkg_dir.glob("*.py") if p.stem != "__init__"}
    expected = {
        "onboarding",
        "autodetect",
        "digest_background",
        "digest_schedule",
        "email",
        "notifications",
        "progress",
        "webhook",
        "diff_collab",
    }
    missing = expected - py_files
    extra = py_files - expected
    assert not missing, f"missing onboarding modules: {missing}"
    assert not extra, f"unexpected onboarding modules: {extra}"


def test_autodetect_module_exports() -> None:
    """onboarding.autodetect exports infer_auto_completed_steps."""
    from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps
    assert callable(infer_auto_completed_steps)


def test_digest_background_module_exports() -> None:
    """onboarding.digest_background exports start_digest_background_task."""
    from lingwen_creator.onboarding.digest_background import (
        digest_poll_interval_sec,
        start_digest_background_task,
        tick_digest_for_active_project,
    )
    assert callable(start_digest_background_task)
    assert callable(digest_poll_interval_sec)
    assert callable(tick_digest_for_active_project)


def test_email_module_exports() -> None:
    """onboarding.email exports save_email_config + dispatch_approval_email."""
    from lingwen_creator.onboarding.email import (
        dispatch_approval_email,
        dispatch_digest_email,
        dispatch_mention_email,
        load_email_config,
        save_email_config,
    )
    assert callable(save_email_config)
    assert callable(dispatch_approval_email)
    assert callable(dispatch_mention_email)
    assert callable(dispatch_digest_email)
    assert callable(load_email_config)


def test_notifications_module_exports() -> None:
    """onboarding.notifications exports list_onboarding_notifications + ack."""
    from lingwen_creator.onboarding.notifications import (
        ack_onboarding_notifications,
        build_notification_digest,
        list_onboarding_notifications,
        record_mentions_from_notes,
        unread_mention_count,
    )
    assert callable(list_onboarding_notifications)
    assert callable(ack_onboarding_notifications)
    assert callable(build_notification_digest)
    assert callable(record_mentions_from_notes)
    assert callable(unread_mention_count)


def test_progress_module_exports() -> None:
    """onboarding.progress exports save_onboarding_progress + load_onboarding_progress."""
    from lingwen_creator.onboarding.progress import (
        build_step_mentions,
        effective_completed_step_ids,
        extract_step_mentions,
        load_onboarding_progress,
        merge_step_mention_maps,
        merge_step_notes,
        progress_pct,
        reconcile_onboarding_toggle,
        save_onboarding_progress,
    )
    assert callable(save_onboarding_progress)
    assert callable(load_onboarding_progress)
    assert callable(build_step_mentions)
    assert callable(extract_step_mentions)
    assert callable(merge_step_notes)
    assert callable(merge_step_mention_maps)
    assert callable(effective_completed_step_ids)
    assert callable(reconcile_onboarding_toggle)
    assert callable(progress_pct)


def test_webhook_module_exports() -> None:
    """onboarding.webhook exports save_webhook_config + dispatch_approval_webhook."""
    from lingwen_creator.onboarding.webhook import (
        dispatch_approval_webhook,
        dispatch_digest_webhook,
        dispatch_mention_webhook,
        load_webhook_config,
        save_webhook_config,
    )
    assert callable(save_webhook_config)
    assert callable(dispatch_approval_webhook)
    assert callable(dispatch_mention_webhook)
    assert callable(dispatch_digest_webhook)
    assert callable(load_webhook_config)


def test_diff_collab_module_exports() -> None:
    """onboarding.diff_collab exports diff_collab_notes_payload + save/load."""
    from lingwen_creator.onboarding.diff_collab import (
        diff_collab_notes_payload,
        load_diff_collab_notes,
        merge_diff_collab_notes,
        save_diff_collab_notes,
    )
    assert callable(diff_collab_notes_payload)
    assert callable(save_diff_collab_notes)
    assert callable(load_diff_collab_notes)
    assert callable(merge_diff_collab_notes)


def test_digest_schedule_module_exports() -> None:
    """onboarding.digest_schedule exports load/save_digest_schedule + dispatch + retries."""
    from lingwen_creator.onboarding.digest_schedule import (
        dispatch_scheduled_digest,
        enqueue_digest_retry,
        load_digest_dead_letter,
        load_digest_dispatch_stats,
        load_digest_retry_queue,
        load_digest_schedule,
        process_digest_retries,
        record_digest_dispatch,
        replay_digest_dead_letter,
        save_digest_schedule,
    )
    assert callable(load_digest_schedule)
    assert callable(save_digest_schedule)
    assert callable(load_digest_dead_letter)
    assert callable(replay_digest_dead_letter)
    assert callable(load_digest_dispatch_stats)
    assert callable(load_digest_retry_queue)
    assert callable(process_digest_retries)
    assert callable(dispatch_scheduled_digest)
    assert callable(record_digest_dispatch)
    assert callable(enqueue_digest_retry)


def test_onboarding_main_module_exports() -> None:
    """onboarding.onboarding (main) exports wizard payload + save functions."""
    from lingwen_creator.onboarding.onboarding import (
        apply_wizard_share_done,
        dismiss_onboarding_wizard_panel,
        onboarding_wizard_payload,
        save_onboarding_notes_from_ui,
        save_onboarding_progress_from_ui,
        save_onboarding_wizard_panel_collapsed,
    )
    assert callable(onboarding_wizard_payload)
    assert callable(save_onboarding_progress_from_ui)
    assert callable(dismiss_onboarding_wizard_panel)
    assert callable(save_onboarding_wizard_panel_collapsed)
    assert callable(apply_wizard_share_done)
    assert callable(save_onboarding_notes_from_ui)


def test_onboarding_forward_references_creator_mode() -> None:
    """onboarding.onboarding imports creation_mode constants via lingwen_creator.shared.mode.

    Phase 126 v16.2.4 T1 closed the legacy forward-reference to infra.creator_mode.
    Now uses `from lingwen_creator.shared.mode import ...` (cross-subdomain utility per
    spec §2.4) without any noqa workaround. Verifies the symbols remain re-exported
    through the onboarding module for any callers relying on `from lingwen_creator.onboarding
    .onboarding import CREATION_MODE_*`.
    """
    from lingwen_creator.onboarding.onboarding import (
        CREATION_MODE_ADVANCE,
        CREATION_MODE_COMPANION,
        CREATION_MODE_STUDIO,
        settings_from_project_config,
    )
    assert CREATION_MODE_COMPANION == "companion"
    assert CREATION_MODE_ADVANCE == "advance"
    assert CREATION_MODE_STUDIO == "studio"
    assert callable(settings_from_project_config)


# --- Shim back-compat tests ---


def test_shim_backcompat_autodetect() -> None:
    """Backwards compat: `from infra.creator_onboarding_autodetect import ...` works."""
    from infra.creator_onboarding_autodetect import infer_auto_completed_steps
    assert callable(infer_auto_completed_steps)


def test_shim_backcompat_digest_background() -> None:
    """Backwards compat: `from infra.creator_onboarding_digest_background import ...` works."""
    from infra.creator_onboarding_digest_background import (
        digest_poll_interval_sec,
        start_digest_background_task,
    )
    assert callable(start_digest_background_task)
    assert callable(digest_poll_interval_sec)


def test_shim_backcompat_email() -> None:
    """Backwards compat: `from infra.creator_onboarding_email import ...` works."""
    from infra.creator_onboarding_email import dispatch_approval_email, load_email_config
    assert callable(dispatch_approval_email)
    assert callable(load_email_config)


def test_shim_backcompat_notifications() -> None:
    """Backwards compat: `from infra.creator_onboarding_notifications import ...` works."""
    from infra.creator_onboarding_notifications import list_onboarding_notifications
    assert callable(list_onboarding_notifications)


def test_shim_backcompat_progress() -> None:
    """Backwards compat: `from infra.creator_onboarding_progress import ...` works."""
    from infra.creator_onboarding_progress import save_onboarding_progress
    assert callable(save_onboarding_progress)


def test_shim_backcompat_webhook() -> None:
    """Backwards compat: `from infra.creator_onboarding_webhook import ...` works."""
    from infra.creator_onboarding_webhook import dispatch_approval_webhook
    assert callable(dispatch_approval_webhook)


def test_shim_backcompat_diff_collab() -> None:
    """Backwards compat: `from infra.creator_diff_collab import ...` works."""
    from infra.creator_diff_collab import diff_collab_notes_payload
    assert callable(diff_collab_notes_payload)


def test_shim_backcompat_digest_schedule() -> None:
    """Backwards compat: `from infra.creator_onboarding_digest_schedule import ...` works."""
    from infra.creator_onboarding_digest_schedule import (
        dispatch_scheduled_digest,
        load_digest_schedule,
        process_digest_retries,
        save_digest_schedule,
    )
    assert callable(load_digest_schedule)
    assert callable(save_digest_schedule)
    assert callable(dispatch_scheduled_digest)
    assert callable(process_digest_retries)


def test_shim_backcompat_onboarding_main() -> None:
    """Backwards compat: `from infra.creator_onboarding import ...` works (main file)."""
    from infra.creator_onboarding import (
        dismiss_onboarding_wizard_panel,
        onboarding_wizard_payload,
        save_onboarding_notes_from_ui,
        save_onboarding_progress_from_ui,
    )
    assert callable(onboarding_wizard_payload)
    assert callable(save_onboarding_progress_from_ui)
    assert callable(dismiss_onboarding_wizard_panel)
    assert callable(save_onboarding_notes_from_ui)


# --- Cross-subdomain imports ---


def test_onboarding_uses_volume_plan_intra_package() -> None:
    """onboarding.autodetect imports load_volume_plan from lingwen_creator.volume.plan (volume migrated)."""
    from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps
    from lingwen_creator.volume.plan import load_volume_plan
    # Both importable; intra-package reference is resolved at import time
    assert callable(infer_auto_completed_steps)
    assert callable(load_volume_plan)


def test_notifications_intra_package_loads_progress() -> None:
    """onboarding.notifications uses lingwen_creator.onboarding.progress.extract_step_mentions (intra-package)."""
    from lingwen_creator.onboarding.notifications import record_mentions_from_notes
    from lingwen_creator.onboarding.progress import extract_step_mentions
    assert callable(record_mentions_from_notes)
    assert callable(extract_step_mentions)
