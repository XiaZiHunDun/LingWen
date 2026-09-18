"""Verify write_workspace auto_generate settings read end-to-end (Phase 98 Task 12).

Phase 90 wrote the dead-branch code:
    settings = _get_illustration_settings(project)
    if settings.get("auto_generate", False):
        background_tasks.add_task(illustrations_auto_generate_task, ...)

Phase 96 added ProjectSettings with only default_provider, so auto_generate
was always False (never persisted).

Phase 98 Task 3 extended ProjectSettings to 4 fields with auto_generate
default False. This test verifies that PUT /settings with auto_generate=True
round-trips and that _get_illustration_settings surfaces it correctly.
"""
from __future__ import annotations

from pathlib import Path


def test_auto_generate_settings_persists_and_loads(tmp_path, monkeypatch):
    """PUT settings with auto_generate=True round-trips through _get_illustration_settings."""
    from fastapi.testclient import TestClient

    from apps.studio_api.app import create_app
    from apps.studio_api.background import _get_illustration_settings

    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "test-slug").mkdir(parents=True)

    app = create_app()
    client = TestClient(app)

    # 1. PUT settings with auto_generate=True
    resp = client.put(
        "/api/projects/test-slug/settings",
        json={
            "default_provider": "minimax",
            "auto_generate": True,
            "max_assets": 20,
            "confirm_before_generate": False,
        },
    )
    assert resp.status_code == 200

    # 2. _get_illustration_settings reads back auto_generate=True
    settings = _get_illustration_settings("test-slug")
    assert settings.get("auto_generate") is True
    assert settings.get("default_provider") == "minimax"


def test_auto_generate_defaults_to_false(tmp_path, monkeypatch):
    """Without settings yaml, auto_generate defaults to False (silent no-op)."""
    from apps.studio_api.background import _get_illustration_settings

    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "test-slug").mkdir(parents=True)

    # No yaml on disk — should silently default
    settings = _get_illustration_settings("test-slug")
    assert settings.get("auto_generate") is False
