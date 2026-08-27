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


def test_settings_package_layout():
    """All 3 modules must be importable via package."""
    from lingwen_creator.settings import docs, history, merge_preferences
    assert docs.__file__.endswith("settings/docs.py")
    assert history.__file__.endswith("settings/history.py")
    assert merge_preferences.__file__.endswith("settings/merge_preferences.py")


def test_settings_intra_package_imports_terminates():
    """Intra-package imports must not introduce circular dependency."""
    # If circular, this would fail or hang at module-load time
    from lingwen_creator.settings.docs import creator_settings_docs_payload
    from lingwen_creator.settings.history import append_settings_snapshot
    from lingwen_creator.settings.merge_preferences import load_merge_preferences
    # All 3 should be callable (import chain terminates via sys.modules)


def test_settings_no_stale_infra_imports():
    """Verify no module-level stale infra paths in settings package.

    Function-body lazy imports for circular-dep avoidance are intentional
    (per plan §12.2) and not flagged by this test.
    """
    import subprocess
    result = subprocess.run(
        ["grep", "-rn", "^from infra.creator_",
         "packages/lingwen-creator/src/lingwen_creator/settings/"],
        capture_output=True, text=True,
    )
    assert result.stdout == "", f"Found stale infra imports:\n{result.stdout}"
