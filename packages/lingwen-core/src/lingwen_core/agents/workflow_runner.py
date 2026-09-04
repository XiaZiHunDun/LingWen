"""Phase 27 P2-WFRUNNER — MasterController 工作流运行 service.

从 WorkflowMixin.run_workflow / resume_workflow (181 行) 拆出,
自含 budget + scheduler + state 生命周期管理. Mixin.run_workflow()
变 1 行 delegate: return self._get_runner().run(...).
"""
from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from lingwen_pipeline.master_controller import MasterController

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """MasterController 工作流运行 service (Phase 27 P2-WFRUNNER).

    封装 run_workflow / resume_workflow + 4 internal helpers.
    读 / 写 controller._state (WorkflowState) 直传 — 不持独立 state.
    """

    def __init__(self, controller: "MasterController") -> None:
        self._controller = controller

    def run(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """运行工作流 (Phase 27 P2-WFRUNNER).

        Returns:
            {summary, graph, executions, pending_decisions, incremental_backfill, memory_context}
        """
        controller = self._controller

        # Phase 8.8: 先写 budget, AgentComputeFn 才读得到
        controller._current_budget_usd = cost_budget_usd
        # Phase 8.12: run_id (uuid4 hex) + 持久化到 budget_service
        run_id = uuid.uuid4().hex
        controller._current_run_id = run_id
        # getattr 兜底 __new__ 构造的 test stub
        budget_service = getattr(controller, "budget_service", None)
        if budget_service is not None and cost_budget_usd is not None:
            budget_service.set(scope="run", usd=cost_budget_usd, run_id=run_id)
        try:
            # 延迟 import: 避免 got ↔ agent_system 循环, 且让测试可 monkeypatch
            from lingwen_core.agents.got_bridge import build_got_scheduler

            scheduler, graph = build_got_scheduler(
                master=controller,
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
            controller._state = controller._state.with_updates(
                initial_inputs=dict(seed_inputs),
                workflow_name=workflow_name,
                start_nodes=list(start_nodes),
            )

            summary = scheduler.run(start_nodes=start_nodes, initial_inputs=seed_inputs)
            executions = self._collect_executions(graph)

            # 缓存活跃工作流状态 (Phase 5) — resume_workflow() / dashboard 用它
            incremental_backfill = self._maybe_incremental_backfill(
                workflow_name=workflow_name,
                initial_inputs=seed_inputs,
                executions=executions,
                summary=summary,
            )
            controller._state = controller._state.with_updates(
                scheduler=scheduler,
                graph=graph,
                incremental_backfill=incremental_backfill,
                memory_context=memory_context,
            )

            return {
                "summary": summary,
                "graph": graph,
                "executions": executions,
                "pending_decisions": pending_decisions,
                "incremental_backfill": incremental_backfill,
                "memory_context": memory_context,
            }
        finally:
            # Phase 8.8 / 8.12: reset 防跨 run leak
            controller._current_budget_usd = None
            controller._current_run_id = None

    def resume(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Dict[str, Any]:
        """恢复 DECISION 暂停的工作流 (Phase 27 P2-WFRUNNER).

        Returns:
            同 run() 结构 + resolved_decision (HumanDecision 对象)

        Raises:
            RuntimeError: 无活跃工作流 (从未 run_workflow) / queue 未初始化
            KeyError: decision_id 不存在
            ValueError: 决策已 RESOLVED / option 不在 options / node 非 WAITING
        """
        controller = self._controller

        # 1. 检查有活跃工作流
        scheduler = controller._state.scheduler
        graph = controller._state.graph
        if scheduler is None or graph is None:
            raise RuntimeError(
                "no active workflow; call run_workflow() first before resume_workflow()"
            )

        # 2. 查决策 → 拿 node_id (KeyError if missing)
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")

        decision = queue.get(decision_id)

        # 3. 标 RESOLVED (lock + write)
        resolved = self._resolve_decision_locked(decision_id, option, resolved_by)

        # 4. 标 DECISION 节点 WAITING → COMPLETED, 写入 option
        scheduler.resume(
            decision_node_id=decision.node_id,
            option=option,
            resolved_by=resolved_by,
        )

        # 5. 扫描新 DECISION 节点 (下游可能有)
        pending_decisions = self._harvest_decision_specs(
            graph,
            initial_inputs=controller._state.initial_inputs,
        )

        # 6. 继续执行 — 用上次缓存的 start_nodes
        start_nodes = list(controller._state.start_nodes)
        if not start_nodes:
            start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]

        summary = scheduler.run(start_nodes=start_nodes)

        # 7. 收集 executions
        executions = self._collect_executions(graph)

        incremental_backfill = self._maybe_incremental_backfill(
            workflow_name=controller._state.workflow_name,
            initial_inputs=controller._state.initial_inputs,
            executions=executions,
            summary=summary,
        )
        controller._state = controller._state.with_updates(
            incremental_backfill=incremental_backfill,
        )

        return {
            "summary": summary,
            "graph": graph,
            "executions": executions,
            "pending_decisions": pending_decisions,
            "resolved_decision": resolved,
            "incremental_backfill": incremental_backfill,
            "memory_context": controller._state.memory_context,
        }

    def _maybe_memory_context(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
    ) -> Any:
        """Phase 9.70 F62: optional MemoryGateway RAG context for chapter workflows."""
        mode = getattr(self._controller, "_memory_rag_mode", None)
        if mode is None:
            return None  # early return when disabled (避免调 real hook with None mode)
        from lingwen_core.agents.chapter_memory_hook import maybe_attach_memory_context
        return maybe_attach_memory_context(workflow_name, initial_inputs, mode=mode)

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
            enabled=getattr(self._controller, "_incremental_backfill_enabled", None),
        )

    def _harvest_decision_specs(
        self,
        graph: Any,
        *,
        initial_inputs: Optional[Dict[str, Any]] = None,
    ) -> list:
        """扫描 DECISION 节点 → 创建 HumanDecision → 返回序列化列表.

        Phase 4.3: run_workflow 自动识别 NodeType.DECISION 节点, 包装为
        HumanDecision 放进决策队列, 供人工介入.
        Phase 9.69 F61: skip 已有 execution 且非 WAITING 的节点 (resume 后不重复 harvest).
        Phase 9.83 F75: context 带上 chapter_num (dashboard 决策卡片展示用).
        """
        from lingwen_core.agents.decision_queue import create_decision
        from lingwen_pipeline.master_controller import (
            _DEFAULT_DECISION_OPTIONS,
            _DEFAULT_DECISION_PRIORITY,
            _infer_decision_kind,
        )

        from infra.got.data_structures import NodeStatus, NodeType

        controller = self._controller
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            return []

        pending_node_ids = {d.node_id for d in queue.pending()}
        seed = initial_inputs
        if seed is None:
            seed = controller._state.initial_inputs

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
            with queue.with_lock():
                queue.add(decision)
            harvested.append(decision.to_dict())
        return harvested

    def _resolve_decision_locked(
        self,
        decision_id: str,
        option: str,
        resolved_by: str,
    ) -> Any:
        """标 RESOLVED + fcntl 排他锁 (Phase 6.5 with_lock pattern).

        From WorkflowMixin.resolve_decision extracted body, 仅供 resume() step 3 调用.
        """
        controller = self._controller
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        with queue.with_lock():
            return queue.resolve(decision_id, option, resolved_by=resolved_by)

    @staticmethod
    def _collect_executions(graph: Any) -> Dict[str, Any]:
        """收集图中全部 NodeExecution (node_id → NodeExecution)."""
        executions: Dict[str, Any] = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)
        return executions
