"""灵文提示词工程 · YAML 模板加载

Phase 1.3 — Doc 2 (提示词工程 v1.0) §7: 模板加载 + 渲染。

设计原则 (per Doc 2):
- Template YAML 结构: scenario, version, agent_role, system_prompt, user_prompt,
  constraints_block (list), requirements_block (list), output_schema
- 模板路径: {base_dir}/{scenario}_v{version}.yaml
- load_template(scenario, version=1, base_dir=...): 加载 → Template
- render_template(template, context): 用 {key} 占位符填充 → RenderedPrompt
- 必需字段缺失 → TemplateParseError
- 文件不存在 → TemplateNotFoundError
- YAML 解析错误 → TemplateParseError

不实施 (后续阶段):
- Jinja2 模板 (Phase 1.5+,现用 {key} 占位符)
- 模板继承 / 片段 (Phase 1.5+)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

# 必需字段
_REQUIRED_FIELDS = (
    "scenario", "version", "agent_role", "system_prompt", "user_prompt",
)


class TemplateError(Exception):
    """Template 基类异常"""


class TemplateNotFoundError(TemplateError):
    """模板文件不存在"""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"template not found: {path}")


class TemplateParseError(TemplateError):
    """模板解析错误 (YAML 语法 / 字段缺失)"""

    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.path = path
        if path is not None:
            super().__init__(f"{message} (path={path})")
        else:
            super().__init__(message)


@dataclass(frozen=True)
class Template:
    """YAML 模板数据结构

    constraints_block: 约束列表 (字数/必须有钩子)
    requirements_block: 要求列表 (符合大纲/不能跑题)
    output_schema: 输出 schema 名 ("dict" / class name)
    """

    scenario: str
    version: int
    agent_role: str
    system_prompt: str
    user_prompt: str
    constraints_block: tuple[str, ...] = ()
    requirements_block: tuple[str, ...] = ()
    output_schema: str = "dict"


@dataclass(frozen=True)
class RenderedPrompt:
    """渲染后的提示词 — 准备送给 LLM

    system_prompt: 已填充
    user_prompt: 已填充
    constraints_block: 已填充并 join
    requirements_block: 已填充并 join
    output_schema: 原样
    """

    system_prompt: str
    user_prompt: str
    constraints_block: str = ""
    requirements_block: str = ""
    output_schema: str = "dict"


def _template_path(scenario: str, version: int, base_dir: Path) -> Path:
    """构造模板文件路径"""
    return base_dir / f"{scenario}_v{version}.yaml"


def load_template(
    scenario: str,
    version: int = 1,
    base_dir: Optional[Path] = None,
) -> Template:
    """加载 YAML 模板

    Args:
        scenario: 12 SCENARIOS 之一
        version: 模板版本号 (默认 1)
        base_dir: 模板所在目录 (默认 infra/prompt_engineering/templates/examples/)

    Returns:
        Template 数据类

    Raises:
        TemplateNotFoundError: 文件不存在
        TemplateParseError: YAML 解析错误 / 必需字段缺失
    """
    if base_dir is None:
        # 默认 base_dir
        base_dir = Path(__file__).parent / "templates" / "examples"

    path = _template_path(scenario, version, base_dir)
    if not path.exists():
        raise TemplateNotFoundError(path)

    # 解析 YAML
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise TemplateParseError(f"invalid YAML: {e}", path) from e

    if not isinstance(data, dict):
        raise TemplateParseError(f"expected dict, got {type(data).__name__}", path)

    # 验证必需字段
    for field_name in _REQUIRED_FIELDS:
        if field_name not in data:
            raise TemplateParseError(
                f"missing required field: {field_name!r}", path
            )

    # 构造 Template
    constraints = data.get("constraints_block") or []
    requirements = data.get("requirements_block") or []
    return Template(
        scenario=data["scenario"],
        version=int(data["version"]),
        agent_role=data["agent_role"],
        system_prompt=data["system_prompt"],
        user_prompt=data["user_prompt"],
        constraints_block=tuple(constraints),
        requirements_block=tuple(requirements),
        output_schema=data.get("output_schema", "dict"),
    )


def _fill_placeholders(text: str, context: dict[str, Any]) -> str:
    """用 {key} 占位符填充文本

    未提供的占位符保留原样 {key} (不报错)
    """
    if not text:
        return text
    try:
        return text.format(**context)
    except KeyError:
        # 部分占位符缺失 → 用 safe_substitute 模式
        # 简化实现:逐个替换,失败的保留
        result = text
        for k, v in context.items():
            result = result.replace("{" + str(k) + "}", str(v))
        return result


def render_template(
    template: Template,
    context: dict[str, Any],
) -> RenderedPrompt:
    """渲染 Template → RenderedPrompt

    用 {key} 占位符填充 system_prompt / user_prompt / constraints / requirements
    """
    return RenderedPrompt(
        system_prompt=_fill_placeholders(template.system_prompt, context),
        user_prompt=_fill_placeholders(template.user_prompt, context),
        constraints_block="\n".join(
            _fill_placeholders(s, context) for s in template.constraints_block
        ),
        requirements_block="\n".join(
            _fill_placeholders(s, context) for s in template.requirements_block
        ),
        output_schema=template.output_schema,
    )


__all__ = [
    "Template",
    "RenderedPrompt",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateParseError",
    "load_template",
    "render_template",
]
