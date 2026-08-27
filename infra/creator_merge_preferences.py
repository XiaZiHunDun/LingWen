"""Phase 126 v16.2.2 shim: re-export from lingwen_creator.settings.merge_preferences.

Migrated to packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_merge_preferences import load_merge_preferences, save_merge_preferences, ...

Shim will be deleted in v16.2.7 final cleanup.

Note: settings/merge_preferences.py has ~20 underscore-prefixed helpers (e.g.
_semver_tuple, _conflicts_from_packages, _prefs_*, _preset_*, _factory_*).
Per v16.2.1 §5.1 lesson 3, audit (T7) will add explicit re-exports if any
test imports private symbols.
"""
from lingwen_creator.settings.merge_preferences import *  # noqa: F403
from lingwen_creator.settings.merge_preferences import (  # noqa: F401
    _factory_preset_packages_path,
    _global_prefs_path,
    _normalize_factory_preset_id,
)
