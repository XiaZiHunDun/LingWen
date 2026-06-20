"""Dashboard studio endpoints (Phase 10.04)."""
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


class TestStudioEndpoints:
    def test_list_projects(self, client: TestClient) -> None:
        resp = client.get("/api/studio/projects")
        assert resp.status_code == 200
        data = resp.json()
        slugs = {p["slug"] for p in data["projects"]}
        assert "anye-xinbiao" in slugs
        assert data["active_slug"] == "anye-xinbiao"

    def test_get_active(self, client: TestClient) -> None:
        resp = client.get("/api/studio/active")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "anye-xinbiao"

    def test_set_active(self, client: TestClient) -> None:
        resp = client.put("/api/studio/active", json={"slug": "xingyun-jiyuan"})
        assert resp.status_code == 200
        assert resp.json()["slug"] == "xingyun-jiyuan"

    def test_summary(self, client: TestClient) -> None:
        resp = client.get("/api/studio/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "anye-xinbiao"
        assert data["chapter_count"] == 10

    def test_quality(self, client: TestClient) -> None:
        resp = client.get("/api/studio/quality")
        assert resp.status_code == 200
        data = resp.json()
        assert data["golden_set_status"] == "ready"

    def test_quality_report(self, client: TestClient) -> None:
        resp = client.get("/api/studio/quality-report")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "anye-xinbiao"
        assert "total" in data
        assert "chapters" in data

    def test_quality_report_includes_prose_heatmap(self, client: TestClient) -> None:
        resp = client.get("/api/studio/quality-report")
        assert resp.status_code == 200
        data = resp.json()
        assert "prose_heatmap" in data
        assert "chapters" in data["prose_heatmap"]

    def test_prose_diff_available(self, client: TestClient) -> None:
        resp = client.get("/api/studio/prose-diff")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "anye-xinbiao"
        assert data["available"] is True
        assert "total_delta" in data
        assert "chapters" in data
        assert "has_regression" in data
        assert isinstance(data["net_prose_p1_delta"], int)

    def test_prose_diff_no_baseline(self, client: TestClient) -> None:
        resp = client.put("/api/studio/active", json={"slug": "huangsha-dangan"})
        assert resp.status_code == 200
        resp = client.get("/api/studio/prose-diff")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "huangsha-dangan"
        assert data["available"] is False
        assert data["reason"] == "no_baseline"
        assert "run-prose-diff.sh" in (data.get("save_command") or "")

    def test_preflight(self, client: TestClient) -> None:
        resp = client.post(
            "/api/studio/production/preflight?budget_usd=0.12",
            json={"start_chapter": 1, "end_chapter": 2, "mode": "canon"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["all_ok"] is True
        assert "run-project-batch.sh" in data["batch_command"]
