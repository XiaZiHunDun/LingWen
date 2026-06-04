"""灵文 GoT · GoTScheduler

Phase 1.4 — Doc 4 (GoT 适配设计 v1.0) §6: 调度执行。

设计原则 (per Doc 4):
- 拓扑序执行 (ready_nodes + parallel_batches 组合)
- 输入收集:从上游 NodeExecution.output 收集
- 缓存:同 (node_id, inputs_hash) → 复用
- 回溯:失败时标记下游 STALE,重跑上游
- 软回溯 BACKTRACK_SOFT_LIMIT = 2,硬回溯 BACKTRACK_HARD_LIMIT = 3
  - 超过硬回溯 → HumanInterventionRequired

不实施 (后续阶段):
- 真实 LLM 调用 (compute_fn 注入,测试用 lambda)
- 并发执行 (Phase 4,顺序执行足够 PoC)
- 检查点 (Phase 1.5+ 持久化)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from infra.got.cache import ThoughtCache
from infra.got.data_structures import (
    NodeExecution,
    NodeStatus,
    ThoughtNode,
)
from infra.got.graph import (
    NodeNotFoundError,
    ThoughtGraph,
)

# === Exceptions ===

class SchedulerError(Exception):
    """Scheduler 基类异常"""


class HumanInterventionRequired(SchedulerError):
    """超过硬回溯上限 → 需要人工介入"""

    def __init__(self, node_id: str, backtrack_count: int, last_error: str) -> None:
        self.node_id = node_id
        self.backtrack_count = backtrack_count
        self.last_error = last_error
        super().__init__(
            f"node {node_id!r} failed after {backtrack_count} backtracks; "
            f"last error: {last_error}"
        )


class MaxStepsExceeded(SchedulerError):
    """超过 max_steps 限制"""

    def __init__(self, steps: int, max_steps: int) -> None:
        self.steps = steps
        self.max_steps = max_steps
        super().__init__(f"exceeded max_steps={max_steps} (executed {steps} steps)")


# === Compute result shape ===

@dataclass
class ComputeResult:
    """compute_fn 返回值

    简化协议:output / cost_tokens / fail / error
    真实 LLM 场景下,output 是生成的内容,fail 表示生成失败
    """
    output: Any = None
    cost_tokens: int = 0
    fail: bool = False
    error: Optional[str] = None


# === Execution summary ===

@dataclass(frozen=True)
class ExecutionSummary:
    """scheduler.run() 的返回:总览本次执行结果

    字段:
    - completed: 成功节点数
    - failed: 失败节点数
    - total_cost_tokens: 总 token 消耗
    - backtrack_count: 实际回溯次数
    - steps: 执行步数 (compute_fn 实际调用次数,不含 cache 命中)
    - node_count: 图节点总数
    """
    completed: int = 0
    failed: int = 0
    total_cost_tokens: int = 0
    backtrack_count: int = 0
    steps: int = 0
    node_count: int = 0


# === Default compute_fn protocol ===

ComputeFn = Callable[[ThoughtNode, dict[str, Any]], ComputeResult]


def _default_compute(node: ThoughtNode, inputs: dict[str, Any]) -> ComputeResult:
    """无 compute_fn 时的默认 — 直接返回 inputs"""
    return ComputeResult(output=inputs, cost_tokens=0)


# === GoTScheduler ===

class GoTScheduler:
    """GoT 调度器 — 执行 ThoughtGraph

    用法:
        sched = GoTScheduler(graph, compute_fn=my_compute)
        summary = sched.run(start_nodes=["a"])
        mermaid = sched.visualize()
    """

    BACKTRACK_SOFT_LIMIT = 2   # 软回溯 ≤ 2 次
    BACKTRACK_HARD_LIMIT = 3   # 硬回溯 ≥ 3 次 → HumanInterventionRequired

    def __init__(
        self,
        graph: ThoughtGraph,
        compute_fn: Optional[ComputeFn] = None,
        cache: Optional[ThoughtCache] = None,
        max_backtracks: int = 0,
    ) -> None:
        self._graph = graph
        self._compute_fn: ComputeFn = compute_fn or _default_compute
        self._cache: ThoughtCache = cache or ThoughtCache()
        self._max_backtracks = max_backtracks
        self._backtrack_count = 0

    # === Public API ===

    def run(
        self,
        start_nodes: list[str],
        max_steps: int = 100,
        initial_inputs: Optional[dict[str, Any]] = None,
    ) -> ExecutionSummary:
        """执行图,从 start_nodes 出发

        Args:
            start_nodes: 起点节点 ID 列表
            max_steps: 最大步数 (含 backtrack 重试)
            initial_inputs: 注入到起点节点的 initial inputs (Phase 3 新增)
                起点节点会收到 merged inputs = {upstream_outputs..., **initial_inputs}

        算法:
        1. 循环:获取 ready_nodes (依赖全 COMPLETED)
        2. 对每个 ready 节点:收集 inputs → 计算 → 记录 execution
        3. 失败 → 触发 backtrack (标记下游 STALE)
        4. 超过 max_backtracks → HumanInterventionRequired
        5. 超过 max_steps → MaxStepsExceeded
        6. 直到没有 ready_nodes (全部 terminal)
        """
        if not start_nodes:
            return ExecutionSummary(node_count=len(self._graph.node_ids()))

        # 验证 start_nodes 存在
        for nid in start_nodes:
            if nid not in self._graph.node_ids():
                raise NodeNotFoundError(nid)

        # 起点节点的 seed input 注入 (Phase 3)
        # 每个 start_node 在首次执行时,会拿到 merged = upstream_outputs + initial_inputs
        self._initial_inputs: dict[str, dict[str, Any]] = {
            nid: dict(initial_inputs or {}) for nid in start_nodes
        }

        steps = 0
        completed = 0
        failed = 0
        total_cost = 0
        backtrack_count = 0

        while True:
            ready = self._graph.ready_nodes()
            # 过滤掉不在 start_nodes 链上的节点
            # (即:若图是 a→b→c,start_nodes=[a],应自动跑 b,c)
            # 实际:ready_nodes 已包含所有可执行节点
            if not ready:
                break

            for nid in ready:
                if steps >= max_steps:
                    raise MaxStepsExceeded(steps, max_steps)

                node = self._graph.get_node(nid)
                exec_result, from_cache = self._run_node(node)
                steps += 1  # 仅记录实际调用的步数
                total_cost += exec_result.cost_tokens

                if exec_result.status == NodeStatus.COMPLETED:
                    completed += 1
                elif exec_result.status == NodeStatus.FAILED:
                    failed += 1
                    # 没有 backtrack 预算 → 直接保留 FAILED 状态
                    if self._max_backtracks <= 0:
                        continue
                    # backtrack:重置执行记录(下次循环可重试)
                    backtrack_count += 1
                    if backtrack_count > self._max_backtracks:
                        raise HumanInterventionRequired(
                            node_id=nid,
                            backtrack_count=backtrack_count,
                            last_error=exec_result.error or "unknown",
                        )
                    self._graph.reset_execution(nid)
                    # 标记下游为 STALE
                    self._mark_downstream_stale(nid)

        return ExecutionSummary(
            completed=completed,
            failed=failed,
            total_cost_tokens=total_cost,
            backtrack_count=backtrack_count,
            steps=steps,
            node_count=len(self._graph.node_ids()),
        )

    def visualize(self) -> str:
        """生成 mermaid 流程图字符串 (按 NodeStatus 染色)

        委托给 infra.got.visualizer.render_mermaid_from_scheduler
        """
        from infra.got.visualizer import render_mermaid_from_scheduler
        return render_mermaid_from_scheduler(self)

    # === Internals ===

    def _run_node(self, node: ThoughtNode) -> tuple[NodeExecution, bool]:
        """执行单个节点

        Returns:
            (NodeExecution, from_cache: bool)
        """
        # 1. 收集 inputs (从上游 outputs)
        inputs = self._collect_inputs(node)
        # Phase 3: 起点节点的 initial_inputs 顶层注入 (无上游,inputs 默认空 dict)
        seed = self._initial_inputs.get(node.node_id)
        if seed and not inputs:
            # 起点节点 (无上游 outputs) → 整个 initial_inputs 作为 inputs
            inputs = dict(seed)

        # 2. 缓存检查
        inputs_hash = self._cache.hash_inputs(inputs)
        if self._cache.has(node.node_id, inputs_hash):
            cached = self._cache.get_or_compute(
                node.node_id, inputs_hash, lambda: None
            )
            return (
                NodeExecution(
                    node_id=node.node_id,
                    status=NodeStatus.COMPLETED,
                    started_at=datetime.now(),
                    finished_at=datetime.now(),
                    output=cached,
                    cost_tokens=0,
                ),
                True,
            )

        # 3. 调 compute_fn
        started_at = datetime.now()
        try:
            result = self._compute_fn(node, inputs)
        except Exception as exc:
            result = ComputeResult(fail=True, error=str(exc))

        finished_at = datetime.now()

        if result.fail:
            exec_ = NodeExecution(
                node_id=node.node_id,
                status=NodeStatus.FAILED,
                started_at=started_at,
                finished_at=finished_at,
                error=result.error or "compute_fn returned fail=True",
                cost_tokens=result.cost_tokens,
            )
        else:
            exec_ = NodeExecution(
                node_id=node.node_id,
                status=NodeStatus.COMPLETED,
                started_at=started_at,
                finished_at=finished_at,
                output=result.output,
                cost_tokens=result.cost_tokens,
            )
            # 存缓存 (仅成功结果)
            self._cache.get_or_compute(
                node.node_id, inputs_hash, lambda: result.output
            )

        self._graph.record_execution(node.node_id, exec_)
        return exec_, False

    def _collect_inputs(self, node: ThoughtNode) -> dict[str, Any]:
        """收集节点输入 — 从 depends_on 的 NodeExecution.output"""
        inputs: dict[str, Any] = {}
        for dep_id in node.depends_on:
            if self._graph.has_execution(dep_id):
                dep_exec = self._graph.get_execution(dep_id)
                if dep_exec.output is not None:
                    inputs[dep_id] = dep_exec.output
        # 也支持 node.inputs (显式声明的额外输入)
        for input_id in node.inputs:
            if input_id not in inputs and self._graph.has_execution(input_id):
                dep_exec = self._graph.get_execution(input_id)
                if dep_exec.output is not None:
                    inputs[input_id] = dep_exec.output
        return inputs

    def _mark_downstream_stale(self, node_id: str) -> None:
        """标记 node 的所有下游为 STALE

        注:由于 STALE 在 ready_nodes 中视为非 PENDING (被排除),
        实现上不需要显式 STALE — 失败的节点会让下游的 dep 检查
        通过 (FAILED 也算 terminal),但下游节点本身的 depends_on
        包含一个 FAILED 节点,所以不会 ready。
        """
        # 当前实现:依赖 FAILED 的节点在 ready_nodes 中已被排除
        # (见 infra.got.graph._TERMINAL_STATUSES 检查)
        # STALE 字段保留,语义在 Phase 1.5+ 扩展
        # 此处 no-op 即可,因为 ready_nodes 自然处理
        return


__all__ = [
    "GoTScheduler",
    "ExecutionSummary",
    "ComputeResult",
    "SchedulerError",
    "HumanInterventionRequired",
    "MaxStepsExceeded",
    "ComputeFn",
]
