"""Phase 100: ProviderAdapter dataclass extension tests.

Validates the new `models` + `default_model` fields are populated by
get_provider() for all 3 known providers.
"""
from __future__ import annotations

import pytest


def test_adapter_has_models_and_default_model_fields():
    """ProviderAdapter must expose `models` tuple + `default_model` string."""
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider("minimax")
    assert hasattr(adapter, "models")
    assert hasattr(adapter, "default_model")
    assert isinstance(adapter.models, tuple)
    assert isinstance(adapter.default_model, str)
    assert len(adapter.models) > 0
    assert adapter.default_model in adapter.models


@pytest.mark.parametrize("name,expected_count,expected_default", [
    ("minimax", 2, "minimax-multimodal"),
    ("openai", 4, "dall-e-3"),
    ("stability", 5, "sd3-medium"),
])
def test_get_provider_returns_correct_catalog(name, expected_count, expected_default):
    """Each known provider has the documented catalog (full spec section 3)."""
    from lingwen_illustrations.providers import get_provider

    adapter = get_provider(name)
    assert len(adapter.models) == expected_count
    assert adapter.default_model == expected_default
    assert expected_default in adapter.models


def test_get_provider_unknown_still_raises_unknown_provider_error():
    """Backwards compat: unknown provider still raises UnknownProviderError."""
    from lingwen_illustrations.providers import UnknownProviderError, get_provider

    with pytest.raises(UnknownProviderError):
        get_provider("nonexistent")


def test_get_provider_dynamic_lookup_monkeypatch_compat_catalog(monkeypatch):
    """Phase 100: monkeypatching KNOWN_MODELS + DEFAULT_MODEL must be reflected in adapter.

    Extends the Phase 97 pattern (test_get_provider_dynamic_lookup_monkeypatch_compat
    in test_providers_registry_adapter.py) to the NEW catalog fields. Same dynamic
    importlib.import_module lookup — reads module attrs at adapter creation time.
    Defensive guard against future refactors that break catalog monkeypatch compat.
    """
    from lingwen_illustrations import providers
    from lingwen_illustrations.providers import get_provider

    monkeypatch.setattr(
        "lingwen_illustrations.providers.minimax.KNOWN_MODELS",
        ("x-test", "y-test"),
    )
    monkeypatch.setattr(
        "lingwen_illustrations.providers.minimax.DEFAULT_MODEL",
        "y-test",
    )

    adapter = get_provider("minimax")
    assert adapter.models == ("x-test", "y-test")
    assert adapter.default_model == "y-test"
