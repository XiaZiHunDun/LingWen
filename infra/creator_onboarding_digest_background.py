"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.digest_background.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/digest_background.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.digest_background import *  # noqa: F401,F403
from lingwen_creator.onboarding.digest_background import (  # noqa: F401
    _DEFAULT_POLL_SEC,
    digest_poll_interval_sec,
    run_digest_background_loop,
    start_digest_background_task,
    tick_digest_for_active_project,
)
