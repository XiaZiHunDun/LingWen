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


def test_autodetect_module_exports() -> None:
    """onboarding.autodetect exports infer_auto_completed_steps."""
    from lingwen_creator.onboarding.autodetect import infer_auto_completed_steps
    assert callable(infer_auto_completed_steps)


def test_digest_background_module_exports() -> None:
    """onboarding.digest_background exports start_digest_background_task."""
    from lingwen_creator.onboarding.digest_background import (
        start_digest_background_task,
        digest_poll_interval_sec,
        tick_digest_for_active_project,
    )
    assert callable(start_digest_background_task)
    assert callable(digest_poll_interval_sec)
    assert callable(tick_digest_for_active_project)


def test_email_module_exports() -> None:
    """onboarding.email exports save_email_config + dispatch_approval_email."""
    from lingwen_creator.onboarding.email import (
        save_email_config,
        dispatch_approval_email,
        dispatch_mention_email,
        dispatch_digest_email,
        load_email_config,
    )
    assert callable(save_email_config)
    assert callable(dispatch_approval_email)
    assert callable(dispatch_mention_email)
    assert callable(dispatch_digest_email)
    assert callable(load_email_config)


def test_notifications_module_exports() -> None:
    """onboarding.notifications exports list_onboarding_notifications + ack."""
    from lingwen_creator.onboarding.notifications import (
        list_onboarding_notifications,
        ack_onboarding_notifications,
        build_notification_digest,
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
        save_onboarding_progress,
        load_onboarding_progress,
        build_step_mentions,
        extract_step_mentions,
        merge_step_notes,
        merge_step_mention_maps,
        effective_completed_step_ids,
        reconcile_onboarding_toggle,
        progress_pct,
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
        save_webhook_config,
        dispatch_approval_webhook,
        dispatch_mention_webhook,
        dispatch_digest_webhook,
        load_webhook_config,
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
        save_diff_collab_notes,
        load_diff_collab_notes,
        merge_diff_collab_notes,
    )
    assert callable(diff_collab_notes_payload)
    assert callable(save_diff_collab_notes)
    assert callable(load_diff_collab_notes)
    assert callable(merge_diff_collab_notes)


def test_digest_schedule_module_exports() -> None:
    """onboarding.digest_schedule exports load/save_digest_schedule + dispatch + retries."""
    from lingwen_creator.onboarding.digest_schedule import (
        load_digest_schedule,
        save_digest_schedule,
        load_digest_dead_letter,
        replay_digest_dead_letter,
        load_digest_dispatch_stats,
        load_digest_retry_queue,
        process_digest_retries,
        dispatch_scheduled_digest,
        record_digest_dispatch,
        enqueue_digest_retry,
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


# --- Shim back-compat tests ---


def test_shim_backcompat_autodetect() -> None:
    """Backwards compat: `from infra.creator_onboarding_autodetect import ...` works."""
    from infra.creator_onboarding_autodetect import infer_auto_completed_steps
    assert callable(infer_auto_completed_steps)


def test_shim_backcompat_digest_background() -> None:
    """Backwards compat: `from infra.creator_onboarding_digest_background import ...` works."""
    from infra.creator_onboarding_digest_background import (
        start_digest_background_task,
        digest_poll_interval_sec,
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
        load_digest_schedule,
        save_digest_schedule,
        dispatch_scheduled_digest,
        process_digest_retries,
    )
    assert callable(load_digest_schedule)
    assert callable(save_digest_schedule)
    assert callable(dispatch_scheduled_digest)
    assert callable(process_digest_retries)


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
