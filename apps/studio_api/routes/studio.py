"""
Phase 15.0 T1.4: /api/studio/* routes.

- studio_list_projects, studio_get_active, studio_set_active, studio_project_summary (lines 1176-1234)
- studio quality + production endpoints (lines 3488-3676)

Most routes share a pattern: lookup active project, 404 if None, then delegate to
infra.studio_registry / infra.studio_batch_runner. We declare a local helper
to dedupe the project lookup boilerplate.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse

from apps.studio_api.models import (
    StudioActiveResponse,
    StudioBatchJobListResponse,
    StudioBatchJobResponse,
    StudioBatchJobSummary,
    StudioBatchRunRequest,
    StudioBatchTemplate,
    StudioBatchTemplateCreateRequest,
    StudioBatchTemplateListResponse,
    StudioBatchTemplateUpdateRequest,
    StudioPreflightChapter,
    StudioPreflightRequest,
    StudioPreflightResponse,
    StudioProjectItem,
    StudioProjectsResponse,
    StudioProseDiffChapter,
    StudioProseDiffResponse,
    StudioProseDiffTotals,
    StudioProseJudgeChapter,
    StudioProseJudgeRating,
    StudioProseJudgeResponse,
    StudioProseJudgeSignal,
    StudioQualityReportResponse,
    StudioQualityResponse,
    StudioSetActiveRequest,
    StudioSummaryResponse,
)
from apps.studio_api.routes.ctx import RoutesContext


def _require_project(ctx: RoutesContext):
    """Look up the active studio project or raise 404. Used by most studio routes."""
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        raise HTTPException(404, "no active studio project")
    return project


def _batch_job_to_response(job) -> StudioBatchJobResponse:
    """Map infra.studio_batch_runner.BatchJob → lingwen_shared StudioBatchJobResponse.

    Both shapes share the same 13 fields; StudioBatchJobResponse adds `log_tail`
    with a None default, so a flat unpack is sufficient.
    """
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


def _template_to_response(template) -> StudioBatchTemplate:
    """Map infra.studio_batch_templates.BatchTemplate → StudioBatchTemplate DTO.

    Both shapes share identical field names, so a flat unpack is sufficient.
    """
    return StudioBatchTemplate(**template.to_dict())


def _validate_event_types(event_types: list[str] | None, known: frozenset[str]) -> None:
    """Raise 400 when any template event preference is not a known SSE type.

    Mirrors the Phase 25 ``/api/studio/batch/<id>/events`` ``event_types`` filter
    validation so a saved preset always maps to subscribeable event types.
    """
    if not event_types:
        return
    unknown = [e for e in event_types if e not in known]
    if unknown:
        raise HTTPException(400, f"unknown event type(s): {', '.join(unknown)}")


def register_studio(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/studio/projects", response_model=StudioProjectsResponse)
    def studio_list_projects() -> StudioProjectsResponse:
        from infra.studio_registry import active_project, list_projects

        projects = list_projects()
        active = active_project()
        return StudioProjectsResponse(
            projects=[
                StudioProjectItem(
                    slug=p.slug,
                    name=p.name,
                    role=p.role,
                    root=str(p.root),
                    location=p.location,
                )
                for p in projects
            ],
            active_slug=active.slug if active else None,
        )

    @app.get("/api/studio/active", response_model=StudioActiveResponse)
    def studio_get_active() -> StudioActiveResponse:
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no studio projects configured")
        return StudioActiveResponse(
            slug=project.slug,
            name=project.name,
            root=str(project.root),
            role=project.role,
        )

    @app.put("/api/studio/active", response_model=StudioActiveResponse)
    def studio_set_active(req: StudioSetActiveRequest) -> StudioActiveResponse:
        from infra.studio_registry import activate_project, get_project_by_slug

        if get_project_by_slug(req.slug) is None:
            raise HTTPException(404, f"unknown project slug: {req.slug!r}")
        try:
            project = activate_project(req.slug)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return StudioActiveResponse(
            slug=project.slug,
            name=project.name,
            root=str(project.root),
            role=project.role,
        )

    @app.get("/api/studio/summary", response_model=StudioSummaryResponse)
    def studio_project_summary() -> StudioSummaryResponse:
        from infra.studio_registry import project_summary

        project = _require_project(ctx)
        return StudioSummaryResponse(**project_summary(project))

    @app.get("/api/studio/quality", response_model=StudioQualityResponse)
    def studio_quality_dashboard() -> StudioQualityResponse:
        from infra.studio_registry import quality_summary

        project = _require_project(ctx)
        return StudioQualityResponse(**quality_summary(project))

    @app.get("/api/studio/quality-report", response_model=StudioQualityReportResponse)
    def studio_quality_report() -> StudioQualityReportResponse:
        from infra.studio_registry import quality_report_summary

        project = _require_project(ctx)
        data = quality_report_summary(project)
        return StudioQualityReportResponse(slug=project.slug, **data)

    @app.get("/api/studio/prose-diff", response_model=StudioProseDiffResponse)
    def studio_prose_diff() -> StudioProseDiffResponse:
        from infra.studio_registry import prose_diff_summary

        project = _require_project(ctx)
        data = prose_diff_summary(project)
        total_delta = data.get("total_delta")
        chapters = [StudioProseDiffChapter(**row) for row in data.get("chapters") or []]
        return StudioProseDiffResponse(
            slug=data["slug"],
            available=data["available"],
            reason=data.get("reason"),
            snapshot_path=data.get("snapshot_path") or "",
            report_path=data.get("report_path"),
            save_command=data.get("save_command"),
            before_captured_at=data.get("before_captured_at"),
            after_captured_at=data.get("after_captured_at"),
            total_delta=StudioProseDiffTotals(**total_delta) if total_delta else None,
            chapters=chapters,
            improved_count=int(data.get("improved_count") or 0),
            regressed_count=int(data.get("regressed_count") or 0),
            has_regression=bool(data.get("has_regression")),
            net_prose_p1_delta=int(data.get("net_prose_p1_delta") or 0),
        )

    @app.get("/api/studio/prose-judge", response_model=StudioProseJudgeResponse)
    def studio_prose_judge() -> StudioProseJudgeResponse:
        from infra.studio_registry import prose_judge_summary

        project = _require_project(ctx)
        data = prose_judge_summary(project)
        if not data.get("available"):
            return StudioProseJudgeResponse(
                slug=data["slug"],
                available=False,
                reason=data.get("reason"),
                report_path=data.get("report_path") or "",
                generate_command=data.get("generate_command"),
            )

        chapters = [
            StudioProseJudgeChapter(
                chapter=int(row["chapter"]),
                avg_score=float(row["avg_score"]),
                ratings=[StudioProseJudgeRating(**r) for r in row.get("ratings") or []],
            )
            for row in data.get("chapters") or []
        ]

        def _signals(key: str) -> list[StudioProseJudgeSignal]:
            return [StudioProseJudgeSignal(**row) for row in data.get(key) or []]

        return StudioProseJudgeResponse(
            slug=data["slug"],
            available=True,
            report_path=data.get("report_path") or "",
            generate_command=data.get("generate_command"),
            source=data.get("source"),
            judged_at=data.get("judged_at"),
            golden_chapters=[int(n) for n in data.get("golden_chapters") or []],
            weighted_avg=float(data.get("weighted_avg") or 0),
            chapters=chapters,
            high_priority_count=int(data.get("high_priority_count") or 0),
            false_positive_candidate_count=int(data.get("false_positive_candidate_count") or 0),
            review_needed_count=int(data.get("review_needed_count") or 0),
            high_priority=_signals("high_priority"),
            false_positive_candidates=_signals("false_positive_candidates"),
            review_needed=_signals("review_needed"),
        )

    @app.post("/api/studio/production/preflight", response_model=StudioPreflightResponse)
    def studio_production_preflight(
        req: StudioPreflightRequest,
        budget_usd: float = Query(default=0.15, ge=0, le=100),
    ) -> StudioPreflightResponse:
        from infra.studio_registry import batch_command, production_preflight

        project = _require_project(ctx)
        if req.end_chapter < req.start_chapter:
            raise HTTPException(400, "end_chapter must be >= start_chapter")

        try:
            result = production_preflight(
                project,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                mode=req.mode,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        cmd = batch_command(
            project,
            start_chapter=req.start_chapter,
            end_chapter=req.end_chapter,
            budget_usd=budget_usd,
        )
        return StudioPreflightResponse(
            slug=result["slug"],
            mode=result["mode"],
            start_chapter=result["start_chapter"],
            end_chapter=result["end_chapter"],
            all_ok=result["all_ok"],
            chapters=[StudioPreflightChapter(**row) for row in result["chapters"]],
            batch_command=cmd,
        )

    @app.post("/api/studio/production/run", response_model=StudioBatchJobResponse)
    def studio_production_run(
        req: StudioBatchRunRequest,
        priority: int = Query(default=0, ge=0, le=100),
    ) -> StudioBatchJobResponse:
        """Start a batch run, or enqueue it (priority-ordered) if already busy."""
        from infra.studio_batch_runner import (
            BatchAlreadyRunningError,
            BatchNotAllowedError,
            BatchPreflightError,
            submit_batch_job,
        )

        project = _require_project(ctx)
        if req.end_chapter < req.start_chapter:
            raise HTTPException(400, "end_chapter must be >= start_chapter")

        try:
            job = submit_batch_job(
                project,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                budget_usd=req.budget_usd,
                mode=req.mode,
                skip_preflight=req.skip_preflight,
                priority=priority,
                max_attempts=req.max_attempts,
            )
        except BatchAlreadyRunningError as exc:
            raise HTTPException(409, str(exc)) from exc
        except BatchNotAllowedError as exc:
            raise HTTPException(403, str(exc)) from exc
        except BatchPreflightError as exc:
            raise HTTPException(422, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        return StudioBatchJobResponse(**job.to_dict())

    @app.get("/api/studio/batch/queue", response_model=StudioBatchJobListResponse)
    def studio_batch_queue_endpoint(
        slug: str,
    ) -> StudioBatchJobListResponse:
        """List queued (not yet started) batch jobs for a slug, ordered by priority."""
        from infra.studio_batch_runner import list_batch_queue

        rows = list_batch_queue(slug)
        return StudioBatchJobListResponse(jobs=[StudioBatchJobSummary.model_validate(r) for r in rows])

    @app.get("/api/studio/production/jobs/active", response_model=Optional[StudioBatchJobResponse])
    def studio_production_active_job() -> Optional[StudioBatchJobResponse]:
        from infra.studio_batch_runner import active_batch_job_for_project

        payload = active_batch_job_for_project()
        if payload is None:
            return None
        return StudioBatchJobResponse(**payload)

    @app.get("/api/studio/production/jobs/{job_id}", response_model=StudioBatchJobResponse)
    def studio_production_job_status(job_id: str) -> StudioBatchJobResponse:
        from infra.studio_batch_runner import get_batch_job

        payload = get_batch_job(job_id)
        if payload is None:
            raise HTTPException(404, f"unknown batch job: {job_id!r}")
        return StudioBatchJobResponse(**payload)

    @app.post("/api/studio/batch/{job_id}/cancel", response_model=StudioBatchJobResponse)
    def studio_batch_cancel_endpoint(job_id: str) -> StudioBatchJobResponse:
        """Cancel a running batch job (SIGTERM + 5s grace + SIGKILL fallback)."""
        from infra.studio_batch_runner import cancel_batch_job

        try:
            job = cancel_batch_job(job_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            # BatchAlreadyRunningError is RuntimeError subclass.
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _batch_job_to_response(job)

    @app.get("/api/studio/batch/history", response_model=StudioBatchJobListResponse)
    def studio_batch_history_endpoint(
        slug: str,
        limit: int = Query(default=20, ge=1, le=100),
    ) -> StudioBatchJobListResponse:
        """List recent batch jobs for a slug (Pilot Page history)."""
        from infra.studio_batch_runner import list_batch_jobs_for_slug

        rows = list_batch_jobs_for_slug(slug, limit=limit)
        return StudioBatchJobListResponse(jobs=[StudioBatchJobSummary.model_validate(r) for r in rows])

    @app.get("/api/studio/batch/{job_id}/events")
    async def studio_batch_events_endpoint(
        job_id: str,
        event_types: str | None = Query(default=None),
        replay: int = Query(default=0),
        slug: str | None = Query(default=None),
        mode: str | None = Query(default=None),
    ) -> StreamingResponse:
        """SSE stream of batch job events (job_state + chapter + terminal).

        Phase 25 enhancements:
        - ``event_types``: comma-separated whitelist, server-side filtered.
        - ``replay=1``: first replay deterministic history from disk (reconnect recovery).
        - ``slug`` / ``mode``: guard params; 403 when the job does not match.
        """
        from infra.studio_batch_runner import (
            _load_job,
            _poll_job,
            dashboard_batch_allowed,
            replay_events,
        )
        from infra.studio_batch_streamer import (
            EVENT_JOB_STATE,
            KNOWN_EVENT_TYPES,
            format_event,
            subscribe,
            unsubscribe,
        )

        job = _load_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"unknown batch job: {job_id!r}")
        job = _poll_job(job)

        # Auth hardening (Phase 25): reads gated by the same flag as writes.
        if not dashboard_batch_allowed():
            raise HTTPException(
                status_code=403,
                detail="batch events disabled; set LINGWEN_ALLOW_DASHBOARD_BATCH=1",
            )

        if slug is not None and job.slug != slug:
            raise HTTPException(
                status_code=403,
                detail=f"batch job {job_id!r} does not belong to project {slug!r}",
            )
        if mode is not None and job.mode != mode:
            raise HTTPException(
                status_code=403,
                detail=(f"batch job {job_id!r} mode {job.mode!r} != requested mode {mode!r}"),
            )

        filter_types: frozenset[str] | None = None
        if event_types:
            parts = [token.strip() for token in event_types.split(",") if token.strip()]
            if not parts:
                raise HTTPException(status_code=400, detail="event_types must not be empty")
            unknown = [token for token in parts if token not in KNOWN_EVENT_TYPES]
            if unknown:
                raise HTTPException(
                    status_code=400,
                    detail=f"unknown event type(s): {', '.join(unknown)}",
                )
            filter_types = frozenset(parts)

        queue = subscribe(job_id, filter_types)
        term_names = ("job_completed", "job_failed", "job_cancelled")
        status_to_event = {
            "completed": "job_completed",
            "failed": "job_failed",
            "cancelled": "job_cancelled",
        }

        def _is_terminal_message(data: bytes) -> bool:
            text = data.decode("utf-8", "replace")
            return any(f"event: {name}" in text for name in term_names)

        def _matches_filter(event_type: str) -> bool:
            return filter_types is None or event_type in filter_types

        # Build the initial event set at connect time, honoring replay + filter.
        if replay:
            initial_events = replay_events(job)
        else:
            initial_events = [(EVENT_JOB_STATE, job.to_dict())]
            terminal_type = status_to_event.get(job.status)
            if terminal_type is not None:
                initial_events.append((terminal_type, job.to_dict()))
        is_terminal = job.status in status_to_event

        async def event_stream():
            try:
                for event_type, payload in initial_events:
                    if not _matches_filter(event_type):
                        continue
                    yield format_event(event_type, payload)
                if is_terminal:
                    # Job already terminal on disk: close after initial events
                    # instead of waiting forever. (Phase 24 behavior preserved.)
                    return
                last_heartbeat = time.time()
                while True:
                    watcher = _load_job(job_id)
                    if watcher is not None:
                        _poll_job(watcher)
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        if time.time() - last_heartbeat >= 15.0:
                            yield b": ping\n\n"
                            last_heartbeat = time.time()
                        continue
                    yield data
                    last_heartbeat = time.time()
                    if _is_terminal_message(data):
                        break
            finally:
                unsubscribe(job_id, queue)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.post(
        "/api/studio/batch/templates",
        response_model=StudioBatchTemplate,
        status_code=201,
    )
    def studio_batch_template_create(
        req: StudioBatchTemplateCreateRequest,
    ) -> StudioBatchTemplate:
        """Create a saved batch-run preset (Track B batch templates)."""
        from infra.studio_batch_streamer import KNOWN_EVENT_TYPES
        from infra.studio_batch_templates import create_batch_template
        from infra.studio_registry import get_project_by_slug

        slug = req.slug or _require_project(ctx).slug
        if get_project_by_slug(slug) is None:
            raise HTTPException(404, f"unknown project slug: {slug!r}")
        _validate_event_types(req.event_types, KNOWN_EVENT_TYPES)
        try:
            template = create_batch_template(
                slug=slug,
                name=req.name,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                budget_usd=req.budget_usd,
                mode=req.mode,
                skip_preflight=req.skip_preflight,
                event_types=req.event_types,
                description=req.description,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return _template_to_response(template)

    @app.get(
        "/api/studio/batch/templates/{template_id}",
        response_model=StudioBatchTemplate,
    )
    def studio_batch_template_get(template_id: str) -> StudioBatchTemplate:
        """Load a single saved batch template by id."""
        from infra.studio_batch_templates import get_batch_template

        payload = get_batch_template(template_id)
        if payload is None:
            raise HTTPException(404, f"unknown batch template: {template_id!r}")
        return StudioBatchTemplate(**payload)

    @app.get(
        "/api/studio/batch/templates",
        response_model=StudioBatchTemplateListResponse,
    )
    def studio_batch_template_list(
        slug: str | None = Query(default=None),
    ) -> StudioBatchTemplateListResponse:
        """List saved batch templates, optionally filtered by project slug."""
        from infra.studio_batch_templates import list_batch_templates

        rows = list_batch_templates(slug=slug)
        return StudioBatchTemplateListResponse(
            templates=[StudioBatchTemplate(**row) for row in rows],
        )

    @app.put(
        "/api/studio/batch/templates/{template_id}",
        response_model=StudioBatchTemplate,
    )
    def studio_batch_template_update(
        template_id: str,
        req: StudioBatchTemplateUpdateRequest,
    ) -> StudioBatchTemplate:
        """Partially update an existing saved batch template."""
        from infra.studio_batch_streamer import KNOWN_EVENT_TYPES
        from infra.studio_batch_templates import update_batch_template

        _validate_event_types(req.event_types, KNOWN_EVENT_TYPES)
        try:
            template = update_batch_template(
                template_id,
                name=req.name,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                budget_usd=req.budget_usd,
                mode=req.mode,
                skip_preflight=req.skip_preflight,
                event_types=req.event_types,
                description=req.description,
            )
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return _template_to_response(template)

    @app.delete(
        "/api/studio/batch/templates/{template_id}",
        response_model=StudioBatchTemplate,
    )
    def studio_batch_template_delete(template_id: str) -> StudioBatchTemplate:
        """Delete a saved batch template by id; returns the deleted template."""
        from infra.studio_batch_templates import delete_batch_template

        try:
            template = delete_batch_template(template_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return _template_to_response(template)
