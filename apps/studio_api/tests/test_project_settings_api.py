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
    """No yaml on disk → returns ProjectSettings() with all defaults (Phase 98: 4 fields)."""
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "default_provider": "minimax",
        "auto_generate": False,
        "max_assets": 20,
        "confirm_before_generate": False,
    }


def test_put_settings_persists_yaml(client):
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"default_provider": "openai"},
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "default_provider": "openai",
        "auto_generate": False,
        "max_assets": 20,
        "confirm_before_generate": False,
    }

    yaml_path = Path("projects") / "test-slug" / ".lingwen" / "illustration_settings.yaml"
    assert yaml_path.exists()
    # Phase 98: yaml now contains all 4 fields (PyYAML sorts alphabetically)
    assert yaml_path.read_text(encoding="utf-8").strip() == (
        "auto_generate: false\n"
        "confirm_before_generate: false\n"
        "default_provider: openai\n"
        "max_assets: 20"
    )


def test_put_then_get_round_trips(client):
    client.put("/api/projects/test-slug/settings", json={"default_provider": "stability"})
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.json() == {
        "default_provider": "stability",
        "auto_generate": False,
        "max_assets": 20,
        "confirm_before_generate": False,
    }


def test_get_settings_corrupt_yaml_returns_defaults(client, tmp_path):
    """Corrupt yaml file → silently fallback to defaults (Phase 96 §3.8)."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text("not: valid: yaml: [", encoding="utf-8")

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    assert resp.json() == {
        "default_provider": "minimax",
        "auto_generate": False,
        "max_assets": 20,
        "confirm_before_generate": False,
    }


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


# Phase 98: schema migration tests (S1-S5)


def test_old_yaml_defaults_fill(client, tmp_path):
    """S1: old yaml with only default_provider gets other fields defaulted."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text(
        "default_provider: openai\n", encoding="utf-8"
    )

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_provider"] == "openai"
    assert body["auto_generate"] is False
    assert body["max_assets"] == 20
    assert body["confirm_before_generate"] is False


def test_partial_yaml_merges(client, tmp_path):
    """S2: partial yaml (only max_assets) preserves other fields via defaults."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text(
        "max_assets: 5\n", encoding="utf-8"
    )

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["max_assets"] == 5
    assert body["default_provider"] == "minimax"
    assert body["auto_generate"] is False
    assert body["confirm_before_generate"] is False


def test_full_yaml_round_trip(client):
    """S3: full yaml with all 4 fields preserves all on PUT then GET."""
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={
            "default_provider": "stability",
            "auto_generate": True,
            "max_assets": 10,
            "confirm_before_generate": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_provider"] == "stability"
    assert body["auto_generate"] is True
    assert body["max_assets"] == 10
    assert body["confirm_before_generate"] is True

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.json() == body


def test_malformed_yaml_defaults(client, tmp_path):
    """S4: malformed yaml returns all defaults (existing test_get_settings_corrupt_yaml_returns_defaults also covers this)."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text(
        ":::bad yaml:::\n", encoding="utf-8"
    )

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_provider"] == "minimax"
    assert body["auto_generate"] is False
    assert body["max_assets"] == 20
    assert body["confirm_before_generate"] is False


def test_missing_yaml_defaults(client):
    """S5: missing yaml returns all defaults (covered by test_get_settings_returns_defaults_when_yaml_missing — verify new fields)."""
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_provider"] == "minimax"
    assert body["auto_generate"] is False
    assert body["max_assets"] == 20
    assert body["confirm_before_generate"] is False
