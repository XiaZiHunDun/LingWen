"""ProviderAdapter registry tests (Phase 97)."""
from __future__ import annotations

import pytest


def test_get_provider_returns_adapter_with_4_fields():
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("minimax")
    assert hasattr(adapter, "name")
    assert hasattr(adapter, "generate")
    assert hasattr(adapter, "generate_with_reference")
    assert hasattr(adapter, "supports_i2i")
    assert adapter.name == "minimax"
    assert adapter.supports_i2i is True


def test_get_provider_adapter_for_openai():
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("openai")
    assert adapter.name == "openai"
    assert adapter.supports_i2i is False


def test_get_provider_adapter_for_stability():
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("stability")
    assert adapter.name == "stability"
    assert adapter.supports_i2i is True


def test_get_provider_dynamic_lookup_monkeypatch_compat(monkeypatch):
    """Phase 96 tests monkeypatch providers.X.generate — adapter must reflect patched function."""
    from lingwen_illustrations import providers

    async def patched_generate(*, prompt, api_key, api_host, timeout=60.0):
        return b"patched-bytes"

    monkeypatch.setattr(providers.minimax, "generate", patched_generate)
    adapter = providers.get_provider("minimax")
    assert adapter.generate is patched_generate


def test_get_provider_unknown_raises():
    from lingwen_illustrations.providers import UnknownProviderError, get_provider

    with pytest.raises(UnknownProviderError):
        get_provider("unknown-provider")


def test_provider_adapter_all_3_have_callable_methods():
    """Each adapter's generate and generate_with_reference must be callable."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    for name in KNOWN_PROVIDERS:
        adapter = get_provider(name)
        assert callable(adapter.generate), f"{name}.generate not callable"
        assert callable(adapter.generate_with_reference), f"{name}.generate_with_reference not callable"