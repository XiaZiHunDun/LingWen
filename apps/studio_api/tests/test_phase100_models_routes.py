"""Phase 100: illustrations route model field + provider models catalog tests.

Validates the new GET /api/illustrations/providers/{name}/models endpoint that
returns the per-provider model catalog (Phase 100 Multi-Model Per Provider).
The endpoint is mounted via register_illustrations(); we use the same
minimal-app pattern as test_illustrations_api.py (no full create_app —
avoids CVG / studio / onboarding router boot).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _stub_ctx():
    """Minimal RoutesContext — illustrations router doesn't read any field today."""
    from apps.studio_api.routes.ctx import RoutesContext

    return RoutesContext(
        db=None,  # type: ignore[arg-type]
        master_controller=None,
        manager=None,  # type: ignore[arg-type]
        limiter=None,  # type: ignore[arg-type]
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,  # type: ignore[arg-type]
    )


@pytest.fixture
def client():
    """Spin up TestClient with illustrations router only."""
    from apps.studio_api.routes.illustrations import register_illustrations

    app = FastAPI()
    register_illustrations(app, _stub_ctx())
    return TestClient(app)


def test_get_provider_models_returns_catalog(client):
    """GET /api/illustrations/providers/openai/models returns 4 models + default."""
    resp = client.get("/api/illustrations/providers/openai/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openai"
    assert set(data["models"]) == {"dall-e-3", "dall-e-3-hd", "dall-e-2", "gpt-image-1"}
    assert data["default_model"] == "dall-e-3"


def test_get_provider_models_unknown_returns_404(client):
    """GET with unknown provider name returns 404."""
    resp = client.get("/api/illustrations/providers/nonexistent/models")
    assert resp.status_code == 404


def test_get_provider_models_minimax_catalog(client):
    """GET /api/illustrations/providers/minimax/models returns 2 models."""
    resp = client.get("/api/illustrations/providers/minimax/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "minimax"
    assert set(data["models"]) == {"minimax-multimodal", "minimax-vision-01"}
    assert data["default_model"] == "minimax-multimodal"


def test_get_provider_models_stability_catalog(client):
    """GET /api/illustrations/providers/stability/models returns 5 models."""
    resp = client.get("/api/illustrations/providers/stability/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "stability"
    assert set(data["models"]) == {
        "sd3-medium",
        "sd3-large",
        "sd3-large-turbo",
        "stable-image-core",
        "stable-image-ultra",
    }
    assert data["default_model"] == "sd3-medium"
