"""Onboarding subdomain — wizard payload + progress + notifications + webhooks.

Module structure (Phase 126 v16.2.3):
- onboarding: main wizard payload + progress + dismiss/collapse
- autodetect: auto-detect completed steps (depends on volume.plan)
- digest_background: background task lifecycle
- digest_schedule: schedule config + dead-letter + retry + dispatch
- email: email config + dispatch
- notifications: notification list + ack + digest
- progress: onboarding progress state
- webhook: webhook config + dispatch
- diff_collab: diff collab notes
"""

from lingwen_creator.onboarding import (
    autodetect,  # noqa: F401
    diff_collab,  # noqa: F401
    digest_background,  # noqa: F401
    digest_schedule,  # noqa: F401
    email,  # noqa: F401
    notifications,  # noqa: F401
    onboarding,  # noqa: F401
    progress,  # noqa: F401
    webhook,  # noqa: F401
)
