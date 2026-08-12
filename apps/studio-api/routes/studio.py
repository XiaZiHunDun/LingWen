"""
Phase 15.0 T1.4: /api/studio/* routes.

Extracted from dashboard/app.py create_app closure:
- studio_list_projects, studio_get_active, studio_set_active, studio_project_summary (lines 1176-1234)
- studio quality + production endpoints (lines 3488-3676)

Most routes share a pattern: lookup active project, 404 if None, then delegate to
infra.studio_registry / infra.studio_batch_runner. We declare a local helper
to dedupe the project lookup boilerplate.
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from dashboard.models import (
    StudioActiveResponse,
    StudioBatchJobResponse,
    StudioBatchRunRequest,
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
from dashboard.routes.ctx import RoutesContext


def _require_project(ctx: RoutesContext):
    """Look up the active studio project or raise 404. Used by most studio routes."""
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        raise HTTPException(404, "no active studio project")
    return project


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
    def studio_production_run(req: StudioBatchRunRequest) -> StudioBatchJobResponse:
        from infra.studio_batch_runner import (
            BatchAlreadyRunningError,
            BatchNotAllowedError,
            BatchPreflightError,
            start_batch_job,
        )

        project = _require_project(ctx)
        if req.end_chapter < req.start_chapter:
            raise HTTPException(400, "end_chapter must be >= start_chapter")

        try:
            job = start_batch_job(
                project,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                budget_usd=req.budget_usd,
                mode=req.mode,
                skip_preflight=req.skip_preflight,
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
