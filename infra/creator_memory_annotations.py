"""Phase 126 v16.2.6 shim: re-export from lingwen_creator.memory.annotations.

Migrated to packages/lingwen-creator/src/lingwen_creator/memory/annotations.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_memory_annotations import load_memory_annotations, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.memory.annotations import *  # noqa: F403
