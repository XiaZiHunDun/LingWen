"""Tests for prompt_engineering character_consistency template (Phase 2.8).

Doc 2 §5 SCENARIOS:character_consistency 是 auditor scenario,抽检角色一致性。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestCharacterConsistencyTemplate:
    """character_consistency_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("character_consistency", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("character_consistency", version=1)
        assert template.scenario == "character_consistency"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 角色一致性 → 必含 "角色/character"
        assert "角色" in template.system_prompt or "character" in template.system_prompt.lower()
        assert "{character_profiles}" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("character_consistency", version=1)
        ctx = {
            "character_profiles": "林尘:沉稳/果决/炼气期。暗皇:阴鸷/智谋/筑基期。",
            "chapter_content": "林尘在战斗中突然变得冲动...",
        }
        rendered = render_template(template, ctx)
        assert "林尘:沉稳" in rendered.user_prompt
        assert "突然变得冲动" in rendered.user_prompt
