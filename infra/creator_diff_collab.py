"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.diff_collab.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/diff_collab.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.diff_collab import *  # noqa: F401,F403
from lingwen_creator.onboarding.diff_collab import (  # noqa: F401
    _MAX_NOTE_LEN,
    _STATE_VERSION,
    _normalize_notes,
    _now_iso,
    _path,
    diff_collab_notes_payload,
    load_diff_collab_notes,
    merge_diff_collab_notes,
    save_diff_collab_notes,
)
