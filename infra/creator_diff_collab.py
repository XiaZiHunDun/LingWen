"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.diff_collab.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/diff_collab.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.diff_collab import *  # noqa: F401,F403
from lingwen_creator.onboarding.diff_collab import (  # noqa: F401
    load_diff_collab_notes,
    save_diff_collab_notes,
    merge_diff_collab_notes,
    diff_collab_notes_payload,
    _STATE_VERSION,
    _MAX_NOTE_LEN,
    _path,
    _now_iso,
    _normalize_notes,
)
