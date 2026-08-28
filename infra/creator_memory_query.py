"""Phase 126 v16.2.6 shim: re-export from lingwen_creator.memory.query.

Migrated to packages/lingwen-creator/src/lingwen_creator/memory/query.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_memory_query import creator_memory_query

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.memory.query import *  # noqa: F403
