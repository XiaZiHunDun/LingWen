"""
Phase 15.0 T1.4: /api/decisions/* routes.

Extracted from dashboard/app.py create_app closure (was at app.py lines 382-442).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from dashboard.helpers.decision import _decision_to_response
from dashboard.models import (
    CancelDecisionRequest,
    DecisionResponse,
    DeferDecisionRequest,
    ResolveDecisionRequest,
)
from dashboard.routes.ctx import RoutesContext, require_controller


def register_decisions(app: FastAPI, ctx: RoutesContext) -> None:
    @app.get("/api/decisions/pending", response_model=list[DecisionResponse])
    def get_pending_decisions() -> list[DecisionResponse]:
        """列出 PENDING 决策 (按 priority desc + due_at asc)"""
        ctrl = require_controller(ctx)
        return [_decision_to_response(d) for d in ctrl.list_pending_decisions()]

    @app.get("/api/decisions/all", response_model=list[DecisionResponse])
    def get_all_decisions() -> list[DecisionResponse]:
        """列出全部决策 (含 RESOLVED/DEFERRED/CANCELLED)"""
        ctrl = require_controller(ctx)
        queue = ctrl.get_decision_queue()
        return [_decision_to_response(d) for d in queue.all_decisions()]

    @app.post(
        "/api/decisions/{decision_id}/resolve",
        response_model=DecisionResponse,
    )
    def resolve_decision(decision_id: str, body: ResolveDecisionRequest) -> DecisionResponse:
        """解决决策 (PENDING → RESOLVED)"""
        ctrl = require_controller(ctx)
        try:
            d = ctrl.resolve_decision(
                decision_id, body.option, resolved_by=body.resolved_by
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _decision_to_response(d)

    @app.post(
        "/api/decisions/{decision_id}/defer",
        response_model=DecisionResponse,
    )
    def defer_decision(decision_id: str, body: DeferDecisionRequest) -> DecisionResponse:
        """推迟决策 (PENDING → DEFERRED)"""
        ctrl = require_controller(ctx)
        try:
            d = ctrl.defer_decision(decision_id, reason=body.reason)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _decision_to_response(d)

    @app.post(
        "/api/decisions/{decision_id}/cancel",
        response_model=DecisionResponse,
    )
    def cancel_decision(decision_id: str, body: CancelDecisionRequest) -> DecisionResponse:
        """取消决策 (PENDING → CANCELLED)"""
        ctrl = require_controller(ctx)
        try:
            d = ctrl.cancel_decision(decision_id, reason=body.reason)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _decision_to_response(d)
