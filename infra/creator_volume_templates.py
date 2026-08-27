"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.volume.templates.

Migrated to packages/lingwen-creator/src/lingwen_creator/volume/templates.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_volume_templates import list_volume_templates, save_custom_volume_template, ...

Private names are re-exported explicitly because Python's `from module import *`
skips underscore-prefixed names, but `infra.creator_template_approvals` + tests
import private names like `_load_custom_store` from this shim path.

NOTE: Monkeypatching the shim's private attributes does NOT affect the underlying
implementation (templates.py uses its own namespace). Tests that need to monkeypatch
private helpers must target `lingwen_creator.volume.templates` directly via string path.

Shim will be deleted in v16.2.7 final cleanup.
"""
import lingwen_creator.volume.templates as _impl  # noqa: F401
from lingwen_creator.volume.templates import *  # noqa: F403

# Re-export underscore-prefixed names used by infra.creator_template_approvals + tests
_append_version_changelog = _impl._append_version_changelog
_apply_template_rollback = _impl._apply_template_rollback
_build_builtin_template = _impl._build_builtin_template
_build_visual_diff_lines = _impl._build_visual_diff_lines
_changelog_for_list = _impl._changelog_for_list
_chunk_end = _impl._chunk_end
_custom_templates_path = _impl._custom_templates_path
_enrich_changelog_diff = _impl._enrich_changelog_diff
_EXPORT_SCHEMA_VERSION = _impl._EXPORT_SCHEMA_VERSION
_factory_templates_path = _impl._factory_templates_path
_find_changelog_entry = _impl._find_changelog_entry
_load_custom_store = _impl._load_custom_store
_load_factory_store = _impl._load_factory_store
_normalize_factory_template_id = _impl._normalize_factory_template_id
_normalize_import_entry = _impl._normalize_import_entry
_normalize_template_id = _impl._normalize_template_id
_normalize_version_label = _impl._normalize_version_label
_now_iso = _impl._now_iso
_resolve_factory_template = _impl._resolve_factory_template
_restore_volumes_from_snapshot = _impl._restore_volumes_from_snapshot
_save_custom_store = _impl._save_custom_store
_save_factory_store = _impl._save_factory_store
_scale_volumes = _impl._scale_volumes
_snapshot_volumes = _impl._snapshot_volumes
_template_list_row = _impl._template_list_row
_volumes_repr = _impl._volumes_repr
