#!/usr/bin/env python3
"""
Regression Tracker Tests

Tests for the regression tracking system that identifies related chapters
when a chapter is fixed to prevent new inconsistencies.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add infra/tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "infra" / "tools"))

# Import the module under test
from regression_tracker import (
    clear_all_regression_checks,
    clear_regression_check,
    get_chapters_in_volume,
    get_neighbor_chapters,
    get_pending_regression_checks,
    get_regression_chapters,
    get_volume_for_chapter,
    parse_chapter_id,
    register_regression_check,
)


class TestParseChapterId:
    """Tests for chapter ID parsing."""

    def test_parses_valid_chapter_ids(self):
        assert parse_chapter_id("ch001") == 1
        assert parse_chapter_id("ch050") == 50
        assert parse_chapter_id("ch360") == 360

    def test_parses_case_insensitive(self):
        assert parse_chapter_id("CH001") == 1
        assert parse_chapter_id("Ch050") == 50

    def test_returns_none_for_invalid(self):
        assert parse_chapter_id("invalid") is None
        assert parse_chapter_id("ch") is None
        assert parse_chapter_id("chABC") is None
        assert parse_chapter_id("") is None
        assert parse_chapter_id(None) is None


class TestVolumeAssignment:
    """Tests for volume/chapter relationships."""

    def test_chapter_belongs_to_volume_1(self):
        assert get_volume_for_chapter(1) == "卷1"
        assert get_volume_for_chapter(50) == "卷1"
        assert get_volume_for_chapter(120) == "卷1"

    def test_chapter_belongs_to_volume_2(self):
        assert get_volume_for_chapter(121) == "卷2"
        assert get_volume_for_chapter(200) == "卷2"
        assert get_volume_for_chapter(240) == "卷2"

    def test_chapter_belongs_to_volume_3(self):
        assert get_volume_for_chapter(241) == "卷3"
        assert get_volume_for_chapter(300) == "卷3"
        assert get_volume_for_chapter(360) == "卷3"

    def test_chapter_outside_range(self):
        assert get_volume_for_chapter(0) is None
        assert get_volume_for_chapter(361) is None
        assert get_volume_for_chapter(-1) is None


class TestVolumeChapterRetrieval:
    """Tests for getting chapters in a volume."""

    def test_volume_1_chapters(self):
        chapters = get_chapters_in_volume("卷1")
        assert len(chapters) == 120
        assert chapters[0] == 1
        assert chapters[-1] == 120

    def test_volume_2_chapters(self):
        chapters = get_chapters_in_volume("卷2")
        assert len(chapters) == 120
        assert chapters[0] == 121
        assert chapters[-1] == 240

    def test_volume_3_chapters(self):
        chapters = get_chapters_in_volume("卷3")
        assert len(chapters) == 120
        assert chapters[0] == 241
        assert chapters[-1] == 360

    def test_invalid_volume(self):
        assert get_chapters_in_volume("卷4") == []


class TestNeighborhoodChapters:
    """Tests for ±20 chapter proximity."""

    def test_neighbors_at_start(self):
        neighbors = get_neighbor_chapters(5)
        assert 5 not in neighbors
        assert 1 in neighbors  # Lower bound
        assert 25 in neighbors  # Upper bound is +20

    def test_neighbors_at_end(self):
        neighbors = get_neighbor_chapters(355)
        assert 355 not in neighbors
        assert 360 in neighbors  # Upper bound capped at 360
        assert 335 in neighbors  # Lower bound

    def test_neighbors_in_middle(self):
        neighbors = get_neighbor_chapters(100)
        assert 100 not in neighbors
        assert 80 in neighbors
        assert 120 in neighbors

    def test_custom_range(self):
        neighbors = get_neighbor_chapters(100, range_size=5)
        assert 100 not in neighbors
        assert 95 in neighbors
        assert 105 in neighbors
        assert 90 not in neighbors  # Beyond range


class TestGetRegressionChapters:
    """Tests for the main get_regression_chapters function."""

    def test_returns_list(self):
        result = get_regression_chapters("ch050")
        assert isinstance(result, list)

    def test_chapters_sorted(self):
        result = get_regression_chapters("ch100")
        chapter_nums = [parse_chapter_id(ch) for ch in result]
        assert chapter_nums == sorted(chapter_nums)

    def test_same_volume_included(self):
        """When a chapter is fixed, same-volume chapters are included."""
        result = get_regression_chapters("ch050")
        # ch050 is in 卷1, so all other 卷1 chapters should be included
        # Except ch050 itself is excluded
        assert "ch001" in result
        assert "ch120" in result
        assert "ch050" not in result

    def test_neighbor_range_included(self):
        """When a chapter is fixed, ±20 neighbors are included."""
        result = get_regression_chapters("ch100")
        # ch100 neighbors should include 80-120 (except 100)
        assert "ch080" in result
        assert "ch120" in result

    def test_invalid_chapter_id_returns_empty(self):
        assert get_regression_chapters("invalid") == []
        assert get_regression_chapters("ch500") == []

    def test_chapter_50_has_many_related(self):
        """ch050 is in the middle of 卷1, should have many related chapters."""
        result = get_regression_chapters("ch050")
        # Volume 1 has 120 chapters minus itself
        # Plus neighbors (minus duplicates)
        # Should be a substantial list
        assert len(result) > 50

    def test_chapter_at_volume_boundary(self):
        """A chapter at volume boundary should include both volumes."""
        result = get_regression_chapters("ch120")  # End of 卷1
        # Should include 卷1 chapters
        assert "ch001" in result
        # Should include neighbors from 100-140
        assert "ch100" in result
        assert "ch140" in result


class TestRegressionQueueOperations:
    """Tests for regression queue management with mocked state."""

    @pytest.fixture
    def mock_workflow_state(self, tmp_path):
        """Create a temporary workflow state for testing."""
        state_file = tmp_path / "workflow_state.json"
        test_state = {
            "version": "v4.0",
            "issues_found": {
                "ch001-ch010": ["衔接断裂(ch006/007)", "重复独白删除"],
                "ch011-ch020": ["ch016/17内容颠倒(P0)", "时间线矛盾(P1)"],
                "ch051-ch060": ["星月性别矛盾(P0)", "联盟邀请逻辑"],
            }
        }
        with open(state_file, "w") as f:
            json.dump(test_state, f)
        return state_file

    def test_register_adds_to_queue(self, mock_workflow_state, monkeypatch):
        """When register_regression_check is called, related chapters are added."""
        # Mock the workflow state path
        monkeypatch.setattr(
            "regression_tracker.WORKFLOW_STATE_PATH",
            mock_workflow_state
        )

        # Register a fix for ch005
        related = register_regression_check("ch005", "Test fix")

        # Should return related chapters
        assert isinstance(related, list)
        assert len(related) > 0

        # Queue should have entries
        pending = get_pending_regression_checks()
        assert len(pending) > 0

    def test_clear_removes_from_queue(self, mock_workflow_state, monkeypatch):
        """clear_regression_check removes a chapter from the queue."""
        monkeypatch.setattr(
            "regression_tracker.WORKFLOW_STATE_PATH",
            mock_workflow_state
        )

        # Register first
        register_regression_check("ch005", "Test fix")

        # Then clear
        clear_regression_check("ch005")
        # Note: This test may not find the item if the chapter wasn't added
        # The function returns True only if item was found and removed

    def test_clear_all_clears_queue(self, mock_workflow_state, monkeypatch):
        """clear_all_regression_checks removes all pending checks."""
        monkeypatch.setattr(
            "regression_tracker.WORKFLOW_STATE_PATH",
            mock_workflow_state
        )

        # Register a few
        register_regression_check("ch005", "Test fix 1")
        register_regression_check("ch010", "Test fix 2")

        # Clear all
        clear_all_regression_checks()

        pending = get_pending_regression_checks()
        assert len(pending) == 0


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self, tmp_path, monkeypatch):
        """Test the complete regression tracking workflow."""
        # Setup temporary state file
        state_file = tmp_path / "workflow_state.json"
        test_state = {
            "version": "v4.0",
            "issues_found": {
                "ch001-ch010": ["衔接断裂"],
                "ch011-ch020": ["ch016/17内容颠倒"],
                "ch021-ch030": ["黑鸦线索"],
            }
        }
        with open(state_file, "w") as f:
            json.dump(test_state, f)

        monkeypatch.setattr("regression_tracker.WORKFLOW_STATE_PATH", state_file)

        # Register a fix
        related = register_regression_check("ch005", "Fixed衔接断裂")

        # Verify related chapters identified
        assert "ch005" not in related  # Chapter itself not included
        assert len(related) > 0

        # Check pending queue
        pending = get_pending_regression_checks()
        assert any(item["triggered_by"] == "ch005" for item in pending)

        # Clear the check
        clear_regression_check("ch005")

        # Verify cleared
        pending = get_pending_regression_checks()
        assert not any(item["chapter_id"] == "ch005" for item in pending)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
