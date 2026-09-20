"""Phase 102: pipeline.resolve_model — is_fallback param + fallback_models priority.

Validates that resolve_model() picks fallback_models[provider] when
is_fallback=True (chain retry path) and falls through to default_models
when fallback_models is absent. Primary path (is_fallback=False) MUST
ignore fallback_models — Phase 100 behavior preserved.
"""
from __future__ import annotations

import pytest


def test_is_fallback_true_prefers_fallback_models():
    """is_fallback=True and fallback_models[provider] → use that model."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("dall-e-3", "gpt-image-1"), default="dall-e-3")
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings={
            "default_models": {"openai": "dall-e-3"},
            "fallback_models": {"openai": "gpt-image-1"},
        },
        adapter=adapter,
        is_fallback=True,
    )
    assert result == "gpt-image-1"


def test_is_fallback_true_falls_through_to_default_models():
    """is_fallback=True but fallback_models[provider] missing → use default_models[provider]."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("dall-e-3",), default="dall-e-3")
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings={"default_models": {"openai": "dall-e-3"}},
        adapter=adapter,
        is_fallback=True,
    )
    assert result == "dall-e-3"


def test_is_fallback_true_falls_through_to_adapter_default():
    """is_fallback=True with no settings → use adapter.default_model."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("dall-e-3",), default="dall-e-3")
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings={},
        adapter=adapter,
        is_fallback=True,
    )
    assert result == "dall-e-3"


def test_is_fallback_false_ignores_fallback_models():
    """Primary path MUST NOT use fallback_models — only default_models."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(
        models=("dall-e-3", "gpt-image-1"), default="dall-e-3"
    )
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings={
            "default_models": {"openai": "dall-e-3"},
            "fallback_models": {"openai": "gpt-image-1"},
        },
        adapter=adapter,
        is_fallback=False,  # primary path
    )
    assert result == "dall-e-3"  # NOT gpt-image-1


def test_is_fallback_default_false_preserves_phase_100_behavior():
    """Omitting is_fallback → defaults to False (Phase 100 behavior unchanged)."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(
        models=("dall-e-3", "gpt-image-1"), default="dall-e-3"
    )
    # No is_fallback kwarg — must default to False.
    result = resolve_model(
        provider="openai",
        explicit=None,
        project_settings={
            "default_models": {"openai": "dall-e-3"},
            "fallback_models": {"openai": "gpt-image-1"},
        },
        adapter=adapter,
    )
    assert result == "dall-e-3"


def test_explicit_still_wins_over_fallback_models():
    """Explicit (API request) model takes precedence over all settings layers."""
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(
        models=("dall-e-3", "gpt-image-1", "custom-model"), default="dall-e-3"
    )
    result = resolve_model(
        provider="openai",
        explicit="custom-model",
        project_settings={
            "default_models": {"openai": "dall-e-3"},
            "fallback_models": {"openai": "gpt-image-1"},
        },
        adapter=adapter,
        is_fallback=True,
    )
    assert result == "custom-model"


def test_explicit_invalid_raises_unknown_model():
    """Explicit model not in adapter.models → UnknownModelError."""
    from lingwen_illustrations.exceptions import UnknownModelError
    from lingwen_illustrations.pipeline import resolve_model

    adapter = _fake_adapter(models=("dall-e-3",), default="dall-e-3")
    with pytest.raises(UnknownModelError):
        resolve_model(
            provider="openai",
            explicit="invalid-model",
            project_settings={},
            adapter=adapter,
        )


def _fake_adapter(models, default):
    """Build a minimal ProviderAdapter-like object for resolve_model tests."""

    class _Adapter:
        pass

    a = _Adapter()
    a.models = tuple(models)
    a.default_model = default
    return a
