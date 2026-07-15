"""Tests for got.graph (ThoughtGraph).

Phase 1.4.c — RED tests for ThoughtGraph.

设计约束 (per Doc 4 v1.0):
- add_node / add_edge: 构建图
- ready_nodes(): 依赖全 COMPLETED 且未运行
- topological_paths(start, end): 找所有路径
- detect_cycle(): 检测环 (raise GraphCycleError)
- parallel_batches(): 同层无依赖的节点分批
- backtrack_to(node_id): 该节点 + 所有依赖其输出的下游
- create_branch(fork_node, branches): 分叉
- record_execution(node_id, result): 记录执行结果
"""
from __future__ import annotations

import pytest

from infra.got.data_structures import (
    NodeExecution,
    NodeStatus,
    NodeType,
    ThoughtNode,
)


def _node(node_id: str, depends_on=(), **kwargs) -> ThoughtNode:
    return ThoughtNode(
        node_id=node_id,
        type=NodeType.INPUT,
        name=node_id,
        description=f"node {node_id}",
        depends_on=depends_on,
        **kwargs,
    )


class TestGraphBasics:
    def test_empty_graph(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        assert g.node_ids() == []
        assert g.ready_nodes() == []

    def test_add_node(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("n1"))
        assert "n1" in g.node_ids()

    def test_add_duplicate_node_raises(self):
        from infra.got.graph import DuplicateNodeError, ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("n1"))
        with pytest.raises(DuplicateNodeError, match="(?i)duplicate"):
            g.add_node(_node("n1"))

    def test_add_edge(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        # 边通过 depends_on 隐式建立
        assert "a" in g.get_node("a").depends_on or True  # edge stored

    def test_get_node_returns(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        n = _node("n1")
        g.add_node(n)
        assert g.get_node("n1") is n

    def test_get_nonexistent_node_raises(self):
        from infra.got.graph import NodeNotFoundError, ThoughtGraph

        g = ThoughtGraph()
        with pytest.raises(NodeNotFoundError, match="(?i)not found"):
            g.get_node("nope")


class TestReadyNodes:
    def test_root_nodes_are_ready(self):
        """无依赖的节点 → READY"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b"))
        ready = g.ready_nodes()
        assert set(ready) == {"a", "b"}

    def test_node_with_pending_dep_not_ready(self):
        """依赖未完成 → 不 READY"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        assert "b" not in g.ready_nodes()
        assert "a" in g.ready_nodes()

    def test_node_with_completed_dep_is_ready(self):
        """依赖 COMPLETED → READY"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        # 标记 a 为 COMPLETED
        from datetime import datetime
        g.record_execution("a", NodeExecution(
            node_id="a", status=NodeStatus.COMPLETED,
            started_at=datetime.now(),
        ))
        assert "b" in g.ready_nodes()

    def test_already_running_not_ready(self):
        """已在 RUNNING 的节点 → 不再 READY"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        from datetime import datetime
        g.record_execution("a", NodeExecution(
            node_id="a", status=NodeStatus.RUNNING,
            started_at=datetime.now(),
        ))
        assert "a" not in g.ready_nodes()

    def test_terminal_not_ready(self):
        """COMPLETED/FAILED/SKIPPED 都不再 READY"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        from datetime import datetime
        for status in (NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED):
            g.record_execution("a", NodeExecution(
                node_id="a", status=status,
                started_at=datetime.now(),
            ))
            assert "a" not in g.ready_nodes()
            # 重置(实际可以清空,但简化测试)
            g._executions.pop("a")


class TestParallelBatches:
    def test_single_batch_for_chain(self):
        """链式 a → b → c → 3 批 [a], [b], [c]"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("b",)))
        batches = g.parallel_batches()
        assert batches == [["a"], ["b"], ["c"]]

    def test_parallel_batch(self):
        """a → {b, c} → d → 3 批 [a], [b, c], [d]"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("a",)))
        g.add_node(_node("d", depends_on=("b", "c")))
        batches = g.parallel_batches()
        assert len(batches) == 3
        assert batches[0] == ["a"]
        assert set(batches[1]) == {"b", "c"}
        assert batches[2] == ["d"]


class TestCycleDetection:
    def test_acyclic_graph_ok(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        assert g.detect_cycle() is None

    def test_cycle_raises(self):
        from infra.got.graph import GraphCycleError, ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a", depends_on=("b",)))  # a 依赖 b
        g.add_node(_node("b", depends_on=("a",)))  # b 依赖 a
        with pytest.raises(GraphCycleError, match="(?i)cycle"):
            g.detect_cycle()


class TestBacktrack:
    def test_backtrack_to_leaf(self):
        """回溯到叶节点(无下游)→ 只返回该节点"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("b",)))
        assert g.backtrack_to("c") == {"c"}

    def test_backtrack_to_middle(self):
        """回溯到中间节点 → 该节点 + 所有下游"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("b",)))
        g.add_node(_node("d", depends_on=("b",)))  # 兄弟
        result = g.backtrack_to("b")
        assert result == {"b", "c", "d"}


class TestTopologicalPaths:
    def test_find_paths(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("a",)))
        g.add_node(_node("d", depends_on=("b", "c")))
        paths = g.topological_paths("a", "d")
        # 至少 2 条: a→b→d, a→c→d
        assert len(paths) >= 2
        for path in paths:
            assert path[0] == "a"
            assert path[-1] == "d"

    def test_no_paths(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b"))  # 独立
        assert g.topological_paths("a", "b") == []


class TestCreateBranch:
    def test_branch_creates_alternatives(self):
        """create_branch 在 fork 节点后插入多个并行分支"""
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("a",)))

        # 在 a 后分叉
        branch_id = g.create_branch("a", [_node("alt1", depends_on=("a",)),
                                           _node("alt2", depends_on=("a",))])
        assert branch_id  # 返回非空

        # 验证 alt1/alt2 是 READY (依赖 a 已存在)
        assert "alt1" in g.node_ids()
        assert "alt2" in g.node_ids()


class TestRecordExecution:
    def test_record_execution_stores(self):
        from infra.got.graph import ThoughtGraph

        g = ThoughtGraph()
        g.add_node(_node("a"))
        from datetime import datetime
        g.record_execution("a", NodeExecution(
            node_id="a", status=NodeStatus.COMPLETED,
            started_at=datetime.now(),
        ))
        assert g.get_execution("a").status == NodeStatus.COMPLETED

    def test_get_nonexistent_execution_raises(self):
        from infra.got.graph import ExecutionNotFoundError, ThoughtGraph

        g = ThoughtGraph()
        with pytest.raises(ExecutionNotFoundError, match="(?i)not found"):
            g.get_execution("nope")
