"""Phase 126 v16.2.4: tests for content/ subdomain (8 modules + __init__ star-imports)."""
from __future__ import annotations


def test_content_package_imports() -> None:
    """lingwen_creator.content package is importable."""
    import lingwen_creator.content
    assert lingwen_creator.content.__name__ == "lingwen_creator.content"


def test_content_star_imports_all_8_submodules() -> None:
    """content/__init__.py star-imports re-export from 8 submodules."""
    from lingwen_creator.content import (
        CreatorSettings,  # via mode.py shim → shared.mode
        creator_overview,
        creator_preferences_payload,
        enrich_batch_history_job,
        list_creator_models_payload,
        resolve_creator_ui_profile,
        run_creator_agent_plan,
        run_creator_logic_check,
    )
    assert callable(run_creator_agent_plan)
    assert callable(enrich_batch_history_job)
    assert callable(creator_overview)
    assert callable(run_creator_logic_check)
    assert callable(list_creator_models_payload)
    assert callable(creator_preferences_payload)
    assert callable(resolve_creator_ui_profile)


def test_content_mode_shim_re_exports_shared() -> None:
    """content/mode.py is a shim → lingwen_creator.shared.mode."""
    from lingwen_creator.content.mode import CreatorSettings as ContentCreatorSettings
    from lingwen_creator.shared.mode import CreatorSettings as SharedCreatorSettings
    assert ContentCreatorSettings is SharedCreatorSettings


def test_content_dashboard_chapter_preview_exists() -> None:
    """content.dashboard exports creator_chapter_preview."""
    from lingwen_creator.content.dashboard import (
        creator_chapter_preview,
        save_creator_chapter_body,
        save_creator_chapter_outline,
    )
    assert callable(creator_chapter_preview)
    assert callable(save_creator_chapter_outline)
    assert callable(save_creator_chapter_body)


def test_content_preferences_uses_shared_mode() -> None:
    """content.preferences imports from lingwen_creator.shared.mode (intra-package)."""
    from lingwen_creator.content.preferences import creator_preferences_payload
    assert callable(creator_preferences_payload)


def test_legacy_shims_deleted_mode() -> None:
    """v16.2.7 T4.9: infra.creator_mode shim deleted, must raise ModuleNotFoundError."""
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_mode import CreatorSettings  # noqa: F401


def test_legacy_shims_deleted_content() -> None:
    """v16.2.7 T4.10+T4.11+T4.12: 7 content shims deleted, must raise ModuleNotFoundError.

    T4.10: creator_models/preferences/logic_check/dashboard.
    T4.11: creator_agent/batch_history.
    T4.12: creator_ui_profile.
    """
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_models import list_creator_models_payload  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_preferences import creator_preferences_payload  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_logic_check import run_creator_logic_check  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_dashboard import creator_overview  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_agent import run_creator_agent_plan  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_batch_history import enrich_batch_history_job  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_ui_profile import resolve_creator_ui_profile  # noqa: F401


def test_legacy_shim_deleted_revision() -> None:
    """v16.2.7 T4.12: infra.creator_revision shim deleted (2 production routes patched)."""
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_revision import CreatorDocConflictError  # noqa: F401
