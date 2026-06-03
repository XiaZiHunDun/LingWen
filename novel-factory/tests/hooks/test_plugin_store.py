#!/usr/bin/env python3
"""
Plugin Store Tests
"""
import pytest

from infra.hooks.plugin_store import PluginMetadata, PluginStore


@pytest.fixture
def store():
    """Create empty plugin store"""
    return PluginStore()


@pytest.fixture
def sample_plugin():
    """Create sample plugin"""
    return PluginMetadata(
        id="test_plugin_1",
        name="Test Plugin",
        version="1.0.0",
        description="A plugin for testing",
        author="Test Author",
        hooks=["test_hook"],
        actions=["test_action"]
    )


@pytest.fixture
def populated_store():
    """Create pre-populated plugin store"""
    store = PluginStore()
    plugins = [
        PluginMetadata(
            id="quality_checker",
            name="Quality Checker",
            version="1.0.0",
            description="Checks chapter quality",
            author="Author A",
            hooks=["chapter_review"],
            actions=["run_checker"]
        ),
        PluginMetadata(
            id="style_formatter",
            name="Style Formatter",
            version="1.0.0",
            description="Formats text style",
            author="Author B",
            hooks=["chapter_review"],
            actions=["format_text"]
        ),
        PluginMetadata(
            id="notifier",
            name="Notifier",
            version="1.0.0",
            description="Sends notifications",
            author="Author C",
            hooks=["notify_hook"],
            actions=["notify"]
        ),
        PluginMetadata(
            id="archive_tool",
            name="Archive Tool",
            version="1.0.0",
            description="Archives completed chapters",
            author="Author D",
            hooks=["archive_hook"],
            actions=["archive"],
            enabled=False
        ),
    ]
    for plugin in plugins:
        store.register_plugin(plugin)
    return store


class TestPluginRegistration:
    """Test plugin registration"""

    def test_plugin_registration(self, store, sample_plugin):
        """Test registering a plugin"""
        result = store.register_plugin(sample_plugin)
        assert result is True
        assert store.get_plugin("test_plugin_1") == sample_plugin

    def test_plugin_duplicate_id(self, store, sample_plugin):
        """Test duplicate ID returns False"""
        store.register_plugin(sample_plugin)
        duplicate = PluginMetadata(
            id="test_plugin_1",
            name="Another Plugin",
            version="1.0.0",
            description="Duplicate ID",
            author="Another Author",
            hooks=["another_hook"],
            actions=[]
        )
        result = store.register_plugin(duplicate)
        assert result is False
        assert store.get_plugin("test_plugin_1") == sample_plugin

    def test_unregister_plugin(self, store, sample_plugin):
        """Test unregistering a plugin"""
        store.register_plugin(sample_plugin)
        result = store.unregister_plugin("test_plugin_1")
        assert result is True
        assert store.get_plugin("test_plugin_1") is None

    def test_unregister_nonexistent(self, store):
        """Test unregister nonexistent returns False"""
        result = store.unregister_plugin("nonexistent")
        assert result is False


class TestListPlugins:
    """Test listing plugins"""

    def test_list_plugins(self, populated_store):
        """Test listing all enabled plugins"""
        plugins = populated_store.list_plugins()
        assert len(plugins) == 3  # archive_tool is disabled

    def test_list_empty_store(self, store):
        """Test list from empty store"""
        plugins = store.list_plugins()
        assert len(plugins) == 0

    def test_list_excludes_disabled_by_default(self, populated_store):
        """Test disabled plugins excluded by default"""
        plugins = populated_store.list_plugins()
        assert all(p.enabled for p in plugins)

    def test_list_includes_disabled(self, populated_store):
        """Test disabled plugins included when requested"""
        plugins = populated_store.list_plugins(include_disabled=True)
        assert len(plugins) == 4


class TestEnableDisable:
    """Test enabling/disabling plugins"""

    def test_enable_disable_plugin(self, store, sample_plugin):
        """Test enable/disable toggles correctly"""
        store.register_plugin(sample_plugin)
        assert sample_plugin.enabled is True

        result = store.disable_plugin("test_plugin_1")
        assert result is True
        assert sample_plugin.enabled is False

        result = store.enable_plugin("test_plugin_1")
        assert result is True
        assert sample_plugin.enabled is True

    def test_enable_nonexistent(self, store):
        """Test enable nonexistent returns False"""
        result = store.enable_plugin("nonexistent")
        assert result is False

    def test_disable_nonexistent(self, store):
        """Test disable nonexistent returns False"""
        result = store.disable_plugin("nonexistent")
        assert result is False


class TestSearchPlugins:
    """Test searching plugins"""

    def test_search_by_name(self, populated_store):
        """Test search finds plugin by name"""
        results = populated_store.search_plugins("Quality")
        assert len(results) == 1
        assert results[0].name == "Quality Checker"

    def test_search_by_description(self, populated_store):
        """Test search finds plugin by description"""
        results = populated_store.search_plugins("notification")
        assert len(results) == 1
        assert results[0].name == "Notifier"

    def test_search_case_insensitive(self, populated_store):
        """Test search is case-insensitive"""
        results = populated_store.search_plugins("QUALITY")
        assert len(results) == 1
        assert results[0].name == "Quality Checker"

    def test_search_no_match(self, populated_store):
        """Test search with no match returns empty"""
        results = populated_store.search_plugins("xyz123")
        assert len(results) == 0

    def test_search_empty_query(self, populated_store):
        """Test empty query returns all plugins (including disabled)"""
        results = populated_store.search_plugins("")
        assert len(results) == 4


class TestGetPluginsByHook:
    """Test getting plugins by hook name"""

    def test_get_plugins_by_hook(self, populated_store):
        """Test get plugins filtered by hook name"""
        results = populated_store.get_plugins_by_hook("chapter_review")
        assert len(results) == 2
        names = [p.name for p in results]
        assert "Quality Checker" in names
        assert "Style Formatter" in names

    def test_get_plugins_no_match(self, populated_store):
        """Test get plugins for nonexistent hook"""
        results = populated_store.get_plugins_by_hook("nonexistent_hook")
        assert len(results) == 0


class TestPluginCount:
    """Test plugin count"""

    def test_plugin_count(self, populated_store):
        """Test count returns correct stats"""
        stats = populated_store.get_plugin_count()
        assert stats["total"] == 4
        assert stats["enabled"] == 3
        assert stats["disabled"] == 1

    def test_plugin_count_empty_store(self, store):
        """Test empty store count is all zeros"""
        stats = store.get_plugin_count()
        assert stats["total"] == 0
        assert stats["enabled"] == 0
        assert stats["disabled"] == 0

    def test_plugin_count_after_disable(self, populated_store):
        """Test count updates after disable"""
        populated_store.disable_plugin("quality_checker")
        stats = populated_store.get_plugin_count()
        assert stats["total"] == 4
        assert stats["enabled"] == 2
        assert stats["disabled"] == 2


if __name__ == "__main__":
    import unittest
    unittest.main()
