"""Tests for AntiPatternAggregator."""

import pytest

from infra.story_contracts.anti_patterns import (
    AntiPattern,
    AntiPatternAggregator,
)


class TestAntiPatternAggregator:
    """Tests for AntiPatternAggregator.merge() method."""

    def test_aggregator_deduplicates_by_text(self):
        """Verify deduplication works based on text (case-sensitive exact match)."""
        aggregator = AntiPatternAggregator()

        group1 = [
            {"text": "Hello world", "source_table": "table_a", "source_id": "1"},
            {"text": "Foo bar", "source_table": "table_a", "source_id": "2"},
        ]
        group2 = [
            {"text": "Hello world", "source_table": "table_b", "source_id": "3"},
            {"text": "Baz qux", "source_table": "table_b", "source_id": "4"},
        ]

        result = aggregator.merge(group1, group2)

        assert len(result) == 3
        texts = [ap.text for ap in result]
        assert "Hello world" in texts
        assert "Foo bar" in texts
        assert "Baz qux" in texts

    def test_aggregator_preserves_first_occurrence_metadata(self):
        """Verify first occurrence metadata is kept when duplicates exist."""
        aggregator = AntiPatternAggregator()

        group1 = [
            {"text": "Hello world", "source_table": "table_a", "source_id": "1"},
        ]
        group2 = [
            {"text": "Hello world", "source_table": "table_b", "source_id": "2"},
        ]

        result = aggregator.merge(group1, group2)

        assert len(result) == 1
        assert result[0].text == "Hello world"
        assert result[0].source_table == "table_a"
        assert result[0].source_id == "1"

    def test_aggregator_empty_input(self):
        """Verify empty input returns empty list."""
        aggregator = AntiPatternAggregator()

        result = aggregator.merge()

        assert result == []

    def test_aggregator_preserves_order(self):
        """Verify insertion order is maintained in the result."""
        aggregator = AntiPatternAggregator()

        group1 = [
            {"text": "Alpha", "source_table": "t1", "source_id": "1"},
            {"text": "Beta", "source_table": "t1", "source_id": "2"},
        ]
        group2 = [
            {"text": "Gamma", "source_table": "t2", "source_id": "3"},
            {"text": "Delta", "source_table": "t2", "source_id": "4"},
        ]

        result = aggregator.merge(group1, group2)

        assert [ap.text for ap in result] == ["Alpha", "Beta", "Gamma", "Delta"]
