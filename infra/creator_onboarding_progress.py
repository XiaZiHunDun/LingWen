"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.progress.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/progress.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.progress import *  # noqa: F401,F403
from lingwen_creator.onboarding.progress import (  # noqa: F401
    _MAX_NOTE_LEN,
    _MENTION_RE,
    _STATE_VERSION,
    _normalize_step_mentions,
    _normalize_step_notes,
    _now_iso,
    _progress_path,
    build_step_mentions,
    dismiss_wizard_panel,
    effective_completed_step_ids,
    extract_step_mentions,
    load_onboarding_progress,
    merge_step_mention_maps,
    merge_step_notes,
    progress_pct,
    reconcile_onboarding_toggle,
    save_onboarding_progress,
    save_wizard_panel_collapsed,
)
