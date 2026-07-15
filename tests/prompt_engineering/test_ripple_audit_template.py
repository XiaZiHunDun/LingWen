"""Tests for prompt_engineering ripple_audit template (Phase 2.2).

Doc 1 §3.4 + Doc 2 §6.2:ripple_audit 是 auditor scenario,负责审计涟漪。
SCENARIOS 中已有 ripple_audit 描述,但缺 YAML 模板。

测试覆盖:
- 模板加载成功
- 必需字段存在 (scenario/version/agent_role/system_prompt/user_prompt)
- 模板可被 render_template 渲染 (含 chapter_num / active_ripples / collapse_risk)
"""
from __future__ import annotations

from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)


class TestRippleAuditTemplate:
    """ripple_audit_v1.yaml 加载 + 字段校验"""

    def test_loads_successfully(self):
        template = load_template("ripple_audit", version=1)
        assert template is not None
        assert isinstance(template, Template)

    def test_required_fields(self):
        template = load_template("ripple_audit", version=1)
        assert template.scenario == "ripple_audit"
        assert template.version == 1
        assert template.agent_role == "auditor"
        # 审计员场景 — system_prompt 应提到"审计/违规/审计员"
        assert "审计" in template.system_prompt or "audit" in template.system_prompt.lower()
        # user_prompt 应含章节占位符
        assert "{chapter_num}" in template.user_prompt
        assert "{active_ripples}" in template.user_prompt
        assert "{collapse_risk" in template.user_prompt
        assert "{chapter_content}" in template.user_prompt

    def test_renders_with_context(self):
        template = load_template("ripple_audit", version=1)
        ctx = {
            "chapter_num": 200,
            "chapter_content": "林尘觉醒...",
            "active_ripples": "r1 (open)\nr2 (propagating)",
            "active_count": 2,
            "collapse_risk": 0.3,
            "alarm_status": "OK",
        }
        rendered = render_template(template, ctx)
        # 占位符被填充
        assert "{chapter_num}" not in rendered.user_prompt
        assert "200" in rendered.user_prompt
        assert "林尘觉醒" in rendered.user_prompt
        assert "0.3" in rendered.user_prompt or "0.30" in rendered.user_prompt
