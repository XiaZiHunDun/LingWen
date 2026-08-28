"""Phase 126 v16.2.6 shim: re-export from lingwen_creator.memory.assets.

Migrated to packages/lingwen-creator/src/lingwen_creator/memory/assets.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_memory_assets import creator_memory_assets_payload, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.memory.assets import *  # noqa: F403
