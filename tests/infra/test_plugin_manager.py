"""Regression test for plugin_manager._discover_internal_providers module path bug.

Phase 126 v16.5 #N.16 Task 2 — closes v15.7.1 carryover for plugin_manager.

Before fix: PluginManager.load_plugins() at lines 58 + 81 attempted to import
from 'infra.ai_service.X' (a non-existent module). Result: 3 warnings logged per
LLMService.get() call, _plugins dict empty.

After fix: load_plugins() correctly discovers providers via canonical
'lingwen_llm.providers.X' module path, populating _plugins with all 3 providers
(minimax, anthropic, openai).
"""
import pytest
from lingwen_llm.providers.plugin_manager import PluginManager


@pytest.fixture
def fresh_plugin_manager():
    """Create a fresh PluginManager instance for each test."""
    return PluginManager()


def test_load_plugins_populates_all_three_providers(fresh_plugin_manager):
    """load_plugins() should discover all 3 internal providers via canonical path.

    Asserts the fix for the v15.7.1 carryover bug at plugin_manager.py:58,81.
    """
    pm = fresh_plugin_manager
    pm.load_plugins()

    discovered = set(pm._plugins.keys())
    assert "minimax" in discovered, (
        f"minimax provider missing; discovered: {sorted(discovered)}"
    )
    assert "anthropic" in discovered, (
        f"anthropic provider missing; discovered: {sorted(discovered)}"
    )
    assert "openai" in discovered, (
        f"openai provider missing; discovered: {sorted(discovered)}"
    )


def test_load_plugins_logs_no_broken_import_warnings(fresh_plugin_manager, caplog):
    """load_plugins() should not emit warnings about failed module imports.

    Pre-fix, 3 warnings were logged (one per provider, all attempting the broken
    'infra.ai_service.X' path). After fix, no such warnings should appear.
    """
    import logging

    pm = fresh_plugin_manager
    with caplog.at_level(logging.WARNING):
        pm.load_plugins()

    # Filter for the specific broken-import warnings the bug would emit
    broken_import_warnings = [
        record for record in caplog.records
        if "Failed to load" in record.getMessage()
    ]
    assert broken_import_warnings == [], (
        f"Expected no broken-import warnings, got: "
        f"{[r.getMessage() for r in broken_import_warnings]}"
    )


def test_get_provider_class_returns_class_after_load(fresh_plugin_manager):
    """After load_plugins, get_provider_class() should return the actual provider class."""
    pm = fresh_plugin_manager
    pm.load_plugins()

    for name in ("minimax", "anthropic", "openai"):
        cls = pm.get_provider_class(name)
        assert cls is not None, f"get_provider_class({name!r}) returned None"
        assert callable(cls), f"get_provider_class({name!r}) returned non-callable: {cls!r}"
