"""Integration tests for GET /api/studio/batch/history (Phase 23 Task 6)."""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.studio_api.routes.studio import register_studio


@pytest.fixture
def app():
    a = FastAPI()
    register_studio(a, ctx=None)
    return a


@pytest.fixture
def client(app):
    return TestClient(app)


def test_history_route_returns_jobs_for_slug(client):
    rows = [
        {
            "job_id": "j1",
            "slug": "my-project",
            "start_chapter": 1,
            "end_chapter": 10,
            "budget_usd": 0.15,
            "mode": "canon",
            "status": "completed",
            "pid": 99999,
            "log_path": "/tmp/j1.log",
            "started_at": "2026-09-01T00:00:00+00:00",
            "finished_at": "2026-09-01T00:10:00+00:00",
            "exit_code": 0,
            "error": None,
        },
        {
            "job_id": "j2",
            "slug": "my-project",
            "start_chapter": 11,
            "end_chapter": 20,
            "budget_usd": 0.2,
            "mode": "pilot",
            "status": "failed",
            "pid": None,
            "log_path": "/tmp/j2.log",
            "started_at": "2026-09-02T00:00:00+00:00",
            "finished_at": None,
            "exit_code": None,
            "error": "oops",
        },
    ]
    with patch(
        "infra.studio_batch_runner.list_batch_jobs_for_slug",
        return_value=rows,
    ):
        resp = client.get("/api/studio/batch/history", params={"slug": "my-project", "limit": 20})
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["jobs"]) == 2
    # pid/log_path dropped from summary DTO (extra="ignore")
    assert "pid" not in payload["jobs"][0]
    assert "log_path" not in payload["jobs"][0]
    assert payload["jobs"][0]["job_id"] == "j1"
    assert payload["jobs"][1]["status"] == "failed"


def test_history_route_uses_default_limit_20(client):
    """When no limit param is provided, the route should still respond successfully.

    The infra call's actual `limit` value is exercised by the
    `infra.studio_batch_runner.list_batch_jobs_for_slug` mock — we only
    assert the route shape here.
    """
    with patch(
        "infra.studio_batch_runner.list_batch_jobs_for_slug",
        return_value=[],
    ) as mock_list:
        resp = client.get("/api/studio/batch/history", params={"slug": "anything"})
    assert resp.status_code == 200
    assert resp.json() == {"jobs": []}
    # Default limit passed via FastAPI query param default=20 → list_batch_jobs_for_slug
    args, kwargs = mock_list.call_args
    assert kwargs.get("limit") == 20


def test_history_route_filters_by_slug(client):
    """Route must pass slug to infra helper so jobs from other slugs don't leak."""
    with patch(
        "infra.studio_batch_runner.list_batch_jobs_for_slug",
        return_value=[],
    ) as mock_list:
        resp = client.get("/api/studio/batch/history", params={"slug": "项目 with spaces"})
    assert resp.status_code == 200
    args, kwargs = mock_list.call_args
    assert args[0] == "项目 with spaces"


def test_history_route_rejects_oversized_limit(client):
    resp = client.get("/api/studio/batch/history", params={"slug": "x", "limit": 9999})
    assert resp.status_code == 422