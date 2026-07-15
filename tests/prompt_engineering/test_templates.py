"""Tests for prompt_engineering.templates.

Phase 1.3.g — RED tests for YAML template loader (load_template, render).

设计约束 (per Doc 2 v1.0):
- Template YAML 结构: scenario, version, agent_role, system_prompt, user_prompt,
  constraints_block, requirements_block, output_schema
- 模板路径: infra/prompt_engineering/templates/examples/{scenario}_v{version}.yaml
- load_template(scenario, version=1): 加载 YAML → Template dataclass
- render_template(template, context): 用 {key} 占位符填充 → RenderedPrompt
- RenderedPrompt: system_prompt, user_prompt 填充好,validate output_schema
"""
from __future__ import annotations

from pathlib import Path

import pytest


class TestLoadTemplate:
    def test_load_existing_template(self, tmp_path: Path):
        """加载存在的 YAML 模板"""
        from infra.prompt_engineering.templates import load_template

        # 创建测试 YAML
        yaml_path = tmp_path / "chapter_writing_v1.yaml"
        yaml_path.write_text(
            "scenario: chapter_writing\n"
            "version: 1\n"
            "agent_role: content_writer\n"
            "system_prompt: 你是网文写手\n"
            "user_prompt: '写第 {chapter_num} 章,主角 {protagonist}'\n"
            "constraints_block:\n"
            "  - 字数 {min_words}-{max_words}\n"
            "  - 必须有钩子\n"
            "requirements_block:\n"
            "  - 符合大纲\n"
            "output_schema: dict\n",
            encoding="utf-8",
        )

        tpl = load_template("chapter_writing", version=1, base_dir=tmp_path)
        assert tpl.scenario == "chapter_writing"
        assert tpl.version == 1
        assert tpl.agent_role == "content_writer"
        assert "网文写手" in tpl.system_prompt
        assert "{chapter_num}" in tpl.user_prompt

    def test_load_nonexistent_raises(self, tmp_path: Path):
        from infra.prompt_engineering.templates import TemplateNotFoundError, load_template

        with pytest.raises(TemplateNotFoundError, match="(?i)template"):
            load_template("nonexistent", version=1, base_dir=tmp_path)

    def test_default_version_1(self, tmp_path: Path):
        """load_template 默认 version=1"""
        from infra.prompt_engineering.templates import load_template

        yaml_path = tmp_path / "x_v1.yaml"
        yaml_path.write_text(
            "scenario: x\nversion: 1\nagent_role: r\n"
            "system_prompt: s\nuser_prompt: u\n",
            encoding="utf-8",
        )
        tpl = load_template("x", base_dir=tmp_path)
        assert tpl.version == 1

    def test_load_invalid_yaml_raises(self, tmp_path: Path):
        from infra.prompt_engineering.templates import TemplateParseError, load_template

        yaml_path = tmp_path / "bad_v1.yaml"
        yaml_path.write_text("invalid: yaml: [bad", encoding="utf-8")
        with pytest.raises(TemplateParseError, match="(?i)yaml"):
            load_template("bad", version=1, base_dir=tmp_path)

    def test_load_missing_required_field_raises(self, tmp_path: Path):
        from infra.prompt_engineering.templates import TemplateParseError, load_template

        yaml_path = tmp_path / "missing_v1.yaml"
        yaml_path.write_text(
            "scenario: x\nversion: 1\n"
            # 缺 agent_role
            "system_prompt: s\nuser_prompt: u\n",
            encoding="utf-8",
        )
        with pytest.raises(TemplateParseError, match="(?i)agent_role"):
            load_template("missing", version=1, base_dir=tmp_path)


class TestTemplateDataclass:
    def test_template_fields(self):
        from infra.prompt_engineering.templates import Template

        tpl = Template(
            scenario="x",
            version=1,
            agent_role="y",
            system_prompt="s",
            user_prompt="u",
            constraints_block=("c1", "c2"),
            requirements_block=("r1",),
            output_schema="dict",
        )
        assert tpl.constraints_block == ("c1", "c2")
        assert tpl.output_schema == "dict"

    def test_template_is_frozen(self):
        from infra.prompt_engineering.templates import Template

        tpl = Template(
            scenario="x", version=1, agent_role="y",
            system_prompt="s", user_prompt="u",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            tpl.scenario = "z"  # type: ignore[misc]


class TestRenderTemplate:
    def _template(self):
        from infra.prompt_engineering.templates import Template

        return Template(
            scenario="chapter_writing",
            version=1,
            agent_role="content_writer",
            system_prompt="你是网文写手",
            user_prompt="写第 {chapter_num} 章,主角 {protagonist}",
            constraints_block=("字数 {min_words}-{max_words}", "必须有钩子"),
            requirements_block=("符合大纲",),
            output_schema="dict",
        )

    def test_render_replaces_placeholders(self):
        from infra.prompt_engineering.templates import render_template

        tpl = self._template()
        rendered = render_template(
            tpl,
            {
                "chapter_num": 5,
                "protagonist": "林尘",
                "min_words": 2000,
                "max_words": 3000,
            },
        )
        assert "林尘" in rendered.user_prompt
        assert "5" in rendered.user_prompt
        assert "2000" in rendered.constraints_block
        assert "3000" in rendered.constraints_block

    def test_render_preserves_system_prompt(self):
        from infra.prompt_engineering.templates import render_template

        tpl = self._template()
        rendered = render_template(
            tpl,
            {"chapter_num": 1, "protagonist": "x", "min_words": 1, "max_words": 2},
        )
        assert rendered.system_prompt == "你是网文写手"

    def test_render_keeps_unfilled_placeholders(self):
        """未提供的占位符保留 {xxx} (不报错)"""
        from infra.prompt_engineering.templates import render_template

        tpl = self._template()
        rendered = render_template(
            tpl,
            {"chapter_num": 1},  # 缺 protagonist
        )
        # protagonist 占位符保留
        assert "{protagonist}" in rendered.user_prompt

    def test_render_returns_rendered_prompt(self):
        from infra.prompt_engineering.templates import RenderedPrompt, render_template

        tpl = self._template()
        rendered = render_template(tpl, {"chapter_num": 1, "protagonist": "x",
                                         "min_words": 1, "max_words": 2})
        assert isinstance(rendered, RenderedPrompt)
        assert isinstance(rendered.system_prompt, str)
        assert isinstance(rendered.user_prompt, str)
        assert isinstance(rendered.constraints_block, str)
        assert isinstance(rendered.requirements_block, str)
