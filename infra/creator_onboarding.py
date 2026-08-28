"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.onboarding.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.onboarding import *  # noqa: F401,F403
from lingwen_creator.onboarding.onboarding import (  # noqa: F401
    _MODE_LABELS,
    _progress_response,
    _step_mentions_for_steps,
    _unread_mention_count,
    apply_wizard_share_done,
    dismiss_onboarding_wizard_panel,
    onboarding_wizard_payload,
    save_onboarding_notes_from_ui,
    save_onboarding_progress_from_ui,
    save_onboarding_wizard_panel_collapsed,
)
