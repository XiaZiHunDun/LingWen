"""Test PUT/GET /api/projects/{slug}/settings (Phase 96)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.studio_api.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with tmp_path as project_root parent."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "test-slug").mkdir(parents=True)
    app = create_app()
    return TestClient(app)


def test_get_settings_returns_defaults_when_yaml_missing(client):
    """No yaml on disk → returns ProjectSettings() with default_provider='minimax'."""
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"default_provider": "minimax"}


def test_put_settings_persists_yaml(client):
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"default_provider": "openai"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"default_provider": "openai"}

    yaml_path = Path("projects") / "test-slug" / ".lingwen" / "illustration_settings.yaml"
    assert yaml_path.exists()
    assert yaml_path.read_text(encoding="utf-8").strip() == "default_provider: openai"


def test_put_then_get_round_trips(client):
    client.put("/api/projects/test-slug/settings", json={"default_provider": "stability"})
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.json() == {"default_provider": "stability"}


def test_get_settings_corrupt_yaml_returns_defaults(client, tmp_path):
    """Corrupt yaml file → silently fallback to defaults (Phase 96 §3.8)."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text("not: valid: yaml: [", encoding="utf-8")

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    assert resp.json() == {"default_provider": "minimax"}


def test_put_settings_invalid_provider_rejected(client):
    """Pydantic Literal validation: unknown provider name → 422."""
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"default_provider": "anthropic"},  # not in Literal
    )
    assert resp.status_code == 422


def test_put_settings_unknown_project_404(client):
    """Project slug not in projects/ → 404."""
    resp = client.put(
        "/api/projects/nonexistent-slug/settings",
        json={"default_provider": "openai"},
    )
    assert resp.status_code == 404
