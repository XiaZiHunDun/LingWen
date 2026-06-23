"""Dashboard creator overview endpoint."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    import infra.studio_registry as registry
    from dashboard.app import create_app

    state = tmp_path / "studio_active.json"
    monkeypatch.setattr(registry, "active_state_path", lambda: state)
    registry.activate_project("anye-xinbiao")

    app = create_app()
    return TestClient(app)


class TestCreatorEndpoints:
    def test_overview(self, client: TestClient) -> None:
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "anye-xinbiao"
        assert data["chapters_written"] == 10
        assert len(data["chapters"]) >= 10
        assert "companion_check_cmd" in data

    def test_summary_includes_creation_mode(self, client: TestClient) -> None:
        resp = client.get("/api/studio/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "creation_mode" in data
        assert "quality_profile" in data
