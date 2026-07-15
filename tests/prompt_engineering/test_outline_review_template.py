"""Tests for prompt_engineering outline_review template (Phase 2.8).

Doc 2 §5 SCENARIOS:outline_review 是 auditor scenario,审核大纲结构/伏笔/驱动链。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestOutlineReviewTemplate:
    """outline_review_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("outline_review", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("outline_review", version=1)
        assert template.scenario == "outline_review"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 审核 → 必含 "审核/review"
        assert "审核" in template.system_prompt or "review" in template.system_prompt.lower()
        assert "{outline}" in template.user_prompt
        assert "{volume_index}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("outline_review", version=1)
        ctx = {
            "volume_index": 1,
            "outline": "第一卷: 林尘觉醒...",
            "drive_chain": "第1章:诞生 → 第10章:初战",
        }
        rendered = render_template(template, ctx)
        assert "1" in rendered.user_prompt
        assert "林尘觉醒" in rendered.user_prompt
