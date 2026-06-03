"""Tests for got.data_structures.

Phase 1.4.a — RED tests for ThoughtNode + NodeExecution + 2 enums.

设计约束 (per Doc 4 v1.0):
- 8 NodeType: INPUT, ANALYSIS, SYNTHESIS, GENERATION, EVALUATION, DECISION, AGGREGATION, OUTPUT
- 7 NodeStatus: PENDING, READY, RUNNING, COMPLETED, FAILED, SKIPPED, STALE
- ThoughtNode: 不可变 (frozen) — 节点定义
- NodeExecution: 可变 — 运行时状态
- inputs/outputs/depends_on 是 tuple[str, ...] (节点 ID)
"""
from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest


class TestNodeType:
    def test_8_node_types_defined(self):
        from infra.got.data_structures import NodeType

        assert len(NodeType) == 8
        assert {t.value for t in NodeType} == {
            "input", "analysis", "synthesis", "generation",
            "evaluation", "decision", "aggregation", "output",
        }

    def test_node_type_is_str_enum(self):
        from infra.got.data_structures import NodeType

        assert NodeType.INPUT == "input"
        assert NodeType.OUTPUT == "output"


class TestNodeStatus:
    def test_7_node_statuses_defined(self):
        from infra.got.data_structures import NodeStatus

        assert len(NodeStatus) == 7
        assert {s.value for s in NodeStatus} == {
            "pending", "ready", "running", "completed",
            "failed", "skipped", "stale",
        }

    def test_terminal_statuses(self):
        """COMPLETED, FAILED, SKIPPED 是终态"""
        from infra.got.data_structures import NodeStatus

        for terminal in (NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED):
            assert terminal.value in {"completed", "failed", "skipped"}


class TestThoughtNode:
    def test_minimal_thought_node(self):
        """最小 ThoughtNode: node_id + type + name + description"""
        from infra.got.data_structures import NodeType, ThoughtNode

        node = ThoughtNode(
            node_id="n1",
            type=NodeType.INPUT,
            name="Read Snapshot",
            description="Read world snapshot",
        )
        assert node.node_id == "n1"
        assert node.type == NodeType.INPUT
        assert node.name == "Read Snapshot"
        # 默认
        assert node.inputs == ()
        assert node.outputs == ()
        assert node.depends_on == ()
        assert node.parallel_with == ()
        assert node.conflicts_with == ()
        assert node.prompt_scenario is None
        assert node.output_schema is None
        assert node.token_budget == 0
        assert node.timeout_s == 60

    def test_thought_node_is_frozen(self):
        from infra.got.data_structures import NodeType, ThoughtNode

        node = ThoughtNode(node_id="n1", type=NodeType.INPUT, name="x", description="y")
        with pytest.raises(dataclasses.FrozenInstanceError):
            node.name = "z"  # type: ignore[misc]

    def test_thought_node_with_dependencies(self):
        from infra.got.data_structures import NodeType, ThoughtNode

        node = ThoughtNode(
            node_id="n2",
            type=NodeType.GENERATION,
            name="Write",
            description="Write chapter",
            inputs=("n1",),
            outputs=("n3",),
            depends_on=("n1",),
            token_budget=8000,
            timeout_s=300,
            prompt_scenario="chapter_writing",
        )
        assert node.inputs == ("n1",)
        assert node.depends_on == ("n1",)
        assert node.token_budget == 8000
        assert node.prompt_scenario == "chapter_writing"

    def test_thought_node_to_dict(self):
        from infra.got.data_structures import NodeType, ThoughtNode

        node = ThoughtNode(
            node_id="n1",
            type=NodeType.INPUT,
            name="Read",
            description="Read world",
        )
        d = node.to_dict()
        assert d["node_id"] == "n1"
        assert d["type"] == "input"
        assert d["name"] == "Read"
        # output_schema 是 class 引用 → None
        assert d["output_schema"] is None

    def test_thought_node_validation(self):
        """node_id 必填非空"""
        from infra.got.data_structures import NodeType, ThoughtNode

        with pytest.raises(ValueError, match="node_id"):
            ThoughtNode(node_id="", type=NodeType.INPUT, name="x", description="y")


class TestNodeExecution:
    def test_minimal_node_execution(self):
        """最小 NodeExecution: node_id + status + started_at"""
        from infra.got.data_structures import NodeExecution, NodeStatus

        now = datetime(2026, 6, 3, 10, 0, 0)
        exec_ = NodeExecution(node_id="n1", status=NodeStatus.PENDING, started_at=now)
        assert exec_.node_id == "n1"
        assert exec_.status == NodeStatus.PENDING
        assert exec_.started_at == now
        # 默认
        assert exec_.finished_at is None
        assert exec_.output is None
        assert exec_.error is None
        assert exec_.attempt == 1
        assert exec_.cost_tokens == 0

    def test_node_execution_is_mutable(self):
        """NodeExecution 应该是可变的 (运行时更新)"""
        from infra.got.data_structures import NodeExecution, NodeStatus

        now = datetime(2026, 6, 3, 10, 0, 0)
        exec_ = NodeExecution(node_id="n1", status=NodeStatus.PENDING, started_at=now)
        # 可以原地修改
        exec_.status = NodeStatus.RUNNING
        exec_.attempt = 2
        assert exec_.status == NodeStatus.RUNNING
        assert exec_.attempt == 2

    def test_node_execution_to_dict(self):
        from infra.got.data_structures import NodeExecution, NodeStatus

        now = datetime(2026, 6, 3, 10, 0, 0)
        exec_ = NodeExecution(
            node_id="n1",
            status=NodeStatus.COMPLETED,
            started_at=now,
            finished_at=datetime(2026, 6, 3, 10, 5, 0),
            output={"chapters": 5},
            cost_tokens=1000,
        )
        d = exec_.to_dict()
        assert d["node_id"] == "n1"
        assert d["status"] == "completed"
        assert d["cost_tokens"] == 1000
        assert d["output"] == {"chapters": 5}

    def test_node_execution_validation(self):
        """node_id 必填非空"""
        from infra.got.data_structures import NodeExecution, NodeStatus

        with pytest.raises(ValueError, match="node_id"):
            NodeExecution(
                node_id="",
                status=NodeStatus.PENDING,
                started_at=datetime.now(),
            )

    def test_node_execution_duration_ms(self):
        """辅助方法: 计算耗时(毫秒)"""
        from infra.got.data_structures import NodeExecution, NodeStatus

        exec_ = NodeExecution(
            node_id="n1",
            status=NodeStatus.COMPLETED,
            started_at=datetime(2026, 6, 3, 10, 0, 0),
            finished_at=datetime(2026, 6, 3, 10, 0, 5),  # 5 秒
        )
        assert exec_.duration_ms() == 5000

    def test_node_execution_duration_no_finish(self):
        """未完成时 duration 返回 0"""
        from infra.got.data_structures import NodeExecution, NodeStatus

        exec_ = NodeExecution(
            node_id="n1",
            status=NodeStatus.RUNNING,
            started_at=datetime(2026, 6, 3, 10, 0, 0),
            finished_at=None,
        )
        assert exec_.duration_ms() == 0
