"""Tests for HookTracker."""

from unittest.mock import MagicMock

import pytest

from infra.reading_power.hook_tracker import HookTracker


def test_track_and_get_hooks() -> None:
    """Test tracking hooks and retrieving them."""
    mock_db = MagicMock()
    mock_db.get_hooks.return_value = [
        {"hook_type": "危机钩", "strength": 0.8, "position": "结尾"}
    ]

    tracker = HookTracker(mock_db)

    hooks = [
        {"type": "危机钩", "strength": 0.8, "position": "结尾", "content": "危险..."}
    ]
    tracker.track(1, hooks)

    mock_db.save_hook.assert_called_once()
    result = tracker.get_hooks(1)
    assert len(result) == 1


def test_get_hook_summary() -> None:
    """Test getting hook summary."""
    mock_db = MagicMock()
    mock_db.get_hooks.return_value = [
        {"hook_type": "危机钩", "strength": 0.8},
        {"hook_type": "悬念钩", "strength": 0.6},
    ]

    tracker = HookTracker(mock_db)
    summary = tracker.get_hook_summary(1)

    assert summary["count"] == 2
    assert summary["avg_strength"] == 0.7


def test_get_hook_summary_empty() -> None:
    """Test getting hook summary for chapter with no hooks."""
    mock_db = MagicMock()
    mock_db.get_hooks.return_value = []

    tracker = HookTracker(mock_db)
    summary = tracker.get_hook_summary(1)

    assert summary["count"] == 0
    assert summary["avg_strength"] == 0.0
    assert summary["types"] == []


def test_track_multiple_hooks() -> None:
    """Test tracking multiple hooks in one call."""
    mock_db = MagicMock()
    mock_db.get_hooks.return_value = []

    tracker = HookTracker(mock_db)

    hooks = [
        {"type": "危机钩", "strength": 0.8, "position": "结尾", "content": "危险..."},
        {"type": "悬念钩", "strength": 0.6, "position": "中段", "content": "谜团..."},
        {"type": "情感钩", "strength": 0.7, "position": "开头", "content": "温情..."},
    ]
    tracker.track(1, hooks)

    assert mock_db.save_hook.call_count == 3


def test_get_all_hooks_by_type() -> None:
    """Test getting all hooks of a specific type."""
    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_db._get_connection.return_value = mock_conn
    mock_conn.execute.return_value.fetchall.return_value = [
        {"hook_type": "危机钩", "strength": 0.8, "chapter": "1"},
        {"hook_type": "危机钩", "strength": 0.9, "chapter": "5"},
    ]
    mock_conn.close = MagicMock()

    tracker = HookTracker(mock_db)
    result = tracker.get_all_hooks_by_type("危机钩",1, 10)

    assert len(result) == 2
    mock_conn.execute.assert_called_once()
