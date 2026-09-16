"""Test provider registry (Phase 96 providers/__init__.py)."""
from __future__ import annotations

import pytest
from lingwen_illustrations.providers import (
    DEFAULT_PROVIDER,
    KNOWN_PROVIDERS,
    UnknownProviderError,
    get_provider,
)


def test_known_providers_tuple_is_canonical():
    assert KNOWN_PROVIDERS == ("minimax", "openai", "stability")


def test_default_provider_is_minimax():
    assert DEFAULT_PROVIDER == "minimax"


def test_get_provider_returns_callable_for_each_known():
    for name in KNOWN_PROVIDERS:
        fn = get_provider(name)
        assert callable(fn)
        import inspect
        assert inspect.iscoroutinefunction(fn)


def test_get_provider_minimax_returns_minimax_generate():
    from lingwen_illustrations.providers import minimax
    fn = get_provider("minimax")
    assert fn is minimax.generate


def test_get_provider_unknown_raises():
    with pytest.raises(UnknownProviderError) as exc:
        get_provider("anthropic")
    assert "anthropic" in str(exc.value)
    assert "expected one of" in str(exc.value)
