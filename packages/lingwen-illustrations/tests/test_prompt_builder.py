"""Test Stage 1 LLM extraction: prompt build + JSON parse + error handling."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from lingwen_illustrations.exceptions import ExtractError
from lingwen_illustrations.prompt_builder import (
    _MAX_CHAPTER_CHARS,
    build_extraction_prompt,
    extract_scene,
    parse_extraction_response,
)


def test_build_extraction_prompt_includes_chapter_text():
    prompt = build_extraction_prompt(
        chapter_text="林渊踏入幽冥谷，薄雾缠绕脚踝。",
        character_bible=[{"name": "林渊", "description": "黑发青年"}],
    )
    assert "林渊踏入幽冥谷" in prompt
    assert "林渊" in prompt
    assert "黑发青年" in prompt
    assert "JSON" in prompt or "json" in prompt


def test_parse_extraction_response_valid_json():
    raw = json.dumps({
        "subject": "林渊",
        "scene": "幽冥谷",
        "mood": "紧张",
        "characters_in_scene": [{"name": "林渊", "role": "主角", "key_visual": "黑发"}],
        "extraction_confidence": 0.85,
    }, ensure_ascii=False)
    parsed = parse_extraction_response(raw)
    assert parsed["subject"] == "林渊"
    assert parsed["extraction_confidence"] == 0.85


def test_parse_extraction_response_with_markdown_fence():
    raw = '```json\n{"subject": "x", "scene": "y", "mood": "z", "characters_in_scene": [], "extraction_confidence": 0.9}\n```'
    parsed = parse_extraction_response(raw)
    assert parsed["subject"] == "x"


def test_parse_extraction_response_missing_field_raises():
    raw = json.dumps({"subject": "x"})  # missing fields
    with pytest.raises(ExtractError) as exc:
        parse_extraction_response(raw)
    assert "scene" in str(exc.value).lower() or "missing" in str(exc.value).lower()


def test_parse_extraction_response_invalid_json_raises():
    with pytest.raises(ExtractError):
        parse_extraction_response("not valid json")


def test_extract_scene_calls_llm_service(monkeypatch):
    """Integration: extract_scene orchestrates LLM call + parse."""
    mock_service = MagicMock()
    mock_service.execute.return_value = json.dumps({
        "subject": "林渊", "scene": "谷", "mood": "紧张",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)

    monkeypatch.setattr("lingwen_illustrations.prompt_builder.get_llm_service",
                        lambda: mock_service)

    result = extract_scene(
        chapter_text="测试章节文本",
        character_bible=[],
    )
    assert result["subject"] == "林渊"
    mock_service.execute.assert_called_once()


def test_extract_scene_llm_failure_raises_extract_error(monkeypatch):
    mock_service = MagicMock()
    mock_service.execute.side_effect = RuntimeError("LLM timeout")

    monkeypatch.setattr("lingwen_illustrations.prompt_builder.get_llm_service",
                        lambda: mock_service)

    with pytest.raises(ExtractError) as exc:
        extract_scene(chapter_text="x", character_bible=[])
    assert exc.value.retryable is True


def test_build_extraction_prompt_truncates_long_chapter():
    """IMPORTANT: >8000 chars must be truncated to avoid LLM context bloat."""
    long_text = "x" * 10_000
    prompt = build_extraction_prompt(chapter_text=long_text, character_bible=[])
    # The full 10K string should NOT appear (truncation occurred)
    assert long_text not in prompt
    # The truncated version (8000 x's) SHOULD appear
    assert "x" * _MAX_CHAPTER_CHARS in prompt
    # And we should NOT have a run of more than _MAX_CHAPTER_CHARS x's
    import re
    runs = re.findall(r"x+", prompt)
    longest_run = max(len(r) for r in runs)
    assert longest_run <= _MAX_CHAPTER_CHARS


def test_build_extraction_prompt_empty_character_bible_falls_back():
    """IMPORTANT: empty character_bible must produce explicit fallback string."""
    prompt = build_extraction_prompt(chapter_text="测试章节", character_bible=[])
    assert "(无角色档案)" in prompt
