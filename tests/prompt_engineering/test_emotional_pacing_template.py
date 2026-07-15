"""Tests for prompt_engineering emotional_pacing template (Phase 2.8).

Doc 2 §5 SCENARIOS:emotional_pacing 是 auditor scenario,诊断情感节奏 (过山车/扁平/失衡)。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestEmotionalPacingTemplate:
    """emotional_pacing_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("emotional_pacing", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("emotional_pacing", version=1)
        assert template.scenario == "emotional_pacing"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 情感节奏 → 必含 "情感/emotion/pacing"
        sp = template.system_prompt.lower()
        assert "情感" in template.system_prompt or "emotion" in sp or "pacing" in sp
        assert "{chapter_content}" in template.user_prompt
        # 多章诊断, 必含 chapter_range
        assert "{chapter_range}" in template.user_prompt or "{chapters}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("emotional_pacing", version=1)
        ctx = {
            "chapter_range": "ch95-ch105",
            "chapter_content": "本章是情感高峰...",
        }
        rendered = render_template(template, ctx)
        assert "ch95" in rendered.user_prompt or "95" in rendered.user_prompt
        assert "情感高峰" in rendered.user_prompt
