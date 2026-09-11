"""lingwen-studio-batch-runner — canonical studio batch runner package.

Phase 47 P3-ARCHDEBT: relocated from infra/studio_batch_runner.py (676 LOC).
NOT-LEAF (depends on lingwen-studio-registry + lingwen-studio-batch-streamer).
"""

from __future__ import annotations

from lingwen_studio_batch_runner.service import (
    BatchAlreadyRunningError,
    BatchJob,
    BatchNotAllowedError,
    BatchPreflightError,
    _jobs_dir,
    _load_job,
    _poll_job,
    active_batch_job_for_project,
    advance_batch_queue,
    cancel_batch_job,
    compute_pilot_eta,
    dashboard_batch_allowed,
    find_running_job,
    get_batch_job,
    list_batch_jobs_for_slug,
    list_batch_queue,
    replay_events,
    start_batch_job,
    submit_batch_job,
)

__all__ = [
    "BatchJob",
    "BatchAlreadyRunningError",
    "BatchNotAllowedError",
    "BatchPreflightError",
    # Public functions
    "dashboard_batch_allowed",
    "find_running_job",
    "start_batch_job",
    "submit_batch_job",
    "advance_batch_queue",
    "list_batch_queue",
    "list_batch_jobs_for_slug",
    "get_batch_job",
    "active_batch_job_for_project",
    "cancel_batch_job",
    "compute_pilot_eta",
    "replay_events",
    # Private symbols re-exported for tests (Phase 42 lesson — tests use private symbols)
    "_jobs_dir",
    "_load_job",
    "_poll_job",
]