# Phase 23 — Pilot Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated `PilotPage` for the batch chapter pipeline with start/observe/cancel/history close-loop + a backend `cancel_batch_job` endpoint (SIGTERM + 5s grace + SIGKILL fallback). 16 atomic commits.

**Architecture:** Light backend touch (`infra/studio_batch_runner.cancel_batch_job` + `POST /api/studio/batch/<id>/cancel` route). Frontend reorganization: extract embedded Pilot surface from `StudioPage.vue` into a top-level page backed by a `usePilotBatch` composable + 5 components + 2 typed API wrappers. Polling at 3s while `status==='running'` (no SSE). ETA from `pilot_records.jsonl` line count.

**Tech Stack:** Python 3.13 / FastAPI / pytest-asyncio / Vue 3 + TypeScript strict / Naive UI / vitest / @vue/test-utils

**Worktree setup** (execute before Task 1):

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-23-pilot-page -b phase-23-pilot-page master
cd .worktrees/phase-23-pilot-page
uv sync --all-packages
uv pip install pytest pytest-asyncio psutil  # per MEMORY.md N.14 lesson 4
# Use worktree's .venv/bin/python (NOT /home/ailearn/miniconda3/bin/python)
```

**Run commands** (per MEMORY.md):

```bash
# Backend (worktree venv)
.venv/bin/python -m pytest <test_path> -v

# Frontend
cd apps/dashboard
pnpm vitest run <test_path>
pnpm tsc --noEmit
pnpm eslint <file>
pnpm exec knip
cd ../..

# Lint
ruff check <file>
ruff format --check <file>
```

---

## File Structure

| File | Action | Reason |
|------|--------|--------|
| `infra/studio_batch_runner.py` | MODIFY: add `cancel_batch_job` + `compute_pilot_eta` | Cancel + ETA core |
| `tests/infra/test_studio_batch_runner_cancel.py` | CREATE | 4 cancel path tests |
| `tests/infra/test_studio_batch_runner_eta.py` | CREATE | 3 ETA tests |
| `apps/studio_api/routes/studio.py` | MODIFY: add cancel route | HTTP boundary |
| `apps/studio_api/tests/test_studio_cancel_route.py` | CREATE | 3 route integration tests |
| `apps/dashboard/src/api/studio.ts` | MODIFY: +2 wrappers | TS contracts |
| `apps/dashboard/tests/unit/api/cancel-studio-batch-job.spec.ts` | CREATE | URL contract |
| `apps/dashboard/tests/unit/api/list-studio-batch-jobs.spec.ts` | CREATE | URL contract |
| `apps/dashboard/src/composables/usePilotBatch.ts` | CREATE | State + actions |
| `apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts` | CREATE | State transitions + polling |
| `apps/dashboard/src/components/pilot/PilotStartForm.vue` | CREATE | Form + submit |
| `apps/dashboard/src/components/pilot/PilotPreflightTable.vue` | CREATE | Pre-flight result table |
| `apps/dashboard/src/components/pilot/PilotLivePanel.vue` | CREATE | Live status + log + ETA |
| `apps/dashboard/src/components/pilot/PilotCancelDialog.vue` | CREATE | Confirm cancel |
| `apps/dashboard/src/components/pilot/PilotHistoryList.vue` | CREATE | Past jobs table |
| `apps/dashboard/tests/unit/components/pilot/*.spec.ts` | CREATE | Per-component tests (5 files) |
| `apps/dashboard/src/pages/PilotPage.vue` | CREATE | Page assembly |
| `apps/dashboard/tests/unit/pages/pilot-page.spec.ts` | CREATE | Page-level tests |
| `apps/dashboard/src/config/dashboardNav.js` | MODIFY: add `pilot` entry | Nav entry |
| `apps/dashboard/tests/unit/config/dashboard-nav.spec.ts` | MODIFY (add test) | Nav test |
| `apps/dashboard/src/pages/StudioPage.vue` | MODIFY: remove embedded pilot section | Cleanup |
| `apps/dashboard/tests/unit/pages/studio-page.spec.ts` | MODIFY (update) | Test cleanup impact |
| `CLAUDE.md` | MODIFY: v23.0 entry | Version bump |
| `.lingwen/architecture.yml` | MODIFY: version "22.0"→"23.0" + pilot_page invariant | Architecture |
| `docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md` | CREATE | Handoff |

**Total: 16 source commits + 1 handoff commit. Architecture invariants preserved (no new module boundary; existing 12+ invariants all KEPT).**

---

## Task 1: `cancel_batch_job` happy path + 409/404 (Part A1-A2)

**Files:**
- Modify: `infra/studio_batch_runner.py:1-50` (imports) and append new functions at end
- Create: `tests/infra/test_studio_batch_runner_cancel.py`

### Step 1.1: Write the RED test for happy path + 409/404

Create `tests/infra/test_studio_batch_runner_cancel.py`:

```python
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
    (jobs_dir / f"{job.job_id}.json").write_text(
        textwrap.dedent(f"""
        job_id: {job.job_id}
        slug: test-slug
        start_chapter: 1
        end_chapter: 10
        budget_usd: 5.0
        mode: pilot
        status: running
        pid: {job.pid}
        log_path: /tmp/dummy.log
        started_at: 2026-09-02T00:00:00+00:00
        """).strip()
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
```

> **Note**: We use `BatchAlreadyRunningError` as the exception type for "already in a terminal state" to reuse the existing exception class. The class name is misleading but renaming would be out of scope; we document via docstring.

### Step 1.2: Run the test to verify RED

Run:
```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-23-pilot-page
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner_cancel.py -v
```

Expected: `ImportError` or `AttributeError: module 'infra.studio_batch_runner' has no attribute 'cancel_batch_job'`.

### Step 1.3: Add `cancel_batch_job` implementation

Modify `infra/studio_batch_runner.py`. Append at end of file (after existing functions):

```python
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
        return job

    os.kill(job.pid, signal.SIGTERM)
    grace_seconds = 5
    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        if not _process_running(job.pid):
            break
        time.sleep(0.2)
    else:
        # Grace expired — force kill
        try:
            os.kill(job.pid, signal.SIGKILL)
        except OSError:
            pass
        job.error = f"force killed after {grace_seconds}s grace"

    job.status = "cancelled"
    job.finished_at = _now_iso()
    _save_job(job)
    return job
```

Also add at top of file (after existing imports):

```python
import signal
import time
```

### Step 1.4: Run test to verify GREEN

Run:
```bash
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner_cancel.py -v
```

Expected: 3 tests pass.

### Step 1.5: Commit

```bash
git add infra/studio_batch_runner.py tests/infra/test_studio_batch_runner_cancel.py
git commit -m "feat(studio-batch-runner): cancel_batch_job() with SIGTERM + 5s grace + SIGKILL fallback

Closes Pilot Page spec §4.2 cancel semantics:
- LookupError for missing job_id
- BatchAlreadyRunningError for terminal-state jobs (409 semantics)
- SIGTERM + 5s grace loop polling _process_running
- SIGKILL fallback sets error='force killed after 5s grace'
- Updates job.status='cancelled' + finished_at, returns mutated BatchJob

3 tests: happy path / already completed / not found. SIGKILL path tested in Task 2."
```

---

## Task 2: SIGKILL fallback test (Part A3)

**Files:**
- Modify: `tests/infra/test_studio_batch_runner_cancel.py` (add 4th test)

### Step 2.1: Write the RED test for SIGKILL path

Append to `tests/infra/test_studio_batch_runner_cancel.py`:

```python
def test_cancel_job_ignoring_sigterm_triggers_sigkill(temp_jobs_dir):
    """Process that ignores SIGTERM should be SIGKILL'd after 5s grace."""
    # Spawn a child that traps SIGTERM
    proc = subprocess.Popen(
        [sys.executable, "-c", textwrap.dedent("""
            import signal, time
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            time.sleep(60)
        """)]
    )
    pid = proc.pid
    try:
        job = BatchJob(
            job_id="stubborn-001", slug="test-slug", start_chapter=1, end_chapter=10,
            budget_usd=5.0, mode="pilot", status="running", pid=pid,
            log_path="/tmp/dummy.log", started_at="2026-09-02T00:00:00+00:00",
        )
        _write_job(temp_jobs_dir, job)

        start = time.time()
        result = cancel_batch_job("stubborn-001")
        elapsed = time.time() - start

        assert result.status == "cancelled"
        assert "force killed" in (result.error or "")
        assert 4.5 < elapsed < 7.0  # grace + small overhead
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
```

### Step 2.2: Run to verify GREEN (impl from Task 1 should already cover this)

Run:
```bash
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner_cancel.py -v
```

Expected: 4 tests pass.

### Step 2.3: Commit

```bash
git add tests/infra/test_studio_batch_runner_cancel.py
git commit -m "test(studio-batch-runner): SIGKILL fallback path for SIGTERM-ignoring process

Spawns Python child with signal.SIG_IGN on SIGTERM, verifies cancel_batch_job:
- Returns cancelled status within 5-7s
- Sets error='force killed after 5s grace'
- Confirms SIGKILL escalation logic in grace-period loop"
```

---

## Task 3: POST /api/studio/batch/<job_id>/cancel route (Part A1 + A4)

**Files:**
- Modify: `apps/studio_api/routes/studio.py` (append route)
- Create: `apps/studio_api/tests/test_studio_cancel_route.py`

### Step 3.1: Write the RED route test

Create `apps/studio_api/tests/test_studio_cancel_route.py`:

```python
"""Integration tests for POST /api/studio/batch/<job_id>/cancel."""
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from apps.studio_api.routes.studio import register_studio_routes


@pytest.fixture
def app():
    a = FastAPI()
    register_studio_routes(a)
    return a


@pytest.fixture
def client(app):
    return TestClient(app)


def test_cancel_route_returns_200_with_cancelled_status(client):
    fake_job = MagicMock()
    fake_job.status = "cancelled"
    fake_job.job_id = "abc-123"
    with patch("infra.studio_batch_runner.cancel_batch_job", return_value=fake_job):
        resp = client.post("/api/studio/batch/abc-123/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


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
        side_effect=RuntimeError("batch job 'done-001' is in terminal state 'completed'"),
    ):
        resp = client.post("/api/studio/batch/done-001/cancel")
    assert resp.status_code == 409
```

### Step 3.2: Run to verify RED

Run:
```bash
.venv/bin/python -m pytest apps/studio_api/tests/test_studio_cancel_route.py -v
```

Expected: `RuntimeError` from missing route or 404 from FastAPI default.

### Step 3.3: Add the route to studio.py

Read `apps/studio_api/routes/studio.py` to find a similar `POST` route pattern. Append (matching existing style):

```python
    @app.post(
        "/api/studio/batch/{job_id}/cancel",
        response_model=StudioBatchJobResponse,
    )
    def studio_batch_cancel_endpoint(job_id: str) -> StudioBatchJobResponse:
        """Cancel a running batch job (SIGTERM + 5s grace + SIGKILL fallback)."""
        from infra.studio_batch_runner import cancel_batch_job
        try:
            job = cancel_batch_job(job_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            # BatchAlreadyRunningError is RuntimeError subclass
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _batch_job_to_response(job)
```

Where `_batch_job_to_response` is a helper at module level. Add near top of `routes/studio.py` after imports:

```python
def _batch_job_to_response(job) -> "StudioBatchJobResponse":
    """Map infra.studio_batch_runner.BatchJob → lingwen_shared StudioBatchJobResponse."""
    from lingwen_shared.contracts.python.studio import StudioBatchJobResponse
    return StudioBatchJobResponse(
        job_id=job.job_id,
        slug=job.slug,
        start_chapter=job.start_chapter,
        end_chapter=job.end_chapter,
        budget_usd=job.budget_usd,
        mode=job.mode,
        status=job.status,
        pid=job.pid,
        log_path=job.log_path,
        log_tail=None,
        started_at=job.started_at,
        finished_at=job.finished_at,
        exit_code=job.exit_code,
        error=job.error,
    )
```

> **Note**: If `log_tail` requires a server-side read, defer it to the existing `get_batch_job` path; cancel response just signals completion.

### Step 3.4: Run to verify GREEN

Run:
```bash
.venv/bin/python -m pytest apps/studio_api/tests/test_studio_cancel_route.py -v
```

Expected: 3 tests pass.

### Step 3.5: Commit

```bash
git add apps/studio_api/routes/studio.py apps/studio_api/tests/test_studio_cancel_route.py
git commit -m "feat(studio-api): POST /api/studio/batch/<job_id>/cancel route

Maps infra.studio_batch_runner.cancel_batch_job exceptions to HTTP:
- LookupError → 404
- BatchAlreadyRunningError (RuntimeError subclass) → 409
- Success → 200 with StudioBatchJobResponse

3 route integration tests via FastAPI TestClient."
```

---

## Task 4: ETA helper (Part A2 eta)

**Files:**
- Modify: `infra/studio_batch_runner.py` (add `compute_pilot_eta`)
- Create: `tests/infra/test_studio_batch_runner_eta.py`

### Step 4.1: Write RED test

Create `tests/infra/test_studio_batch_runner_eta.py`:

```python
"""Tests for compute_pilot_eta() in infra/studio_batch_runner.

ETA algorithm: completed_chapters / elapsed_seconds → projected total time.
"""
import time
from datetime import datetime, timezone, timedelta

import pytest

from infra.studio_batch_runner import compute_pilot_eta


def test_eta_returns_none_when_no_chapters_completed():
    """If pilot_records has 0 lines in range, ETA is unknown."""
    started_at = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    eta = compute_pilot_eta(
        started_at=started_at,
        start_chapter=1,
        end_chapter=10,
        completed_chapters=0,
    )
    assert eta is None


def test_eta_projects_remaining_time_from_throughput():
    """7 of 14 chapters done in 60s → ~60s remaining."""
    started_at = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    eta = compute_pilot_eta(
        started_at=started_at,
        start_chapter=1,
        end_chapter=14,
        completed_chapters=7,
    )
    assert eta is not None
    assert 55.0 <= eta <= 65.0  # ~1 chapter per 8.57s, 7 remaining ≈ 60s


def test_eta_caps_at_double_elapsed_for_anomaly_protection():
    """If completion ratio is suspiciously high, cap to avoid divide-by-near-zero."""
    started_at = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    eta = compute_pilot_eta(
        started_at=started_at,
        start_chapter=1,
        end_chapter=10,
        completed_chapters=9,
    )
    # 9 of 10 done in 10s → throughput = 0.9/s; remaining = 1/0.9 ≈ 1.1s
    assert eta is not None
    assert eta < 30.0  # sanity: very small ETA
```

### Step 4.2: Run RED

```bash
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner_eta.py -v
```

Expected: ImportError.

### Step 4.3: Implement `compute_pilot_eta`

Append to `infra/studio_batch_runner.py`:

```python
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
```

### Step 4.4: Run GREEN

```bash
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner_eta.py -v
```

Expected: 3 tests pass.

### Step 4.5: Commit

```bash
git add infra/studio_batch_runner.py tests/infra/test_studio_batch_runner_eta.py
git commit -m "feat(studio-batch-runner): compute_pilot_eta() helper for live ETA

Algorithm: throughput = completed / elapsed, ETA = remaining / throughput.
Returns None when completed_chapters == 0 (insufficient data).
No state mutation; pure function for composable to call on each poll.

3 tests: no-completed / 7-of-14 / 9-of-10 edge cases."
```

---

## Task 5: cancelStudioBatchJob API wrapper (Part B1)

**Files:**
- Modify: `apps/dashboard/src/api/studio.ts` (add wrapper)
- Create: `apps/dashboard/tests/unit/api/cancel-studio-batch-job.spec.ts`

### Step 5.1: Write RED URL contract test

Create `apps/dashboard/tests/unit/api/cancel-studio-batch-job.spec.ts`:

```typescript
import { describe, expect, it, vi } from 'vitest';
import { cancelStudioBatchJob } from '@/api/studio';

interface CapturedCall { url: string; method: string; }

function mockFetch(returnBody: unknown, status = 200) {
  return vi.fn(async (url: string, init?: RequestInit): Promise<Response> => {
    const captured: CapturedCall = { url, method: init?.method ?? 'GET' };
    (globalThis as { __lastCall?: CapturedCall }).__lastCall = captured;
    return new Response(JSON.stringify(returnBody), {
      status,
      headers: { 'content-type': 'application/json' },
    });
  });
}

describe('cancelStudioBatchJob URL contract', () => {
  it('POSTs to /api/studio/batch/<job_id>/cancel', async () => {
    const fetchMock = mockFetch({ job_id: 'abc-123', status: 'cancelled' });
    vi.stubGlobal('fetch', fetchMock);

    await cancelStudioBatchJob('abc-123');

    const call = (globalThis as { __lastCall?: CapturedCall }).__lastCall;
    expect(call?.method).toBe('POST');
    expect(call?.url).toBe('/api/studio/batch/abc-123/cancel');
    vi.unstubAllGlobals();
  });

  it('returns parsed StudioBatchJobResponseDTO', async () => {
    const body = { job_id: 'xyz-789', status: 'cancelled', mode: 'pilot' };
    const fetchMock = mockFetch(body);
    vi.stubGlobal('fetch', fetchMock);

    const result = await cancelStudioBatchJob('xyz-789');
    expect(result.job_id).toBe('xyz-789');
    expect(result.status).toBe('cancelled');
    vi.unstubAllGlobals();
  });

  it('encodes special characters in job_id', async () => {
    const fetchMock = mockFetch({ status: 'cancelled' });
    vi.stubGlobal('fetch', fetchMock);

    await cancelStudioBatchJob('job with spaces / & special');

    const call = (globalThis as { __lastCall?: CapturedCall }).__lastCall;
    expect(call?.url).toContain('job%20with%20spaces');
    vi.unstubAllGlobals();
  });
});
```

### Step 5.2: Run RED

```bash
cd apps/dashboard
pnpm vitest run tests/unit/api/cancel-studio-batch-job.spec.ts
```

Expected: ImportError on `cancelStudioBatchJob`.

### Step 5.3: Implement wrapper

In `apps/dashboard/src/api/studio.ts`, append:

```typescript
export async function cancelStudioBatchJob(
  jobId: string,
): Promise<StudioBatchJobResponseDTO> {
  const encoded = encodeURIComponent(jobId);
  const res = await fetch(`/api/studio/batch/${encoded}/cancel`, { method: 'POST' });
  const data = await res.json();
  return data as StudioBatchJobResponseDTO;
}
```

### Step 5.4: Run GREEN

```bash
pnpm vitest run tests/unit/api/cancel-studio-batch-job.spec.ts
```

Expected: 3 tests pass.

### Step 5.5: Type-check + commit

```bash
pnpm tsc --noEmit
git add apps/dashboard/src/api/studio.ts apps/dashboard/tests/unit/api/cancel-studio-batch-job.spec.ts
git commit -m "feat(api): cancelStudioBatchJob wrapper

POST /api/studio/batch/<encoded jobId>/cancel → StudioBatchJobResponseDTO.
encodeURIComponent handles special characters in job_id.

3 URL contract tests: method + URL encoding + response shape."
```

---

## Task 6: listStudioBatchJobs API wrapper (Part B2)

**Files:**
- Modify: `apps/dashboard/src/api/studio.ts` (add wrapper + DTO if needed)
- Create: `apps/dashboard/tests/unit/api/list-studio-batch-jobs.spec.ts`

### Step 6.1: Write RED test

Create `apps/dashboard/tests/unit/api/list-studio-batch-jobs.spec.ts`:

```typescript
import { describe, expect, it, vi } from 'vitest';
import { listStudioBatchJobs } from '@/api/studio';

function mockFetch(returnBody: unknown) {
  return vi.fn(async (url: string, init?: RequestInit): Promise<Response> => {
    (globalThis as { __lastCall?: { url: string; method: string } }).__lastCall = {
      url,
      method: init?.method ?? 'GET',
    };
    return new Response(JSON.stringify(returnBody), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  });
}

describe('listStudioBatchJobs URL contract', () => {
  it('GETs /api/studio/batch/history?slug=X&limit=N', async () => {
    const fetchMock = mockFetch({ jobs: [] });
    vi.stubGlobal('fetch', fetchMock);

    await listStudioBatchJobs('my-project', 20);

    const call = (globalThis as { __lastCall?: { url: string; method: string } }).__lastCall;
    expect(call?.method).toBe('GET');
    expect(call?.url).toContain('/api/studio/batch/history');
    expect(call?.url).toContain('slug=my-project');
    expect(call?.url).toContain('limit=20');
    vi.unstubAllGlobals();
  });

  it('returns parsed jobs array', async () => {
    const body = {
      jobs: [
        { job_id: 'j1', status: 'completed', start_chapter: 1, end_chapter: 10 },
        { job_id: 'j2', status: 'failed', start_chapter: 11, end_chapter: 20 },
      ],
    };
    vi.stubGlobal('fetch', mockFetch(body));
    const result = await listStudioBatchJobs('slug', 10);
    expect(result.jobs).toHaveLength(2);
    expect(result.jobs[0].job_id).toBe('j1');
    vi.unstubAllGlobals();
  });

  it('encodes slug special characters', async () => {
    vi.stubGlobal('fetch', mockFetch({ jobs: [] }));
    await listStudioBatchJobs('项目 with spaces', 5);
    const call = (globalThis as { __lastCall?: { url: string } }).__lastCall;
    expect(call?.url).toContain(encodeURIComponent('项目 with spaces'));
    vi.unstubAllGlobals();
  });

  it('uses default limit when omitted', async () => {
    vi.stubGlobal('fetch', mockFetch({ jobs: [] }));
    await listStudioBatchJobs('slug');
    const call = (globalThis as { __lastCall?: { url: string } }).__lastCall;
    expect(call?.url).toContain('limit=20');
    vi.unstubAllGlobals();
  });
});
```

### Step 6.2: Run RED

```bash
pnpm vitest run tests/unit/api/list-studio-batch-jobs.spec.ts
```

Expected: ImportError.

### Step 6.3: Implement wrapper + DTO + backend route

**Frontend** — append to `apps/dashboard/src/api/studio.ts`:

```typescript
export interface StudioBatchJobSummaryDTO {
  job_id: string;
  slug: string;
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  mode: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  exit_code: number | null;
  error: string | null;
}

export interface StudioBatchJobListResponseDTO {
  jobs: StudioBatchJobSummaryDTO[];
}

export async function listStudioBatchJobs(
  slug: string,
  limit: number = 20,
): Promise<StudioBatchJobListResponseDTO> {
  const params = new URLSearchParams({ slug, limit: String(limit) });
  const res = await fetch(`/api/studio/batch/history?${params}`);
  const data = await res.json();
  return data as StudioBatchJobListResponseDTO;
}
```

**Backend** — append to `apps/studio_api/routes/studio.py`:

```python
    @app.get(
        "/api/studio/batch/history",
        response_model=StudioBatchJobListResponse,
    )
    def studio_batch_history_endpoint(
        slug: str, limit: int = 20
    ) -> StudioBatchJobListResponse:
        from infra.studio_batch_runner import list_batch_jobs_for_slug
        rows = list_batch_jobs_for_slug(slug, limit=limit)
        return StudioBatchJobListResponse(
            jobs=[StudioBatchJobSummary.model_validate(r) for r in rows]
        )
```

Add DTOs to `packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py`:

```python
class StudioBatchJobSummary(BaseModel):
    job_id: str
    slug: str
    start_chapter: int
    end_chapter: int
    budget_usd: float
    mode: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None


class StudioBatchJobListResponse(BaseModel):
    jobs: list[StudioBatchJobSummary]
```

And register in `__all__`. Run TS codegen:

```bash
cd /home/ailearn/projects/LingWen
python tooling/contracts/generate.py
```

### Step 6.4: Run GREEN

```bash
cd apps/dashboard
pnpm vitest run tests/unit/api/list-studio-batch-jobs.spec.ts
pnpm tsc --noEmit
cd ../..
.venv/bin/python -m pytest apps/studio_api/tests/ -v -k "history"
```

Expected: 4 frontend tests pass + tsc clean + backend history tests pass.

### Step 6.5: Commit

```bash
git add apps/dashboard/src/api/studio.ts apps/dashboard/tests/unit/api/list-studio-batch-jobs.spec.ts
git add apps/studio_api/routes/studio.py packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/studio.ts  # auto-codegen
git commit -m "feat(api+studio-api): listStudioBatchJobs wrapper + /api/studio/batch/history route

DTOs in lingwen_shared (Python) + auto-codegen to TS.
Backend route reuses infra.studio_batch_runner.list_batch_jobs_for_slug.

4 URL contract tests: query params + encoding + default limit + response shape."
```

---

## Task 7: usePilotBatch composable (Part C)

**Files:**
- Create: `apps/dashboard/src/composables/usePilotBatch.ts`
- Create: `apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts`

### Step 7.1: Write RED test for state + actions

Create `apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts`:

```typescript
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

const mockStartBatch = vi.fn();
const mockActive = vi.fn();
const mockGetJob = vi.fn();
const mockList = vi.fn();
const mockCancel = vi.fn();

vi.mock('@/api/studio', () => ({
  fetchStudioStartBatchJob: (...args: unknown[]) => mockStartBatch(...args),
  fetchStudioActiveBatchJob: () => mockActive(),
  fetchStudioBatchJob: (...args: unknown[]) => mockGetJob(...args),
  listStudioBatchJobs: (...args: unknown[]) => mockList(...args),
  cancelStudioBatchJob: (...args: unknown[]) => mockCancel(...args),
}));

import { usePilotBatch } from '@/composables/usePilotBatch';

function withComposable<T>(cb: (api: ReturnType<typeof usePilotBatch>) => Promise<T>) {
  let captured!: ReturnType<typeof usePilotBatch>;
  const Host = defineComponent({
    setup() {
      captured = usePilotBatch();
      return () => h('div');
    },
  });
  const wrapper = mount(Host);
  return cb(captured).finally(() => wrapper.unmount());
}

beforeEach(() => {
  vi.useFakeTimers();
  mockStartBatch.mockReset();
  mockActive.mockReset();
  mockGetJob.mockReset();
  mockList.mockReset();
  mockCancel.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('usePilotBatch', () => {
  it('exposes initial empty state', async () => {
    await withComposable(async (api) => {
      expect(api.activeJob.value).toBeNull();
      expect(api.history.value).toEqual([]);
    });
  });

  it('refreshActive populates activeJob', async () => {
    const fakeJob = { job_id: 'j1', status: 'running', log_path: '/tmp/x' };
    mockActive.mockResolvedValue(fakeJob);
    await withComposable(async (api) => {
      await api.refreshActive();
      expect(api.activeJob.value).toEqual(fakeJob);
    });
  });

  it('startBatch calls fetchStudioStartBatchJob and refreshes active', async () => {
    const started = { job_id: 'new-j', status: 'running', log_path: '/tmp/y' };
    mockStartBatch.mockResolvedValue(started);
    mockActive.mockResolvedValue(started);
    await withComposable(async (api) => {
      await api.startBatch({ slug: 's1', start_chapter: 1, end_chapter: 10, budget_usd: 5, mode: 'pilot' });
      expect(mockStartBatch).toHaveBeenCalledOnce();
      expect(api.activeJob.value?.job_id).toBe('new-j');
    });
  });

  it('cancelBatch calls cancelStudioBatchJob', async () => {
    mockCancel.mockResolvedValue({ job_id: 'j1', status: 'cancelled' });
    await withComposable(async (api) => {
      await api.cancelBatch('j1');
      expect(mockCancel).toHaveBeenCalledWith('j1');
    });
  });

  it('refreshHistory populates history list', async () => {
    mockList.mockResolvedValue({ jobs: [{ job_id: 'h1', status: 'completed' }] });
    await withComposable(async (api) => {
      await api.refreshHistory('s1', 20);
      expect(api.history.value).toHaveLength(1);
      expect(api.history.value[0].job_id).toBe('h1');
    });
  });
});
```

### Step 7.2: Run RED

```bash
cd apps/dashboard
pnpm vitest run tests/unit/composables/use-pilot-batch.spec.ts
```

Expected: ImportError.

### Step 7.3: Implement composable

Create `apps/dashboard/src/composables/usePilotBatch.ts`:

```typescript
import { computed, onBeforeUnmount, ref } from 'vue';

import {
  cancelStudioBatchJob,
  fetchStudioActiveBatchJob,
  fetchStudioStartBatchJob,
  listStudioBatchJobs,
  type StudioBatchJobResponseDTO,
  type StudioBatchJobListResponseDTO,
} from '@/api/studio';

const POLL_INTERVAL_MS = 3000;

export interface PilotForm {
  slug: string;
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  mode: 'canon' | 'pilot';
}

export function usePilotBatch() {
  const activeJob = ref<StudioBatchJobResponseDTO | null>(null);
  const history = ref<StudioBatchJobListResponseDTO['jobs']>([]);
  const preflightRows = ref<Array<{ chapter: number; ok: boolean; message: string }>>([]);
  const preflightLoading = ref(false);
  const preflightError = ref<string | null>(null);
  const startLoading = ref(false);
  const startError = ref<string | null>(null);
  const cancelLoading = ref(false);
  const cancelError = ref<string | null>(null);

  let pollHandle: ReturnType<typeof setInterval> | null = null;

  function stopPolling() {
    if (pollHandle !== null) {
      clearInterval(pollHandle);
      pollHandle = null;
    }
  }

  function startPolling() {
    stopPolling();
    pollHandle = setInterval(() => {
      void refreshActive();
    }, POLL_INTERVAL_MS);
  }

  async function refreshActive(): Promise<void> {
    try {
      activeJob.value = await fetchStudioActiveBatchJob();
      if (activeJob.value?.status === 'running') {
        startPolling();
      } else {
        stopPolling();
      }
    } catch (err) {
      // Silent failure: keep last activeJob; surface in UI on next render
      console.warn('[usePilotBatch] refreshActive failed', err);
    }
  }

  async function refreshHistory(slug: string, limit = 20): Promise<void> {
    try {
      const result = await listStudioBatchJobs(slug, limit);
      history.value = result.jobs;
    } catch (err) {
      console.warn('[usePilotBatch] refreshHistory failed', err);
    }
  }

  async function runPreflight(form: PilotForm): Promise<void> {
    preflightLoading.value = true;
    preflightError.value = null;
    try {
      // TODO Phase 24+: dedicated preflight wrapper; reuse studio preflight helper
      // For now, surface form validation only
      preflightRows.value = [];
    } finally {
      preflightLoading.value = false;
    }
  }

  async function startBatch(form: PilotForm): Promise<void> {
    startLoading.value = true;
    startError.value = null;
    try {
      const job = await fetchStudioStartBatchJob(form);
      activeJob.value = job;
      startPolling();
    } catch (err) {
      startError.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      startLoading.value = false;
    }
  }

  async function cancelBatch(jobId: string): Promise<void> {
    cancelLoading.value = true;
    cancelError.value = null;
    try {
      await cancelStudioBatchJob(jobId);
      await refreshActive();
    } catch (err) {
      cancelError.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      cancelLoading.value = false;
    }
  }

  const isJobActive = computed(() => activeJob.value?.status === 'running');

  onBeforeUnmount(() => stopPolling());

  return {
    activeJob,
    history,
    preflightRows,
    preflightLoading,
    preflightError,
    startLoading,
    startError,
    cancelLoading,
    cancelError,
    isJobActive,
    refreshActive,
    refreshHistory,
    runPreflight,
    startBatch,
    cancelBatch,
  };
}
```

### Step 7.4: Run GREEN

```bash
pnpm vitest run tests/unit/composables/use-pilot-batch.spec.ts
pnpm tsc --noEmit
```

Expected: 5 tests pass + tsc clean.

### Step 7.5: Commit

```bash
git add apps/dashboard/src/composables/usePilotBatch.ts apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts
git commit -m "feat(composables): usePilotBatch() with state + polling + ETA scaffolding

Encapsulates Pilot page logic:
- State: activeJob, history, *Loading, *Error refs
- Actions: refreshActive / refreshHistory / runPreflight / startBatch / cancelBatch
- Auto polling: 3s interval while status==='running'; clears on terminal or unmount
- Composable returns refs + actions for PilotPage composition

5 tests: initial state / refreshActive / startBatch / cancelBatch / refreshHistory.
runPreflight is stub for Phase 24+ dedicated wrapper (existing preflight endpoint
callers will migrate)."
```

---

## Task 8: PilotStartForm + PilotPreflightTable (Part D1)

**Files:**
- Create: `apps/dashboard/src/components/pilot/PilotStartForm.vue`
- Create: `apps/dashboard/src/components/pilot/PilotPreflightTable.vue`
- Create: `apps/dashboard/tests/unit/components/pilot/pilot-start-form.spec.ts`
- Create: `apps/dashboard/tests/unit/components/pilot/pilot-preflight-table.spec.ts`

### Step 8.1: Write RED test for PilotPreflightTable

Create `apps/dashboard/tests/unit/components/pilot/pilot-preflight-table.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotPreflightTable from '@/components/pilot/PilotPreflightTable.vue';

describe('PilotPreflightTable', () => {
  it('renders one row per preflight result', () => {
    const rows = [
      { chapter: 1, ok: true, message: 'ok' },
      { chapter: 2, ok: false, message: 'foreshadow unresolved' },
    ];
    const wrapper = mount(PilotPreflightTable, { props: { rows } });
    const trs = wrapper.findAll('tbody tr');
    expect(trs).toHaveLength(2);
  });

  it('shows PASS / FAIL pill matching ok flag', () => {
    const rows = [
      { chapter: 1, ok: true, message: 'ok' },
      { chapter: 2, ok: false, message: 'fail' },
    ];
    const wrapper = mount(PilotPreflightTable, { props: { rows } });
    expect(wrapper.text()).toContain('PASS');
    expect(wrapper.text()).toContain('FAIL');
  });

  it('renders empty state when no rows', () => {
    const wrapper = mount(PilotPreflightTable, { props: { rows: [] } });
    expect(wrapper.text()).toContain('无 preflight 结果');
  });
});
```

### Step 8.2: Run RED

```bash
pnpm vitest run tests/unit/components/pilot/pilot-preflight-table.spec.ts
```

Expected: ImportError.

### Step 8.3: Implement PilotPreflightTable

Create `apps/dashboard/src/components/pilot/PilotPreflightTable.vue`:

```vue
<script setup lang="ts">
interface PreflightRow {
  chapter: number;
  ok: boolean;
  message: string;
}

defineProps<{ rows: PreflightRow[] }>();
</script>

<template>
  <div class="pilot-preflight" data-testid="pilot-preflight">
    <p v-if="rows.length === 0" data-testid="pilot-preflight-empty" class="empty-msg">
      无 preflight 结果
    </p>
    <table v-else class="preflight-table" aria-label="Pilot preflight 检查结果">
      <thead>
        <tr><th>章</th><th>状态</th><th>说明</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.chapter" :data-testid="`preflight-row-${row.chapter}`">
          <td>ch{{ String(row.chapter).padStart(3, '0') }}</td>
          <td :class="row.ok ? 'status-ok' : 'status-fail'" :data-testid="row.ok ? 'preflight-status-ok' : 'preflight-status-fail'">
            {{ row.ok ? 'PASS' : 'FAIL' }}
          </td>
          <td>{{ row.message }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.pilot-preflight { width: 100%; }
.preflight-table { width: 100%; border-collapse: collapse; }
.preflight-table th, .preflight-table td { padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border, #ddd); }
.status-ok { color: var(--success, #2c7a2c); font-weight: 600; }
.status-fail { color: var(--error, #c33); font-weight: 600; }
.empty-msg { color: var(--muted, #888); font-style: italic; }
</style>
```

### Step 8.4: Write RED test for PilotStartForm

Create `apps/dashboard/tests/unit/components/pilot/pilot-start-form.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotStartForm from '@/components/pilot/PilotStartForm.vue';

describe('PilotStartForm', () => {
  it('renders mode select + start/end/budget inputs', () => {
    const wrapper = mount(PilotStartForm, { props: { slug: 'proj', preflightRows: [], preflightLoading: false, startLoading: false, error: null } });
    expect(wrapper.find('[data-testid="start-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="start-chapter-from"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="start-chapter-to"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="start-budget-usd"]').exists()).toBe(true);
  });

  it('emits submit-start with form payload when Start clicked', async () => {
    const wrapper = mount(PilotStartForm, {
      props: {
        slug: 'proj',
        preflightRows: [{ chapter: 1, ok: true, message: 'ok' }],
        preflightLoading: false,
        startLoading: false,
        error: null,
        preflightAllOk: true,
      },
    });
    await wrapper.find('[data-testid="start-chapter-from"]').setValue('1');
    await wrapper.find('[data-testid="start-chapter-to"]').setValue('5');
    await wrapper.find('[data-testid="start-budget-usd"]').setValue('5');
    await wrapper.find('[data-testid="start-mode"]').setValue('pilot');
    await wrapper.find('[data-testid="start-submit-btn"]').trigger('click');
    const events = wrapper.emitted('submit-start');
    expect(events).toBeTruthy();
    expect(events![0][0]).toMatchObject({ slug: 'proj', start_chapter: 1, end_chapter: 5, budget_usd: 5, mode: 'pilot' });
  });

  it('disables Start button when preflightAllOk=false', () => {
    const wrapper = mount(PilotStartForm, {
      props: { slug: 'proj', preflightRows: [], preflightLoading: false, startLoading: false, error: null, preflightAllOk: false },
    });
    const btn = wrapper.find('[data-testid="start-submit-btn"]').element as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it('emits submit-preflight when Preflight button clicked', async () => {
    const wrapper = mount(PilotStartForm, {
      props: { slug: 'proj', preflightRows: [], preflightLoading: false, startLoading: false, error: null },
    });
    await wrapper.find('[data-testid="start-chapter-from"]').setValue('1');
    await wrapper.find('[data-testid="start-chapter-to"]').setValue('5');
    await wrapper.find('[data-testid="preflight-btn"]').trigger('click');
    expect(wrapper.emitted('submit-preflight')).toBeTruthy();
  });
});
```

### Step 8.5: Run RED

```bash
pnpm vitest run tests/unit/components/pilot/pilot-start-form.spec.ts
```

Expected: ImportError.

### Step 8.6: Implement PilotStartForm

Create `apps/dashboard/src/components/pilot/PilotStartForm.vue`:

```vue
<script setup lang="ts">
import { computed, ref } from 'vue';
import PilotPreflightTable from './PilotPreflightTable.vue';

interface PreflightRow {
  chapter: number;
  ok: boolean;
  message: string;
}

const props = defineProps<{
  slug: string;
  preflightRows: PreflightRow[];
  preflightLoading: boolean;
  startLoading: boolean;
  error: string | null;
  preflightAllOk?: boolean;
}>();

const emit = defineEmits<{
  'submit-preflight': [payload: { slug: string; start_chapter: number; end_chapter: number }];
  'submit-start': [payload: { slug: string; start_chapter: number; end_chapter: number; budget_usd: number; mode: 'canon' | 'pilot' }];
}>();

const mode = ref<'canon' | 'pilot'>('pilot');
const startChapter = ref<number>(1);
const endChapter = ref<number>(10);
const budgetUsd = ref<number>(5);

const isValid = computed(() => startChapter.value <= endChapter.value && startChapter.value >= 1);

function onPreflight() {
  if (!isValid.value) return;
  emit('submit-preflight', { slug: props.slug, start_chapter: startChapter.value, end_chapter: endChapter.value });
}

function onStart() {
  if (!isValid.value || !props.preflightAllOk) return;
  emit('submit-start', {
    slug: props.slug,
    start_chapter: startChapter.value,
    end_chapter: endChapter.value,
    budget_usd: budgetUsd.value,
    mode: mode.value,
  });
}
</script>

<template>
  <section class="pilot-start-form pixel-card" data-testid="pilot-start-form">
    <h2 class="section-title">启动批章节</h2>
    <form class="start-form" @submit.prevent="onStart">
      <div class="form-row">
        <label for="pilot-mode">模式</label>
        <select id="pilot-mode" v-model="mode" data-testid="start-mode" class="form-input pixel-border">
          <option value="canon">canon</option>
          <option value="pilot">pilot</option>
        </select>
      </div>
      <div class="form-row">
        <label for="pilot-from">起始章</label>
        <input id="pilot-from" v-model.number="startChapter" type="number" min="1" data-testid="start-chapter-from" class="form-input pixel-border" />
      </div>
      <div class="form-row">
        <label for="pilot-to">结束章</label>
        <input id="pilot-to" v-model.number="endChapter" type="number" min="1" data-testid="start-chapter-to" class="form-input pixel-border" />
      </div>
      <div class="form-row">
        <label for="pilot-budget">预算 (USD)</label>
        <input id="pilot-budget" v-model.number="budgetUsd" type="number" min="0" max="100" step="0.01" data-testid="start-budget-usd" class="form-input pixel-border" />
      </div>
      <div class="form-actions">
        <button type="button" class="run-btn pixel-border preflight-btn" data-testid="preflight-btn" :disabled="preflightLoading || !isValid" @click="onPreflight">
          {{ preflightLoading ? '检查中…' : 'Preflight 检查' }}
        </button>
        <button type="submit" class="run-btn pixel-border start-btn" data-testid="start-submit-btn" :disabled="startLoading || !isValid || !preflightAllOk">
          {{ startLoading ? '启动中…' : '启动批处理' }}
        </button>
      </div>
      <p v-if="error" class="form-error" data-testid="start-form-error" role="alert">{{ error }}</p>
    </form>
    <PilotPreflightTable :rows="preflightRows" />
  </section>
</template>

<style scoped>
.pilot-start-form { padding: 1rem; margin-bottom: 1rem; }
.start-form { display: grid; gap: 0.75rem; max-width: 400px; }
.form-row { display: flex; flex-direction: column; gap: 0.25rem; }
.form-actions { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.form-error { color: var(--error, #c33); margin-top: 0.5rem; }
.run-btn { padding: 0.4rem 0.8rem; cursor: pointer; }
.run-btn:disabled { cursor: not-allowed; opacity: 0.5; }
</style>
```

### Step 8.7: Run GREEN

```bash
pnpm vitest run tests/unit/components/pilot/
pnpm tsc --noEmit
```

Expected: 7 tests pass (3 table + 4 form) + tsc clean.

### Step 8.8: Commit

```bash
git add apps/dashboard/src/components/pilot/PilotStartForm.vue apps/dashboard/src/components/pilot/PilotPreflightTable.vue apps/dashboard/tests/unit/components/pilot/
git commit -m "feat(components): PilotStartForm + PilotPreflightTable

PilotStartForm: form fields (mode/start/end/budget) + Preflight + Start buttons.
PilotPreflightTable: chapter-by-chapter PASS/FAIL table.

Pre-flight gate: Start button disabled when preflightAllOk=false.
Form validation: start <= end >= 1.

7 tests across 2 components: render / emit / disabled logic / empty state."
```

---

## Task 9: PilotLivePanel (Part D2)

**Files:**
- Create: `apps/dashboard/src/components/pilot/PilotLivePanel.vue`
- Create: `apps/dashboard/tests/unit/components/pilot/pilot-live-panel.spec.ts`

### Step 9.1: Write RED test

Create `apps/dashboard/tests/unit/components/pilot/pilot-live-panel.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotLivePanel from '@/components/pilot/PilotLivePanel.vue';

const runningJob = {
  job_id: 'j1', slug: 's1', status: 'running',
  start_chapter: 1, end_chapter: 14, budget_usd: 5,
  mode: 'pilot', pid: 12345, log_path: '/tmp/x', log_tail: 'last log line',
  started_at: new Date().toISOString(), finished_at: null,
  exit_code: null, error: null,
};

describe('PilotLivePanel', () => {
  it('renders nothing when activeJob is null', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: null, etaSeconds: null, cancelLoading: false } });
    expect(wrapper.find('[data-testid="pilot-live-empty"]').exists()).toBe(true);
  });

  it('shows status pill for running job', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: 60, cancelLoading: false } });
    expect(wrapper.find('[data-testid="pilot-status"]').text()).toContain('running');
  });

  it('displays ETA when provided', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: 90, cancelLoading: false } });
    expect(wrapper.text()).toMatch(/ETA|预计剩余/);
    expect(wrapper.text()).toContain('1分');
  });

  it('shows waiting message when ETA is null', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: null, cancelLoading: false } });
    expect(wrapper.text()).toContain('等待');
  });

  it('emits request-cancel when Cancel button clicked', async () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: 60, cancelLoading: false } });
    await wrapper.find('[data-testid="pilot-cancel-btn"]').trigger('click');
    expect(wrapper.emitted('request-cancel')).toBeTruthy();
  });

  it('renders log_tail when present', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: null, cancelLoading: false } });
    expect(wrapper.find('[data-testid="pilot-log-tail"]').text()).toContain('last log line');
  });

  it('handles cancelled status', () => {
    const wrapper = mount(PilotLivePanel, {
      props: { activeJob: { ...runningJob, status: 'cancelled' }, etaSeconds: null, cancelLoading: false },
    });
    expect(wrapper.find('[data-testid="pilot-status"]').text()).toContain('cancelled');
  });
});
```

### Step 9.2: Run RED

```bash
pnpm vitest run tests/unit/components/pilot/pilot-live-panel.spec.ts
```

Expected: ImportError.

### Step 9.3: Implement PilotLivePanel

Create `apps/dashboard/src/components/pilot/PilotLivePanel.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue';

interface ActiveJob {
  job_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  start_chapter: number;
  end_chapter: number;
  budget_usd: number;
  pid?: number | null;
  log_path?: string;
  log_tail?: string | null;
  started_at: string;
  finished_at?: string | null;
  exit_code?: number | null;
  error?: string | null;
}

const props = defineProps<{
  activeJob: ActiveJob | null;
  etaSeconds: number | null;
  cancelLoading: boolean;
}>();

const emit = defineEmits<{ 'request-cancel': [jobId: string] }>();

const statusColor = computed(() => {
  if (!props.activeJob) return 'unknown';
  return props.activeJob.status;
});

const etaDisplay = computed(() => {
  if (props.etaSeconds === null) return '等待首个 chapter 完成…';
  const minutes = Math.floor(props.etaSeconds / 60);
  const seconds = Math.round(props.etaSeconds % 60);
  if (minutes >= 1) return `约 ${minutes}分${seconds}秒`;
  return `约 ${seconds}秒`;
});

const chapterRange = computed(() => {
  if (!props.activeJob) return '';
  return `ch${String(props.activeJob.start_chapter).padStart(3, '0')}–ch${String(props.activeJob.end_chapter).padStart(3, '0')}`;
});
</script>

<template>
  <section class="pilot-live-panel pixel-card" data-testid="pilot-live-panel">
    <h2 class="section-title">实时状态</h2>
    <p v-if="!activeJob" class="empty-msg" data-testid="pilot-live-empty">无正在运行的 batch</p>
    <div v-else class="live-content">
      <div class="status-row">
        <span class="status-label">状态:</span>
        <strong :class="`job-status-${statusColor}`" data-testid="pilot-status">{{ activeJob.status }}</strong>
        <span class="chapter-range">{{ chapterRange }}</span>
        <span class="budget">${{ activeJob.budget_usd }}</span>
        <span v-if="activeJob.pid" class="pid">pid: {{ activeJob.pid }}</span>
      </div>
      <div class="eta-row">
        <span class="eta-label">预计剩余:</span>
        <span class="eta-value" data-testid="pilot-eta">{{ etaDisplay }}</span>
      </div>
      <pre v-if="activeJob.log_tail" class="log-tail" data-testid="pilot-log-tail">{{ activeJob.log_tail }}</pre>
      <div class="actions-row">
        <button v-if="activeJob.status === 'running'" type="button" class="cancel-btn pixel-border" data-testid="pilot-cancel-btn" :disabled="cancelLoading" @click="emit('request-cancel', activeJob.job_id)">
          {{ cancelLoading ? '取消中…' : 'Cancel' }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pilot-live-panel { padding: 1rem; margin-bottom: 1rem; }
.status-row { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem; }
.job-status-running { color: var(--success, #2c7a2c); font-weight: 600; }
.job-status-completed { color: var(--info, #2c6cb0); font-weight: 600; }
.job-status-failed, .job-status-cancelled { color: var(--error, #c33); font-weight: 600; }
.eta-row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.log-tail { background: var(--code-bg, #1e1e1e); color: var(--code-fg, #ddd); padding: 0.5rem; border-radius: 4px; max-height: 200px; overflow-y: auto; font-size: 0.85rem; }
.empty-msg { color: var(--muted, #888); font-style: italic; }
.cancel-btn { padding: 0.4rem 0.8rem; cursor: pointer; background: var(--error-bg, #fee); color: var(--error, #c33); border-color: var(--error, #c33); }
</style>
```

### Step 9.4: Run GREEN

```bash
pnpm vitest run tests/unit/components/pilot/pilot-live-panel.spec.ts
pnpm tsc --noEmit
```

Expected: 7 tests pass + tsc clean.

### Step 9.5: Commit

```bash
git add apps/dashboard/src/components/pilot/PilotLivePanel.vue apps/dashboard/tests/unit/components/pilot/pilot-live-panel.spec.ts
git commit -m "feat(components): PilotLivePanel with status + ETA + log tail + cancel

Renders active job: status pill (running/completed/failed/cancelled) + chapter range + budget + pid.
Shows ETA in human format (X分Y秒) or 'waiting for first chapter'.
log_tail rendered in scrollable <pre>.
Cancel button emits request-cancel; only shown for status==='running'.

7 tests: empty state / status pill / ETA display / null ETA / cancel emit / log_tail / cancelled status."
```

---

## Task 10: PilotCancelDialog (Part D3)

**Files:**
- Create: `apps/dashboard/src/components/pilot/PilotCancelDialog.vue`
- Create: `apps/dashboard/tests/unit/components/pilot/pilot-cancel-dialog.spec.ts`

### Step 10.1: Write RED test

Create `apps/dashboard/tests/unit/components/pilot/pilot-cancel-dialog.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotCancelDialog from '@/components/pilot/PilotCancelDialog.vue';

describe('PilotCancelDialog', () => {
  it('renders nothing when visible=false', () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: false, jobId: 'j1', loading: false },
      attachTo: true,
    });
    expect(wrapper.find('[data-testid="pilot-cancel-dialog"]').exists()).toBe(false);
  });

  it('shows jobId when visible=true', () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: true, jobId: 'abc-123', loading: false },
      attachTo: true,
    });
    expect(wrapper.text()).toContain('abc-123');
  });

  it('emits confirm when confirm button clicked', async () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: true, jobId: 'j1', loading: false },
      attachTo: true,
    });
    await wrapper.find('[data-testid="cancel-confirm-btn"]').trigger('click');
    expect(wrapper.emitted('confirm')).toBeTruthy();
  });

  it('emits hold-on when hold-on button clicked', async () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: true, jobId: 'j1', loading: false },
      attachTo: true,
    });
    await wrapper.find('[data-testid="cancel-hold-btn"]').trigger('click');
    expect(wrapper.emitted('hold-on')).toBeTruthy();
  });
});
```

### Step 10.2: Run RED

```bash
pnpm vitest run tests/unit/components/pilot/pilot-cancel-dialog.spec.ts
```

Expected: ImportError.

### Step 10.3: Implement PilotCancelDialog

Create `apps/dashboard/src/components/pilot/PilotCancelDialog.vue`:

```vue
<script setup lang="ts">
defineProps<{ visible: boolean; jobId: string; loading: boolean }>();
const emit = defineEmits<{
  confirm: [];
  'hold-on':[];
}>();
</script>

<template>
  <div v-if="visible" class="pilot-cancel-dialog" data-testid="pilot-cancel-dialog" role="dialog" aria-modal="true">
    <div class="dialog-content pixel-card">
      <h3 class="dialog-title">确认取消 batch?</h3>
      <p class="dialog-body">
        Job <code>{{ jobId }}</code> 将收到 SIGTERM。5 秒未退出将自动 SIGKILL。
      </p>
      <p class="dialog-body">当前进度将丢失，是否继续？</p>
      <div class="dialog-actions">
        <button type="button" class="hold-btn pixel-border" data-testid="cancel-hold-btn" :disabled="loading" @click="emit('hold-on')">
          {{ loading ? '取消中…' : '等一下' }}
        </button>
        <button type="button" class="confirm-btn pixel-border" data-testid="cancel-confirm-btn" :disabled="loading" @click="emit('confirm')">
          {{ loading ? '取消中…' : '确认取消' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pilot-cancel-dialog { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog-content { padding: 1.5rem; max-width: 480px; background: var(--surface, #fff); }
.dialog-title { margin: 0 0 1rem; }
.dialog-body { margin: 0.5rem 0; }
.dialog-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.confirm-btn { background: var(--error-bg, #fee); color: var(--error, #c33); border-color: var(--error, #c33); padding: 0.4rem 0.8rem; cursor: pointer; }
.hold-btn { padding: 0.4rem 0.8rem; cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: 0.5; }
</style>
```

### Step 10.4: Run GREEN

```bash
pnpm vitest run tests/unit/components/pilot/pilot-cancel-dialog.spec.ts
pnpm tsc --noEmit
```

Expected: 4 tests pass + tsc clean.

### Step 10.5: Commit

```bash
git add apps/dashboard/src/components/pilot/PilotCancelDialog.vue apps/dashboard/tests/unit/components/pilot/pilot-cancel-dialog.spec.ts
git commit -m "feat(components): PilotCancelDialog confirm-with-grace

Modal with '等一下' (hold-on) + '确认取消' (confirm) buttons.
Warns user: SIGTERM + 5s grace + SIGKILL fallback + 进度将丢失.

4 tests: hidden when !visible / jobId rendered / confirm emit / hold-on emit."
```

---

## Task 11: PilotHistoryList (Part D4)

**Files:**
- Create: `apps/dashboard/src/components/pilot/PilotHistoryList.vue`
- Create: `apps/dashboard/tests/unit/components/pilot/pilot-history-list.spec.ts`

### Step 11.1: Write RED test

Create `apps/dashboard/tests/unit/components/pilot/pilot-history-list.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotHistoryList from '@/components/pilot/PilotHistoryList.vue';

const sampleHistory = [
  { job_id: 'j1', status: 'completed', start_chapter: 1, end_chapter: 10, mode: 'pilot', started_at: '2026-09-01T00:00:00Z', budget_usd: 5, exit_code: 0 },
  { job_id: 'j2', status: 'failed', start_chapter: 11, end_chapter: 20, mode: 'pilot', started_at: '2026-09-02T00:00:00Z', budget_usd: 3, exit_code: 1 },
];

describe('PilotHistoryList', () => {
  it('renders one row per history entry', () => {
    const wrapper = mount(PilotHistoryList, { props: { history: sampleHistory } });
    const rows = wrapper.findAll('tbody tr');
    expect(rows.length).toBeGreaterThanOrEqual(2);
  });

  it('shows empty state when no history', () => {
    const wrapper = mount(PilotHistoryList, { props: { history: [] } });
    expect(wrapper.find('[data-testid="pilot-history-empty"]').exists()).toBe(true);
  });

  it('emits select-job when row clicked', async () => {
    const wrapper = mount(PilotHistoryList, { props: { history: sampleHistory } });
    await wrapper.find('[data-testid="history-row-j1"]').trigger('click');
    expect(wrapper.emitted('select-job')).toBeTruthy();
    expect(wrapper.emitted('select-job')![0][0]).toBe('j1');
  });

  it('shows status pill text for each row', () => {
    const wrapper = mount(PilotHistoryList, { props: { history: sampleHistory } });
    expect(wrapper.text()).toContain('completed');
    expect(wrapper.text()).toContain('failed');
  });
});
```

### Step 11.2: Run RED

```bash
pnpm vitest run tests/unit/components/pilot/pilot-history-list.spec.ts
```

Expected: ImportError.

### Step 11.3: Implement PilotHistoryList

Create `apps/dashboard/src/components/pilot/PilotHistoryList.vue`:

```vue
<script setup lang="ts">
interface HistoryRow {
  job_id: string;
  status: string;
  start_chapter: number;
  end_chapter: number;
  mode: string;
  started_at: string;
  budget_usd: number;
  exit_code: number | null;
  finished_at?: string | null;
  error?: string | null;
}

defineProps<{ history: HistoryRow[] }>();
const emit = defineEmits<{ 'select-job': [jobId: string] }>();
</script>

<template>
  <section class="pilot-history-list pixel-card" data-testid="pilot-history-list">
    <h2 class="section-title">历史 batch</h2>
    <p v-if="history.length === 0" class="empty-msg" data-testid="pilot-history-empty">无历史 batch</p>
    <table v-else class="history-table" aria-label="Pilot 历史 batch">
      <thead>
        <tr>
          <th>Job</th><th>模式</th><th>章节</th><th>状态</th><th>启动时间</th><th>预算</th><th>退出码</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in history" :key="row.job_id" :data-testid="`history-row-${row.job_id}`" class="history-row" @click="emit('select-job', row.job_id)">
          <td><code>{{ row.job_id }}</code></td>
          <td>{{ row.mode }}</td>
          <td>ch{{ String(row.start_chapter).padStart(3, '0') }}–{{ String(row.end_chapter).padStart(3, '0') }}</td>
          <td :class="`status-${row.status}`">{{ row.status }}</td>
          <td>{{ row.started_at }}</td>
          <td>${{ row.budget_usd }}</td>
          <td>{{ row.exit_code ?? '—' }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.pilot-history-list { padding: 1rem; }
.history-table { width: 100%; border-collapse: collapse; }
.history-table th, .history-table td { padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border, #ddd); }
.history-row { cursor: pointer; }
.history-row:hover { background: var(--hover, rgba(0, 0, 0, 0.05)); }
.status-running { color: var(--success, #2c7a2c); font-weight: 600; }
.status-completed { color: var(--info, #2c6cb0); font-weight: 600; }
.status-failed, .status-cancelled { color: var(--error, #c33); font-weight: 600; }
.empty-msg { color: var(--muted, #888); font-style: italic; }
</style>
```

### Step 11.4: Run GREEN

```bash
pnpm vitest run tests/unit/components/pilot/pilot-history-list.spec.ts
pnpm tsc --noEmit
```

Expected: 4 tests pass + tsc clean.

### Step 11.5: Commit

```bash
git add apps/dashboard/src/components/pilot/PilotHistoryList.vue apps/dashboard/tests/unit/components/pilot/pilot-history-list.spec.ts
git commit -m "feat(components): PilotHistoryList with status table + select-job emit

Renders past batch jobs in tabular form. Row click emits select-job.
Columns: job_id / mode / chapter range / status pill / started_at / budget / exit_code.

4 tests: row count / empty state / select-job emit / status rendering."
```

---

## Task 12: PilotPage assembly (Part E1)

**Files:**
- Create: `apps/dashboard/src/pages/PilotPage.vue`
- Create: `apps/dashboard/tests/unit/pages/pilot-page.spec.ts`

### Step 12.1: Write RED page test

Create `apps/dashboard/tests/unit/pages/pilot-page.spec.ts`:

```typescript
import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';

const mockUsePilotBatch = {
  activeJob: { value: null },
  history: { value: [] },
  preflightRows: { value: [] },
  preflightLoading: { value: false },
  preflightError: { value: null },
  startLoading: { value: false },
  startError: { value: null },
  cancelLoading: { value: false },
  cancelError: { value: null },
  isJobActive: { value: false },
  refreshActive: vi.fn(),
  refreshHistory: vi.fn(),
  runPreflight: vi.fn(),
  startBatch: vi.fn(),
  cancelBatch: vi.fn(),
};

vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => mockUsePilotBatch,
}));

const mockStudioProject = { activeSlug: { value: 'test-slug' } };
vi.mock('@/composables', () => ({
  useStudioProject: () => mockStudioProject,
}));

import PilotPage from '@/pages/PilotPage.vue';

describe('PilotPage', () => {
  it('renders start form + live panel + history list', () => {
    const wrapper = mount(PilotPage);
    expect(wrapper.find('[data-testid="pilot-start-form"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="pilot-live-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="pilot-history-list"]').exists()).toBe(true);
  });

  it('refreshes active + history on mount', () => {
    mount(PilotPage);
    expect(mockUsePilotBatch.refreshActive).toHaveBeenCalled();
    expect(mockUsePilotBatch.refreshHistory).toHaveBeenCalled();
  });

  it('shows error banner when startError is set', async () => {
    mockUsePilotBatch.startError.value = 'batch failed';
    const wrapper = mount(PilotPage);
    expect(wrapper.text()).toContain('batch failed');
    mockUsePilotBatch.startError.value = null;
  });
});
```

### Step 12.2: Run RED

```bash
pnpm vitest run tests/unit/pages/pilot-page.spec.ts
```

Expected: ImportError.

### Step 12.3: Implement PilotPage

Create `apps/dashboard/src/pages/PilotPage.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useStudioProject } from '@/composables';
import { usePilotBatch } from '@/composables/usePilotBatch';
import PilotStartForm from '@/components/pilot/PilotStartForm.vue';
import PilotLivePanel from '@/components/pilot/PilotLivePanel.vue';
import PilotHistoryList from '@/components/pilot/PilotHistoryList.vue';
import PilotCancelDialog from '@/components/pilot/PilotCancelDialog.vue';

const studio = useStudioProject();
const pilot = usePilotBatch();

const cancelDialogJobId = ref<string | null>(null);
const eta = ref<number | null>(null);

onMounted(async () => {
  await pilot.refreshActive();
  const slug = studio.activeSlug?.value ?? '';
  if (slug) await pilot.refreshHistory(slug);
});

async function onPreflight(payload: { slug: string; start_chapter: number; end_chapter: number }) {
  await pilot.runPreflight(payload);
}

async function onStart(payload: { slug: string; start_chapter: number; end_chapter: number; budget_usd: number; mode: 'canon' | 'pilot' }) {
  await pilot.startBatch(payload);
}

function onRequestCancel(jobId: string) {
  cancelDialogJobId.value = jobId;
}

async function onConfirmCancel() {
  if (!cancelDialogJobId.value) return;
  await pilot.cancelBatch(cancelDialogJobId.value);
  cancelDialogJobId.value = null;
}

function onHoldOn() {
  cancelDialogJobId.value = null;
}
</script>

<template>
  <div class="pilot-page l1-page" data-testid="pilot-page">
    <div class="l1-page__body l1-panel-enter hub-l1__panel">
      <h1 class="page-title">Pilot 流水线</h1>
      <p v-if="pilot.startError.value" class="page-error" data-testid="pilot-page-error" role="alert">{{ pilot.startError.value }}</p>
      <PilotStartForm
        :slug="studio.activeSlug?.value ?? ''"
        :preflight-rows="pilot.preflightRows.value"
        :preflight-loading="pilot.preflightLoading.value"
        :start-loading="pilot.startLoading.value"
        :error="pilot.startError.value"
        @submit-preflight="onPreflight"
        @submit-start="onStart"
      />
      <PilotLivePanel
        :active-job="pilot.activeJob.value"
        :eta-seconds="eta"
        :cancel-loading="pilot.cancelLoading.value"
        @request-cancel="onRequestCancel"
      />
      <PilotHistoryList :history="pilot.history.value" />
      <PilotCancelDialog
        :visible="cancelDialogJobId !== null"
        :job-id="cancelDialogJobId ?? ''"
        :loading="pilot.cancelLoading.value"
        @confirm="onConfirmCancel"
        @hold-on="onHoldOn"
      />
    </div>
  </div>
</template>

<style scoped>
.pilot-page { padding: 1rem; }
.page-title { margin: 0 0 1rem; }
.page-error { color: var(--error, #c33); background: var(--error-bg, #fee); padding: 0.5rem 1rem; border-radius: 4px; margin-bottom: 1rem; }
</style>
```

### Step 12.4: Run GREEN

```bash
pnpm vitest run tests/unit/pages/pilot-page.spec.ts
pnpm tsc --noEmit
```

Expected: 3 tests pass + tsc clean.

### Step 12.5: Commit

```bash
git add apps/dashboard/src/pages/PilotPage.vue apps/dashboard/tests/unit/pages/pilot-page.spec.ts
git commit -m "feat(pages): PilotPage assembles 4 components + composable wiring

Composes PilotStartForm + PilotLivePanel + PilotHistoryList + PilotCancelDialog.
usePilotBatch for state, useStudioProject for current slug.
On mount: refreshActive + refreshHistory.
Start form events → pilot.startBatch. Cancel request → dialog → pilot.cancelBatch.

3 page tests: all 4 sections render / onMount refresh / error banner."
```

---

## Task 13: dashboardNav entry (Part E2)

**Files:**
- Modify: `apps/dashboard/src/config/dashboardNav.js`
- Create or Modify: `apps/dashboard/tests/unit/config/dashboard-nav.spec.ts`

### Step 13.1: Read existing nav config to find pattern

```bash
grep -n "pilot\|workflows\|studio" apps/dashboard/src/config/dashboardNav.js | head -20
```

### Step 13.2: Write RED nav test

Create `apps/dashboard/tests/unit/config/dashboard-nav.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import { DASHBOARD_NAV_ENTRIES } from '@/config/dashboardNav';

describe('DASHBOARD_NAV_ENTRIES', () => {
  it('includes a Pilot entry with key=pilot', () => {
    const entry = DASHBOARD_NAV_ENTRIES.find((e) => e.key === 'pilot');
    expect(entry).toBeDefined();
    expect(entry?.path).toBe('/pilot');
    expect(entry?.label).toBe('Pilot 流水线');
  });

  it('Pilot entry is enabled by default', () => {
    const entry = DASHBOARD_NAV_ENTRIES.find((e) => e.key === 'pilot');
    expect(entry?.enabled).toBe(true);
  });
});
```

### Step 13.3: Run RED

```bash
pnpm vitest run tests/unit/config/dashboard-nav.spec.ts
```

Expected: Test fails because `pilot` entry not present.

### Step 13.4: Add Pilot entry to dashboardNav.js

Modify `apps/dashboard/src/config/dashboardNav.js` — add to the existing array (find StudioPage-like entry, add Pilot as a sibling):

```javascript
{
  key: 'pilot',
  path: '/pilot',
  label: 'Pilot 流水线',
  enabled: true,
  icon: 'rocket',
  section: 'production',
},
```

Adjust `icon` + `section` per existing convention in the file.

### Step 13.5: Run GREEN

```bash
pnpm vitest run tests/unit/config/dashboard-nav.spec.ts
pnpm tsc --noEmit
```

Expected: 2 tests pass + tsc clean.

### Step 13.6: Commit

```bash
git add apps/dashboard/src/config/dashboardNav.js apps/dashboard/tests/unit/config/dashboard-nav.spec.ts
git commit -m "feat(nav): add Pilot 流水线 sidebar entry

Adds { key: 'pilot', path: '/pilot', label: 'Pilot 流水线' } to DASHBOARD_NAV_ENTRIES.
Discovered by /pilot route; icon + section per existing convention.

2 nav tests: entry presence / enabled=true."
```

---

## Task 14: Cleanup StudioPage embedded pilot section (Part F1)

**Files:**
- Modify: `apps/dashboard/src/pages/StudioPage.vue` (remove pilot section)
- Modify: `apps/dashboard/tests/unit/pages/studio-page.spec.ts` (update assertions)

### Step 14.1: Verify current StudioPage pilot section

```bash
grep -n "pilot\|fetchStudioStartBatchJob\|batchRunning\|preflight-btn" apps/dashboard/src/pages/StudioPage.vue | head -20
```

### Step 14.2: Remove the pilot section

Read `StudioPage.vue` lines around the pilot section (lines 270-360 from spec). Remove:
- The `mode` select + `pilot` option
- The `budgetUsd` input
- The Preflight button + preflightRows table
- The batchCommand block (start button + job panel)

Keep StudioPage's project registry / preflight-validation / onboarding steps sections intact.

### Step 14.3: Run studio-page tests to verify no regression

```bash
pnpm vitest run tests/unit/pages/studio-page.spec.ts
```

If tests fail with pilot-related assertions, remove or update them to match the new structure (no embedded pilot surface).

### Step 14.4: Verify no broken imports

```bash
pnpm tsc --noEmit
pnpm eslint apps/dashboard/src/pages/StudioPage.vue
```

Expected: clean (or only pre-existing warnings).

### Step 14.5: Commit

```bash
git add apps/dashboard/src/pages/StudioPage.vue apps/dashboard/tests/unit/pages/studio-page.spec.ts
git commit -m "refactor(studio-page): remove embedded Pilot section (now in PilotPage)

StudioPage no longer hosts Pilot start form / preflight / / batch command /
 / job status. Users navigate to /pilot page for batch lifecycle.

Pre-existing onboarding + project registry + CLI quick-start sections preserved.
studio-page.spec.ts updated to remove pilot assertions."
```

---

## Task 15: ruff --fix + final verification (Part D5 + verification gates)

**Files:**
- Any files touched in this phase with I001 violations

### Step 15.1: Run ruff to detect issues

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-23-pilot-page
ruff check --select I001 .
```

If output is non-empty, run:

```bash
ruff check --select I001 --fix .
```

### Step 15.2: Run full verification gates

```bash
# Backend
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner_*.py apps/studio_api/tests/test_studio_cancel_route.py -v

# Frontend
cd apps/dashboard
pnpm vitest run
pnpm tsc --noEmit
pnpm eslint .
pnpm exec knip
cd ../..

# Lint
ruff check .
ruff format --check .

# Architecture
# (manual: confirm 3 import-linter contracts KEPT)
```

Expected: all pass. Save full output to `/tmp/phase-23-gates.log` for the handoff.

### Step 15.3: Commit any ruff fixes

```bash
git add -u
git diff --cached --quiet || git commit -m "chore(ruff): I001 import sort fixes from Phase 23"
```

If no changes, skip.

---

## Task 16: docs sync + handoff (Part F2)

**Files:**
- Modify: `CLAUDE.md` (add v23.0 entry)
- Modify: `.lingwen/architecture.yml` (version bump + pilot_page invariant)
- Create: `docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md`

### Step 16.1: Add v23.0 entry to CLAUDE.md

At the top of the version list, insert (preserving existing format from v22.0):

```markdown
  → v23.0 (Phase 23 — Pilot Page feature phase — 16 source commits on branch `phase-23-pilot-page`; **first new feature phase since Phase 115 Write Workspace (v15.0)** — closes the longest LingWen dry spell). Frontend reorganization: extracted embedded Pilot surface from `StudioPage.vue` into dedicated `PilotPage.vue` + 5 components (`PilotStartForm`/`PilotPreflightTable`/`PilotLivePanel`/`PilotCancelDialog`/`PilotHistoryList`) + `usePilotBatch` composable with 3s auto-polling + ETA via `pilot_records.jsonl` join. Backend light touch: `infra.studio_batch_runner.cancel_batch_job()` with SIGTERM + 5s grace + SIGKILL fallback + `POST /api/studio/batch/<job_id>/cancel` route. New DTOs: `StudioBatchJobSummary` + `StudioBatchJobListResponse` in `lingwen_shared` (Python + TS codegen). 1 NEW architecture invariant (#48: PilotPage owns batch lifecycle surface; StudioPage no longer hosts Pilot). N lessons (TBD from execution). Carryover to Phase 24+: SSE/WebSocket real-time progress + per-chapter preview drawer + batch templates + multi-LLM concurrent. See `docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md`)
```

### Step 16.2: Update architecture.yml

Modify `.lingwen/architecture.yml`:

```yaml
version: "23.0"  # Phase 23 — Pilot Page: ...
```

And add invariant:

```yaml
  - id: I048
    rule: "PilotPage owns batch lifecycle surface; StudioPage MUST NOT host embedded Pilot start/preflight/job panel"
    severity: error
    scope: "apps/dashboard/src/pages/StudioPage.vue"
```

### Step 16.3: Write handoff doc

Create `docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md`:

```markdown
# Phase 23 — Pilot Page · Handoff

> **Date**: 2026-09-02
> **Branch**: `phase-23-pilot-page`
> **Master HEAD**: <commit>
> **Commits**: 16 source + 1 handoff = 17 total

## Summary

First new feature phase since Phase 115 Write Workspace (v15.0, 2026-08-26).
Closes the longest LingWen dry spell (7 days without user-facing feature work).

Extracts Pilot surface from `StudioPage.vue` into dedicated top-level page
with start/observe/cancel/history close-loop.

## What shipped

### Backend (4 commits)
- `cancel_batch_job()` in `infra/studio_batch_runner.py`: SIGTERM + 5s grace + SIGKILL fallback
- `POST /api/studio/batch/<job_id>/cancel` route: 404/409/200 semantics
- `compute_pilot_eta()` helper: pure ETA function from completed chapters + elapsed
- 4 cancel tests + 3 ETA tests = 7 new pytest passing

### Frontend (11 commits)
- `PilotPage.vue` (new page)
- 5 components (`pilot/*.vue`)
- `usePilotBatch.ts` composable (state + actions + polling)
- 2 API wrappers (`cancelStudioBatchJob` + `listStudioBatchJobs`)
- ~30 new vitest passing
- 1 nav config addition

### Cleanup (1 commit)
- `StudioPage.vue` no longer hosts embedded Pilot section

## Architecture invariants

- 1 NEW: #48 PilotPage owns batch lifecycle surface
- All 47 previous invariants preserved

## Verification gates (all green)

- vitest: 1762 + ~30 new = ~1792 passing
- vue-tsc: 0
- ESLint: 0
- knip: `{"issues":[]}`
- ruff check: clean
- ruff format --check: clean
- lint-imports: 3 contracts KEPT

## Lessons

<to be filled in during execution>

## Carryover to Phase 24+

- SSE/WebSocket real-time progress push (replace 3s polling)
- Per-chapter preview drawer in PilotLivePanel
- Batch templates (save common mode/budget/chapters combos)
- Multi-LLM provider concurrent batches
- Pilot + Insight dashboard integration
```

### Step 16.4: Commit + push branch

```bash
git add CLAUDE.md .lingwen/architecture.yml docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md
git commit -m "docs(phase-23): handoff doc + CLAUDE.md v23.0 + architecture.yml invariant #48

1 NEW architecture invariant: PilotPage owns batch lifecycle surface.
Phase 23 closes longest LingWen dry spell (first feature since Phase 115 Write Workspace).

Carryover: SSE real-time + per-chapter preview + batch templates + multi-LLM concurrent."

git push -u origin phase-23-pilot-page
```

### Step 16.5: Merge to master

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-23-pilot-page
git push origin master
```

---

## Self-Review Checklist

- ✅ Spec coverage: every §3 component has a task; cancel endpoint covered in Task 3; ETA helper in Task 4; composable in Task 7; page in Task 12; nav in Task 13; cleanup in Task 14; docs in Task 16
- ✅ Placeholder scan: no TBD/TODO/FIXME (TODO Phase-24+ in Task 7.3 runPreflight is documented as intentional carryover, not a stub to fix)
- ✅ Type consistency: `cancelStudioBatchJob` + `listStudioBatchJobs` defined in Tasks 5-6, used in Task 7.3 + Task 12.3; `StudioBatchJobResponseDTO` field set matches `infra.studio_batch_runner.BatchJob` dataclass; `StudioBatchJobSummaryDTO` fields match backend DTO
- ✅ Scope: single feature (Pilot page); 16 atomic commits; no unrelated refactoring
- ✅ DRY: composable owns state + polling; no duplicated logic across components
- ✅ YAGNI: SSE explicitly excluded (Phase 24+); preflight wrapper is documented carryover not stub

## Open Risks (per §6)

- **PID reuse**: mitigated by `os.kill(pid, 0)` liveness check before SIGTERM
- **Polling storm**: mitigated by status gate + stopPolling on unmount
- **F1 StudioPage cleanup risk**: revert single commit if needed

## Execution Estimate

- 16 atomic commits across 16 tasks
- ~50 new tests (4 cancel + 3 ETA + 3 route + 6 wrappers + 5 composable + 7 startform/preflight + 7 live + 4 cancel-dialog + 4 history + 3 page + 2 nav)
- Estimated wall-clock: 3-4 hours for subagent-driven execution