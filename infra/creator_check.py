"""Phase 126 v16.2.0 shim: re-export from lingwen_creator.shared.check.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/check.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_check import load_creator_check_context, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.check import *  # noqa: F403
