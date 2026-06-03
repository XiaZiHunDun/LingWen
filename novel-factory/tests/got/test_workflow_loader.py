"""Tests for got.workflow_loader (load_workflow).

Phase 1.4.k — RED tests for workflow_loader.

设计约束 (per Doc 4 v1.0):
- 路径: infra/got/workflows/*.yaml (例: novel_writing.yaml)
- 格式:
    workflow: novel_writing
    version: 1
    nodes:
      - id: read_snapshot
        type: input
        name: Read WorldSnapshot
        description: 读取当前世界快照
        depends_on: []
        prompt_scenario: null
        output_schema: null
      - id: write_chapter
        type: generation
        name: Write Chapter
        depends_on: [read_snapshot]
        prompt_scenario: chapter_writing
        output_schema: ChapterDraft
        token_budget: 8000
        timeout_s: 120
- load_workflow(name) → ThoughtGraph
- 默认 workflows 目录: infra/got/workflows/
- 不存在 → WorkflowNotFoundError
- YAML 格式错 → WorkflowParseError
- 节点缺 id → WorkflowValidationError
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Minimal valid YAML used across tests
_MINIMAL_YAML = """
workflow: test_wf
version: 1
nodes:
  - id: a
    type: input
    name: Node A
    description: First node
    depends_on: []
  - id: b
    type: generation
    name: Node B
    description: Depends on A
    depends_on: [a]
    prompt_scenario: chapter_writing
    token_budget: 1000
    timeout_s: 30
"""


def _write_workflow(tmp_path: Path, name: str, content: str) -> Path:
    """辅助:把 YAML 写到 tmp_path/{name}.yaml"""
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    p = wf_dir / f"{name}.yaml"
    p.write_text(content, encoding="utf-8")
    return wf_dir


class TestLoadWorkflowBasics:
    def test_load_minimal_workflow(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        g = load_workflow("minimal", base_dir=wf_dir)
        assert "a" in g.node_ids()
        assert "b" in g.node_ids()

    def test_load_returns_thought_graph(self, tmp_path):
        from infra.got.graph import ThoughtGraph
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        g = load_workflow("minimal", base_dir=wf_dir)
        assert isinstance(g, ThoughtGraph)

    def test_load_respects_depends_on(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        g = load_workflow("minimal", base_dir=wf_dir)
        b = g.get_node("b")
        assert "a" in b.depends_on

    def test_load_respects_node_type(self, tmp_path):
        from infra.got.data_structures import NodeType
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        g = load_workflow("minimal", base_dir=wf_dir)
        assert g.get_node("a").type == NodeType.INPUT
        assert g.get_node("b").type == NodeType.GENERATION

    def test_load_respects_prompt_scenario(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        g = load_workflow("minimal", base_dir=wf_dir)
        assert g.get_node("b").prompt_scenario == "chapter_writing"
        assert g.get_node("a").prompt_scenario is None  # 默认

    def test_load_respects_token_budget(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        g = load_workflow("minimal", base_dir=wf_dir)
        assert g.get_node("b").token_budget == 1000
        assert g.get_node("b").timeout_s == 30


class TestLoadWorkflowErrors:
    def test_workflow_not_found(self, tmp_path):
        from infra.got.workflow_loader import (
            WorkflowNotFoundError,
            load_workflow,
        )

        wf_dir = _write_workflow(tmp_path, "minimal", _MINIMAL_YAML)
        with pytest.raises(WorkflowNotFoundError, match="(?i)not found"):
            load_workflow("does_not_exist", base_dir=wf_dir)

    def test_invalid_yaml_raises(self, tmp_path):
        from infra.got.workflow_loader import (
            WorkflowParseError,
            load_workflow,
        )

        wf_dir = _write_workflow(tmp_path, "broken", ":\n  invalid: : :")
        with pytest.raises(WorkflowParseError, match="(?i)parse|yaml"):
            load_workflow("broken", base_dir=wf_dir)

    def test_missing_node_id_raises(self, tmp_path):
        from infra.got.workflow_loader import (
            WorkflowValidationError,
            load_workflow,
        )

        yaml_content = """
workflow: bad_wf
version: 1
nodes:
  - type: input
    name: No ID
    description: Missing id field
"""
        wf_dir = _write_workflow(tmp_path, "bad", yaml_content)
        with pytest.raises(WorkflowValidationError, match="(?i)id"):
            load_workflow("bad", base_dir=wf_dir)

    def test_duplicate_node_id_raises(self, tmp_path):
        from infra.got.graph import DuplicateNodeError
        from infra.got.workflow_loader import load_workflow

        yaml_content = """
workflow: dup_wf
version: 1
nodes:
  - id: a
    type: input
    name: First A
  - id: a
    type: input
    name: Second A
"""
        wf_dir = _write_workflow(tmp_path, "dup", yaml_content)
        with pytest.raises(DuplicateNodeError, match="(?i)duplicate"):
            load_workflow("dup", base_dir=wf_dir)

    def test_unknown_node_type_raises(self, tmp_path):
        from infra.got.workflow_loader import (
            WorkflowValidationError,
            load_workflow,
        )

        yaml_content = """
workflow: bad_type_wf
version: 1
nodes:
  - id: a
    type: invalid_type
    name: Bad type
"""
        wf_dir = _write_workflow(tmp_path, "bad_type", yaml_content)
        with pytest.raises(WorkflowValidationError, match="(?i)type"):
            load_workflow("bad_type", base_dir=wf_dir)


class TestLoadWorkflowSingleNode:
    def test_single_node_workflow(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        yaml_content = """
workflow: single
version: 1
nodes:
  - id: solo
    type: output
    name: Single Node
    description: Only node
"""
        wf_dir = _write_workflow(tmp_path, "single", yaml_content)
        g = load_workflow("single", base_dir=wf_dir)
        assert g.node_ids() == ["solo"]


class TestLoadWorkflowNoExtension:
    def test_load_with_yaml_extension(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "named", _MINIMAL_YAML)
        # 自动补 .yaml 扩展名
        g = load_workflow("named", base_dir=wf_dir)
        assert "a" in g.node_ids()

    def test_load_with_full_extension(self, tmp_path):
        from infra.got.workflow_loader import load_workflow

        wf_dir = _write_workflow(tmp_path, "named", _MINIMAL_YAML)
        # 显式带 .yaml 也应可工作
        g = load_workflow("named.yaml", base_dir=wf_dir)
        assert "a" in g.node_ids()
