import pytest
from unittest.mock import MagicMock, patch
from infra.reading_power.engine import ReadingPowerEngine

def test_analyze_chapter_with_rule_matcher():
    mock_db = MagicMock()
    mock_db.get_chapter_summary.return_value = None

    with patch('infra.reading_power.rule_matcher.RuleMatcher') as MockMatcher:
        mock_matcher = MagicMock()
        mock_matcher.scan.return_value = [
            MagicMock(segment_type="hook", pattern_name="危机钩",
                      content="危险...", confidence=0.8, position="结尾", offset=100),
            MagicMock(segment_type="coolpoint", pattern_name="装逼打脸",
                      content="打脸...", confidence=0.9, position="中段", offset=200),
        ]
        MockMatcher.return_value = mock_matcher

        engine = ReadingPowerEngine(db=mock_db)
        engine.rule_matcher = mock_matcher

        result = engine.analyze_chapter(1, "章节内容：危险逼近，打脸场景")

        assert result.success is True
        mock_matcher.scan.assert_called_once()

def test_analyze_empty_chapter():
    mock_db = MagicMock()
    engine = ReadingPowerEngine(db=mock_db)

    result = engine.analyze_chapter(1, "")

    assert result.success is True
    assert result.hooks == []
    assert result.coolpoints == []