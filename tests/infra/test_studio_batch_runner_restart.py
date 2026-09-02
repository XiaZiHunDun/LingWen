"""Tests for auto-restart on failure (P2-RESTART) in infra/studio_batch_runner.

Covers: default single-attempt is terminal on failure, bounded retries keep the
same job_id while incrementing attempt, success after a restart, and queued
jobs preserving max_attempts on promotion.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.studio_batch_runner import (
    _load_job,
    _poll_job,
    submit_batch_job,
)
from infra.studio_registry import get_project_by_slug


@pytest.fixture
def anye_project(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("infra.studio_batch_runner._jobs_dir", lambda: tmp_path / "jobs")
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    return get_project_by_slug("anye-xinbiao")


def test_default_single_attempt_fails_terminal(anye_project, monkeypatch):
    """max_attempts unset (default 1) must not auto-restart on failure."""
    with (
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            return_value=MagicMock(pid=123),
        ),
        patch("infra.studio_batch_runner._process_running", return_value=False),
        patch("infra.studio_batch_runner._read_exit_code", return_value=1),
    ):
        job = submit_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.1,
            skip_preflight=True,
        )
        got = _poll_job(_load_job(job.job_id))
        assert got.status == "failed"
        assert got.exit_code == 1
        assert got.attempt == 1


def test_auto_restart_retries_until_max_then_fails(anye_project, monkeypatch):
    """Failure restarts the same job (same id) until max_attempts is reached."""
    calls = {"n": 0}

    def fake_popen(*args, **kwargs):
        calls["n"] += 1
        return MagicMock(pid=100 + calls["n"])

    with (
        patch("infra.studio_batch_runner.subprocess.Popen", side_effect=fake_popen),
        patch("infra.studio_batch_runner._process_running", return_value=False),
        patch("infra.studio_batch_runner._read_exit_code", return_value=1),
    ):
        job = submit_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.1,
            skip_preflight=True,
            max_attempts=3,
        )
        assert job.attempt == 1

        got = _poll_job(_load_job(job.job_id))
        assert got.status == "running" and got.attempt == 2
        assert got.job_id == job.job_id

        got = _poll_job(_load_job(job.job_id))
        assert got.status == "running" and got.attempt == 3
        assert got.finished_at is None

        got = _poll_job(_load_job(job.job_id))
        assert got.status == "failed"
        assert got.exit_code == 1
        assert got.attempt == 3

    assert calls["n"] == 3  # initial spawn + 2 restarts


def test_restart_then_complete(anye_project, monkeypatch):
    """A job that fails once and succeeds on retry ends completed."""
    exit_codes = iter([1, 0])
    calls = {"n": 0}

    def fake_popen(*args, **kwargs):
        calls["n"] += 1
        return MagicMock(pid=200 + calls["n"])

    with (
        patch("infra.studio_batch_runner.subprocess.Popen", side_effect=fake_popen),
        patch("infra.studio_batch_runner._process_running", return_value=False),
        patch(
            "infra.studio_batch_runner._read_exit_code",
            side_effect=lambda job: next(exit_codes),
        ),
    ):
        job = submit_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.1,
            skip_preflight=True,
            max_attempts=2,
        )
        got = _poll_job(_load_job(job.job_id))
        assert got.status == "running" and got.attempt == 2

        got = _poll_job(_load_job(job.job_id))
        assert got.status == "completed"
        assert got.exit_code == 0
        assert got.attempt == 2

    assert calls["n"] == 2


def test_queued_job_keeps_max_attempts_on_promotion(anye_project, monkeypatch):
    """A queued job carries its max_attempts through auto-promotion."""
    pids = iter([1, 2])

    def fake_popen(*args, **kwargs):
        return MagicMock(pid=next(pids))

    with (
        patch("infra.studio_batch_runner.subprocess.Popen", side_effect=fake_popen),
        patch("infra.studio_batch_runner._process_running", return_value=True),
    ):
        first = submit_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.1,
            skip_preflight=True,
            max_attempts=1,
        )
        queued = submit_batch_job(
            anye_project,
            start_chapter=2,
            end_chapter=2,
            budget_usd=0.1,
            skip_preflight=True,
            max_attempts=4,
        )

    assert queued.status == "queued"
    assert queued.max_attempts == 4

    # Complete the running job; _poll_job auto-promotes the queued head.
    with (
        patch("infra.studio_batch_runner._process_running", return_value=False),
        patch("infra.studio_batch_runner._read_exit_code", return_value=0),
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            return_value=MagicMock(pid=999),
        ),
    ):
        _poll_job(_load_job(first.job_id))

    promoted = _load_job(queued.job_id)
    assert promoted.status == "running"
    assert promoted.max_attempts == 4
    assert promoted.attempt == 1
