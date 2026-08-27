"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.volume.plan.

Migrated to packages/lingwen-creator/src/lingwen_creator/volume/plan.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_volume_plan import load_volume_plan, save_volume_plan, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.volume.plan import *  # noqa: F403
