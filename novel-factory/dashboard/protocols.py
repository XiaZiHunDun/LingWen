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

import logging
from datetime import datetime
from typing import Any, Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from infra.agent_system.decision_queue import (
    HumanDecision,
    HumanDecisionQueue,
)
from infra.ai_service.model_tiers import ModelTier

logger = logging.getLogger(__name__)

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

    def get_active_workflow_status(
        self, since: Optional[datetime] = None
    ) -> dict[str, Any]:
        """当前活跃工作流状态(is_active / workflow_name / paused / ...).
        Phase 8.16: since 透传 (additive kwarg, default None 走旧 path)."""
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

    Phase 8.12: 类级别 _controller 单例 — dashboard 新 budget endpoints
    (GET/PUT /api/budgets) 直接读 MasterControllerAdapter._controller
    (不走 closure 捕获的 master_controller),便于测试注入。
    create_app() 启动时如果传 MasterControllerAdapter 实例,
    会自动同步 _controller 到类级别。
    """

    # 类级别单例 (Phase 8.12):dashboard budget endpoints 直接读这个
    _controller: Any = None

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

    def get_active_workflow_status(
        self, since: Optional[datetime] = None
    ) -> dict[str, Any]:
        """读 MC._last_* 缓存(Phase 5 run_workflow 写入).
        Phase 8.16: since 透传到 3 _extract_cost_* helper (additive kwarg).
        """
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
        # 扫描 pending decisions (调 controller 方法;__new__ stub 可能无 _decision_queue,
        # method 内部 hasattr/getattr 防御返 [])
        pending: list[dict[str, Any]] = []
        try:
            pending = self._controller._harvest_decision_specs(graph)
        except Exception:
            pending = []
        summary_obj = getattr(scheduler, "_summary", None)
        steps = getattr(summary_obj, "steps", 0) if summary_obj else 0

        # Phase 7.6: 抽 S1-S8 评分数据 (从 NodeExecution.output)
        score_data: dict[str, dict[str, Any]] = {}
        for nid, ex in executions.items():
            output = getattr(ex, "output", None) or {}
            if not isinstance(output, dict):
                continue
            # 识别: 7.5 polish_merge_synthesis 返的 dict (含 scores_a + scores_b)
            if "scores_a" in output and "scores_b" in output:
                labels = output.get("_labels", ()) or ()
                score_data[nid] = {
                    "scores_a": output.get("scores_a", {}),
                    "scores_b": output.get("scores_b", {}),
                    "scores_total_a": output.get("scores_total_a", 0.0),
                    "scores_total_b": output.get("scores_total_b", 0.0),
                    "scores_delta": output.get("scores_delta", 0.0),
                    "winner": output.get("winner"),
                    "label_a": labels[0] if len(labels) >= 1 else None,
                    "label_b": labels[1] if len(labels) >= 2 else None,
                    "fallback": output.get("fallback"),
                }

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
            "executions": {
                nid: ex.status.value  # "completed" | "running" | "waiting" | "pending" | ...
                for nid, ex in executions.items()
            },
            "score_data": score_data,  # Phase 7.6
            "cost_by_scenario": _extract_cost_by_scenario(self._controller, since=since),  # Phase 8.16
            "cost_by_tier": _extract_cost_by_tier(self._controller, since=since),  # Phase 8.16
            "cost_by_day": _extract_cost_by_day(self._controller, since=since),  # Phase 8.23
            "cost_by_day_per_tier": _extract_cost_by_day_per_tier(  # Phase 9.28 F12
                self._controller, since=since
            ),
            "cost_budget_status": _extract_budget_status(self._controller),  # 0 改 (走 since=None)
            "budget_per_day": _extract_budget_per_window(self._controller, "day"),  # 0 改
            "budget_per_week": _extract_budget_per_window(self._controller, "week"),  # 0 改
            "budget_by_tier": _extract_budget_by_tier(self._controller),  # 0 改
            # Phase 8.5: pull total cost from master's cost_tracker (0.0 if not wired)
            "total_cost_usd": _extract_total_cost(self._controller, since=since),  # Phase 8.16
        }


def _extract_total_cost(
    controller: Any, since: Optional[datetime] = None
) -> float:
    """Phase 8.5: 拿 master.cost_tracker.total_cost() 填字段, 0.0 if 未注入.
    Phase 8.16: 加 since 透传 (additive kwarg, default None 走旧 path).

    用 getattr 防御 cost_tracker 字段 (测试 stub 可能没) + 失败时 log warning 而非静默。
    """
    cost_tracker = getattr(controller, "cost_tracker", None)
    if cost_tracker is None:
        return 0.0
    try:
        return float(cost_tracker.total_cost(since=since))
    except Exception as exc:
        logger.warning("cost_tracker.total_cost() failed: %s", exc)
        return 0.0


def _extract_cost_by_scenario(
    controller: Any, since: Optional[datetime] = None
) -> dict[str, float]:
    """Phase 8.7: 跟 _extract_total_cost 同模式 — 拿 controller.cost_tracker 调 cost_by_scenario().
    Phase 8.16: 加 since 透传 (additive kwarg, default None 走旧 path).

    Args:
        controller: MasterController 实例 (decoupling Protocol)
        since: UTC datetime, Phase 8.16 time window filter (default None = 全部)

    Returns:
        dict[scenario, cost_usd] — 空 dict if cost_tracker is None / 无该属性 / 无 records
    """
    cost_tracker = getattr(controller, "cost_tracker", None)
    if cost_tracker is None:
        return {}
    try:
        return dict(cost_tracker.cost_by_scenario(since=since))
    except Exception as exc:
        logger.warning("cost_tracker.cost_by_scenario() failed: %s", exc)
        return {}


def _extract_cost_by_tier(
    controller: Any, since: Optional[datetime] = None
) -> dict[str, float]:
    """Phase 8.13: 跟 _extract_cost_by_scenario 同模式 — 拿 controller.cost_tracker 调 cost_by_tier().
    Phase 8.16: 加 since 透传 (additive kwarg, default None 走旧 path).

    Mirrors _extract_cost_by_scenario silent-degrade pattern: returns empty
    dict when controller has no cost_tracker or when cost_tracker.cost_by_tier()
    raises. ModelTier enum keys are serialized via .value (e.g. HAIKU → "haiku").

    Args:
        controller: MasterController 实例 (decoupling Protocol)
        since: UTC datetime, Phase 8.16 time window filter (default None = 全部)

    Returns:
        dict[tier_name, cost_usd] — 空 dict if cost_tracker is None / 无该属性 / 抛异常
    """
    cost_tracker = getattr(controller, "cost_tracker", None)
    if cost_tracker is None:
        return {}
    try:
        return {
            tier.value: float(amt)
            for tier, amt in cost_tracker.cost_by_tier(since=since).items()
        }
    except Exception as exc:  # noqa: BLE001 — silent degrade by design
        logger.warning("cost_tracker.cost_by_tier() failed: %s", exc)
        return {}


def _extract_cost_by_day(
    controller: Any, since: Optional[datetime] = None
) -> dict[str, float]:
    """Phase 8.23: 跟 _extract_cost_by_tier 同模式 — 拿 controller.cost_tracker 调 cost_by_day().

    Mirrors _extract_cost_by_scenario silent-degrade pattern: returns empty
    dict when controller has no cost_tracker or when cost_tracker.cost_by_day()
    raises. Keys are 'YYYY-MM-DD' UTC date strings, values are float USD.

    Args:
        controller: MasterController 实例 (decoupling Protocol)
        since: UTC datetime, Phase 8.16 time window filter (default None = 全部)

    Returns:
        dict[date_str, cost_usd] — 空 dict if cost_tracker is None / 无该属性 / 抛异常
    """
    cost_tracker = getattr(controller, "cost_tracker", None)
    if cost_tracker is None:
        return {}
    try:
        return dict(cost_tracker.cost_by_day(since=since))
    except Exception as exc:  # noqa: BLE001 — silent degrade by design
        logger.warning("cost_tracker.cost_by_day() failed: %s", exc)
        return {}


def _extract_cost_by_day_per_tier(
    controller: Any, since: Optional[datetime] = None
) -> dict[str, dict[str, float]]:
    """Phase 9.28 F12: day × tier cross-dim aggregation for per-tier trend chart.

    Mirrors _extract_cost_by_day silent-degrade pattern. Keys are 'YYYY-MM-DD'
    date strings; inner dict keys are tier names (haiku/sonnet/opus).
    """
    cost_tracker = getattr(controller, "cost_tracker", None)
    if cost_tracker is None:
        return {}
    try:
        raw = cost_tracker.cost_by_day_per_tier(since=since)
        return {
            day: {str(tier): float(amt) for tier, amt in tiers.items()}
            for day, tiers in raw.items()
        }
    except Exception as exc:  # noqa: BLE001 — silent degrade by design
        logger.warning("cost_tracker.cost_by_day_per_tier() failed: %s", exc)
        return {}


def _extract_budget_status(controller: Any) -> dict[str, Any]:
    """Phase 8.8 T5: 拿 controller._current_budget_usd + cost_tracker 算 budget status.

    跟 _extract_cost_by_scenario 同模式 (silent degrade 返 {}):
    - 无 budget (_current_budget_usd=None) → {}
    - 无 cost_tracker → {}
    - 异常 → log warning + {}

    Returns:
        dict with keys:
            status: "ok" | "exceeded"
            budget_usd: float
            used_usd: float
            used_pct: float (0-100+ range, >100 when over budget)
        or {} if no budget set or cost_tracker missing.
    """
    try:
        budget = getattr(controller, "_current_budget_usd", None)
        if budget is None:
            return {}
        cost_tracker = getattr(controller, "cost_tracker", None)
        if cost_tracker is None:
            return {}
        used = float(cost_tracker.total_cost())
        used_pct = (used / budget * 100) if budget > 0 else 0.0
        status = "exceeded" if used > budget else "ok"
        return {
            "status": status,
            "budget_usd": budget,
            "used_usd": used,
            "used_pct": used_pct,
        }
    except Exception as exc:
        logger.warning("_extract_budget_status 失败: %s", exc)
        return {}


def _extract_budget_per_window(controller: Any, scope: str) -> dict[str, Any]:
    """Phase 8.12 T5: 拿 controller.budget_service 查 current scope + window check,
    算 status (跟 _extract_budget_status 同模式, silent degrade 返 {}).

    Args:
        controller: MasterController 实例
        scope: 'day' or 'week' (per-run 走 _extract_budget_status 旧 path)

    Returns:
        dict with keys (status, budget_usd, used_usd, used_pct) or {} if no budget or budget_service missing
    """
    from datetime import datetime, timedelta, timezone
    try:
        service = getattr(controller, "budget_service", None)
        if service is None:
            return {}
        entry = service.get_current(scope)
        if entry is None:
            return {}
        # Window check (per-day = UTC same date, per-week = Mon-Sun)
        now = datetime.now(timezone.utc)
        if scope == "day":
            in_window = entry.set_at.date() == now.date()
        elif scope == "week":
            days_since_monday = now.weekday()
            week_start = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            in_window = entry.set_at >= week_start
        else:
            in_window = True
        if not in_window:
            return {}  # window 失效, 视为无 budget
        # 算 used
        cost_tracker = getattr(controller, "cost_tracker", None)
        used = float(cost_tracker.total_cost()) if cost_tracker is not None else 0.0
        used_pct = (used / entry.usd * 100) if entry.usd > 0 else 0.0
        status = "exceeded" if used > entry.usd else "ok"
        return {
            "status": status,
            "budget_usd": entry.usd,
            "used_usd": used,
            "used_pct": used_pct,
        }
    except Exception as exc:
        logger.warning("_extract_budget_per_window failed for scope=%s: %s", scope, exc)
        return {}


def _extract_budget_by_tier(master: Any) -> dict[str, dict[str, Any] | None]:
    """Phase 8.15 T5: 拿 master.budget_service_by_tier 查 3 tier current budget entries.

    Mirror _extract_budget_per_window silent-degrade pattern (getattr + try/except).
    3 tier 顺序: haiku → sonnet → opus (Enum 顺序, deterministic).

    Args:
        master: MasterController 实例 (duck-typed via getattr)

    Returns:
        dict[tier_name, {"usd": float, "set_at": str} | None] (3 tier 永远 present)
        - master.budget_service_by_tier = None → 3 tier 都 None
        - service.get_by_tier(tier) returns None → 该 tier None
        - 否则 {"usd": entry.usd, "set_at": entry.set_at.isoformat()}
    """
    empty: dict[str, dict[str, Any] | None] = {tier.value: None for tier in ModelTier}
    try:
        service = getattr(master, "budget_service_by_tier", None)
        if service is None:
            return empty
        result: dict[str, dict[str, Any] | None] = {}
        for tier in ModelTier:  # haiku, sonnet, opus (Enum 顺序, deterministic)
            entry = service.get_by_tier(tier)
            if entry is None:
                result[tier.value] = None
            else:
                result[tier.value] = {
                    "usd": entry.usd,
                    "set_at": entry.set_at.isoformat() if entry.set_at else None,
                }
        return result
    except Exception as exc:
        logger.warning("_extract_budget_by_tier failed: %s", exc)
        return empty


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
    from infra.cross_volume.incremental_backfill import backfill_stats_to_dict

    return {
        "summary": summary_dict,
        "executions": executions_dict,
        "pending_decisions": result.get("pending_decisions", []),
        "incremental_backfill": backfill_stats_to_dict(
            result.get("incremental_backfill")
        ),
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


# ==================== Phase 9.13: CVG Pydantic Schemas ====================
# Re-exported from dashboard.app for the 4 CVG REST endpoints (5 endpoints use these).
# 跟 DecisionResponse / WorkflowListItem 1:1 mirror (但这些 Pydantic schemas 历史上在
# app.py 内部,本次为了 additive 解耦,把 CVG 系列提到 protocols.py)。


class RippleListItemResponse(BaseModel):
    """Phase 9.13: ripple list item (跟 DecisionResponse 1:1 mirror)."""
    ripple_id: str
    dimension: str  # placeholder, real value via JOIN in future
    relationship_type: str
    source_chapter: int
    target_chapter: int
    status: str
    confidence: int = 1  # Phase 9.12 additive
    created_at: datetime
    impact_score: float = 0.0  # Phase 9.59 F50
    parent_ripple_id: str | None = None  # Phase 9.64 F55
    child_count: int = 0  # Phase 9.64 F55


class RippleDetailResponse(RippleListItemResponse):
    """Phase 9.13: ripple detail (extends list item, 跟 DecisionDetailResponse 1:1)."""
    evidence: str = ""
    source_payload: dict[str, Any] = Field(default_factory=dict)
    target_payload: dict[str, Any] = Field(default_factory=dict)
    edge_payload: dict[str, Any] = Field(default_factory=dict)


class RippleActionResponse(BaseModel):
    """Phase 9.13: apply/reject action response."""
    ripple_id: str
    status: str
    actor: str
    applied_at: Optional[datetime] = None


class RippleStatsResponse(BaseModel):
    """Phase 9.13: ripple stats (count by status + volume, 跟 DecisionStats 1:1)."""
    total: int
    by_status: dict[str, int]
    by_volume: dict[str, int] = Field(default_factory=dict)


__all__ = [
    "MasterControllerLike",
    "MasterControllerAdapter",
    "RippleListItemResponse",
    "RippleDetailResponse",
    "RippleActionResponse",
    "RippleStatsResponse",
    "RippleAuditEntryResponse",
    "RippleRollbackRequest",
    "RippleActionRequest",
    "CascadeNodeResponse",
    "CascadeEdgeResponse",
    "CascadeResponse",
    "CascadePreviewResponse",
    "CascadeRunResponse",
    "CascadeUpdatePayload",
    "CascadeCancelPayload",
    "CascadeCancelRequest",
]


# === Phase 9.14: ripple audit + rollback schemas ===

class RippleAuditEntryResponse(BaseModel):
    """Phase 9.14: 1 row of ripple_audit table (newest first list item)."""
    id: int
    ripple_id: str
    action: Literal["created", "applied", "rejected", "failed", "rolled_back"]
    prev_status: str | None
    new_status: str
    actor: str
    origin: Literal["ui", "cli", "system"]
    reason: str | None
    created_at: datetime


class RippleRollbackRequest(BaseModel):
    """Phase 9.14: POST /rollback body (reason required)."""
    actor: str = "user"
    origin: Literal["ui", "cli", "system"] = "ui"
    reason: str = Field(..., min_length=1, max_length=500)


class RippleActionRequest(BaseModel):
    """Phase 9.14: Optional body for /apply and /reject (backward compat).

    既有 Phase 9.13 既有的 /apply /reject 不传 body 仍 work (全 Optional 字段)。
    """
    actor: str | None = None
    origin: Literal["ui", "cli", "system"] | None = None
    reason: str | None = None


# === Phase 9.15: cascade BFS + dry-run preview schemas (T4) ===

class CascadeNodeResponse(BaseModel):
    """Phase 9.15: ReferenceNode in cascade BFS result (1:1 mirror)."""
    id: str
    dimension: str
    volume: int
    chapter: int
    title: str = ""
    description: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class CascadeEdgeResponse(BaseModel):
    """Phase 9.15: ReferenceEdge in cascade BFS result (1:1 mirror)."""
    id: str
    from_node_id: str
    to_node_id: str
    relationship_type: str
    weight: float
    payload: dict[str, Any] = Field(default_factory=dict)


class CascadeResponse(BaseModel):
    """Phase 9.15: full cascade BFS result for a single ripple.

    Mirrors CascadedRipple dataclass (infra/cross_volume/reference_graph.py).
    """
    trigger_ripple_id: str
    cascade_nodes: list[CascadeNodeResponse]
    cascade_edges: list[CascadeEdgeResponse]
    cascade_actions: list[dict[str, Any]]
    depth_reached: int
    generated_at: str
    bfs_algorithm_version: str = "v1"


class CascadePreviewResponse(BaseModel):
    """Phase 9.15: dry-run preview summary for apply confirmation modal.

    Aggregate counts from the persisted BFS result; no LLM calls.
    """
    ripple_id: str
    affected_chapter_count: int = 0
    affected_character_count: int = 0
    affected_setting_count: int = 0
    estimated_change_count: int = 0
    cascade_node_count: int = 0
    cascade_edge_count: int = 0
    max_depth: int = 0


# === Phase 9.41 F30: CVG reference graph (ImpactGraph) ===

class ReferenceGraphResponse(BaseModel):
    """Phase 9.41: persisted reference_nodes + reference_edges snapshot for dashboard."""

    nodes: list[CascadeNodeResponse]
    edges: list[CascadeEdgeResponse]
    total_node_count: int
    total_edge_count: int
    truncated: bool = False


# === Phase 9.20: cascade_runs table row response ===

class CascadeRunResponse(BaseModel):
    """Phase 9.20: cascade_runs table row → API response.

    Mirrors CascadeRun dataclass (infra/cross_volume/storage.py). 11 fields:
    autoincrement id, ripple_id, BFS inputs (max_depth/depth_reached/algorithm),
    timestamps (started_at/completed_at), status, and the BFS output payload
    (cascade_nodes/cascade_edges/cascade_actions).

    Reuses CascadeNodeResponse / CascadeEdgeResponse for node/edge payload
    serialization (1:1 with Phase 9.15 CascadeResponse).
    """
    id: int
    ripple_id: str
    max_depth: int
    depth_reached: int
    algorithm: str
    started_at: datetime
    completed_at: datetime
    status: str
    cascade_nodes: list[CascadeNodeResponse]
    cascade_edges: list[CascadeEdgeResponse]
    cascade_actions: list[dict[str, Any]]

    @classmethod
    def from_dataclass(cls, run: Any) -> "CascadeRunResponse":
        """Map CascadeRun dataclass → response (handles tuple fields).

        cascade_nodes / cascade_edges are tuples of ReferenceNode / ReferenceEdge
        dataclass instances. cascade_actions is a tuple[str, ...]. We materialize
        to list for Pydantic JSON serialization.
        """
        return cls(
            id=run.id,
            ripple_id=run.ripple_id,
            max_depth=run.max_depth,
            depth_reached=run.depth_reached,
            algorithm=run.algorithm,
            started_at=run.started_at,
            completed_at=run.completed_at,
            status=run.status,
            cascade_nodes=[CascadeNodeResponse(**_cvg_node_to_dict(n)) for n in run.cascade_nodes],
            cascade_edges=[CascadeEdgeResponse(**_cvg_edge_to_dict(e)) for e in run.cascade_edges],
            cascade_actions=list(run.cascade_actions),
        )


def _cvg_node_to_dict(node: Any) -> dict:
    """Phase 9.20: ReferenceNode → dict for CascadeNodeResponse(**).

    Local copy of dashboard.app._node_to_dict_for_response (kept here to avoid
    circular import: dashboard.app imports CascadeRunResponse from protocols).
    Converts dataclass → dict (datetime → isoformat) so Pydantic v2 can bind
    fields it knows and ignore extras (created_at / created_by / confidence).
    """
    from dataclasses import asdict, is_dataclass
    if is_dataclass(node):
        d = asdict(node)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(node)


def _cvg_edge_to_dict(edge: Any) -> dict:
    """Phase 9.20: ReferenceEdge → dict for CascadeEdgeResponse(**).

    Local copy of dashboard.app._edge_to_dict_for_response (see _cvg_node_to_dict
    for circular-import rationale).
    """
    from dataclasses import asdict, is_dataclass
    if is_dataclass(edge):
        d = asdict(edge)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(edge)


# === Phase 9.17: cascade update WS payload schema ===

class CascadeUpdatePayload(BaseModel):
    """Phase 9.17: WS cascade.update payload schema (跟 RippleRollbackRequest 1:1 风格).

    替换 Phase 9.16 dict literal {ripple_id, cascade_node_count, cascade_edge_count,
    depth_reached, bfs_algorithm_version} — IDE 显式 types + Pydantic v2 runtime
    ValidationError 提前 (negative count / typo bfs_algorithm_version 立刻 fail).

    双路径: cascade_notifier.notify_cascade_update 既接受 typed CascadeUpdatePayload
    instance, 也接受 dict (走 model_validate fallback 兜底, 0 改旧 caller).
    """
    ripple_id: str = Field(..., min_length=1)
    cascade_node_count: int = Field(..., ge=0)
    cascade_edge_count: int = Field(..., ge=0)
    depth_reached: int = Field(..., ge=0)
    bfs_algorithm_version: Literal["v1", "v2_weighted"]
    latency_ms: Optional[int] = Field(default=None, ge=0)


class CascadeCancelPayload(BaseModel):
    """Phase 9.21: WS cascade.cancel payload schema.

    跟 CascadeUpdatePayload 1:1 风格 (Pydantic v2 typed schema + Field 约束).
    cascade_notifier.notify_cascade_cancel 双路径: typed instance 直接用, dict
    走 model_validate fallback 兜底 (0 改旧 caller, backward compat).
    """
    run_id: int = Field(..., ge=1)
    ripple_id: str = Field(..., min_length=1)
    status: Literal["cancelled"] = "cancelled"
    reason: str = ""


class CascadeCancelRequest(BaseModel):
    """Phase 9.21: POST cancel endpoint request body (optional reason)."""
    reason: str = ""


class AuditCreatedPayload(BaseModel):
    """Phase 9.62 F53: WS audit.created payload (1:1 RippleAuditEntryResponse)."""
    id: int
    ripple_id: str
    action: Literal["created", "applied", "rejected", "failed", "rolled_back"]
    prev_status: str | None
    new_status: str
    actor: str
    origin: Literal["ui", "cli", "system"]
    reason: str | None
    created_at: datetime


# === Phase 9.44 F33: cascade broadcast log persistence ===

class CascadeBroadcastLogResponse(BaseModel):
    """cascade_broadcast_log table row → API response."""

    id: int = Field(..., ge=1)
    ripple_id: str = Field(..., min_length=1)
    latency_ms: int = Field(..., ge=0)
    created_at: str

    @classmethod
    def from_dataclass(cls, entry: Any) -> "CascadeBroadcastLogResponse":
        return cls(
            id=entry.id,
            ripple_id=entry.ripple_id,
            latency_ms=entry.latency_ms,
            created_at=entry.created_at.isoformat(),
        )
