"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.shared.mode.

Creator mode utilities (CreatorSettings + CREATION_MODE_* + settings_from_project_config)
live in lingwen_creator.shared.mode because they are cross-subdomain utilities
used by:
  - shared.check.format_check_mode_banner
  - content.preferences (resolve_creator_settings for save)
  - onboarding.onboarding (wizard validation)
  - infra.project_config / project_init (YAML resolution)

This content/mode.py shim maintains backwards compat for spec §2.1
(content/mode.py canonical path) + any code using:
    from lingwen_creator.content.mode import CreatorSettings, ...

Will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.mode import *  # noqa: F401,F403
