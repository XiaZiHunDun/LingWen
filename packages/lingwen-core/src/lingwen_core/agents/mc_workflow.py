"""MasterController 工作流相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的工作流相关方法。

Phase 25.9 (human_review 全流水线重构):
run_workflow / resume_workflow / resolve_decision / list_pending_decisions
重写为对齐真实 GoT API 的实现:
- 走 got_bridge.build_got_scheduler(master, workflow_name, base_dir, max_backtracks)
  工厂 (真 GoTScheduler 签名是 (graph, compute_fn, cache, max_backtracks),
  不是 workflow_name=...)
- scheduler.run(start_nodes, initial_inputs) 返 ExecutionSummary (不是 dict)
- scheduler.resume(decision_node_id, option, resolved_by) 返 NodeExecution,
  需再 run() 一次才会推进下游节点
- HumanDecisionQueue 的方法是 pending() / resolve(id, option, resolved_by=...)
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class WorkflowMixin:
    """工作流相关方法"""

    def advance_step(self, target_step: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """推进工作流步骤"""
        return self._orchestrator.advance_step(target_step, context)

    def dispatch_task(
        self,
        task_name: str,
        agent: str,
        context: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """分发任务"""
        return self._orchestrator.dispatch_task(task_name, agent, context, priority)

    def verify_task(self, task_id: str, result: Dict[str, Any]) -> Tuple[bool, str]:
        """验证任务完成"""
        return self._orchestrator.verify_task(task_id, result)

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return self._orchestrator.get_workflow_status()

    def run_workflow(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """用 GoT 调度器运行工作流 (Doc 4 Phase 3 + 4)

        Args:
            workflow_name: workflow YAML 名 (如 'novel_writing')
            start_nodes: 起点节点 ID 列表 (None = 自动找无依赖节点)
            initial_inputs: 起点节点的 seed inputs (e.g. chapter_num=1)
            cost_budget_usd: Phase 8.8 cost budget 阈值 (USD, None=unlimited).
                _current_budget_usd 单 run 期间有效, finally 必 reset 防跨 run leak.
            max_backtracks: 软回溯预算 (默认 2)
            base_dir: workflow YAML 目录 (None = 默认 infra/got/workflows/)

        Returns:
            {
                "summary": ExecutionSummary,
                "graph": ThoughtGraph,
                "executions": dict[node_id, NodeExecution],
                "pending_decisions": list[dict] (HumanDecision.to_dict()),
                "incremental_backfill": BackfillStats | None,
                "memory_context": dict | None,
            }

        Raises:
            WorkflowError: 加载失败
            HumanInterventionRequired: 回溯超限
            MaxStepsExceeded: 步数超限
        """
        # Phase 8.8: 先写 budget, AgentComputeFn 才读得到
        self._current_budget_usd = cost_budget_usd
        # Phase 8.12: run_id (uuid4 hex) + 持久化到 budget_service
        run_id = uuid.uuid4().hex
        self._current_run_id = run_id
        # getattr 兜底 __new__ 构造的 test stub (没走 __init__, 没这些属性)
        budget_service = getattr(self, "budget_service", None)
        if budget_service is not None and cost_budget_usd is not None:
            budget_service.set(scope="run", usd=cost_budget_usd, run_id=run_id)
        try:
            # 延迟 import: 避免 got ↔ agent_system 循环, 且让测试可 monkeypatch
            # got_bridge.build_got_scheduler (call time 才解析模块属性)
            from .got_bridge import build_got_scheduler

            scheduler, graph = build_got_scheduler(
                master=self,
                workflow_name=workflow_name,
                base_dir=base_dir,
                max_backtracks=max_backtracks,
            )

            # 默认起点: 无依赖的节点
            if start_nodes is None:
                start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]

            # Phase 9.70 F62: 可选 MemoryGateway RAG context
            seed_inputs: Dict[str, Any] = dict(initial_inputs or {})
            memory_context = self._maybe_memory_context(workflow_name, seed_inputs)
            if memory_context is not None:
                seed_inputs.setdefault("memory_context", memory_context)

            # Phase 4.3: 扫描 DECISION 节点 → 创建 HumanDecision (须先于 run)
            pending_decisions = self._harvest_decision_specs(graph, initial_inputs=seed_inputs)

            # emit_chapter 等节点在 scheduler.run 期间读 chapter_num — 须先于 run 写入
            self._last_initial_inputs = dict(seed_inputs)
            self._last_workflow_name = workflow_name
            self._last_start_nodes = list(start_nodes)

            summary = scheduler.run(start_nodes=start_nodes, initial_inputs=seed_inputs)

            executions = self._collect_executions(graph)

            # 缓存活跃工作流状态 (Phase 5) — resume_workflow() / dashboard 用它
            self._last_scheduler = scheduler
            self._last_graph = graph

            incremental_backfill = self._maybe_incremental_backfill(
                workflow_name=workflow_name,
                initial_inputs=seed_inputs,
                executions=executions,
                summary=summary,
            )
            self._last_incremental_backfill = incremental_backfill
            self._last_memory_context = memory_context

            return {
                "summary": summary,
                "graph": graph,
                "executions": executions,
                "pending_decisions": pending_decisions,
                "incremental_backfill": incremental_backfill,
                "memory_context": memory_context,
            }
        finally:
            # Phase 8.8 / 8.12: reset 防跨 run leak (即使 raise 也走 finally)
            self._current_budget_usd = None
            self._current_run_id = None

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Any:
        """解决决策 (委托 HumanDecisionQueue.resolve)

        Returns:
            更新后的 HumanDecision

        Raises:
            RuntimeError: decision queue 未初始化
            KeyError / ValueError: 见 HumanDecisionQueue.resolve
        """
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        # Phase 6.5: with_lock() 拿 fcntl 排他锁 + 重读 + 写回,
        # 防 CLI 与 dashboard 跨进程写 decisions.json 的 race condition
        with queue.with_lock():
            resolved = queue.resolve(decision_id, option, resolved_by=resolved_by)
        return resolved

    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Dict[str, Any]:
        """恢复 DECISION 暂停的工作流 (Phase 5) — 三步合一

        1. 标记 HumanDecision 为 RESOLVED (PENDING → RESOLVED)
        2. 把对应 GoT DECISION 节点 WAITING → COMPLETED, 写入 option
        3. 重新调 scheduler.run() 让下游节点继续执行

        Returns:
            同 run_workflow() 结构 + resolved_decision (HumanDecision 对象)

        Raises:
            RuntimeError: 无活跃工作流 (从未 run_workflow) / queue 未初始化
            KeyError: decision_id 不存在
            ValueError: 决策已 RESOLVED / option 不在 options / node 非 WAITING
        """
        # 1. 检查有活跃工作流
        scheduler = getattr(self, "_last_scheduler", None)
        graph = getattr(self, "_last_graph", None)
        if scheduler is None or graph is None:
            raise RuntimeError("no active workflow; call run_workflow() first before resume_workflow()")

        # 2. 查决策 → 拿 node_id (KeyError if missing)
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        decision = queue.get(decision_id)

        # 3. 标 RESOLVED
        resolved = self.resolve_decision(decision_id, option, resolved_by=resolved_by)

        # 4. 标 DECISION 节点 WAITING → COMPLETED, 写入 option
        scheduler.resume(
            decision_node_id=decision.node_id,
            option=option,
            resolved_by=resolved_by,
        )

        # 5. 扫描新 DECISION 节点 (下游可能有)
        pending_decisions = self._harvest_decision_specs(
            graph,
            initial_inputs=getattr(self, "_last_initial_inputs", None) or {},
        )

        # 6. 继续执行 — 用上次缓存的 start_nodes
        start_nodes = list(getattr(self, "_last_start_nodes", None) or [])
        if not start_nodes:
            start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]

        summary = scheduler.run(start_nodes=start_nodes)

        # 7. 收集 executions
        executions = self._collect_executions(graph)

        incremental_backfill = self._maybe_incremental_backfill(
            workflow_name=getattr(self, "_last_workflow_name", "") or "",
            initial_inputs=getattr(self, "_last_initial_inputs", None),
            executions=executions,
            summary=summary,
        )
        self._last_incremental_backfill = incremental_backfill

        return {
            "summary": summary,
            "graph": graph,
            "executions": executions,
            "pending_decisions": pending_decisions,
            "resolved_decision": resolved,
            "incremental_backfill": incremental_backfill,
            "memory_context": getattr(self, "_last_memory_context", None),
        }

    def list_pending_decisions(self) -> list[dict[str, Any]]:
        """列出 PENDING 决策 (按 priority desc + due_at asc 排序)

        Returns:
            list of HumanDecision.to_dict() 序列化结果 (queue 未初始化 → [])
        """
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            return []
        return [d.to_dict() for d in queue.pending()]

    def get_decision_queue(self):
        """获取决策队列实例"""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        return queue

    # === Internals ===

    @staticmethod
    def _collect_executions(graph: Any) -> Dict[str, Any]:
        """收集图中全部 NodeExecution (node_id → NodeExecution)"""
        executions: Dict[str, Any] = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)
        return executions

    def _maybe_memory_context(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
    ) -> Any:
        """Phase 9.70 F62: optional MemoryGateway RAG context for chapter workflows."""
        from .chapter_memory_hook import maybe_attach_memory_context

        return maybe_attach_memory_context(
            workflow_name,
            initial_inputs,
            mode=getattr(self, "_memory_rag_mode", None),
        )

    def _maybe_incremental_backfill(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
        executions: Dict[str, Any],
        summary: Any,
    ) -> Any:
        """Phase 9.63 F54: optional incremental CVG backfill after emit_chapter."""
        from infra.cross_volume.incremental_backfill import maybe_after_workflow

        return maybe_after_workflow(
            workflow_name,
            initial_inputs,
            executions,
            summary,
            enabled=getattr(self, "_incremental_backfill_enabled", None),
        )

    def _harvest_decision_specs(
        self,
        graph: Any,
        *,
        initial_inputs: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """扫描图中的 DECISION 节点 → 创建 HumanDecision → 返回序列化列表

        Phase 4.3: run_workflow 自动识别 NodeType.DECISION 节点, 包装为
        HumanDecision 放进决策队列, 供人工介入。
        Phase 9.69 F61: skip 已有 execution 且非 WAITING 的节点 (resume 后不重复 harvest)。
        Phase 9.83 F75: context 带上 chapter_num (dashboard 决策卡片展示用)。
        """
        # 延迟 import: 避免 core ↔ pipeline 模块级循环 (kind 映射表真源在
        # lingwen_pipeline.master_controller, 测试也从那里 import _infer_decision_kind)
        from lingwen_pipeline.master_controller import (
            _DEFAULT_DECISION_OPTIONS,
            _DEFAULT_DECISION_PRIORITY,
            _infer_decision_kind,
        )

        from infra.got.data_structures import NodeStatus, NodeType

        from .decision_queue import create_decision

        # 防御: __new__ 构造的测试 stub 可能没有 _decision_queue
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            return []

        pending_node_ids = {d.node_id for d in queue.pending()}
        seed = initial_inputs
        if seed is None:
            seed = getattr(self, "_last_initial_inputs", None) or {}

        harvested: List[Dict[str, Any]] = []
        for nid in graph.node_ids():
            node = graph.get_node(nid)
            if node.type != NodeType.DECISION:
                continue
            if graph.has_execution(nid):
                if graph.get_execution(nid).status != NodeStatus.WAITING:
                    continue
            elif nid in pending_node_ids:
                continue
            kind = _infer_decision_kind(nid)
            ctx: Dict[str, Any] = {}
            chapter_num = seed.get("chapter_num")
            if chapter_num is not None:
                ctx["chapter_num"] = chapter_num
            decision = create_decision(
                decision_kind=kind,
                node_id=nid,
                prompt=node.description or f"决策点: {node.name or nid}",
                options=_DEFAULT_DECISION_OPTIONS.get(kind.value, ("approve", "reject")),
                priority=_DEFAULT_DECISION_PRIORITY.get(kind.value, 5),
                context=ctx,
            )
            # Phase 6.5: with_lock() 让 add 也是原子的
            with queue.with_lock():
                queue.add(decision)
            harvested.append(decision.to_dict())
        return harvested
