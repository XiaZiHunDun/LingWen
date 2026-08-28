"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.notifications.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/notifications.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.notifications import *  # noqa: F401,F403
from lingwen_creator.onboarding.notifications import (  # noqa: F401
    record_mentions_from_notes,
    list_onboarding_notifications,
    list_notification_handles,
    unread_mention_count,
    ack_onboarding_notifications,
    build_notification_digest,
    _STATE_VERSION,
    _MAX_NOTIFICATIONS,
    _MAX_NOTE_EXCERPT,
    _notifications_path,
    _now_iso,
    _load_store,
    _save_store,
)
