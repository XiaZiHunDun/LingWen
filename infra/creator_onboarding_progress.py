"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.progress.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/progress.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.progress import *  # noqa: F401,F403
from lingwen_creator.onboarding.progress import (  # noqa: F401
    extract_step_mentions,
    build_step_mentions,
    load_onboarding_progress,
    save_onboarding_progress,
    dismiss_wizard_panel,
    save_wizard_panel_collapsed,
    merge_step_notes,
    merge_step_mention_maps,
    effective_completed_step_ids,
    reconcile_onboarding_toggle,
    progress_pct,
    _STATE_VERSION,
    _MAX_NOTE_LEN,
    _MENTION_RE,
    _progress_path,
    _now_iso,
    _normalize_step_notes,
    _normalize_step_mentions,
)
