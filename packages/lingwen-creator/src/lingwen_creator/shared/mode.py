"""Phase 126 v16.3 — mode.py moved to lingwen_shared (true leaf).

Per v16.3 layer_dependencies contract (import-linter), infra is the leaf layer
and MUST NOT import from lingwen_creator. mode.py is pure utility (no infra
deps), so it belongs in lingwen_shared — alongside contracts/ports.

This shim preserves back-compat for existing consumers in:
  - shared.check, content.*, onboarding.*
  - lingwen_cli (parsers/init_project + commands/init_project)
New code should import from `lingwen_shared.mode` directly.
"""
from __future__ import annotations

from lingwen_shared.mode import (  # noqa: F401
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    CREATION_MODES,
    QUALITY_CREATOR_RELAXED,
    QUALITY_PROFILES,
    QUALITY_STUDIO_FULL,
    CreatorSettings,
    normalize_creation_mode,
    normalize_quality_profile,
    resolve_creator_settings,
    settings_from_project_config,
)
