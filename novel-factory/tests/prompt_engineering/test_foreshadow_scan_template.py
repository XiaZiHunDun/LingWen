"""Tests for prompt_engineering foreshadow_scan template (Phase 2.8).

Doc 2 §5 SCENARIOS:foreshadow_scan 是 auditor scenario,扫描伏笔未回收/重复/混乱。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestForeshadowScanTemplate:
    """foreshadow_scan_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("foreshadow_scan", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("foreshadow_scan", version=1)
        assert template.scenario == "foreshadow_scan"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 伏笔 → 必含 "伏笔/foreshadow"
        assert "伏笔" in template.system_prompt or "foreshadow" in template.system_prompt.lower()
        assert "{active_foreshadows}" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("foreshadow_scan", version=1)
        ctx = {
            "active_foreshadows": "1. 暗皇身世 (ch50, 计划ch150回收)\n2. 灵虚戒 (ch80, 计划ch120回收)",
            "chapter_content": "本章暗示了灵虚戒的来历...",
        }
        rendered = render_template(template, ctx)
        assert "暗皇身世" in rendered.user_prompt
        assert "灵虚戒" in rendered.user_prompt
