"""
Phase 15.0 T1.4: /api/budgets and /api/budgets/by-tier routes.

Extracted from dashboard/app.py create_app closure (was at app.py lines 1071-1172).

Note: budget endpoints read from `MasterControllerAdapter._controller` (class-level
singleton), not from the closure-captured master_controller. This is the historical
behavior — kept identical after extraction.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from dashboard.models import BudgetSetRequest, BudgetTierSetRequest
from dashboard.routes.ctx import RoutesContext


def register_budgets(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/budgets")
    async def get_budgets() -> dict[str, Any]:
        """Phase 8.12 T5: 返 3 档 current budget + status

        Returns:
            dict with keys: per_run, per_day, per_week
            每个 value 是 dict {status, budget_usd, used_usd, used_pct} 或 {} (无 budget)
        """
        from dashboard.protocols import (
            MasterControllerAdapter,
            _extract_budget_per_window,
            _extract_budget_status,
        )
        controller = MasterControllerAdapter._controller
        return {
            "per_run": _extract_budget_status(controller),
            "per_day": _extract_budget_per_window(controller, "day"),
            "per_week": _extract_budget_per_window(controller, "week"),
        }

    @app.put("/api/budgets/{scope}")
    async def set_budget(scope: str, req: BudgetSetRequest) -> dict[str, Any]:
        """Phase 8.12 T5: 设置 day/week budget (per-run 不暴露, run 启动时传)

        Raises:
            400: scope not in ('day', 'week')
            422: usd < 0 or usd > 10000
            503: budget_service not initialized on controller
        """
        if scope not in ("day", "week"):
            raise HTTPException(400, "scope must be 'day' or 'week'")
        from dashboard.protocols import MasterControllerAdapter
        controller = MasterControllerAdapter._controller
        service = getattr(controller, "budget_service", None)
        if service is None:
            raise HTTPException(503, "budget service not initialized")
        service.set(scope, req.usd, run_id=None)
        return {"ok": True, "scope": scope, "usd": req.usd}

    @app.get("/api/budgets/by-tier")
    async def get_budgets_by_tier() -> dict[str, Any]:
        """Phase 8.15 T6: 返 3 tier current budget entries (haiku/sonnet/opus)."""
        from dashboard.protocols import (
            MasterControllerAdapter,
            _extract_budget_by_tier,
        )
        controller = MasterControllerAdapter._controller
        return _extract_budget_by_tier(controller)

    @app.put("/api/budgets/by-tier/{tier}")
    async def set_budget_by_tier(tier: str, req: BudgetTierSetRequest) -> dict[str, Any]:
        """Phase 8.15 T6: 设置 tier budget (haiku/sonnet/opus 各自).

        Raises:
            404: tier not in ('haiku','sonnet','opus')
            422: usd < 0 or usd > 10000
            503: budget_service_by_tier not initialized on controller
        """
        from dashboard.protocols import MasterControllerAdapter
        from infra.ai_service.model_tiers import ModelTier

        try:
            tier_enum = ModelTier(tier)
        except ValueError:
            raise HTTPException(
                404, f"invalid tier: {tier!r}, must be 'haiku'/'sonnet'/'opus'"
            )
        controller = MasterControllerAdapter._controller
        service = getattr(controller, "budget_service_by_tier", None)
        if service is None:
            raise HTTPException(503, "tier budget service not initialized")
        service.set_by_tier(tier_enum, req.usd)
        return {"ok": True, "tier": tier, "usd": req.usd}
