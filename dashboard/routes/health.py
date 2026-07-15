"""
Phase 15.0 T1.4: /api/health route.

Extracted from dashboard/app.py create_app closure (was at app.py line 243-246).
"""
from __future__ import annotations

from fastapi import FastAPI

from dashboard.models import HealthResponse
from dashboard.routes.ctx import RoutesContext


def register_health(app: FastAPI, ctx: RoutesContext) -> None:
    @app.get("/api/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", service="reading-power-dashboard")
