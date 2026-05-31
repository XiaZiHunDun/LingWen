"""Tests for CoolPointTracker."""

import pytest
from unittest.mock import MagicMock

from infra.reading_power.coolpoint_tracker import CoolPointTracker


def test_track_and_get_coolpoints() -> None:
    """Test tracking coolpoints and retrieving them."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": "[]"}
    ]

    tracker = CoolPointTracker(mock_db)

    coolpoints = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": [], "content": "打脸..."}
    ]
    tracker.track(1, coolpoints)

    mock_db.save_coolpoint.assert_called_once()
    result = tracker.get_coolpoints(1)
    assert len(result) == 1


def test_get_coolpoint_summary() -> None:
    """Test getting coolpoint summary."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": "[]"},
        {"pattern": "扮猪吃虎", "density": 0.85, "combo_with": "[]"},
    ]

    tracker = CoolPointTracker(mock_db)
    summary = tracker.get_coolpoint_summary(1)

    assert summary["count"] == 2
    assert summary["avg_density"] == 0.875


def test_get_coolpoint_summary_empty() -> None:
    """Test getting coolpoint summary for chapter with no coolpoints."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = []

    tracker = CoolPointTracker(mock_db)
    summary = tracker.get_coolpoint_summary(1)

    assert summary["count"] == 0
    assert summary["avg_density"] == 0.0
    assert summary["patterns"] == []


def test_track_multiple_coolpoints() -> None:
    """Test tracking multiple coolpoints in one call."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = []

    tracker = CoolPointTracker(mock_db)

    coolpoints = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": [], "content": "打脸..."},
        {"pattern": "扮猪吃虎", "density": 0.85, "combo_with": [], "content": "隐藏实力..."},
        {"pattern": "越级反杀", "density": 0.95, "combo_with": [], "content": "绝杀..."},
    ]
    tracker.track(1, coolpoints)

    assert mock_db.save_coolpoint.call_count == 3


def test_get_combo_pairs() -> None:
    """Test getting combo pairs from coolpoints."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": '["越级反杀", "绝地翻盘"]'},
        {"pattern": "扮猪吃虎", "density": 0.85, "combo_with": '["装逼打脸"]'},
    ]

    tracker = CoolPointTracker(mock_db)
    pairs = tracker.get_combo_pairs(1)

    assert len(pairs) == 3
    assert ("装逼打脸", "越级反杀") in pairs
    assert ("装逼打脸", "绝地翻盘") in pairs
    assert ("扮猪吃虎", "装逼打脸") in pairs


def test_combo_with_parsing() -> None:
    """Test that combo_with is properly parsed from JSON."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": '["越级反杀"]'}
    ]

    tracker = CoolPointTracker(mock_db)
    coolpoints = tracker.get_coolpoints(1)

    assert coolpoints[0]["combo_with"] == ["越级反杀"]


def test_combo_with_invalid_json() -> None:
    """Test handling of invalid JSON in combo_with."""
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": "not valid json"}
    ]

    tracker = CoolPointTracker(mock_db)
    coolpoints = tracker.get_coolpoints(1)

    assert coolpoints[0]["combo_with"] == []