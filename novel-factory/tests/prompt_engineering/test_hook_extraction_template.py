"""Tests for prompt_engineering hook_extraction template (Phase 2.9).

Doc 2 §5 SCENARIOS:hook_extraction 是 polisher scenario,提取章节钩子 (开篇钩/结尾钩)。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestHookExtractionTemplate:
    """hook_extraction_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("hook_extraction", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("hook_extraction", version=1)
        assert template.scenario == "hook_extraction"
        assert template.version == 1
        assert template.agent_role == "polisher"
        # 钩子提取 → 必含 "钩子/hook"
        assert "钩子" in template.system_prompt or "hook" in template.system_prompt.lower()
        assert "{chapter_num}" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("hook_extraction", version=1)
        ctx = {
            "chapter_num": 100,
            "chapter_content": "林尘在黑暗中醒来...",
        }
        rendered = render_template(template, ctx)
        assert "100" in rendered.user_prompt
        assert "林尘在黑暗中醒来" in rendered.user_prompt
