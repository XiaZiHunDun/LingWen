"""Tests for prompt_engineering chapter_outline template (Phase 2.7).

Doc 2 §5 SCENARIOS:chapter_outline 是 content_writer scenario,负责写章节大纲。
SCENARIOS 中已有 chapter_outline 描述,但缺 YAML 模板。

测试覆盖:
- 模板加载成功
- 必需字段存在 (scenario/version/agent_role/system_prompt/user_prompt)
- 模板可被 render_template 渲染 (含 chapter_num / volume_outline / drive_chain)
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestChapterOutlineTemplate:
    """chapter_outline_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("chapter_outline", version=1)
        assert template is not None
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("chapter_outline", version=1)
        assert template.scenario == "chapter_outline"
        assert template.version == 1
        assert template.agent_role == "content_writer"
        # 大纲写作 — system_prompt 应提到"大纲/outline"
        assert "大纲" in template.system_prompt or "outline" in template.system_prompt.lower()
        # user_prompt 应含章节/卷/驱动链占位符
        assert "{chapter_num}" in template.user_prompt
        assert "{volume_outline}" in template.user_prompt
        assert "{drive_chain}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("chapter_outline", version=1)
        ctx = {
            "chapter_num": 100,
            "volume_outline": "第一卷:林尘觉醒...",
            "drive_chain": "第99章:林尘遇险 → 第100章:觉醒",
            "previous_chapter_outline": "第99章:林尘误入禁地...",
        }
        rendered = render_template(template, ctx)
        # 占位符被填充
        assert "{chapter_num}" not in rendered.user_prompt
        assert "100" in rendered.user_prompt
        assert "林尘觉醒" in rendered.user_prompt
        assert "第99章:林尘遇险" in rendered.user_prompt
