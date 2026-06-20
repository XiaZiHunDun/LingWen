"""Tests for infra/studio_batch_runner.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.paths import ProjectPaths
from infra.studio_batch_runner import (
    BatchAlreadyRunningError,
    BatchNotAllowedError,
    BatchPreflightError,
    dashboard_batch_allowed,
    get_batch_job,
    start_batch_job,
)
from infra.studio_registry import activate_project, get_project_by_slug


@pytest.fixture(autouse=True)
def _reset_paths():
    ProjectPaths.reset()
    yield
    ProjectPaths.reset()


@pytest.fixture
def anye_project(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "infra.studio_batch_runner._jobs_dir",
        lambda: tmp_path / "jobs",
    )
    return get_project_by_slug("anye-xinbiao")


def test_dashboard_batch_requires_allow_flag(anye_project, monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "infra.studio_batch_runner._jobs_dir",
        lambda: tmp_path / "jobs",
    )
    monkeypatch.delenv("LINGWEN_ALLOW_DASHBOARD_BATCH", raising=False)
    with pytest.raises(BatchNotAllowedError):
        start_batch_job(
            anye_project,
            start_chapter=1,
            end_chapter=1,
            budget_usd=0.12,
            skip_preflight=True,
        )


def test_dashboard_batch_allowed_flag(monkeypatch):
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    assert dashboard_batch_allowed() is True
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "0")
    assert dashboard_batch_allowed() is False
    monkeypatch.delenv("LINGWEN_ALLOW_DASHBOARD_BATCH", raising=False)


def test_start_batch_job_requires_preflight(anye_project, monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    monkeypatch.setattr(
        "infra.studio_batch_runner._jobs_dir",
        lambda: tmp_path / "jobs",
    )
    with pytest.raises(BatchPreflightError):
        start_batch_job(
            anye_project,
            start_chapter=999,
            end_chapter=999,
            budget_usd=0.1,
        )


@patch("infra.studio_batch_runner.subprocess.Popen")
def test_start_batch_job_spawns_process(mock_popen, anye_project, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    monkeypatch.setattr(
        "infra.studio_batch_runner._jobs_dir",
        lambda: tmp_path / "jobs",
    )
    proc = MagicMock()
    proc.pid = 4242
    mock_popen.return_value = proc

    job = start_batch_job(
        anye_project,
        start_chapter=1,
        end_chapter=1,
        budget_usd=0.12,
        skip_preflight=True,
    )
    assert job.status == "running"
    assert job.pid == 4242
    mock_popen.assert_called_once()

    loaded = get_batch_job(job.job_id)
    assert loaded is not None
    assert loaded["job_id"] == job.job_id


@patch("infra.studio_batch_runner._process_running", return_value=True)
@patch("infra.studio_batch_runner.subprocess.Popen")
def test_start_batch_job_rejects_duplicate(mock_popen, _mock_running, anye_project, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LINGWEN_ALLOW_DASHBOARD_BATCH", "1")
    monkeypatch.setattr(
        "infra.studio_batch_runner._jobs_dir",
        lambda: tmp_path / "jobs",
    )
    proc = MagicMock()
    proc.pid = 1111
    mock_popen.return_value = proc

    start_batch_job(
        anye_project,
        start_chapter=1,
        end_chapter=1,
        budget_usd=0.12,
        skip_preflight=True,
    )

    with pytest.raises(BatchAlreadyRunningError):
        start_batch_job(
            anye_project,
            start_chapter=2,
            end_chapter=2,
            budget_usd=0.12,
            skip_preflight=True,
        )
