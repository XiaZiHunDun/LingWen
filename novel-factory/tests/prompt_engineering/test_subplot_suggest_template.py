"""Tests for prompt_engineering subplot_suggest template (Phase 2.10).

Doc 2 §5 SCENARIOS:subplot_suggest 是 outline_master scenario,每 5 章建议支线开/关。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestSubplotSuggestTemplate:
    """subplot_suggest_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("subplot_suggest", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("subplot_suggest", version=1)
        assert template.scenario == "subplot_suggest"
        assert template.version == 1
        assert template.agent_role == "outline_master"
        # 支线建议 → 必含 "支线/subplot"
        sp = template.system_prompt
        assert "支线" in sp or "subplot" in sp.lower()
        assert "{active_subplots}" in template.user_prompt
        assert "{current_chapter}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("subplot_suggest", version=1)
        ctx = {
            "current_chapter": 100,
            "active_subplots": "p1: 林尘寻亲 (active, ch10-)\np2: 灵虚戒秘密 (active, ch80-)",
            "main_plot": "林尘觉醒 → 暗皇对决",
        }
        rendered = render_template(template, ctx)
        assert "100" in rendered.user_prompt
        assert "p1: 林尘寻亲" in rendered.user_prompt
