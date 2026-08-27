def test_settings_docs_module_exists():
    """settings/docs.py must exist and expose key functions after migration."""
    from lingwen_creator.settings.docs import (
        assert_settings_revisions,
        creator_settings_docs_payload,
        preview_settings_docs_diff,
        preview_settings_merge_strategy,
        preview_settings_three_way,
        resolve_merged_settings,
        save_creator_settings_docs,
        text_diff_summary,
    )
    # If import fails, this test fails (RED)


def test_settings_history_module_exists():
    from lingwen_creator.settings.history import (
        append_settings_snapshot,
        restore_settings_snapshot,
        settings_history_payload,
    )


def test_settings_merge_preferences_module_exists():
    """settings/merge_preferences.py is largest (1355 lines, ~50 functions)."""
    from lingwen_creator.settings.merge_preferences import (
        apply_all_merge_preset_fixes,
        apply_merge_preset_fix,
        apply_toposort_merge_preset_order,
        build_merge_preset_graph,
        delete_factory_merge_preset_package,
        detect_factory_merge_preset_conflicts,
        detect_merge_preset_conflicts,
        export_merge_preferences,
        export_merge_preset_packages,
        get_merge_preset_package,
        import_merge_preferences,
        import_merge_preset_packages,
        list_factory_merge_preset_packages,
        list_merge_preset_changelog,
        list_merge_preset_packages,
        load_global_merge_preferences,
        load_merge_preferences,
        preflight_factory_merge_preset_pull,
        preflight_merge_preset_import,
        preview_merge_preset_changelog_diff,
        preview_merge_preset_import_diff,
        publish_merge_preset_to_factory,
        pull_factory_merge_presets_to_project,
        resolve_factory_merge_preset_conflict,
        save_global_merge_preferences,
        save_merge_preferences,
        save_merge_preset_package,
        suggest_merge_preset_fixes,
        toposort_merge_preset_packages,
    )
