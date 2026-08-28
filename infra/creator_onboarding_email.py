"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.email.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/email.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.email import *  # noqa: F401,F403
from lingwen_creator.onboarding.email import (  # noqa: F401
    _EMAIL_RE,
    _MAX_ADDRESS,
    _MAX_ADDRESSES,
    _SMTP_TIMEOUT_SEC,
    _STATE_VERSION,
    _build_approval_email_body,
    _build_digest_email_body,
    _build_email_body,
    _email_path,
    _normalize_addresses,
    dispatch_approval_email,
    dispatch_digest_email,
    dispatch_mention_email,
    load_email_config,
    save_email_config,
)
