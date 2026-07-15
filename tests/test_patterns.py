"""Tests for PatternRegistry singleton"""
import pytest

from infra.patterns import PatternRegistry


def test_singleton():
    """Test that PatternRegistry returns the same instance"""
    r1 = PatternRegistry.get_instance()
    r2 = PatternRegistry.get_instance()
    assert r1 is r2


def test_get_pattern():
    """Test that dialog pattern is available"""
    registry = PatternRegistry.get_instance()
    assert 'dialog' in registry.list_patterns()


def test_pattern_is_compiled():
    """Test that pattern has match method (is compiled regex)"""
    registry = PatternRegistry.get_instance()
    pattern = registry.get('dialog')
    assert hasattr(pattern, 'match')


def test_list_patterns():
    """Test that list_patterns returns non-empty list"""
    registry = PatternRegistry.get_instance()
    patterns = registry.list_patterns()
    assert len(patterns) > 0


def test_dialog_pattern_matches():
    """Test that dialog pattern actually matches dialogue"""
    registry = PatternRegistry.get_instance()
    pattern = registry.get('dialog')
    assert pattern is not None
    match = pattern.search('他说：「你好」')
    assert match is not None
    assert match.group() == '「你好」'
