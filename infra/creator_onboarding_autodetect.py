"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.autodetect.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/autodetect.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.autodetect import *  # noqa: F401,F403
from lingwen_creator.onboarding.autodetect import (  # noqa: F401
    infer_auto_completed_steps,
    _PILLARS_MIN_CHARS,
)
