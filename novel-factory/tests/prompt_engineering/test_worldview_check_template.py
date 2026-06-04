"""Tests for prompt_engineering worldview_check template (Phase 2.8).

Doc 2 §5 SCENARIOS:worldview_check 是 auditor scenario,抽检世界观一致性。
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestWorldviewCheckTemplate:
    """worldview_check_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("worldview_check", version=1)
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("worldview_check", version=1)
        assert template.scenario == "worldview_check"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 世界观 → 必含 "世界观/worldview"
        assert "世界观" in template.system_prompt or "worldview" in template.system_prompt.lower()
        assert "{world_setting}" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("worldview_check", version=1)
        ctx = {
            "world_setting": "修真世界,境界划分:炼气→筑基→金丹...",
            "chapter_content": "林尘突破到金丹期...",
        }
        rendered = render_template(template, ctx)
        assert "修真世界" in rendered.user_prompt
        assert "林尘突破" in rendered.user_prompt
