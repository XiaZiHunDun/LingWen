"""Tests for prompt_engineering chapter_review template (Phase 2.8).

Doc 2 §5 SCENARIOS:chapter_review 是 auditor scenario,S1-S8 八维度评估章节。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestChapterReviewTemplate:
    """chapter_review_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("chapter_review", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("chapter_review", version=1)
        assert template.scenario == "chapter_review"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 章节审核 — 必含 S1-S8 八维
        assert "S1" in template.user_prompt or "剧情完整" in template.user_prompt
        assert "{chapter_num}" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("chapter_review", version=1)
        ctx = {
            "chapter_num": 100,
            "chapter_content": "林尘觉醒...",
        }
        rendered = render_template(template, ctx)
        assert "100" in rendered.user_prompt
        assert "林尘觉醒" in rendered.user_prompt
