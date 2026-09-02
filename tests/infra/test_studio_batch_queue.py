"""Tests for the batch priority queue in infra/studio_batch_runner.

Covers: queue when busy, priority ordering (highest first), auto-promotion on
terminal/cancel, id-preserving promotion, and no-op guards.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.studio_batch_runner import (
    BatchJob,
    _load_job,
    _poll_job,
    advance_batch_queue,
    list_batch_queue,
    start_batch_job,
    submit_batch_job,
)
from infra.studio_registry import get_project_by_slug


@pytest.fixture
def anye_project(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("infra.studio_batch_runner._jobs_dir", lambda: tmp_path / "jobs")
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    return get_project_by_slug("anye-xinbiao")


def _popen_returning(pids: list[int]):
    return [MagicMock(pid=pid) for pid in pids]


def test_submit_idle_starts_immediately(anye_project, monkeypatch):
    with (
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            return_value=MagicMock(pid=1234),
        ),
        patch("infra.studio_batch_runner._process_running", return_value=True),
    ):
        job = submit_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.12,
            skip_preflight=True,
            priority=0,
        )
    assert job.status == "running"
    assert job.pid == 1234


def test_submit_busy_queues_and_orders_by_priority(anye_project, monkeypatch):
    with (
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            side_effect=_popen_returning([11, 22, 33]),
        ),
        patch("infra.studio_batch_runner._process_running", return_value=True),
    ):
        # First run starts immediately; the next two are queued.
        assert (
            submit_batch_job(
                anye_project,
                start_chapter=1,
                end_chapter=1,
                budget_usd=0.1,
                skip_preflight=True,
                priority=0,
            ).status
            == "running"
        )
        low = submit_batch_job(
            anye_project,
            start_chapter=2,
            end_chapter=2,
            budget_usd=0.1,
            skip_preflight=True,
            priority=5,
        )
        high = submit_batch_job(
            anye_project,
            start_chapter=3,
            end_chapter=3,
            budget_usd=0.1,
            skip_preflight=True,
            priority=9,
        )
        assert low.status == "queued" and high.status == "queued"

        queue = list_batch_queue(anye_project.slug)
        # Highest priority first.
        assert [row["priority"] for row in queue] == [9, 5]


def test_advance_promotes_head_and_keeps_job_id(anye_project, monkeypatch):
    from infra.studio_batch_runner import _save_job

    head = BatchJob(
        job_id="head-001",
        slug=anye_project.slug,
        start_chapter=2,
        end_chapter=2,
        budget_usd=0.1,
        mode="canon",
        status="queued",
        pid=None,
        log_path="",
        started_at="2026-09-02T00:00:00+00:00",
        priority=7,
    )
    tail = BatchJob(
        job_id="tail-001",
        slug=anye_project.slug,
        start_chapter=3,
        end_chapter=3,
        budget_usd=0.1,
        mode="canon",
        status="queued",
        pid=None,
        log_path="",
        started_at="2026-09-02T00:00:00+01:00",
        priority=5,
    )
    _save_job(head)
    _save_job(tail)

    with patch(
        "infra.studio_batch_runner.subprocess.Popen",
        return_value=MagicMock(pid=4444),
    ):
        promoted = advance_batch_queue(anye_project.slug)

    assert promoted is not None
    assert promoted.status == "running"
    assert promoted.job_id == "head-001"  # highest priority first + id preserved
    assert _load_job("head-001").status == "running"
    assert _load_job("tail-001").status == "queued"
    remaining = list_batch_queue(anye_project.slug)
    assert [row["job_id"] for row in remaining] == ["tail-001"]


def test_advance_noop_when_running(anye_project, monkeypatch):
    with (
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            side_effect=_popen_returning([1, 2]),
        ),
        patch("infra.studio_batch_runner._process_running", return_value=True),
    ):
        start_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.1,
            skip_preflight=True,
        )
        submit_batch_job(
            anye_project,
            start_chapter=2,
            end_chapter=2,
            budget_usd=0.1,
            skip_preflight=True,
        )

        with patch(
            "infra.studio_batch_runner.subprocess.Popen",
            side_effect=AssertionError("should not spawn while running"),
        ):
            assert advance_batch_queue(anye_project.slug) is None


def test_poll_auto_advances_after_terminal(anye_project, monkeypatch):
    with (
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            side_effect=_popen_returning([1, 2, 3]),
        ),
        patch("infra.studio_batch_runner._process_running", return_value=True),
    ):
        first = start_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.1,
            skip_preflight=True,
        )
        queued = submit_batch_job(
            anye_project,
            start_chapter=2,
            end_chapter=2,
            budget_usd=0.1,
            skip_preflight=True,
        )

    # First job exits cleanly; polling it should auto-start the queued job.
    with (
        patch(
            "infra.studio_batch_runner.subprocess.Popen",
            return_value=MagicMock(pid=5555),
        ),
        patch("infra.studio_batch_runner._process_running", return_value=False),
        patch("infra.studio_batch_runner._read_exit_code", return_value=0),
    ):
        done = _poll_job(_load_job(first.job_id))

    assert done.status == "completed"
    queued_after = _load_job(queued.job_id)
    assert queued_after.status == "running"
    assert queued_after.pid == 5555


def test_poll_queued_untouched(anye_project, monkeypatch):
    """Polling a queued job must not advance it (no running slot yet)."""
    from infra.studio_batch_runner import _save_job

    job = BatchJob(
        job_id="pending-01",
        slug=anye_project.slug,
        start_chapter=1,
        end_chapter=1,
        budget_usd=0.1,
        mode="canon",
        status="queued",
        pid=None,
        log_path="",
        started_at="2026-09-02T00:00:00+00:00",
    )
    _save_job(job)
    with patch(
        "infra.studio_batch_runner.subprocess.Popen",
        side_effect=AssertionError("must not spawn while queued"),
    ):
        result = _poll_job(_load_job("pending-01"))
    assert result.status == "queued"
