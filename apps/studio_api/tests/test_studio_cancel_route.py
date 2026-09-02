"""Integration tests for POST /api/studio/batch/<job_id>/cancel."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.studio_api.routes.studio import register_studio
from infra.studio_batch_runner import BatchJob


@pytest.fixture
def app():
    a = FastAPI()
    register_studio(a, ctx=None)
    return a


@pytest.fixture
def client(app):
    return TestClient(app)


def _make_running_job(job_id: str = "abc-123") -> BatchJob:
    """Construct a real BatchJob dataclass (MagicMock would fail Pydantic validation)."""
    return BatchJob(
        job_id=job_id,
        slug="test-slug",
        start_chapter=1,
        end_chapter=10,
        budget_usd=5.0,
        mode="pilot",
        status="running",
        pid=99999,
        log_path="/tmp/fake.log",
        started_at="2026-09-02T00:00:00+00:00",
    )


def test_cancel_route_returns_200_with_cancelled_status(client):
    job = _make_running_job("abc-123")
    with patch(
        "infra.studio_batch_runner.cancel_batch_job",
        return_value=job,
    ):
        resp = client.post("/api/studio/batch/abc-123/cancel")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["job_id"] == "abc-123"
    assert payload["status"] == "running"


def test_cancel_route_returns_404_for_unknown_job_id(client):
    with patch(
        "infra.studio_batch_runner.cancel_batch_job",
        side_effect=LookupError("batch job not found: 'ghost'"),
    ):
        resp = client.post("/api/studio/batch/ghost/cancel")
    assert resp.status_code == 404


def test_cancel_route_returns_409_for_terminal_state(client):
    with patch(
        "infra.studio_batch_runner.cancel_batch_job",
        side_effect=RuntimeError("batch job 'done-001' is in terminal state 'completed', cannot cancel"),
    ):
        resp = client.post("/api/studio/batch/done-001/cancel")
    assert resp.status_code == 409
