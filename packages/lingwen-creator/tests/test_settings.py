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
