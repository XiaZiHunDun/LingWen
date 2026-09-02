"""Integration tests for GET /api/studio/batch/<job_id>/events SSE route (Phase 24)."""

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


def _job(job_id: str = "j1", **overrides) -> BatchJob:
    base = dict(
        job_id=job_id,
        slug="my-project",
        start_chapter=1,
        end_chapter=10,
        budget_usd=0.15,
        mode="pilot",
        status="completed",
        pid=None,
        log_path="/tmp/j1.log",
        started_at="2026-09-01T00:00:00+00:00",
        finished_at="2026-09-01T00:10:00+00:00",
        exit_code=0,
        error=None,
    )
    base.update(overrides)
    return BatchJob(**base)


def test_events_route_returns_404_for_missing_job(client):
    with patch("infra.studio_batch_runner._load_job", return_value=None):
        resp = client.get("/api/studio/batch/nope/events")
    assert resp.status_code == 404
    assert "nope" in resp.json()["detail"]


def test_events_route_returns_200_with_sse_headers(client):
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j1")):
        resp = client.get("/api/studio/batch/j1/events")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert resp.headers["cache-control"] == "no-cache"


def test_events_route_sends_initial_job_state_event(client):
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j3")):
        resp = client.get("/api/studio/batch/j3/events")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "event: job_state" in body
    assert '"job_id": "j3"' in body


def test_events_route_terminal_job_closes_stream_with_terminal_event(client):
    job = _job(job_id="j4", status="failed", exit_code=1, error="boom")
    with patch("infra.studio_batch_runner._load_job", return_value=job):
        resp = client.get("/api/studio/batch/j4/events")
    assert resp.status_code == 200
    body = resp.content.decode()
    # Initial state + a synthesized terminal event lets the client close instead
    # of waiting on an already-finished job forever.
    assert "event: job_state" in body
    assert "event: job_failed" in body
    assert '"status": "failed"' in body