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


_PHASE_102_DEFAULT_SETTINGS = {
    "default_provider": "minimax",
    "default_models": {},
    "auto_generate": False,
    "max_assets": 20,
    "confirm_before_generate": False,
    "fallback_chain": [],  # Phase 101
    "fallback_models": {},  # Phase 102 NEW
    "chapter_overrides": {},  # Phase 102 NEW
    "notify_threshold": 3,  # Phase 102 NEW. Phase 104 widens to int|dict; int default = 3 (no validator run when field unset)
}


def test_get_settings_returns_defaults_when_yaml_missing(client):
    """No yaml on disk → returns ProjectSettings() with all defaults (Phase 102: 9 fields)."""
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    expected = dict(_PHASE_102_DEFAULT_SETTINGS)
    assert body == expected


def test_put_settings_persists_yaml(client):
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"default_provider": "openai"},
    )
    assert resp.status_code == 200
    expected = dict(_PHASE_102_DEFAULT_SETTINGS, default_provider="openai")
    assert resp.json() == expected

    yaml_path = Path("projects") / "test-slug" / ".lingwen" / "illustration_settings.yaml"
    assert yaml_path.exists()
    # Phase 102: yaml now contains all 9 fields (PyYAML sorts alphabetically)
    assert yaml_path.read_text(encoding="utf-8").strip() == (
        "auto_generate: false\n"
        "chapter_overrides: {}\n"
        "confirm_before_generate: false\n"
        "default_models: {}\n"
        "default_provider: openai\n"
        "fallback_chain: []\n"
        "fallback_models: {}\n"
        "max_assets: 20\n"
        "notify_threshold: 3"
    )


def test_put_then_get_round_trips(client):
    """Phase 104: PUT response uses int=3 field default; GET read-time validator
    expands `notify_threshold` to 4-key dict. Test asserts both forms valid."""
    client.put("/api/projects/test-slug/settings", json={"default_provider": "stability"})
    resp = client.get("/api/projects/test-slug/settings")
    expected = dict(_PHASE_102_DEFAULT_SETTINGS, default_provider="stability")
    # notify_threshold: field default = 3 (int) at PUT-time validator skip;
    # read-time validator expands to 4-key dict on GET
    expected["notify_threshold"] = {
        "generation": 3, "regeneration": 3, "cleanup": 3, "deletion": 3,
    }
    assert resp.json() == expected


def test_get_settings_corrupt_yaml_returns_defaults(client, tmp_path):
    """Corrupt yaml file → silently fallback to defaults (Phase 96 §3.8)."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text("not: valid: yaml: [", encoding="utf-8")

    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    assert resp.json() == _PHASE_102_DEFAULT_SETTINGS


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
    # Phase 104 read-time validator expands int=3 to 4-key dict on read;
    # PUT response uses int field default. Assert per-field instead of full equality.
    get_body = resp.json()
    assert get_body["default_provider"] == body["default_provider"]
    assert get_body["auto_generate"] == body["auto_generate"]
    assert get_body["max_assets"] == body["max_assets"]
    assert get_body["confirm_before_generate"] == body["confirm_before_generate"]
    assert get_body["notify_threshold"] == {
        "generation": 3, "regeneration": 3, "cleanup": 3, "deletion": 3,
    }


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


# ---- Phase 101: fallback_chain field ----

def test_settings_pydantic_accepts_fallback_chain():
    """Phase 101: ProjectSettings accepts fallback_chain as list[str]."""
    from apps.studio_api.routes.project_settings import ProjectSettings
    s = ProjectSettings(fallback_chain=["openai", "stability"])
    assert s.fallback_chain == ["openai", "stability"]


def test_settings_pydantic_default_empty_list():
    """Phase 101: default fallback_chain is []."""
    from apps.studio_api.routes.project_settings import ProjectSettings
    s = ProjectSettings()
    assert s.fallback_chain == []


def test_put_then_get_fallback_chain_round_trips(client):
    """Phase 101: PUT then GET round-trips fallback_chain."""
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={"fallback_chain": ["openai", "stability"]},
    )
    assert resp.status_code == 200
    assert resp.json()["fallback_chain"] == ["openai", "stability"]

    resp2 = client.get("/api/projects/test-slug/settings")
    assert resp2.json()["fallback_chain"] == ["openai", "stability"]


def test_old_yaml_missing_fallback_chain_defaults_empty(client, tmp_path):
    """Phase 101 back-compat: old yaml (no fallback_chain) loads with []."""
    yaml_path = tmp_path / "projects" / "test-slug" / ".lingwen"
    yaml_path.mkdir(parents=True)
    (yaml_path / "illustration_settings.yaml").write_text(
        "default_provider: openai\n",
        encoding="utf-8",
    )
    resp = client.get("/api/projects/test-slug/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_provider"] == "openai"
    assert body["fallback_chain"] == []  # back-compat: defaults fill
