"""Thin-shell tests for /api/world/* routes."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    from apps.studio_api.routes.ctx import RoutesContext
    return RoutesContext(
        db=None, master_controller=None, manager=None, limiter=None,
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,
    )


def _mount(app):
    from apps.studio_api.routes.world import register_world
    register_world(app, _stub_ctx())


def test_world_routes_registered():
    app = FastAPI()
    _mount(app)
    methods = {(r.path, tuple(sorted(r.methods or []))) for r in app.routes}
    assert ("/api/world/characters", ("GET",)) in methods
    assert ("/api/world/factions", ("GET",)) in methods
    assert ("/api/world/lore", ("GET",)) in methods
    assert ("/api/world/timeline", ("GET",)) in methods
    assert ("/api/world/proposals", ("GET",)) in methods
