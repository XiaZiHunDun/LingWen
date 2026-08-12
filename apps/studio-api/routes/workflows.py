"""
Phase 15.0 T1.4: /api/workflows/* routes.

Also registers /api/ws/workflows WebSocket endpoint.

Extracted from dashboard/app.py create_app closure (was at app.py lines 971-1069,
3680-3817).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect

from dashboard import app as _app_module  # for monkeypatch-compatible _default_storage lookup
from dashboard.helpers.time_window import _parse_time_window
from dashboard.helpers.workflow import _list_workflow_yamls, _workflow_result_to_response
from dashboard.models import (
    ResumeWorkflowRequest,
    RunWorkflowRequest,
    WorkflowListItem,
    WorkflowMermaidResponse,
    WorkflowStatusResponse,
)
from dashboard.protocols import (
    _extract_cost_by_day,
    _extract_cost_by_day_per_tier,
    _extract_cost_by_scenario,
    _extract_cost_by_tier,
    _extract_total_cost,
)
from dashboard.routes.ctx import RoutesContext, require_controller
from dashboard.ws import EVENT_CONNECTED


def register_workflows(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/workflows/list", response_model=list[WorkflowListItem])
    def list_workflows() -> list[WorkflowListItem]:
        """列出 infra/got/workflows/*.yaml"""
        return _list_workflow_yamls()

    @app.post(
        "/api/workflows/run",
        response_model=WorkflowStatusResponse,
    )
    def run_workflow(body: RunWorkflowRequest) -> WorkflowStatusResponse:
        """运行工作流 (Phase 4-5: 会扫描 DECISION 节点暂停)"""
        ctrl = require_controller(ctx)
        try:
            result = ctrl.run_workflow(
                workflow_name=body.workflow_name,
                start_nodes=body.start_nodes,
                initial_inputs=body.initial_inputs,
                max_backtracks=body.max_backtracks,
                base_dir=body.base_dir,
                cost_budget_usd=body.cost_budget_usd,  # Phase 8.8 NEW
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            if "no active workflow" in str(e):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:  # noqa: BLE001
            err_type = type(e).__name__
            if "WorkflowError" in err_type or "workflow load" in str(e).lower():
                raise HTTPException(status_code=422, detail=f"workflow load failed: {e}")
            if "MaxSteps" in err_type:
                raise HTTPException(status_code=500, detail=f"max steps: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        inner_ctrl = getattr(ctrl, "_controller", ctrl)
        return _workflow_result_to_response(
            result,
            cost_by_scenario=_extract_cost_by_scenario(inner_ctrl),
            cost_by_tier=_extract_cost_by_tier(inner_ctrl),  # Phase 8.13
            cost_by_day=_extract_cost_by_day(inner_ctrl),  # Phase 8.23
            cost_by_day_per_tier=_extract_cost_by_day_per_tier(inner_ctrl),  # Phase 9.28 F12
            total_cost_usd=_extract_total_cost(inner_ctrl),
        )

    @app.post(
        "/api/workflows/resume",
        response_model=WorkflowStatusResponse,
    )
    def resume_workflow(body: ResumeWorkflowRequest) -> WorkflowStatusResponse:
        """恢复 DECISION 暂停的工作流"""
        ctrl = require_controller(ctx)
        try:
            result = ctrl.resume_workflow(
                body.decision_id, body.option, resolved_by=body.resolved_by
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            if "no active workflow" in str(e):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e))
        inner_ctrl = getattr(ctrl, "_controller", ctrl)
        return _workflow_result_to_response(
            result,
            cost_by_scenario=_extract_cost_by_scenario(inner_ctrl),
            cost_by_tier=_extract_cost_by_tier(inner_ctrl),
            cost_by_day=_extract_cost_by_day(inner_ctrl),
            cost_by_day_per_tier=_extract_cost_by_day_per_tier(inner_ctrl),
            total_cost_usd=_extract_total_cost(inner_ctrl),
        )

    @app.get("/api/workflows/active", response_model=WorkflowStatusResponse)
    def get_active_workflow(
        time_window: str = Query("all", description="7d|30d|all (Phase 8.16)"),
    ) -> WorkflowStatusResponse:
        """当前活跃工作流状态 (Phase 5+).
        Phase 8.16: 加 time_window query param (7d|30d|all, default all)
        """
        if ctx.master_controller is None:
            return WorkflowStatusResponse(is_active=False, workflow_name=None)
        since = _parse_time_window(time_window)
        return WorkflowStatusResponse(
            **ctx.master_controller.get_active_workflow_status(since=since)
        )

    @app.websocket("/api/ws/workflows")
    async def ws_workflows(ws: WebSocket) -> None:
        """实时推送工作流状态变化

        事件类型:
        - connected (握手):{type, snapshot: <active workflow dict>}
        - workflow.status:{type, payload: <active workflow dict>}
        - decision.snapshot:{type, payload: <pending decisions list>}

        master_controller 缺失时拒绝连接 (close 1011)。
        """
        if ctx.master_controller is None:
            await ws.close(code=1011, reason="master_controller not configured")
            return

        await ctx.manager.connect(ws)
        try:
            initial_workflow = ctx.master_controller.get_active_workflow_status()
            initial_decisions = ctx.master_controller.list_pending_decisions()
            await ctx.manager.send_to(ws, {
                "type": EVENT_CONNECTED,
                "snapshot": initial_workflow,
                "pending_decisions": initial_decisions,
            })
            while True:
                try:
                    await ws.receive_text()
                except WebSocketDisconnect:
                    break
        finally:
            await ctx.manager.disconnect(ws)

    @app.get(
        "/api/workflows/{workflow_name}/mermaid",
        response_model=WorkflowMermaidResponse,
    )
    def get_workflow_mermaid(
        workflow_name: str,
        include_status: bool = False,
    ) -> WorkflowMermaidResponse:
        """渲染工作流 YAML 为 mermaid 字符串 (供前端 mermaid.js 渲染)

        流程:
        1. load_workflow(name) → ThoughtGraph
        2. 可选:若 include_status=true 且有活跃工作流 → 拿 executions 染色
        3. render_mermaid(graph, executions=...) → mermaid 字符串
        4. 返回 {workflow_name, mermaid, node_count, has_decision_nodes,
                 status_applied, node_statuses}

        Raises:
            404: workflow YAML 不存在
            422: workflow 解析/验证失败
        """
        from datetime import datetime, timezone

        from infra.got.data_structures import NodeExecution, NodeStatus, NodeType
        from infra.got.visualizer import render_mermaid
        from infra.got.workflow_loader import (
            WorkflowError,
            WorkflowNotFoundError,
            load_workflow,
        )

        try:
            graph = load_workflow(workflow_name)
        except WorkflowNotFoundError:
            raise HTTPException(status_code=404, detail=f"workflow not found: {workflow_name}")
        except WorkflowError as e:
            raise HTTPException(status_code=422, detail=f"workflow load failed: {e}")

        status_applied = False
        node_statuses: dict[str, str] = {}
        executions: dict[str, NodeExecution] = {}
        if include_status:
            try:
                ctrl = require_controller(ctx)
                active = ctrl.get_active_workflow_status()
                if active.get("is_active"):
                    raw = active.get("executions", {}) or {}
                    for nid, st in raw.items():
                        try:
                            executions[nid] = NodeExecution(
                                node_id=nid,
                                status=NodeStatus(st),
                                started_at=datetime.now(timezone.utc),
                            )
                        except ValueError:
                            continue
                    node_statuses = dict(raw)
                    status_applied = True
            except Exception:
                pass

        mermaid_str = render_mermaid(graph, executions=executions, include_classdef=True)
        has_decision = any(
            graph.get_node(nid).type == NodeType.DECISION
            for nid in graph.node_ids()
        )
        return WorkflowMermaidResponse(
            workflow_name=workflow_name,
            mermaid=mermaid_str,
            node_count=len(list(graph.node_ids())),
            has_decision_nodes=has_decision,
            status_applied=status_applied,
            node_statuses=node_statuses,
        )
