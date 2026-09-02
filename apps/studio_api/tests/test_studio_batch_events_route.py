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


@pytest.fixture(autouse=True)
def _enable_batch(monkeypatch):
    """Enable the dashboard batch flag so the SSE read gate (Phase 25) allows reads."""
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")


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


def test_events_route_403_when_batch_disabled(client, monkeypatch):
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "0")
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j5")):
        resp = client.get("/api/studio/batch/j5/events")
    assert resp.status_code == 403


def test_events_route_400_for_unknown_event_type(client):
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j6")):
        resp = client.get("/api/studio/batch/j6/events", params={"event_types": "bogus"})
    assert resp.status_code == 400
    assert "bogus" in resp.json()["detail"]


def test_events_route_403_for_slug_mismatch(client):
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j7", slug="my-project")):
        resp = client.get("/api/studio/batch/j7/events", params={"slug": "other-project"})
    assert resp.status_code == 403


def test_events_route_403_for_mode_mismatch(client):
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j8", mode="pilot")):
        resp = client.get("/api/studio/batch/j8/events", params={"mode": "canon"})
    assert resp.status_code == 403


def test_events_route_replay_emits_chapter_history(client):
    job = _job(job_id="j9", status="completed")
    with (
        patch("infra.studio_batch_runner._load_job", return_value=job),
        patch("infra.studio_batch_runner._completed_chapter_nums", return_value=[2, 3]),
    ):
        resp = client.get("/api/studio/batch/j9/events", params={"replay": 1})
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "event: job_state" in body
    assert "event: chapter_completed" in body
    assert '"chapter_num": 2' in body
    assert '"chapter_num": 3' in body
    assert "event: job_completed" in body


def test_events_route_event_types_filter_applied(client):
    # Terminal job so the stream ends immediately (a running job would loop forever
    # in the SSE live tail and hang the blocking TestClient). The requested filter
    # excludes job_state and the terminal event, so none should be emitted.
    with patch("infra.studio_batch_runner._load_job", return_value=_job(job_id="j10", status="completed")):
        resp = client.get("/api/studio/batch/j10/events", params={"event_types": "chapter_completed"})
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "event: job_state" not in body
    assert "event: job_completed" not in body
