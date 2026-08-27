"""Phase 126 v16.2.0 shim: re-export from lingwen_creator.shared.revision.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/revision.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_revision import CreatorDocConflictError, content_revision

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.revision import *  # noqa: F403
