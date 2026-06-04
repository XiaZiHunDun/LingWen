"""infra/got/visualizer.py — 增强 GoT 可视化

Doc 4 (GoT 适配设计 v1.0) §11 Phase 4: 可视化增强

核心 API (纯函数,无 side effect):
- render_mermaid(graph, executions): mermaid + NodeStatus 染色
- render_summary(graph, executions): 节点统计 dict
- render_status_table(graph, executions): markdown 节点表
- render_*_from_scheduler(scheduler): duck-typed 调度器便利包装

设计原则:
- 纯函数:接受 graph + executions,不依赖 scheduler
- 复用现有 GoTScheduler.visualize() 接口 (mermaid 字符串) — 扩展而非替换
- 7 状态全染色: COMPLETED=绿, FAILED=红, RUNNING=蓝, PENDING=灰, ...
- 不实施 (后续阶段):
  - 真实执行时间轴 (Gantt chart) — Phase 4.5+
  - 决策点高亮 (DECISION 类型节点) — Phase 4.2 联合
  - mermaid 主题切换 (forest/dark) — 后续样式
"""
from __future__ import annotations

from typing import Any, Mapping

from infra.got.data_structures import NodeExecution, NodeStatus
from infra.got.graph import ThoughtGraph

# === Status → Mermaid class 映射 ===

NODE_STATUS_CLASS: dict[NodeStatus, str] = {
    NodeStatus.PENDING: "node-pending",
    NodeStatus.READY: "node-ready",
    NodeStatus.RUNNING: "node-running",
    NodeStatus.COMPLETED: "node-completed",
    NodeStatus.FAILED: "node-failed",
    NodeStatus.SKIPPED: "node-skipped",
    NodeStatus.STALE: "node-stale",
}

# Mermaid classDef 样式 (颜色 + 描边)
_CLASSDEF: dict[str, str] = {
    "node-pending": "fill:#cccccc,stroke:#666666,color:#000000",
    "node-ready": "fill:#e3f2fd,stroke:#90caf9,color:#000000",
    "node-running": "fill:#bbdefb,stroke:#1976d2,color:#000000",
    "node-completed": "fill:#c8e6c9,stroke:#388e3c,color:#000000",
    "node-failed": "fill:#ffcdd2,stroke:#c62828,color:#000000",
    "node-skipped": "fill:#eeeeee,stroke:#9e9e9e,color:#666666",
    "node-stale": "fill:#ffe0b2,stroke:#ef6c00,color:#000000",
}


# === Helpers ===

def _node_status(executions: Mapping[str, NodeExecution], nid: str) -> NodeStatus:
    """节点的当前状态 (无 execution → PENDING)"""
    if nid in executions:
        return executions[nid].status
    return NodeStatus.PENDING


# === Core renderers ===

def render_mermaid(
    graph: ThoughtGraph,
    executions: Mapping[str, NodeExecution],
    *,
    include_classdef: bool = True,
) -> str:
    """生成 mermaid 流程图,按 NodeStatus 给节点染色

    Args:
        graph: ThoughtGraph (含 nodes + depends_on 边)
        executions: dict[node_id, NodeExecution],缺失节点视作 PENDING
        include_classdef: 是否输出 classDef 样式块 (默认 True)

    Returns:
        mermaid 字符串
    """
    lines: list[str] = ["graph TD"]

    # 1. 节点声明
    for nid in graph.node_ids():
        node = graph.get_node(nid)
        label = f"{node.type.value.upper()}: {node.name}" if node.name else nid
        # 转义 mermaid 敏感字符 (引号)
        safe_label = label.replace('"', "'")
        lines.append(f'    {nid}["{safe_label}"]')

    # 2. 边
    for nid in graph.node_ids():
        node = graph.get_node(nid)
        for dep in node.depends_on:
            lines.append(f"    {dep} --> {nid}")

    # 3. 样式声明 (可选)
    if include_classdef:
        for cls, style in _CLASSDEF.items():
            lines.append(f"    classDef {cls} {style}")

    # 4. 节点 → class 映射
    for nid in graph.node_ids():
        status = _node_status(executions, nid)
        cls = NODE_STATUS_CLASS[status]
        lines.append(f"    class {nid} {cls}")

    return "\n".join(lines)


def render_summary(
    graph: ThoughtGraph,
    executions: Mapping[str, NodeExecution],
) -> dict[str, Any]:
    """生成执行统计 dict

    Returns:
        {
            "total": int,            # 节点总数
            "by_status": dict[status_value, count],  # 各状态计数
            "completed": int,        # COMPLETED 计数
            "failed": int,           # FAILED 计数
            "pending": int,          # PENDING 计数
            "total_cost_tokens": int,
            "total_duration_ms": int,  # 全部已完成节点的耗时合计
            "completion_ratio": float,  # completed / total
        }
    """
    by_status: dict[str, int] = {s.value: 0 for s in NodeStatus}
    total_cost = 0
    total_duration = 0

    for nid in graph.node_ids():
        status = _node_status(executions, nid)
        by_status[status.value] += 1
        ex = executions.get(nid)
        if ex is not None:
            total_cost += ex.cost_tokens
            if ex.finished_at is not None and ex.started_at is not None:
                delta_ms = int((ex.finished_at - ex.started_at).total_seconds() * 1000)
                total_duration += delta_ms

    total = len(graph.node_ids())
    completed = by_status[NodeStatus.COMPLETED.value]
    return {
        "total": total,
        "by_status": by_status,
        "completed": completed,
        "failed": by_status[NodeStatus.FAILED.value],
        "pending": by_status[NodeStatus.PENDING.value],
        "total_cost_tokens": total_cost,
        "total_duration_ms": total_duration,
        "completion_ratio": (completed / total) if total else 0.0,
    }


def render_status_table(
    graph: ThoughtGraph,
    executions: Mapping[str, NodeExecution],
) -> str:
    """生成 markdown 状态表 (便于嵌入文档 / PR)

    列: node_id | type | status | duration_ms | cost_tokens | error
    """
    lines = [
        "| node_id | type | status | duration_ms | cost_tokens | error |",
        "|---------|------|--------|-------------|-------------|-------|",
    ]
    for nid in graph.node_ids():
        node = graph.get_node(nid)
        ex = executions.get(nid)
        if ex is None:
            lines.append(f"| {nid} | {node.type.value} | pending | - | 0 | - |")
            continue
        duration = ex.duration_ms() if ex.finished_at is not None else "-"
        cost = ex.cost_tokens
        err = ex.error or "-"
        lines.append(
            f"| {nid} | {node.type.value} | {ex.status.value} | {duration} | {cost} | {err} |"
        )
    return "\n".join(lines)


# === Scheduler 便利包装 (duck-typed) ===

def render_mermaid_from_scheduler(scheduler: Any) -> str:
    """从 GoTScheduler 实例直接渲染 (要求 ._graph 属性)"""
    graph = scheduler._graph
    return render_mermaid(graph, graph.all_executions())


def render_summary_from_scheduler(scheduler: Any) -> dict[str, Any]:
    graph = scheduler._graph
    return render_summary(graph, graph.all_executions())


def render_status_table_from_scheduler(scheduler: Any) -> str:
    graph = scheduler._graph
    return render_status_table(graph, graph.all_executions())


__all__ = [
    "NODE_STATUS_CLASS",
    "render_mermaid",
    "render_summary",
    "render_status_table",
    "render_mermaid_from_scheduler",
    "render_summary_from_scheduler",
    "render_status_table_from_scheduler",
]
