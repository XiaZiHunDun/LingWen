"""
Tests for LLMAnalyzer
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from unittest.mock import MagicMock

import pytest

from infra.reading_power.llm_analyzer import AnalysisResult, LLMAnalyzer, SuspectedSegment


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    response = MagicMock()
    response.content = '{"hooks": [{"type": "危机钩", "strength": 0.8, "position": "结尾", "reason": "危险逼近"}], "coolpoints": []}'
    service.completion.return_value = response
    return service


def test_analyze_with_segments(mock_ai_service):
    """Test analyze with suspected segments"""
    segments = [
        SuspectedSegment("hook", "危机钩", "危险逼近...", 0.8, "结尾", 100),
        SuspectedSegment("coolpoint", "装逼打脸", "打脸场景...", 0.9, "中段", 200),
    ]

    analyzer = LLMAnalyzer(mock_ai_service)
    result = analyzer.analyze(segments, "章节文本")

    assert result.success is True
    assert len(result.hooks) == 1
    assert result.hooks[0]["type"] == "危机钩"


def test_analyze_empty_segments(mock_ai_service):
    """Test analyze with empty segments list"""
    analyzer = LLMAnalyzer(mock_ai_service)
    result = analyzer.analyze([], "章节文本")

    assert result.success is True
    assert result.hooks == []
    assert result.coolpoints == []


def test_parse_json_response():
    """Test JSON response parsing"""
    analyzer = LLMAnalyzer(None)

    raw = '{"hooks": [{"type": "测试", "strength": 0.5}], "coolpoints": []}'
    result = analyzer._parse_json_response(raw)

    assert result["hooks"][0]["type"] == "测试"


def test_parse_json_with_code_block():
    """Test parsing JSON wrapped in code block"""
    analyzer = LLMAnalyzer(None)

    raw = '```json\n{"hooks": [{"type": "测试", "strength": 0.5}], "coolpoints": []}\n```'
    result = analyzer._parse_json_response(raw)

    assert result["hooks"][0]["type"] == "测试"


def test_parse_json_with_markdown():
    """Test parsing JSON wrapped in markdown"""
    analyzer = LLMAnalyzer(None)

    raw = '```\n{"hooks": [], "coolpoints": [{"pattern": "装逼打脸", "density": 0.9}]}\n```'
    result = analyzer._parse_json_response(raw)

    assert result["coolpoints"][0]["pattern"] == "装逼打脸"


def test_analyze_with_long_text(mock_ai_service):
    """Test analyze with long chapter text (uses context instead of full text)"""
    segments = [
        SuspectedSegment("hook", "悬念钩", "神秘事件...", 0.7, "开头", 50),
    ]

    # Create text longer than 2000 chars
    long_text = "这是很长的章节文本。" * 500

    analyzer = LLMAnalyzer(mock_ai_service)
    result = analyzer.analyze(segments, long_text)

    assert result.success is True
    # Should have called completion
    mock_ai_service.completion.assert_called_once()


def test_analyze_failure_handling():
    """Test handling of LLM failure"""
    service = MagicMock()
    service.completion.side_effect = Exception("LLM调用失败")

    segments = [
        SuspectedSegment("hook", "危机钩", "危险...", 0.8, "结尾", 100),
    ]

    analyzer = LLMAnalyzer(service)
    result = analyzer.analyze(segments, "章节文本")

    assert result.success is False
    assert result.error is not None
    assert "LLM调用失败" in result.error


def test_analyze_segments_limit():
    """Test that only first 10 segments are analyzed"""
    service = MagicMock()
    response = MagicMock()
    response.content = '{"hooks": [], "coolpoints": []}'
    service.completion.return_value = response

    # Create more than 10 segments
    segments = [
        SuspectedSegment("hook", f"钩子{i}", f"内容{i}...", 0.8, "结尾", i * 10)
        for i in range(15)
    ]

    analyzer = LLMAnalyzer(service)
    result = analyzer.analyze(segments, "章节文本")

    assert result.success is True
    # Verify completion was called (segments limited to 10)
    service.completion.assert_called_once()
