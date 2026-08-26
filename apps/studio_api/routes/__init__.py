"""
Phase 15.0 T1.4: route registration facade.

Each route module exposes a `register_X(app, ctx)` function; this package
re-exports them and provides a single `register_all_routes(app, ctx)` entry
point that dashboard.app.create_app calls once.
"""
from __future__ import annotations

from fastapi import FastAPI

from apps.studio_api.routes.budgets import register_budgets
from apps.studio_api.routes.creator_core import register_creator_core
from apps.studio_api.routes.creator_onboarding import register_creator_onboarding
from apps.studio_api.routes.creator_settings import register_creator_settings
from apps.studio_api.routes.creator_volume import register_creator_volume
from apps.studio_api.routes.ctx import RoutesContext
from apps.studio_api.routes.cvg import register_cvg
from apps.studio_api.routes.decisions import register_decisions
from apps.studio_api.routes.health import register_health
from apps.studio_api.routes.overview import register_overview
from apps.studio_api.routes.studio import register_studio
from apps.studio_api.routes.workflows import register_workflows
from apps.studio_api.routes.write_workspace import register_write_workspace


def register_all_routes(app: FastAPI, ctx: RoutesContext) -> None:
    """Wire every route group onto app.

    Phase 15.0 T1.4: replaces the 167 inline @app.{get,post,put,delete,patch,websocket}
    decorators previously nested inside create_app's closure.
    """
    register_health(app, ctx)
    register_overview(app, ctx)
    register_decisions(app, ctx)
    register_cvg(app, ctx)
    register_workflows(app, ctx)
    register_budgets(app, ctx)
    register_studio(app, ctx)
    register_creator_core(app, ctx)
    register_creator_volume(app, ctx)
    register_creator_onboarding(app, ctx)
    register_creator_settings(app, ctx)
    register_write_workspace(app, ctx)


__all__ = [
    "RoutesContext",
    "register_all_routes",
    "register_health",
    "register_overview",
    "register_decisions",
    "register_cvg",
    "register_workflows",
    "register_budgets",
    "register_studio",
    "register_creator_core",
    "register_creator_volume",
    "register_creator_onboarding",
    "register_creator_settings",
    "register_write_workspace",
]
