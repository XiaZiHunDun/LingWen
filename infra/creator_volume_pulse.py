"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.volume.pulse.

Migrated to packages/lingwen-creator/src/lingwen_creator/volume/pulse.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_volume_pulse import build_volume_pulse, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.volume.pulse import *  # noqa: F403
