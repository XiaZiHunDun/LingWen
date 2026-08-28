"""Phase 126 v16.2.3 shim: re-export from lingwen_creator.onboarding.webhook.

Original module moved to packages/lingwen-creator/src/lingwen_creator/onboarding/webhook.py.
This shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.onboarding.webhook import *  # noqa: F401,F403
from lingwen_creator.onboarding.webhook import (  # noqa: F401
    load_webhook_config,
    save_webhook_config,
    dispatch_mention_webhook,
    dispatch_digest_webhook,
    dispatch_approval_webhook,
    _STATE_VERSION,
    _MAX_URL,
    _MAX_SECRET,
    _WEBHOOK_TIMEOUT_SEC,
    _webhook_path,
    _sign_payload,
    _webhook_headers,
    _post_webhook,
)
