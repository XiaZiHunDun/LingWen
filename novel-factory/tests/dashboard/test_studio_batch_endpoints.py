"""Dashboard studio batch run endpoints."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    import infra.studio_registry as registry
    from dashboard.app import create_app

    state = tmp_path / "studio_active.json"
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    monkeypatch.setattr(registry, "active_state_path", lambda: state)
    monkeypatch.setattr("infra.studio_batch_runner._jobs_dir", lambda: jobs)
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    registry.activate_project("anye-xinbiao")

    app = create_app()
    return TestClient(app)


class TestStudioBatchEndpoints:
    @patch("infra.studio_batch_runner.subprocess.Popen")
    def test_run_batch(self, mock_popen, client: TestClient) -> None:
        proc = MagicMock()
        proc.pid = 9999
        mock_popen.return_value = proc

        resp = client.post(
            "/api/studio/production/run",
            json={
                "start_chapter": 1,
                "end_chapter": 1,
                "mode": "canon",
                "budget_usd": 0.12,
                "skip_preflight": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert data["slug"] == "anye-xinbiao"

        job_id = data["job_id"]
        status = client.get(f"/api/studio/production/jobs/{job_id}")
        assert status.status_code == 200
        assert status.json()["job_id"] == job_id

    def test_production_records_use_active_project(self, client: TestClient) -> None:
        resp = client.get("/api/studio/summary")
        assert resp.status_code == 200
        summary = resp.json()

        records = client.get("/api/production-records/rollup?limit=5")
        assert records.status_code == 200
        assert summary["pilot_records_dir"] in records.json()["records_dir"]
