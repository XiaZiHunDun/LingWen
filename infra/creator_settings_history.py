"""Phase 126 v16.2.2 shim: re-export from lingwen_creator.settings.history.

Migrated to packages/lingwen-creator/src/lingwen_creator/settings/history.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_settings_history import settings_history_payload, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.settings.history import *  # noqa: F403
