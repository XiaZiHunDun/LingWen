"""Tests for prompt_engineering ai_trace_removal template (Phase 2.9).

Doc 2 §5 SCENARIOS:ai_trace_removal 是 polisher scenario,去除 AI 痕迹 (模板句/套话)。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestAiTraceRemovalTemplate:
    """ai_trace_removal_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("ai_trace_removal", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("ai_trace_removal", version=1)
        assert template.scenario == "ai_trace_removal"
        assert template.version == 1
        assert template.agent_role == "polisher"
        # AI 痕迹 → 必含 "AI 痕迹/模板句/套话"
        sp = template.system_prompt
        assert "AI 痕迹" in sp or "模板句" in sp or "套话" in sp or "ai" in sp.lower()
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("ai_trace_removal", version=1)
        ctx = {
            "chapter_content": "林尘紧握拳头,心中暗下决心...他深吸一口气,眼中闪过坚定的光芒。",
        }
        rendered = render_template(template, ctx)
        assert "紧握拳头" in rendered.user_prompt
        assert "深吸一口气" in rendered.user_prompt
