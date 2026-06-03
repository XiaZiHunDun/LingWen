"""灵文 GoT · Workflow YAML Loader

Phase 1.4 — Doc 4 (GoT 适配设计 v1.0) §7: 工作流定义加载。

YAML 格式:
    workflow: <name>
    version: <int>
    nodes:
      - id: <node_id>
        type: <NodeType>
        name: <display_name>
        description: <text>
        depends_on: [<node_id>, ...]   # 可选,默认 []
        prompt_scenario: <scenario>    # 可选
        output_schema: <schema_name>   # 可选(暂不解析)
        token_budget: <int>            # 可选,默认 0
        timeout_s: <int>               # 可选,默认 60

默认 base_dir: infra/got/workflows/

不实施 (后续阶段):
- output_schema 字符串 → 类型映射 (暂只存 None)
- 远程 URL / git 仓库加载
- 工作流继承 / 模板化
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from infra.got.data_structures import NodeType, ThoughtNode
from infra.got.graph import ThoughtGraph

# === Exceptions ===

class WorkflowError(Exception):
    """Workflow loader 基类异常"""


class WorkflowNotFoundError(WorkflowError):
    """workflow 文件未找到"""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"workflow not found: {path!r}")


class WorkflowParseError(WorkflowError):
    """YAML 解析失败"""

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.yaml_message = message
        super().__init__(f"YAML parse error in {path!r}: {message}")


class WorkflowValidationError(WorkflowError):
    """workflow 字段验证失败"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


# === Public API ===

def load_workflow(
    name: str,
    base_dir: Optional[Path] = None,
) -> ThoughtGraph:
    """加载工作流 YAML → ThoughtGraph

    Args:
        name: workflow 名称 (可省略 .yaml 后缀)
        base_dir: 工作流目录 (默认 infra/got/workflows/)

    Returns:
        ThoughtGraph: 加载完成的图

    Raises:
        WorkflowNotFoundError: 文件不存在
        WorkflowParseError: YAML 解析失败
        WorkflowValidationError: 字段缺失或值非法
        DuplicateNodeError: 节点 id 重复(从 ThoughtGraph 传播)
    """
    if base_dir is None:
        base_dir = Path(__file__).parent / "workflows"
    base_dir = Path(base_dir)

    # 解析路径
    file_path = _resolve_path(name, base_dir)
    if not file_path.exists():
        raise WorkflowNotFoundError(str(file_path))

    # 解析 YAML
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise WorkflowParseError(str(file_path), str(exc)) from exc

    if not isinstance(data, dict):
        raise WorkflowValidationError(
            f"workflow root must be a mapping, got {type(data).__name__}"
        )

    # 验证根字段
    if "nodes" not in data:
        raise WorkflowValidationError("missing required field: 'nodes'")
    if not isinstance(data["nodes"], list):
        raise WorkflowValidationError("'nodes' must be a list")

    # 构建图
    graph = ThoughtGraph()
    for node_def in data["nodes"]:
        if not isinstance(node_def, dict):
            raise WorkflowValidationError(
                f"node entry must be a mapping, got {type(node_def).__name__}"
            )
        node = _parse_node(node_def, file_path)
        graph.add_node(node)  # DuplicateNodeError 由 graph 抛

    return graph


# === Internals ===

def _resolve_path(name: str, base_dir: Path) -> Path:
    """解析 workflow 文件路径

    - 已是 .yaml 结尾 → 直接用
    - 否则补 .yaml
    """
    if name.endswith(".yaml") or name.endswith(".yml"):
        return base_dir / name
    return base_dir / f"{name}.yaml"


def _parse_node(node_def: dict[str, Any], file_path: Path) -> ThoughtNode:
    """解析单个节点定义 → ThoughtNode

    Raises:
        WorkflowValidationError: 字段缺失或值非法
    """
    # 1. 必填: id
    if "id" not in node_def:
        raise WorkflowValidationError(
            f"node missing required field 'id' in {node_def!r}"
        )
    node_id = node_def["id"]
    if not isinstance(node_id, str) or not node_id.strip():
        raise WorkflowValidationError(
            f"node id must be non-empty string, got {node_id!r}"
        )

    # 2. 必填: type
    if "type" not in node_def:
        raise WorkflowValidationError(
            f"node {node_id!r} missing required field 'type'"
        )
    type_str = node_def["type"]
    try:
        node_type = NodeType(type_str)
    except ValueError:
        valid = [t.value for t in NodeType]
        raise WorkflowValidationError(
            f"node {node_id!r} has invalid type {type_str!r}; "
            f"valid values: {valid}"
        ) from None

    # 3. 可选字段
    name = node_def.get("name", node_id)
    description = node_def.get("description", "")
    depends_on = tuple(node_def.get("depends_on", ()))
    inputs = tuple(node_def.get("inputs", ()))
    outputs = tuple(node_def.get("outputs", ()))
    parallel_with = tuple(node_def.get("parallel_with", ()))
    conflicts_with = tuple(node_def.get("conflicts_with", ()))
    prompt_scenario = node_def.get("prompt_scenario")
    # output_schema 字符串 → 类型映射留给后续阶段,目前只存 None
    token_budget = int(node_def.get("token_budget", 0))
    timeout_s = int(node_def.get("timeout_s", 60))

    # 4. 类型检查
    if not isinstance(depends_on, (list, tuple)):
        raise WorkflowValidationError(
            f"node {node_id!r}: depends_on must be a list, "
            f"got {type(depends_on).__name__}"
        )
    if not all(isinstance(d, str) for d in depends_on):
        raise WorkflowValidationError(
            f"node {node_id!r}: depends_on must contain only strings"
        )

    return ThoughtNode(
        node_id=node_id,
        type=node_type,
        name=name,
        description=description,
        depends_on=depends_on,
        inputs=inputs,
        outputs=outputs,
        parallel_with=parallel_with,
        conflicts_with=conflicts_with,
        prompt_scenario=prompt_scenario,
        # output_schema 暂不解析字符串 → 类型(后续阶段)
        output_schema=None,
        token_budget=token_budget,
        timeout_s=timeout_s,
    )


__all__ = [
    "load_workflow",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowParseError",
    "WorkflowValidationError",
]
