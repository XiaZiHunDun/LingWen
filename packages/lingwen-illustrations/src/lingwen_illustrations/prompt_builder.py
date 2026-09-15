"""Stage 1: LLM extraction of scene JSON from chapter text + character bible.

Calls lingwen-llm-service (I057). Returns structured JSON for Stage 2
template composition. Failures raise ExtractError (retryable).
"""

from __future__ import annotations

import json
import re
from typing import Any

from lingwen_llm_service import get_llm_service
from lingwen_shared.contracts.python.llm import LLMTask, TaskType

from lingwen_illustrations.exceptions import ExtractError

_REQUIRED_FIELDS = ("subject", "scene", "mood", "characters_in_scene", "extraction_confidence")

# Truncate chapter text to ~2K zh tokens to avoid LLM context bloat.
# Reusable constant; pattern matches `lingwen_world_db.MAX_CHAPTERS_DEFAULT`.
_MAX_CHAPTER_CHARS = 8000


def build_extraction_prompt(
    *,
    chapter_text: str,
    character_bible: list[dict[str, Any]],
) -> str:
    """Construct the LLM prompt for scene extraction."""
    char_lines = "\n".join(
        f"- {c.get('name', '?')}: {c.get('description', '')}"
        for c in character_bible
    ) or "(无角色档案)"

    # Truncate chapter text to avoid LLM token bloat (~2K zh tokens).
    truncated = chapter_text[:_MAX_CHAPTER_CHARS]

    return f"""你是小说场景抽取专家。从以下章节文本中抽取视觉化信息用于生成插图。

# 章节文本
{truncated}

# 角色档案
{char_lines}

# 任务
输出严格 JSON（不要 markdown 包裹），字段：
- subject: 主视觉主体（人物/物体/场景，1-2 词）
- scene: 具体场景（时间/地点/动作，1-2 句）
- mood: 氛围词（紧张/宁静/壮阔等）
- characters_in_scene: 出现在场景中的角色列表，每项含 name/role/key_visual
- extraction_confidence: 0-1 浮点表示抽取置信度
"""


def parse_extraction_response(raw: str) -> dict[str, Any]:
    """Parse LLM response to structured dict. Handles markdown fence.

    Raises:
        ExtractError: If JSON invalid or required fields missing.
    """
    # Strip markdown code fence if present
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ExtractError(f"LLM returned invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ExtractError(f"LLM returned non-dict: {type(data).__name__}")

    missing = [f for f in _REQUIRED_FIELDS if f not in data]
    if missing:
        raise ExtractError(f"LLM JSON missing fields: {missing}")

    if not isinstance(data["extraction_confidence"], (int, float)):
        raise ExtractError("extraction_confidence must be a number")

    return data


def extract_scene(
    *,
    chapter_text: str,
    character_bible: list[dict[str, Any]],
) -> dict[str, Any]:
    """Orchestrate LLM call + response parse.

    Returns:
        Parsed scene JSON dict.

    Raises:
        ExtractError: If LLM call fails or response unparseable.
    """
    prompt = build_extraction_prompt(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    try:
        service = get_llm_service()
        # TaskType.STRUCTURED_EXTRACTION doesn't exist in lingwen-shared;
        # QUALITY_ANALYSIS is the closest semantic fit (analytical JSON
        # output, not text repair). v2 follow-up: add STRUCTURED_EXTRACTION
        # to TaskType enum in lingwen-shared. See BACKLOG "P2-EXTRACT-ENUM".
        task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt=prompt)
        response_raw = service.execute(task)
    except Exception as e:
        raise ExtractError(f"LLM call failed: {e}") from e

    return parse_extraction_response(response_raw)


__all__ = ["build_extraction_prompt", "parse_extraction_response", "extract_scene"]
