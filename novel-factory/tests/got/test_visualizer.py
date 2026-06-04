"""Tests for infra.got.visualizer (Phase 4.1 — Enhanced GoT.visualize)

Doc 4 (GoT 适配设计 v1.0) §11 Phase 4:
- render_mermaid: 增强 mermaid 导出,按 NodeStatus 染色 (PENDING=grey, COMPLETED=green, FAILED=red, RUNNING=blue)
- render_summary: 节点统计 (总数/各状态计数/总 token/总耗时)
- render_status_table: 节点执行表 (markdown)
- 所有函数纯函数,接受 graph + executions,不依赖 scheduler
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from infra.got.data_structures import (
    NodeExecution,
    NodeStatus,
    NodeType,
    ThoughtNode,
)
from infra.got.graph import ThoughtGraph
from infra.got.visualizer import (
    NODE_STATUS_CLASS,
    render_mermaid,
    render_status_table,
    render_summary,
)

# === Test fixtures ===

def _node(nid: str, ntype: NodeType = NodeType.GENERATION, deps: tuple[str, ...] = ()) -> ThoughtNode:
    return ThoughtNode(
        node_id=nid,
        type=ntype,
        name=f"Node {nid}",
        description=f"test node {nid}",
        depends_on=deps,
    )


def _exec(
    nid: str,
    status: NodeStatus,
    started: datetime | None = None,
    finished: datetime | None = None,
    cost_tokens: int = 0,
    error: str | None = None,
) -> NodeExecution:
    return NodeExecution(
        node_id=nid,
        status=status,
        started_at=started or datetime(2026, 6, 4, 10, 0, 0),
        finished_at=finished,
        cost_tokens=cost_tokens,
        error=error,
    )


# === TestRenderMermaidBasics ===

class TestRenderMermaidBasics:
    """render_mermaid 基本格式 (含 graph TD, 节点, 边)"""

    def test_includes_graph_td_header(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_mermaid(graph, {})
        assert out.startswith("graph TD")

    def test_includes_all_nodes(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b"))
        out = render_mermaid(graph, {})
        assert 'a["' in out
        assert 'b["' in out

    def test_includes_edges(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b", deps=("a",)))
        out = render_mermaid(graph, {})
        assert "a --> b" in out

    def test_includes_node_label_with_type(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a", ntype=NodeType.GENERATION))
        out = render_mermaid(graph, {})
        assert "GENERATION" in out
        assert "Node a" in out


# === TestRenderMermaidStatusColoring ===

class TestRenderMermaidStatusColoring:
    """按 NodeStatus 应用 mermaid class 染色"""

    def test_completed_node_uses_green_class(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_mermaid(graph, {"a": _exec("a", NodeStatus.COMPLETED)})
        # NODE_STATUS_CLASS[COMPLETED] = "node-completed" 等
        assert NODE_STATUS_CLASS[NodeStatus.COMPLETED] in out
        # 有 class 声明
        assert "classDef" in out or "class " in out

    def test_failed_node_uses_red_class(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_mermaid(graph, {"a": _exec("a", NodeStatus.FAILED, error="boom")})
        assert NODE_STATUS_CLASS[NodeStatus.FAILED] in out

    def test_pending_node_uses_grey_class(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        # 无 execution → PENDING
        out = render_mermaid(graph, {})
        assert NODE_STATUS_CLASS[NodeStatus.PENDING] in out

    def test_running_node_uses_blue_class(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_mermaid(graph, {"a": _exec("a", NodeStatus.RUNNING)})
        assert NODE_STATUS_CLASS[NodeStatus.RUNNING] in out

    def test_skipped_node_uses_grey_class(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_mermaid(graph, {"a": _exec("a", NodeStatus.SKIPPED)})
        assert NODE_STATUS_CLASS[NodeStatus.SKIPPED] in out

    def test_all_status_classes_declared(self):
        """classDef 块涵盖全部 7 状态"""
        graph = ThoughtGraph()
        for status in NodeStatus:
            nid = f"n_{status.value}"
            graph.add_node(_node(nid))
        out = render_mermaid(graph, {nid: _exec(nid, status) for nid, status in [
            (f"n_{s.value}", s) for s in NodeStatus
        ]})
        # 全部 7 个 classDef
        for status in NodeStatus:
            assert NODE_STATUS_CLASS[status] in out


# === TestRenderSummary ===

class TestRenderSummary:
    """render_summary 节点统计"""

    def test_returns_dict_with_total(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b"))
        out = render_summary(graph, {})
        assert out["total"] == 2

    def test_counts_by_status(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b"))
        graph.add_node(_node("c"))
        executions = {
            "a": _exec("a", NodeStatus.COMPLETED),
            "b": _exec("b", NodeStatus.FAILED, error="x"),
        }
        out = render_summary(graph, executions)
        assert out["by_status"][NodeStatus.COMPLETED.value] == 1
        assert out["by_status"][NodeStatus.FAILED.value] == 1
        assert out["by_status"][NodeStatus.PENDING.value] == 1  # c

    def test_total_cost_tokens(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b"))
        executions = {
            "a": _exec("a", NodeStatus.COMPLETED, cost_tokens=100),
            "b": _exec("b", NodeStatus.COMPLETED, cost_tokens=250),
        }
        out = render_summary(graph, executions)
        assert out["total_cost_tokens"] == 350

    def test_completion_ratio(self):
        graph = ThoughtGraph()
        for n in ["a", "b", "c", "d"]:
            graph.add_node(_node(n))
        executions = {
            "a": _exec("a", NodeStatus.COMPLETED),
            "b": _exec("b", NodeStatus.COMPLETED),
            "c": _exec("c", NodeStatus.FAILED, error="x"),
        }
        out = render_summary(graph, executions)
        assert out["completion_ratio"] == pytest.approx(0.5)  # 2/4

    def test_total_duration_ms(self):
        """已完成节点的耗时合计"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        started = datetime(2026, 6, 4, 10, 0, 0)
        executions = {
            "a": _exec(
                "a",
                NodeStatus.COMPLETED,
                started=started,
                finished=started + timedelta(milliseconds=500),
            ),
        }
        out = render_summary(graph, executions)
        assert out["total_duration_ms"] == 500

    def test_empty_graph_returns_zero_stats(self):
        graph = ThoughtGraph()
        out = render_summary(graph, {})
        assert out["total"] == 0
        assert out["total_cost_tokens"] == 0
        assert out["completion_ratio"] == 0.0


# === TestRenderStatusTable ===

class TestRenderStatusTable:
    """render_status_table 节点执行表 (markdown)"""

    def test_returns_markdown_table(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_status_table(graph, {"a": _exec("a", NodeStatus.COMPLETED)})
        # markdown 表头
        assert "|" in out
        assert "node_id" in out or "Node" in out
        assert "status" in out or "Status" in out

    def test_includes_node_id_and_status(self):
        graph = ThoughtGraph()
        graph.add_node(_node("alpha"))
        out = render_status_table(graph, {"alpha": _exec("alpha", NodeStatus.COMPLETED)})
        assert "alpha" in out
        assert "completed" in out

    def test_includes_cost_tokens(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_status_table(
            graph,
            {"a": _exec("a", NodeStatus.COMPLETED, cost_tokens=123)},
        )
        assert "123" in out

    def test_includes_duration_for_completed(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        started = datetime(2026, 6, 4, 10, 0, 0)
        out = render_status_table(graph, {
            "a": _exec("a", NodeStatus.COMPLETED, started=started, finished=started + timedelta(milliseconds=750)),
        })
        # duration 字段
        assert "750" in out or "0.75" in out

    def test_pending_node_shows_pending(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_status_table(graph, {})  # 无 execution
        assert "pending" in out
        assert "a" in out

    def test_failed_node_includes_error(self):
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        out = render_status_table(
            graph,
            {"a": _exec("a", NodeStatus.FAILED, error="upstream error")},
        )
        assert "failed" in out
        assert "upstream error" in out


# === TestVisualizerAcceptsBothInterfaces ===

class TestVisualizerAcceptsBothInterfaces:
    """visualizer 既接受裸 graph,又接受 scheduler(用 _graph / _executions 抽取)"""

    def test_accepts_scheduler_like_object(self):
        """duck-typed 接受任何 ._graph + ._executions 的对象"""
        from infra.got.scheduler import GoTScheduler

        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b", deps=("a",)))
        sched = GoTScheduler(graph)
        # 用 scheduler 作为源(类属性 _graph, _executions)
        # 实际:render_* 接受 (graph, executions) 二元组
        # 但也提供便利包装 render_from_scheduler
        from infra.got.visualizer import render_mermaid_from_scheduler

        out = render_mermaid_from_scheduler(sched)
        assert "graph TD" in out
        assert "a" in out
        assert "b" in out

    def test_summary_from_scheduler(self):
        from infra.got.scheduler import GoTScheduler
        from infra.got.visualizer import render_summary_from_scheduler

        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        sched = GoTScheduler(graph)
        out = render_summary_from_scheduler(sched)
        assert out["total"] == 1
