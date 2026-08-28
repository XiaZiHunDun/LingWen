"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.shared.mode.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/mode.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_mode import CreatorSettings, settings_from_project_config, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.mode import *  # noqa: F401,F403
