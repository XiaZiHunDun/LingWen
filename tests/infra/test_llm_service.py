"""Tests for infra.llm_service.LLMService provider initialization.

Phase 123 regression: ensure _init_providers uses the decorator-driven
_PROVIDER_REGISTRY (via list_registered_providers) instead of the broken
PluginManager.get_priority() path that tries to import
'infra.ai_service.<name>' modules which don't exist.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def minimax_api_key(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-dummy")


def test_llm_service_loads_minimax_with_env_key(minimax_api_key):
    """LLMService.get() must succeed when MINIMAX_API_KEY is set.

    Pre-fix, this raises RuntimeError because PluginManager._discover_internal_providers
    tries to import 'infra.ai_service.<name>' modules that don't exist, leaving the
    plugin manager's priority list empty.
    """
    from infra.llm_service import LLMService

    service = LLMService.get()
    assert service._providers, "no providers loaded"
    provider_names = [name for name, _ in service._providers]
    assert "minimax" in provider_names


def test_llm_service_uses_decorator_registry_not_broken_plugin_manager(minimax_api_key):
    """Ensure _init_providers consults _PROVIDER_REGISTRY (decorator-populated).

    If it consulted the broken plugin_manager, this would fail because no providers
    are registered there (the discovery is broken).
    """
    from lingwen_llm.providers import list_registered_providers

    from infra.llm_service import LLMService

    registered = list_registered_providers()
    assert "minimax" in registered, "minimax must be registered via @register_provider"

    service = LLMService.get()
    loaded_names = [name for name, _ in service._providers]
    # Only providers that are both registered AND have a key should be loaded
    assert all(name in registered for name in loaded_names)


def test_llm_service_resets_singleton_between_tests(monkeypatch):
    """LLMService.get() uses a singleton; reset between tests to avoid cross-test pollution."""
    from infra.llm_service import LLMService

    monkeypatch.setattr(LLMService, "_instance", None)
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    service = LLMService.get()
    assert service._providers

    # Reset for next test
    monkeypatch.setattr(LLMService, "_instance", None)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="无可用的LLM Provider"):
        LLMService.get()
