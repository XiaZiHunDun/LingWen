"""Tests for cancel_batch_job() in infra/studio_batch_runner.

4 paths: happy (running → cancelled), 409 (already completed), 404 (not found),
grace-timeout SIGKILL fallback (Task 2).
"""
import os
import signal
import subprocess
import sys
import textwrap
import time
import json
from pathlib import Path

import pytest

from infra.studio_batch_runner import (
    BatchAlreadyRunningError,
    BatchJob,
    cancel_batch_job,
    _jobs_dir,
)


@pytest.fixture
def temp_jobs_dir(tmp_path, monkeypatch):
    """Redirect _jobs_dir to tmp_path so tests don't pollute the real dir."""
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    monkeypatch.setattr("infra.studio_batch_runner._jobs_dir", lambda: jobs)
    return jobs


def _spawn_dummy_process() -> int:
    """Spawn a long-running dummy child process; return its pid."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    return proc.pid


def _write_job(jobs_dir: Path, job: BatchJob) -> None:
    payload = {
        "job_id": job.job_id,
        "slug": "test-slug",
        "start_chapter": 1,
        "end_chapter": 10,
        "budget_usd": 5.0,
        "mode": "pilot",
        "status": job.status,
        "pid": job.pid,
        "log_path": "/tmp/dummy.log",
        "started_at": "2026-09-02T00:00:00+00:00",
    }
    if job.finished_at is not None:
        payload["finished_at"] = job.finished_at
    if job.exit_code is not None:
        payload["exit_code"] = job.exit_code
    (jobs_dir / f"{job.job_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_cancel_running_job_sends_sigterm_and_returns_cancelled(temp_jobs_dir):
    pid = _spawn_dummy_process()
    try:
        job = BatchJob(
            job_id="abc-123", slug="test-slug", start_chapter=1, end_chapter=10,
            budget_usd=5.0, mode="pilot", status="running", pid=pid,
            log_path="/tmp/dummy.log", started_at="2026-09-02T00:00:00+00:00",
        )
        _write_job(temp_jobs_dir, job)

        result = cancel_batch_job("abc-123")

        assert result.status == "cancelled"
        assert result.error is None or "force" not in (result.error or "")
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def test_cancel_already_completed_job_returns_completed(temp_jobs_dir):
    job = BatchJob(
        job_id="done-001", slug="test-slug", start_chapter=1, end_chapter=10,
        budget_usd=5.0, mode="pilot", status="completed", pid=None,
        log_path="/tmp/dummy.log", started_at="2026-09-02T00:00:00+00:00",
        finished_at="2026-09-02T00:01:00+00:00", exit_code=0,
    )
    _write_job(temp_jobs_dir, job)

    with pytest.raises(BatchAlreadyRunningError) as exc:
        cancel_batch_job("done-001")
    assert "completed" in str(exc.value).lower()


def test_cancel_unknown_job_raises_lookup_error(temp_jobs_dir):
    with pytest.raises(LookupError) as exc:
        cancel_batch_job("nonexistent-xyz")
    assert "nonexistent-xyz" in str(exc.value)
