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

    def test_volume_plan_get_put(self, client: TestClient) -> None:
        resp = client.get("/api/creator/volume-plan")
        assert resp.status_code == 200
        assert "volumes" in resp.json()

        put = client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 5,
                        "core_conflict": "开篇",
                        "locked": True,
                    },
                ],
            },
        )
        assert put.status_code == 200
        data = put.json()
        assert data["locked_volume_count"] == 1
        assert data["volumes"][0]["locked"] is True

    def test_overview_includes_deviations(self, client: TestClient) -> None:
        client.put(
            "/api/creator/volume-plan",
            json={
                "volumes": [
                    {
                        "label": "一",
                        "start_chapter": 1,
                        "end_chapter": 10,
                        "core_conflict": "全书",
                        "locked": True,
                    },
                ],
            },
        )
        resp = client.get("/api/creator/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locked_volume_count"] == 1
        assert "deviations" in data

    def test_chapter_preview(self, client: TestClient) -> None:
        resp = client.get("/api/creator/chapters/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chapter"] == 1
        assert "body_preview" in data
        assert "outline_preview" in data
        assert data["has_body"] is True

    def test_settings_docs_get(self, client: TestClient) -> None:
        resp = client.get("/api/creator/settings-docs")
        assert resp.status_code == 200
        data = resp.json()
        assert "pillars_text" in data
        assert "global_outline_text" in data
