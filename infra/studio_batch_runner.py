"""Background batch runner for Studio Dashboard (Phase 10.04 follow-up)."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.studio_batch_streamer import (
    EVENT_CHAPTER_COMPLETED,
    EVENT_JOB_CANCELLED,
    EVENT_JOB_COMPLETED,
    EVENT_JOB_FAILED,
    EVENT_JOB_STATE,
    publish,
)
from infra.studio_registry import (
    StudioProject,
    _chapter_nums,
    active_project,
    factory_root,
    get_project_by_slug,
    production_preflight,
)


def _jobs_dir() -> Path:
    path = factory_root() / "infra" / ".state" / "studio_batch_jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_path(job_id: str) -> Path:
    return _jobs_dir() / f"{job_id}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class BatchJob:
    job_id: str
    slug: str
    start_chapter: int
    end_chapter: int
    budget_usd: float
    mode: str
    status: str  # running | completed | failed
    pid: int | None
    log_path: str
    started_at: str
    finished_at: str | None = None
    exit_code: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BatchAlreadyRunningError(RuntimeError):
    pass


class BatchPreflightError(RuntimeError):
    def __init__(self, message: str, *, chapters: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.chapters = chapters or []


class BatchNotAllowedError(RuntimeError):
    """Dashboard batch disabled until LINGWEN_ALLOW_DASHBOARD_BATCH=1."""


def dashboard_batch_allowed() -> bool:
    flag = os.environ.get("LINGWEN_ALLOW_DASHBOARD_BATCH", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _load_job(job_id: str) -> BatchJob | None:
    path = _job_path(job_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return BatchJob(**data)


def _save_job(job: BatchJob) -> None:
    path = _job_path(job.job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(job.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# Per-job count of chapter_completed events already published. Lets _poll_job
# publish only for newly-observed chapters instead of re-emitting every poll.
_published_chapters: dict[str, int] = {}


def _completed_chapter_nums(job: BatchJob) -> list[int]:
    """Numbers in [start, end] that already have a chapter file on disk."""
    project = get_project_by_slug(job.slug)
    if project is None:
        return []
    chapters_dir = project.root / "03_内容仓库" / "04_正文"
    present = set(_chapter_nums(chapters_dir))
    return [n for n in range(job.start_chapter, job.end_chapter + 1) if n in present]


def _publish_chapter_completions(job: BatchJob) -> None:
    """Publish chapter_completed for any newly-written chapter in the range."""
    completed = _completed_chapter_nums(job)
    if not completed:
        return
    published = _published_chapters.get(job.job_id, 0)
    for chapter_num in sorted(completed):
        index = completed.index(chapter_num)
        if index >= published:
            publish(
                job.job_id,
                EVENT_CHAPTER_COMPLETED,
                {"chapter_num": chapter_num, "completed_at": _now_iso()},
            )
    _published_chapters[job.job_id] = len(completed)


def _poll_job(job: BatchJob) -> BatchJob:
    if job.status != "running" or job.pid is None:
        return job
    if _process_running(job.pid):
        _publish_chapter_completions(job)
        return job
    exit_code = _read_exit_code(job)
    job.status = "completed" if exit_code == 0 else "failed"
    job.exit_code = exit_code
    job.finished_at = _now_iso()
    _save_job(job)
    event_type = EVENT_JOB_COMPLETED if job.status == "completed" else EVENT_JOB_FAILED
    publish(
        job.job_id,
        event_type,
        {
            "status": job.status,
            "exit_code": job.exit_code,
            "finished_at": job.finished_at,
        },
    )
    return job


def _process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    # os.kill(pid, 0) succeeds for zombies; explicitly check process state
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("State:"):
                    state = line.split()[1] if len(line.split()) > 1 else ""
                    return state != "Z"
    except OSError:
        return False
    return True


def _read_exit_code(job: BatchJob) -> int:
    if job.pid is None:
        return 1
    try:
        pid, status = os.waitpid(job.pid, os.WNOHANG)
        if pid == 0:
            return 0 if not _process_running(job.pid) else 1
        return os.waitstatus_to_exitcode(status)
    except ChildProcessError:
        return 0


def find_running_job(slug: str) -> BatchJob | None:
    for path in sorted(_jobs_dir().glob("*.json"), reverse=True):
        job = BatchJob(**json.loads(path.read_text(encoding="utf-8")))
        job = _poll_job(job)
        if job.slug == slug and job.status == "running":
            return job
    return None


def start_batch_job(
    project: StudioProject,
    *,
    start_chapter: int,
    end_chapter: int,
    budget_usd: float,
    mode: str = "canon",
    skip_preflight: bool = False,
) -> BatchJob:
    if end_chapter < start_chapter:
        raise ValueError("end_chapter must be >= start_chapter")
    if budget_usd < 0 or budget_usd > 100:
        raise ValueError("budget_usd must be 0..100")
    if not dashboard_batch_allowed():
        raise BatchNotAllowedError(
            "Dashboard batch is disabled; set LINGWEN_ALLOW_DASHBOARD_BATCH=1 on the server",
        )

    running = find_running_job(project.slug)
    if running is not None:
        raise BatchAlreadyRunningError(
            f"batch already running for {project.slug!r}: {running.job_id}",
        )

    if not skip_preflight and mode == "canon":
        preflight = production_preflight(
            project,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            mode=mode,
        )
        if not preflight["all_ok"]:
            failed = [c for c in preflight["chapters"] if not c["ok"]]
            raise BatchPreflightError(
                f"preflight failed for {len(failed)} chapter(s)",
                chapters=failed,
            )

    job_id = uuid.uuid4().hex[:12]
    log_path = Path(f"/tmp/studio-batch-{job_id}.log")
    max_chapters = end_chapter - start_chapter + 1
    script = factory_root() / "scripts" / "run-project-batch.sh"

    env = os.environ.copy()
    env["LINGWEN_PROJECT_ROOT"] = str(project.root)
    env.setdefault("LINGWEN_PRODUCTION_MODE", mode)
    env.setdefault("LINGWEN_REAL_LLM", "1")
    env.setdefault("LINGWEN_EMIT_CHAPTER", "1")
    env.setdefault("LINGWEN_MEMORY_RAG", "stub")

    log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115
    proc = subprocess.Popen(  # noqa: S603
        [
            "bash",
            str(script),
            str(start_chapter),
            str(end_chapter),
            str(max_chapters),
            f"{budget_usd:.2f}",
            "",
            str(log_path),
        ],
        cwd=str(factory_root()),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_file.close()

    job = BatchJob(
        job_id=job_id,
        slug=project.slug,
        start_chapter=start_chapter,
        end_chapter=end_chapter,
        budget_usd=budget_usd,
        mode=mode,
        status="running",
        pid=proc.pid,
        log_path=str(log_path),
        started_at=_now_iso(),
    )
    _save_job(job)
    publish(job.job_id, EVENT_JOB_STATE, job.to_dict())
    return job


def list_batch_jobs_for_slug(slug: str, *, limit: int = 5) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(_jobs_dir().glob("*.json"), reverse=True):
        job = BatchJob(**json.loads(path.read_text(encoding="utf-8")))
        job = _poll_job(job)
        if job.slug != slug:
            continue
        rows.append(job.to_dict())
        if len(rows) >= limit:
            break
    return rows


def get_batch_job(job_id: str, *, log_tail_lines: int = 40) -> dict[str, Any] | None:
    job = _load_job(job_id)
    if job is None:
        return None
    job = _poll_job(job)
    payload = job.to_dict()
    payload["log_tail"] = _read_log_tail(job.log_path, log_tail_lines)
    return payload


def _read_log_tail(log_path: str, lines: int) -> str:
    path = Path(log_path)
    if not path.is_file():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(content[-lines:])


def active_batch_job_for_project() -> dict[str, Any] | None:
    project = active_project()
    if project is None:
        return None
    job = find_running_job(project.slug)
    if job is None:
        return None
    return get_batch_job(job.job_id)


def cancel_batch_job(job_id: str) -> BatchJob:
    """Send SIGTERM to a running batch job; SIGKILL after 5s grace.

    Returns the (mutated) BatchJob with status='cancelled'.
    Raises:
      LookupError: job_id not found
      BatchAlreadyRunningError: job is already in a terminal state (completed/failed/cancelled)
    """
    job = _load_job(job_id)
    if job is None:
        raise LookupError(f"batch job not found: {job_id!r}")
    if job.status != "running":
        raise BatchAlreadyRunningError(
            f"batch job {job_id!r} is in terminal state {job.status!r}, cannot cancel"
        )
    if job.pid is None or not _process_running(job.pid):
        job.status = "cancelled"
        job.finished_at = _now_iso()
        job.error = "process already exited before cancel"
        _save_job(job)
        publish(job.job_id, EVENT_JOB_CANCELLED, job.to_dict())
        return job

    os.kill(job.pid, signal.SIGTERM)
    grace_seconds = 5
    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        if not _process_running(job.pid):
            break
        time.sleep(0.2)
    else:
        try:
            os.kill(job.pid, signal.SIGKILL)
        except OSError:
            pass
        job.error = f"force killed after {grace_seconds}s grace"

    job.status = "cancelled"
    job.finished_at = _now_iso()
    _save_job(job)
    publish(job.job_id, EVENT_JOB_CANCELLED, job.to_dict())
    return job


def compute_pilot_eta(
    *,
    started_at: str,
    start_chapter: int,
    end_chapter: int,
    completed_chapters: int,
) -> float | None:
    """Estimate seconds remaining for a running batch.

    Returns None when no chapters have completed yet (insufficient data).
    Otherwise: (remaining / throughput) where throughput = completed / elapsed.

    Args:
        started_at: ISO-8601 timestamp from BatchJob.started_at.
        start_chapter: inclusive lower bound of chapter range.
        end_chapter: inclusive upper bound of chapter range.
        completed_chapters: count of pilot_records with chapter_num in [start, end].

    Returns:
        Estimated seconds remaining as float, or None if not yet computable.
    """
    if completed_chapters <= 0:
        return None
    started = datetime.fromisoformat(started_at)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    if elapsed <= 0:
        return None
    total = end_chapter - start_chapter + 1
    remaining = max(0, total - completed_chapters)
    throughput = completed_chapters / elapsed
    return remaining / throughput
