"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.volume.summary.

Migrated to packages/lingwen-creator/src/lingwen_creator/volume/summary.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_volume_summary import build_volume_summary, write_volume_summary, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.volume.summary import *  # noqa: F403
