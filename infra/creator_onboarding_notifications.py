"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.notifications.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/notifications.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.notifications import *  # noqa: F401,F403
from lingwen_creator.onboarding.notifications import (  # noqa: F401
    _MAX_NOTE_EXCERPT,
    _MAX_NOTIFICATIONS,
    _STATE_VERSION,
    _load_store,
    _notifications_path,
    _now_iso,
    _save_store,
    ack_onboarding_notifications,
    build_notification_digest,
    list_notification_handles,
    list_onboarding_notifications,
    record_mentions_from_notes,
    unread_mention_count,
)
