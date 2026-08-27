"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.volume.plan_share.

Migrated to packages/lingwen-creator/src/lingwen_creator/volume/plan_share.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_volume_plan_share import encode_share_token, decode_share_token, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.volume.plan_share import *  # noqa: F403
