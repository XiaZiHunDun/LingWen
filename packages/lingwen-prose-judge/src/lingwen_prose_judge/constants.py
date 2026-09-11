"""Prose judge constants — rubric dimensions, actions, issue mapping, LLM prompt.

Phase 51 P3-ARCHDEBT: extracted verbatim from infra/prose_judge.py lines 16-68.
"""

from __future__ import annotations

JUDGE_REPORT_VERSION = 1
REPORT_FILENAME = "prose-judge-report.json"

DIMENSIONS: tuple[str, ...] = (
    "imagery",
    "hook",
    "agency",
    "vitality",
    "dialogue",
    "genre",
)

ACTIONS: tuple[str, ...] = ("keep", "trim", "rewrite")

ISSUE_TYPE_TO_DIMENSION: dict[str, str] = {
    "sentence_diversity_low": "vitality",
    "low_character_agency": "agency",
    "对话AI化": "dialogue",
    "对话过于正式": "dialogue",
    "ai_gloss": "vitality",
    "ai_trace": "vitality",
    "scene_pattern_repeat": "imagery",
    "mechanical_suspense_density": "hook",
    "mechanical_suspense_patterns": "hook",
    "consecutive_mechanical_suspense": "hook",
}

DIMENSION_LABELS: dict[str, str] = {
    "imagery": "画面感",
    "hook": "钩子密度",
    "agency": "人物能动性",
    "vitality": "句式活力",
    "dialogue": "对话真实",
    "genre": "类型完成度",
}

JUDGE_SYSTEM_PROMPT = """你是网文 prose 编辑，按灵文 Prose Rubric v1 六维为单章打分（1–5）。

维度：imagery 画面感 · hook 钩子密度 · agency 人物能动性 · vitality 句式活力 · dialogue 对话真实 · genre 类型完成度

5=样章级优秀 · 3=可接受 · 1=需大改

action：score≥4 → keep · score=3 → trim · score≤2 → rewrite

只输出 JSON（无 markdown）：
{
  "chapter": <int>,
  "ratings": [
    {"dimension": "imagery", "score": 4, "evidence": "一句依据", "action": "keep"},
    ... 共 6 条，dimension 各一
  ]
}
"""
