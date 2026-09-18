"""Phase 100: Pipeline resolve_model + threading + settings loader tests.

Validates the 3-tier resolution order (explicit > project > provider default),
metadata.model records resolved value, and _load_illustration_settings helper
extracts default_models from yaml.
"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_resolve_model_explicit_wins():
    """Explicit model takes precedence over project + provider default."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("m1", "m2", "m3"), default="m1")
    result = resolve_model(
        provider="openai",
        explicit="m3",
        project_settings={"default_models": {"openai": "m2"}},
        adapter=adapter,
    )
    assert result == "m3"


def test_resolve_model_project_default_when_no_explicit():
    """No explicit → project default wins over provider default."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("m1", "m2"), default="m1")
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings={"default_models": {"openai": "m2"}},
        adapter=adapter,
    )
    assert result == "m2"


def test_resolve_model_provider_default_when_no_project():
    """No explicit + no project → provider default wins."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("m1", "m2"), default="m1")
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings=None,
        adapter=adapter,
    )
    assert result == "m1"


def test_resolve_model_explicit_invalid_raises_unknown():
    """Explicit model not in adapter.models → UnknownModelError."""
    from lingwen_illustrations.exceptions import UnknownModelError
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("m1", "m2"), default="m1")
    with pytest.raises(UnknownModelError):
        resolve_model(
            provider="openai",
            explicit="m99-bogus",
            project_settings=None,
            adapter=adapter,
        )


def test_resolve_model_project_default_stale_falls_back(caplog):
    """Project default not in adapter.models → log warning + use provider default."""
    import logging

    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("m1", "m2"), default="m1")
    with caplog.at_level(logging.WARNING):
        result = resolve_model(
            provider="openai",
            explicit=None,
            project_settings={"default_models": {"openai": "m99-stale"}},
            adapter=adapter,
        )
    assert result == "m1"
    assert any("m99-stale" in r.message for r in caplog.records)


def test_load_illustration_settings_reads_default_models(tmp_path: Path):
    """Helper reads default_models dict from illustration_settings.yaml."""
    from lingwen_illustrations.pipeline import _load_illustration_settings

    settings_dir = tmp_path / ".lingwen"
    settings_dir.mkdir()
    settings_file = settings_dir / "illustration_settings.yaml"
    settings_file.write_text(
        "default_provider: openai\n"
        "default_models:\n"
        "  openai: gpt-image-1\n"
        "  minimax: minimax-multimodal\n"
        "auto_generate: false\n",
        encoding="utf-8",
    )
    result = _load_illustration_settings(tmp_path)
    assert result.get("default_models") == {
        "openai": "gpt-image-1",
        "minimax": "minimax-multimodal",
    }


def test_load_illustration_settings_missing_file_returns_empty_dict(tmp_path: Path):
    """No settings file → empty dict (not error)."""
    from lingwen_illustrations.pipeline import _load_illustration_settings

    result = _load_illustration_settings(tmp_path)
    assert result == {}


def _fake_adapter(models, default):
    """Build a minimal ProviderAdapter-like object for resolve_model tests."""

    class _Adapter:
        pass

    a = _Adapter()
    a.models = tuple(models)
    a.default_model = default
    return a
