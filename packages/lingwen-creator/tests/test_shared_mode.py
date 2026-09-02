"""Phase 126 v16.2.4 T1: tests for shared/mode.py migrated utilities."""

from __future__ import annotations

from lingwen_creator.shared.mode import (
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


def test_creation_mode_constants() -> None:
    """CREATION_MODE_* constants frozen + non-empty."""
    assert CREATION_MODE_COMPANION == "companion"
    assert CREATION_MODE_ADVANCE == "advance"
    assert CREATION_MODE_STUDIO == "studio"
    assert CREATION_MODES == frozenset({"companion", "advance", "studio"})


def test_creator_settings_dataclass_fields() -> None:
    """CreatorSettings has all 8 fields (frozen dataclass)."""
    s = CreatorSettings(
        creation_mode=CREATION_MODE_STUDIO,
        quality_profile=QUALITY_STUDIO_FULL,
        fail_severity="P0",
        run_prose_calibration=True,
        run_llm_judge=True,
        run_golden_set=True,
        notify_per_chapter=True,
        advance_volume_summary=False,
    )
    assert s.creation_mode == CREATION_MODE_STUDIO
    assert s.run_llm_judge is True


def test_normalize_creation_mode_validation() -> None:
    """normalize_creation_mode rejects invalid mode."""
    import pytest

    with pytest.raises(ValueError):
        normalize_creation_mode("invalid_mode")


def test_settings_from_project_config_accepts_any() -> None:
    """settings_from_project_config accepts duck-typed ProjectConfig (Any)."""

    class FakeConfig:
        creation_mode = CREATION_MODE_ADVANCE
        quality_profile = None

    settings = settings_from_project_config(FakeConfig())
    assert settings.creation_mode == CREATION_MODE_ADVANCE
    assert settings.advance_volume_summary is True


def test_legacy_shim_deleted() -> None:
    """v16.2.7 T4.9: infra.creator_mode shim deleted, must raise ModuleNotFoundError."""
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_mode import CreatorSettings  # noqa: F401
