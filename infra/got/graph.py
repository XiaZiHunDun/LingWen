"""灵文 GoT · ThoughtGraph

Phase 1.4 — Doc 4 (GoT 适配设计 v1.0) §3: ThoughtGraph 4 capabilities。

4 capabilities:
- Capability 1 (拓扑): ready_nodes, topological_paths, detect_cycle
- Capability 2 (并行): parallel_batches
- Capability 3 (回溯): backtrack_to
- Capability 4 (分叉): create_branch

不实施 (后续阶段):
- conflicts_with 具体冲突解决策略 (字段保留,语义 TBD)
- 真实 LLM 调用 (1.4.j scheduler 负责)
"""
from __future__ import annotations

import uuid
from typing import Optional

from infra.got.data_structures import (
    NodeExecution,
    NodeStatus,
    ThoughtNode,
)


class GraphError(Exception):
    """Graph 基类异常"""


class DuplicateNodeError(GraphError):
    """添加重复 node_id"""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"duplicate node_id: {node_id!r}")


class NodeNotFoundError(GraphError):
    """节点未找到"""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"node not found: {node_id!r}")


class ExecutionNotFoundError(GraphError):
    """执行记录未找到"""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"execution not found: {node_id!r}")


class GraphCycleError(GraphError):
    """检测到环"""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"cycle detected: {' -> '.join(cycle)}")


# 终态 — 不再 READY
_TERMINAL_STATUSES = {
    NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED,
}


class ThoughtGraph:
    """GoT 图 — 4 capabilities

    用法:
        g = ThoughtGraph()
        g.add_node(node1)
        g.add_node(node2, depends_on=("node1",))
        g.detect_cycle()  # 检查环
        g.parallel_batches()  # [[node1], [node2]]
    """

    def __init__(self) -> None:
        self._nodes: dict[str, ThoughtNode] = {}
        self._executions: dict[str, NodeExecution] = {}

    # === Capability 0: CRUD ===

    def add_node(self, node: ThoughtNode) -> None:
        """添加节点"""
        if node.node_id in self._nodes:
            raise DuplicateNodeError(node.node_id)
        self._nodes[node.node_id] = node

    def add_edge(self, src: str, dst: str) -> None:
        """添加边 (src → dst) — 更新 dst.depends_on

        注: 大多数情况用 depends_on 隐式建边,add_edge 用于显式追加
        """
        if src not in self._nodes:
            raise NodeNotFoundError(src)
        if dst not in self._nodes:
            raise NodeNotFoundError(dst)
        src_node = self._nodes[src]
        if dst not in src_node.outputs:
            new_outputs = src_node.outputs + (dst,)
            self._nodes[src] = ThoughtNode(
                **{**src_node.to_dict(), "outputs": new_outputs}
            )

    def get_node(self, node_id: str) -> ThoughtNode:
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return self._nodes[node_id]

    def node_ids(self) -> list[str]:
        return list(self._nodes.keys())

    def record_execution(self, node_id: str, result: NodeExecution) -> None:
        """记录节点执行结果"""
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        self._executions[node_id] = result

    def get_execution(self, node_id: str) -> NodeExecution:
        if node_id not in self._executions:
            raise ExecutionNotFoundError(node_id)
        return self._executions[node_id]

    def has_execution(self, node_id: str) -> bool:
        return node_id in self._executions

    def all_executions(self) -> dict[str, NodeExecution]:
        """返回全部执行记录的浅拷贝 (供可视化/统计用)"""
        return dict(self._executions)

    def reset_execution(self, node_id: str) -> None:
        """重置节点执行记录(回溯时用)

        删除执行记录后,节点会重新出现在 ready_nodes 中(若依赖满足)。
        未找到节点 → 抛 NodeNotFoundError
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        self._executions.pop(node_id, None)

    # === Capability 1: 拓扑 ===

    def ready_nodes(self) -> list[str]:
        """依赖全 COMPLETED + 未在终态/RUNNING 的节点"""
        ready: list[str] = []
        for nid, node in self._nodes.items():
            # 已记录执行且非 PENDING 状态 → 不再 ready
            if nid in self._executions:
                exec_ = self._executions[nid]
                if exec_.status != NodeStatus.PENDING:
                    continue
            # 检查依赖
            all_deps_completed = True
            for dep in node.depends_on:
                if dep not in self._executions:
                    all_deps_completed = False
                    break
                if self._executions[dep].status not in _TERMINAL_STATUSES:
                    all_deps_completed = False
                    break
                # FAILED 也算 terminal,不算 completed
                if self._executions[dep].status == NodeStatus.FAILED:
                    all_deps_completed = False
                    break
            if all_deps_completed:
                ready.append(nid)
        return ready

    def topological_paths(
        self, start: str, end: str, _seen: Optional[set[str]] = None
    ) -> list[list[str]]:
        """所有从 start 到 end 的拓扑路径

        DFS 枚举所有路径,visited 集合防止环
        """
        if _seen is None:
            _seen = set()
        if start == end:
            return [[start]]
        if start in _seen:
            return []
        if start not in self._nodes:
            return []
        _seen = _seen | {start}
        paths: list[list[str]] = []
        node = self._nodes[start]
        # 找下游 (从 outputs)
        for out in node.outputs:
            for path in self.topological_paths(out, end, _seen):
                paths.append([start] + path)
        # 兜底: 如果 outputs 为空,从 depends_on 反向找 (即 next 是依赖自己的)
        if not node.outputs:
            for nid, other in self._nodes.items():
                if start in other.depends_on and nid not in _seen:
                    for path in self.topological_paths(nid, end, _seen):
                        paths.append([start] + path)
        return paths

    def detect_cycle(self) -> Optional[list[str]]:
        """DFS 检测环 — 找到环返回环路径,否则 None

        抛 GraphCycleError if cycle found
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self._nodes}
        parent: dict[str, Optional[str]] = {nid: None for nid in self._nodes}

        def dfs(start: str) -> Optional[list[str]]:
            stack = [(start, iter(self._downstream(start)))]
            color[start] = GRAY
            while stack:
                node, children = stack[-1]
                try:
                    child = next(children)
                    if color[child] == GRAY:
                        # 找到环
                        cycle = [child, node]
                        p = parent[node]
                        while p is not None and p != child:
                            cycle.append(p)
                            p = parent[p]
                        cycle.append(child)
                        return list(reversed(cycle))
                    if color[child] == WHITE:
                        color[child] = GRAY
                        parent[child] = node
                        stack.append((child, iter(self._downstream(child))))
                except StopIteration:
                    color[node] = BLACK
                    stack.pop()
            return None

        for nid in self._nodes:
            if color[nid] == WHITE:
                cycle = dfs(nid)
                if cycle:
                    raise GraphCycleError(cycle)
        return None

    def _downstream(self, node_id: str) -> list[str]:
        """节点的下游 (谁依赖了它)"""
        return [
            nid for nid, node in self._nodes.items()
            if node_id in node.depends_on
        ]

    # === Capability 2: 并行 ===

    def parallel_batches(self) -> list[list[str]]:
        """同层无依赖的节点分批 (拓扑序)

        算法:
        - 计算每个节点的"入度" (被多少上游依赖)
        - 入度 0 的节点 → 第 1 批
        - 移除后,新的入度 0 → 第 2 批
        - 直到所有节点都分批
        """
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        # in_degree[nid] = 多少上游 (即 depends_on 长度)
        for nid, node in self._nodes.items():
            in_degree[nid] = len(node.depends_on)

        # 反向图: 上游 → 下游
        downstream_map: dict[str, list[str]] = {nid: [] for nid in self._nodes}
        for nid, node in self._nodes.items():
            for dep in node.depends_on:
                if dep in downstream_map:
                    downstream_map[dep].append(nid)

        batches: list[list[str]] = []
        remaining = set(self._nodes.keys())

        while remaining:
            # 当前 batch: in_degree == 0 的节点
            batch = [nid for nid in remaining if in_degree.get(nid, 0) == 0]
            if not batch:
                # 应该由 detect_cycle 提前检测
                raise GraphCycleError(list(remaining))
            batches.append(sorted(batch))  # 排序保证确定性
            # 更新 in_degree
            for nid in batch:
                remaining.discard(nid)
                for downstream in downstream_map.get(nid, []):
                    in_degree[downstream] -= 1

        return batches

    # === Capability 3: 回溯 ===

    def backtrack_to(self, node_id: str) -> set[str]:
        """回溯到 node_id — 返回该节点 + 所有依赖其输出的下游节点

        等价: 找所有从 node_id 可达的节点 (传递闭包)
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)

        result: set[str] = {node_id}
        stack = [node_id]
        while stack:
            current = stack.pop()
            for downstream in self._downstream(current):
                if downstream not in result:
                    result.add(downstream)
                    stack.append(downstream)
        return result

    # === Capability 4: 分叉 ===

    def create_branch(
        self, fork_node: str, branches: list[ThoughtNode]
    ) -> str:
        """在 fork_node 后分叉,创建多个并行分支

        每个 branch 节点都被加入图,depends_on 包含 fork_node。
        返回分叉 ID (uuid 短串)。
        """
        if fork_node not in self._nodes:
            raise NodeNotFoundError(fork_node)

        for branch in branches:
            # 验证依赖包含 fork_node
            if fork_node not in branch.depends_on:
                # 强制注入
                self.add_node(ThoughtNode(
                    node_id=branch.node_id,
                    type=branch.type,
                    name=branch.name,
                    description=branch.description,
                    depends_on=(fork_node,) + branch.depends_on,
                    inputs=branch.inputs,
                    outputs=branch.outputs,
                    parallel_with=branch.parallel_with,
                    conflicts_with=branch.conflicts_with,
                    prompt_scenario=branch.prompt_scenario,
                    output_schema=branch.output_schema,
                    token_budget=branch.token_budget,
                    timeout_s=branch.timeout_s,
                ))
            else:
                self.add_node(branch)

        return uuid.uuid4().hex[:8]


__all__ = [
    "ThoughtGraph",
    "GraphError",
    "DuplicateNodeError",
    "NodeNotFoundError",
    "ExecutionNotFoundError",
    "GraphCycleError",
]
