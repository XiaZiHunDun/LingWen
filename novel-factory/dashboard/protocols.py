"""dashboard/protocols.py — MasterController 抽象 + 适配器

Doc 4 §10 Phase 6: 把 MasterController 决策/工作流 API 暴露到 dashboard。

设计:
- MasterControllerLike Protocol: dashboard 视角的最小接口(duck-typed)
  → 测试可用 stub 实现,不拖入 ai_service/orchestrator 重型依赖
- MasterControllerAdapter: 把真 MasterController 的结果转换成
  FastAPI 可序列化的 dict (ExecutionSummary/NodeExecution 含 datetime/Enum)
  + 补全 MC 没暴露的薄方法 (defer/cancel/active status)

解耦:
- 路由 handler 不直接 import MasterController
- 通过 Protocol 依赖注入 (create_app 接收 controller 参数)
- 测试用 _StubMasterController 满足 Protocol

Reference:
- infra/agent_system/master_controller.py (lines 174-396)
- infra/agent_system/decision_queue.py (lines 175-355)
"""
from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from infra.agent_system.decision_queue import (
    HumanDecision,
    HumanDecisionQueue,
)

# === Protocol (duck-typed) ===

@runtime_checkable
class MasterControllerLike(Protocol):
    """dashboard 视角的 MasterController 最小接口。

    满足此 Protocol 的对象即可被 create_app 接收。
    测试用 stub 实现,生产用 MasterControllerAdapter 包装 MasterController。
    """

    def list_pending_decisions(self) -> list[dict[str, Any]]:
        """PENDING 决策列表(已按 priority desc + due_at asc 排序)

        Returns:
            list of HumanDecision.to_dict() 序列化结果
        """
        ...

    def get_decision_queue(self) -> HumanDecisionQueue:
        """底层 HumanDecisionQueue(defer/cancel/save 用)"""
        ...

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> HumanDecision:
        """解决决策(PENDING → RESOLVED)"""
        ...

    def defer_decision(
        self,
        decision_id: str,
        reason: str = "",
    ) -> HumanDecision:
        """推迟决策(PENDING → DEFERRED)"""
        ...

    def cancel_decision(
        self,
        decision_id: str,
        reason: str = "",
    ) -> HumanDecision:
        """取消决策(PENDING → CANCELLED)"""
        ...

    def run_workflow(
        self,
        workflow_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """运行工作流,返回 summary + graph + executions + pending_decisions"""
        ...

    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> dict[str, Any]:
        """恢复 DECISION 暂停的工作流(Phase 5)"""
        ...

    def get_active_workflow_status(self) -> dict[str, Any]:
        """当前活跃工作流状态(is_active / workflow_name / paused / ...)"""
        ...


# === Adapter ===

class MasterControllerAdapter:
    """把真 MasterController 包成 dashboard 友好的接口。

    职责:
    1. 透传 MC 已有方法 (list_pending_decisions / get_decision_queue /
       resolve_decision / run_workflow / resume_workflow)
    2. 补全 MC 没暴露的方法:
       - defer_decision / cancel_decision → queue.defer/cancel
       - get_active_workflow_status → 读 MC._last_* 缓存
    3. 转换 run_workflow/resume_workflow 的返回值
       (ExecutionSummary/NodeExecution 含 datetime/Enum,
       FastAPI 不能自动序列化 → 转 dict)
    """

    def __init__(self, controller: Any) -> None:
        self._controller = controller

    # === 透传 (signature 对齐 MC) ===

    def list_pending_decisions(self) -> list[dict[str, Any]]:
        return self._controller.list_pending_decisions()

    def get_decision_queue(self) -> HumanDecisionQueue:
        return self._controller.get_decision_queue()

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> HumanDecision:
        return self._controller.resolve_decision(
            decision_id, option, resolved_by=resolved_by
        )

    # === 补全方法 ===

    def defer_decision(
        self,
        decision_id: str,
        reason: str = "",
    ) -> HumanDecision:
        queue = self.get_decision_queue()
        deferred = queue.defer(decision_id, reason=reason)
        queue.save()
        return deferred

    def cancel_decision(
        self,
        decision_id: str,
        reason: str = "",
    ) -> HumanDecision:
        queue = self.get_decision_queue()
        cancelled = queue.cancel(decision_id)
        # queue.cancel 不接受 reason;若需 reason,改写一个最小包装
        if reason:
            # 用 from_dict 重建 (frozen=True 不能直接改 reason)
            from infra.agent_system.decision_queue import (
                DecisionStatus,
                HumanDecision,
            )
            cancelled = HumanDecision(
                decision_id=cancelled.decision_id,
                decision_kind=cancelled.decision_kind,
                node_id=cancelled.node_id,
                prompt=cancelled.prompt,
                options=cancelled.options,
                context=dict(cancelled.context),
                priority=cancelled.priority,
                due_at=cancelled.due_at,
                created_at=cancelled.created_at,
                status=DecisionStatus.CANCELLED,
                resolution=cancelled.resolution,
                resolved_at=cancelled.resolved_at,
                resolved_by=cancelled.resolved_by,
                reason=reason,
            )
            queue._decisions[cancelled.decision_id] = cancelled  # type: ignore[attr-defined]
        queue.save()
        return cancelled

    # === Workflow (需要 dict 转换) ===

    def run_workflow(
        self,
        workflow_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        result = self._controller.run_workflow(workflow_name, **kwargs)
        return _workflow_result_to_dict(result)

    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> dict[str, Any]:
        result = self._controller.resume_workflow(
            decision_id, option, resolved_by=resolved_by
        )
        d = _workflow_result_to_dict(result)
        # 额外返回 resolved_decision 序列化
        if "resolved_decision" in result:
            resolved = result["resolved_decision"]
            if hasattr(resolved, "to_dict"):
                d["resolved_decision"] = resolved.to_dict()
        return d

    def get_active_workflow_status(self) -> dict[str, Any]:
        """读 MC._last_* 缓存(Phase 5 run_workflow 写入)"""
        scheduler = getattr(self._controller, "_last_scheduler", None)
        graph = getattr(self._controller, "_last_graph", None)
        workflow_name = getattr(self._controller, "_last_workflow_name", None)
        if scheduler is None or graph is None:
            return {
                "is_active": False,
                "workflow_name": None,
                "pending_decisions": [],
            }
        # 收集 summary
        executions = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)
        from infra.got.data_structures import NodeExecution, NodeStatus

        paused_nodes: list[str] = []
        for nid, ex in executions.items():
            if ex.status in (NodeStatus.WAITING, NodeStatus.PENDING):
                if graph.get_node(nid).type.value == "decision":
                    paused_nodes.append(nid)
        completed = sum(1 for e in executions.values() if e.status == NodeStatus.COMPLETED)
        failed = sum(1 for e in executions.values() if e.status == NodeStatus.FAILED)
        # 扫描 pending decisions
        pending: list[dict[str, Any]] = []
        from infra.agent_system.master_controller import _harvest_decision_specs
        try:
            pending = _harvest_decision_specs(self._controller, graph)
        except Exception:
            pending = []
        summary_obj = getattr(scheduler, "_summary", None)
        steps = getattr(summary_obj, "steps", 0) if summary_obj else 0
        return {
            "is_active": True,
            "workflow_name": workflow_name,
            "completed": completed,
            "failed": failed,
            "paused": bool(paused_nodes),
            "paused_nodes": paused_nodes,
            "node_count": len(list(graph.node_ids())),
            "steps": steps,
            "pending_decisions": pending,
        }


# === 序列化 helpers ===

def _workflow_result_to_dict(result: dict[str, Any]) -> dict[str, Any]:
    """run_workflow/resume_workflow 结果 → FastAPI 友好 dict

    转换:
    - summary (ExecutionSummary dataclass) → dict
    - executions dict[node_id, NodeExecution] → dict[node_id, dict]
    - graph (ThoughtGraph) → 保留引用(只可视化用)
    - pending_decisions 已是 list[dict] (HumanDecision.to_dict)
    """
    summary = result.get("summary")
    summary_dict = _summary_to_dict(summary) if summary is not None else None
    executions = result.get("executions") or {}
    executions_dict = {
        nid: _execution_to_dict(ex) for nid, ex in executions.items()
    }
    return {
        "summary": summary_dict,
        "executions": executions_dict,
        "pending_decisions": result.get("pending_decisions", []),
    }


def _summary_to_dict(summary: Any) -> dict[str, Any]:
    """ExecutionSummary dataclass → dict"""
    if summary is None:
        return {}
    # 用 dataclasses.asdict 简化
    try:
        from dataclasses import asdict, is_dataclass
        if is_dataclass(summary):
            d = asdict(summary)
            # paused_nodes 可能是 tuple → 保持 tuple (JSON 序列化无碍)
            return d
    except Exception:
        pass
    # fallback: 手动取字段
    return {
        "completed": getattr(summary, "completed", 0),
        "failed": getattr(summary, "failed", 0),
        "total_cost_tokens": getattr(summary, "total_cost_tokens", 0),
        "backtrack_count": getattr(summary, "backtrack_count", 0),
        "steps": getattr(summary, "steps", 0),
        "node_count": getattr(summary, "node_count", 0),
        "paused": getattr(summary, "paused", False),
        "paused_nodes": list(getattr(summary, "paused_nodes", ())),
    }


def _execution_to_dict(execution: Any) -> dict[str, Any]:
    """NodeExecution dataclass → dict"""
    if execution is None:
        return {}
    try:
        from dataclasses import asdict, is_dataclass
        if is_dataclass(execution):
            d = asdict(execution)
            # datetime → isoformat
            if d.get("started_at"):
                d["started_at"] = d["started_at"].isoformat()
            if d.get("finished_at"):
                d["finished_at"] = d["finished_at"].isoformat()
            # NodeStatus Enum → .value
            status = d.get("status")
            if hasattr(status, "value"):
                d["status"] = status.value
            return d
    except Exception:
        pass
    # fallback
    return {
        "node_id": getattr(execution, "node_id", ""),
        "status": getattr(execution.status, "value", "unknown"),
        "started_at": getattr(execution.started_at, "isoformat", lambda: None)(),
        "finished_at": getattr(execution.finished_at, "isoformat", lambda: None)(),
        "cost_tokens": getattr(execution, "cost_tokens", 0),
        "error": getattr(execution, "error", None),
    }


__all__ = [
    "MasterControllerLike",
    "MasterControllerAdapter",
]
