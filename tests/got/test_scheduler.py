"""Tests for got.scheduler (GoTScheduler).

Phase 1.4.i — RED tests for GoTScheduler.

设计约束 (per Doc 4 v1.0):
- GoTScheduler: 编排执行 ThoughtGraph
- BACKTRACK_SOFT_LIMIT = 2 (软回溯 ≤ 2 次继续)
- BACKTRACK_HARD_LIMIT = 3 (硬回溯 ≥ 3 次抛错,需人工)
- run(start_nodes, max_steps=100) → ExecutionSummary
- _run_node(node_id) → NodeExecution
- _should_backtrack(node, exec_result) → bool
- visualize() → str (mermaid)
- 支持 compute_fn 注入 (测试用 lambda)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

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


# === Helpers ===

@dataclass
class _FakeComputeResult:
    """compute_fn 的返回类型 — scheduler 内部用,非 public"""
    output: Any = None
    cost_tokens: int = 10
    fail: bool = False
    error: Optional[str] = None


def _ok_compute(output: Any = "ok", cost: int = 10) -> Callable:
    """返回成功的 compute_fn"""
    def _fn(node, inputs):
        return _FakeComputeResult(output=output, cost_tokens=cost)
    return _fn


def _fail_compute(error: str = "boom") -> Callable:
    """返回失败的 compute_fn"""
    def _fn(node, inputs):
        return _FakeComputeResult(fail=True, error=error, cost_tokens=5)
    return _fn


def _flaky_compute(attempts_to_pass: int = 2) -> Callable:
    """前 N 次失败,之后成功 — 测试 backtrack + retry"""
    state = {"count": 0}

    def _fn(node, inputs):
        state["count"] += 1
        if state["count"] < attempts_to_pass:
            return _FakeComputeResult(fail=True, error="transient", cost_tokens=3)
        return _FakeComputeResult(output=f"ok_after_{state['count']}", cost_tokens=10)
    return _fn


# === Test classes ===

class TestSchedulerRunBasics:
    def test_run_empty_graph(self):
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        sched = GoTScheduler(graph=g, compute_fn=_ok_compute())
        summary = sched.run(start_nodes=[])
        assert summary.completed == 0
        assert summary.failed == 0

    def test_run_single_root_node(self):
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        sched = GoTScheduler(graph=g, compute_fn=_ok_compute(output="result_a"))
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 1
        assert summary.failed == 0
        exec_ = g.get_execution("a")
        assert exec_.status == NodeStatus.COMPLETED
        assert exec_.output == "result_a"

    def test_run_chain_a_b_c(self):
        """a → b → c 拓扑链:按顺序完成"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("b",)))

        execution_order: list[str] = []

        def compute(node, inputs):
            execution_order.append(node.node_id)
            return _FakeComputeResult(output=f"out_{node.node_id}")

        sched = GoTScheduler(graph=g, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 3
        assert execution_order == ["a", "b", "c"]

    def test_run_parallel_batch(self):
        """a → {b, c} → d 并行分批"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("a",)))
        g.add_node(_node("d", depends_on=("b", "c")))

        sched = GoTScheduler(graph=g, compute_fn=_ok_compute())
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 4
        # a 先,然后 b/c,然后 d
        assert g.get_execution("a").finished_at is not None
        assert g.get_execution("d").finished_at is not None


class TestSchedulerFailure:
    def test_node_failure_marked_failed(self):
        """compute_fn 返回 fail=True → 节点 FAILED"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        sched = GoTScheduler(graph=g, compute_fn=_fail_compute("oops"))
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 0
        assert summary.failed == 1
        exec_ = g.get_execution("a")
        assert exec_.status == NodeStatus.FAILED
        assert exec_.error == "oops"

    def test_downstream_skipped_on_failure(self):
        """a 失败 → b (依赖 a) 应被跳过或失败"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        sched = GoTScheduler(graph=g, compute_fn=_fail_compute())
        summary = sched.run(start_nodes=["a"])
        assert summary.failed == 1
        # b 不应被执行
        assert not g.has_execution("b")


class TestSchedulerBacktrack:
    def test_soft_backtrack_within_limit(self):
        """前 1-2 次失败后成功 → 应在 soft limit 内完成"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        # 第 2 次成功 (1 次 backtrack)
        sched = GoTScheduler(
            graph=g, compute_fn=_flaky_compute(attempts_to_pass=2),
            max_backtracks=3,
        )
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 1
        assert summary.backtrack_count <= 2

    def test_hard_backtrack_limit_raises(self):
        """连续失败超过 hard limit → 抛错"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import (
            GoTScheduler,
            HumanInterventionRequired,
        )

        g = ThoughtGraph()
        g.add_node(_node("a"))
        # 永不成功
        sched = GoTScheduler(
            graph=g, compute_fn=_fail_compute(),
            max_backtracks=3,
        )
        with pytest.raises(HumanInterventionRequired):
            sched.run(start_nodes=["a"])

    def test_backtrack_count_in_summary(self):
        """summary 应记录实际回溯次数"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        sched = GoTScheduler(
            graph=g, compute_fn=_flaky_compute(attempts_to_pass=3),
            max_backtracks=5,
        )
        summary = sched.run(start_nodes=["a"])
        assert summary.backtrack_count >= 1
        assert summary.completed == 1


class TestSchedulerCache:
    def test_cache_used_for_repeat_inputs(self):
        """相同 inputs 第二次运行应使用缓存"""
        from infra.got.cache import ThoughtCache
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        cache = ThoughtCache()

        call_count = [0]

        def compute(node, inputs):
            call_count[0] += 1
            return _FakeComputeResult(output="x")

        sched1 = GoTScheduler(graph=g, cache=cache, compute_fn=compute)
        sched1.run(start_nodes=["a"])
        assert call_count[0] == 1

        # 第二次运行(相同 graph + cache)→ 应该命中缓存
        sched2 = GoTScheduler(graph=g, cache=cache, compute_fn=compute)
        sched2.run(start_nodes=["a"])
        assert call_count[0] == 1  # 仍只调用 1 次


class TestSchedulerExecutionSummary:
    def test_summary_has_basic_fields(self):
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        sched = GoTScheduler(graph=g, compute_fn=_ok_compute(cost=42))
        summary = sched.run(start_nodes=["a"])
        assert hasattr(summary, "completed")
        assert hasattr(summary, "failed")
        assert hasattr(summary, "total_cost_tokens")
        assert hasattr(summary, "backtrack_count")
        assert summary.total_cost_tokens >= 42

    def test_summary_total_cost_aggregates(self):
        """多个节点 cost 应累加"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        sched = GoTScheduler(
            graph=g,
            compute_fn=_ok_compute(cost=100),
        )
        summary = sched.run(start_nodes=["a"])
        assert summary.total_cost_tokens >= 200  # 2 nodes × 100


class TestSchedulerVisualize:
    def test_visualize_returns_mermaid_string(self):
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        sched = GoTScheduler(graph=g, compute_fn=_ok_compute())
        mermaid = sched.visualize()
        assert isinstance(mermaid, str)
        # mermaid 关键标记
        assert "graph" in mermaid.lower() or "flowchart" in mermaid.lower()
        assert "a" in mermaid
        assert "b" in mermaid


class TestSchedulerMaxSteps:
    def test_max_steps_limits_execution(self):
        """max_steps 限制最大执行步数,防止无限循环"""
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import GoTScheduler, MaxStepsExceeded

        g = ThoughtGraph()
        g.add_node(_node("a"))
        g.add_node(_node("b", depends_on=("a",)))
        g.add_node(_node("c", depends_on=("b",)))
        sched = GoTScheduler(graph=g, compute_fn=_ok_compute())
        with pytest.raises(MaxStepsExceeded):
            sched.run(start_nodes=["a"], max_steps=2)
