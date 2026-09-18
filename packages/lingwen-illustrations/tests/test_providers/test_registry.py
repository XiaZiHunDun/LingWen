"""Test provider registry (Phase 96 + Phase 97 adapter).

Phase 97: get_provider returns a ProviderAdapter dataclass (4 fields).
Phase 96 legacy tests updated to assert against `adapter.generate`
instead of the bare function return.
"""
from __future__ import annotations

import inspect

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
        adapter = get_provider(name)
        assert callable(adapter.generate)
        assert callable(adapter.generate_with_reference)
        assert inspect.iscoroutinefunction(adapter.generate)
        assert inspect.iscoroutinefunction(adapter.generate_with_reference)


def test_get_provider_minimax_returns_minimax_generate():
    from lingwen_illustrations.providers import minimax
    adapter = get_provider("minimax")
    assert adapter.generate is minimax.generate


def test_get_provider_unknown_raises():
    with pytest.raises(UnknownProviderError) as exc:
        get_provider("anthropic")
    assert "anthropic" in str(exc.value)
    assert "expected one of" in str(exc.value)
