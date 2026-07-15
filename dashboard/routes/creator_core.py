"""
Phase 15.0 T1.4: creator core routes (smaller /api/creator/* endpoints).

Routes:
- /api/creator/overview, logic-check, agent/plan, agent/plan/stream
- /api/creator/batch-history, batch-history/export
- /api/creator/models, preferences
- /api/creator/memory-assets, memory-assets/{id}/annotation, memory/query
- /api/creator/export/epub, export/docx, publish, publish/platforms, publish/history
- /api/creator/chapters/{n}, chapters/{n}/outline, chapters/{n}
- /api/creator/volume-summary/generate
- /api/creator/volume-plan/diff  (split off from creator_volume because it's small)

Extracted from dashboard/app.py lines 1236-2646 (excluding volume-plan +
templates + merge/split, which live in creator_volume.py).
"""
from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse

from dashboard.models import (
    CreatorAgentPlanRequest,
    CreatorAgentPlanResponse,
    CreatorBatchHistoryExportResponse,
    CreatorBatchHistoryResponse,
    CreatorChapterBodySaveRequest,
    CreatorChapterOutlineSaveRequest,
    CreatorChapterPreviewResponse,
    CreatorDocxExportRequest,
    CreatorEpubExportRequest,
    CreatorLogicCheckResponse,
    CreatorMemoryAnnotationRequest,
    CreatorMemoryAnnotationResponse,
    CreatorMemoryAssetsResponse,
    CreatorMemoryQueryRequest,
    CreatorMemoryQueryResponse,
    CreatorModelsResponse,
    CreatorOverviewResponse,
    CreatorPreferencesResponse,
    CreatorPreferencesSaveRequest,
    CreatorPublishEntry,
    CreatorPublishHistoryResponse,
    CreatorPublishPlatformsResponse,
    CreatorPublishRequest,
    CreatorVolumePlanDiffResponse,
    CreatorVolumePlanSaveRequest,
    CreatorVolumeSummaryGenerateRequest,
    CreatorVolumeSummaryGenerateResponse,
)
from dashboard.routes.ctx import RoutesContext


def _require_project(ctx: RoutesContext):
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        raise HTTPException(404, "no active project")
    return project


def register_creator_core(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/creator/overview", response_model=CreatorOverviewResponse)
    def creator_overview_endpoint() -> CreatorOverviewResponse:
        from infra.creator_dashboard import creator_overview

        project = _require_project(ctx)
        return CreatorOverviewResponse(**creator_overview(project))

    @app.post("/api/creator/logic-check", response_model=CreatorLogicCheckResponse)
    def creator_logic_check_endpoint(chapter: int | None = None) -> CreatorLogicCheckResponse:
        from infra.creator_logic_check import run_creator_logic_check

        project = _require_project(ctx)
        try:
            result = run_creator_logic_check(project.root, chapter_num=chapter)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorLogicCheckResponse(**result)

    @app.post("/api/creator/agent/plan", response_model=CreatorAgentPlanResponse)
    def creator_agent_plan_endpoint(
        body: CreatorAgentPlanRequest,
    ) -> CreatorAgentPlanResponse:
        from infra.creator_agent import run_creator_agent_plan

        project = _require_project(ctx)
        try:
            result = run_creator_agent_plan(
                project.root,
                action=body.action,
                action_label=body.action_label,
                scope=body.scope.model_dump(),
                body_draft=body.body_draft,
                style_strength=body.style_strength,
                allow_worldbuilding_fill=body.allow_worldbuilding_fill,
                goal_tag=body.goal_tag,
                execution_mode=body.execution_mode,
                lens=body.lens,
                provider_mode=body.provider_mode,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorAgentPlanResponse(**result)

    @app.post("/api/creator/agent/plan/stream")
    def creator_agent_plan_stream_endpoint(
        body: CreatorAgentPlanRequest,
    ) -> StreamingResponse:
        from infra.creator_agent import iter_creator_agent_plan_stream

        project = _require_project(ctx)

        def event_stream():
            try:
                for event in iter_creator_agent_plan_stream(
                    project.root,
                    action=body.action,
                    action_label=body.action_label,
                    scope=body.scope.model_dump(),
                    body_draft=body.body_draft,
                    style_strength=body.style_strength,
                    allow_worldbuilding_fill=body.allow_worldbuilding_fill,
                    goal_tag=body.goal_tag,
                    execution_mode=body.execution_mode,
                    lens=body.lens,
                    provider_mode=body.provider_mode,
                ):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except ValueError as exc:
                payload = {"type": "error", "message": str(exc)}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/creator/batch-history", response_model=CreatorBatchHistoryResponse)
    def creator_batch_history_endpoint() -> CreatorBatchHistoryResponse:
        from infra.creator_batch_history import enrich_batch_history_job
        from infra.studio_batch_runner import list_batch_jobs_for_slug

        project = _require_project(ctx)
        jobs = list_batch_jobs_for_slug(project.slug, limit=5)
        return CreatorBatchHistoryResponse(jobs=[enrich_batch_history_job(row) for row in jobs])

    @app.get("/api/creator/batch-history/export", response_model=CreatorBatchHistoryExportResponse)
    def creator_batch_history_export_endpoint() -> CreatorBatchHistoryExportResponse:
        from infra.creator_batch_history import enrich_batch_history_job
        from infra.studio_batch_runner import list_batch_jobs_for_slug

        project = _require_project(ctx)
        jobs = list_batch_jobs_for_slug(project.slug, limit=20)
        enriched = [enrich_batch_history_job(row) for row in jobs]
        return CreatorBatchHistoryExportResponse(count=len(enriched), jobs=enriched)

    @app.post("/api/creator/volume-plan/diff", response_model=CreatorVolumePlanDiffResponse)
    def creator_volume_plan_diff_endpoint(
        body: CreatorVolumePlanSaveRequest,
    ) -> CreatorVolumePlanDiffResponse:
        from infra.creator_volume_plan import volume_plan_diff_payload

        project = _require_project(ctx)
        draft = [v.model_dump() for v in body.volumes]
        result = volume_plan_diff_payload(project.root, draft)
        return CreatorVolumePlanDiffResponse(**result)

    @app.get("/api/creator/models", response_model=CreatorModelsResponse)
    def creator_models_get() -> CreatorModelsResponse:
        from infra.creator_models import list_creator_models_payload

        return CreatorModelsResponse(**list_creator_models_payload())

    @app.get("/api/creator/preferences", response_model=CreatorPreferencesResponse)
    def creator_preferences_get() -> CreatorPreferencesResponse:
        from infra.creator_preferences import creator_preferences_payload

        project = _require_project(ctx)
        return CreatorPreferencesResponse(**creator_preferences_payload(project))

    @app.put("/api/creator/preferences", response_model=CreatorPreferencesResponse)
    def creator_preferences_put(
        req: CreatorPreferencesSaveRequest,
    ) -> CreatorPreferencesResponse:
        from infra.creator_preferences import (
            creator_preferences_payload,
            load_creator_preferences,
            save_creator_preferences,
        )

        project = _require_project(ctx)
        current = load_creator_preferences(project.root)
        patch = req.model_dump(exclude_unset=True)
        if patch.get("task_models") is not None:
            patch["task_models"] = {
                **current.get("task_models", {}),
                **patch["task_models"],
            }
        if patch.get("intervention_rules") is not None:
            patch["intervention_rules"] = {
                **current.get("intervention_rules", {}),
                **patch["intervention_rules"],
            }
        merged = {**current, **patch}
        save_creator_preferences(project.root, merged)
        return CreatorPreferencesResponse(**creator_preferences_payload(project))

    @app.get("/api/creator/memory-assets", response_model=CreatorMemoryAssetsResponse)
    def creator_memory_assets_get() -> CreatorMemoryAssetsResponse:
        from infra.creator_memory_assets import creator_memory_assets_payload

        project = _require_project(ctx)
        return CreatorMemoryAssetsResponse(**creator_memory_assets_payload(project))

    @app.put(
        "/api/creator/memory-assets/{asset_id}/annotation",
        response_model=CreatorMemoryAnnotationResponse,
    )
    def creator_memory_annotation_put(
        asset_id: str,
        req: CreatorMemoryAnnotationRequest,
    ) -> CreatorMemoryAnnotationResponse:
        from infra.creator_memory_annotations import upsert_memory_annotation

        project = _require_project(ctx)
        if req.note is None and req.pinned is None:
            raise HTTPException(400, "note or pinned required")
        try:
            result = upsert_memory_annotation(
                project.root,
                asset_id,
                note=req.note,
                pinned=req.pinned,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMemoryAnnotationResponse(
            asset_id=result["asset_id"],
            note=result.get("note"),
            pinned=bool(result.get("pinned")),
            updated_at=result.get("updated_at"),
        )

    @app.post("/api/creator/memory/query", response_model=CreatorMemoryQueryResponse)
    def creator_memory_query_endpoint(
        req: CreatorMemoryQueryRequest,
    ) -> CreatorMemoryQueryResponse:
        from infra.creator_memory_query import creator_memory_query

        project = _require_project(ctx)
        if not req.query.strip():
            raise HTTPException(400, "query required")
        return CreatorMemoryQueryResponse(
            **creator_memory_query(
                project,
                query=req.query,
                scope=req.scope,
                top_k=req.top_k,
            ),
        )

    @app.post("/api/creator/export/epub")
    def creator_export_epub(req: CreatorEpubExportRequest) -> Response:
        from infra.creator_export_epub import build_creator_epub_bytes

        project = _require_project(ctx)
        mode = req.mode if req.mode in {"full", "range", "submission"} else "full"
        try:
            data = build_creator_epub_bytes(
                project,
                mode=mode,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                title=req.title,
                author=req.author,
                description=req.description,
                submission_sample_count=req.submission_sample_count or 3,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        filename = f"{project.slug}-{mode}.epub"
        return Response(
            content=data,
            media_type="application/epub+zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/api/creator/export/docx")
    def creator_export_docx(req: CreatorDocxExportRequest) -> Response:
        from infra.creator_export_docx import build_creator_docx_bytes

        project = _require_project(ctx)
        mode = req.mode if req.mode in {"full", "range", "submission"} else "full"
        try:
            data = build_creator_docx_bytes(
                project,
                mode=mode,
                start_chapter=req.start_chapter,
                end_chapter=req.end_chapter,
                title=req.title,
                author=req.author,
                description=req.description,
                submission_sample_count=req.submission_sample_count or 3,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        filename = f"{project.slug}-{mode}.docx"
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/api/creator/publish", response_model=CreatorPublishEntry)
    def creator_publish_submit(req: CreatorPublishRequest) -> CreatorPublishEntry:
        from infra.creator_publish import submit_creator_publish

        project = _require_project(ctx)
        entry = submit_creator_publish(
            project,
            platform=req.platform,
            include_outline=req.include_outline,
            intro=req.intro,
            mode=req.mode,
        )
        return CreatorPublishEntry(**entry)

    @app.get("/api/creator/publish/platforms", response_model=CreatorPublishPlatformsResponse)
    def creator_publish_platforms() -> CreatorPublishPlatformsResponse:
        from infra.creator_publish import list_publish_platforms

        project = _require_project(ctx)
        return CreatorPublishPlatformsResponse(
            slug=project.slug,
            platforms=list_publish_platforms(project),
        )

    @app.get("/api/creator/publish/history", response_model=CreatorPublishHistoryResponse)
    def creator_publish_history(
        limit: int = 10,
    ) -> CreatorPublishHistoryResponse:
        from infra.creator_publish import list_creator_publish_history

        project = _require_project(ctx)
        return CreatorPublishHistoryResponse(**list_creator_publish_history(project, limit=limit))

    @app.get(
        "/api/creator/chapters/{chapter_num}",
        response_model=CreatorChapterPreviewResponse,
    )
    def creator_chapter_preview_endpoint(
        chapter_num: int,
        full: bool = False,
    ) -> CreatorChapterPreviewResponse:
        from infra.creator_dashboard import creator_chapter_preview

        project = _require_project(ctx)
        try:
            return CreatorChapterPreviewResponse(
                **creator_chapter_preview(
                    project,
                    chapter_num,
                    include_full_body=full,
                    include_full_outline=full,
                ),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.put(
        "/api/creator/chapters/{chapter_num}/outline",
        response_model=CreatorChapterPreviewResponse,
    )
    def creator_chapter_outline_put(
        chapter_num: int,
        req: CreatorChapterOutlineSaveRequest,
    ) -> CreatorChapterPreviewResponse:
        from infra.creator_dashboard import save_creator_chapter_outline

        project = _require_project(ctx)
        try:
            return CreatorChapterPreviewResponse(
                **save_creator_chapter_outline(project, chapter_num, req.outline),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.put(
        "/api/creator/chapters/{chapter_num}",
        response_model=CreatorChapterPreviewResponse,
    )
    def creator_chapter_body_put(
        chapter_num: int,
        req: CreatorChapterBodySaveRequest,
    ) -> CreatorChapterPreviewResponse:
        from infra.creator_dashboard import save_creator_chapter_body

        project = _require_project(ctx)
        try:
            return CreatorChapterPreviewResponse(
                **save_creator_chapter_body(project, chapter_num, req.body),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post(
        "/api/creator/volume-summary/generate",
        response_model=CreatorVolumeSummaryGenerateResponse,
    )
    def creator_volume_summary_generate(
        req: CreatorVolumeSummaryGenerateRequest,
    ) -> CreatorVolumeSummaryGenerateResponse:
        from infra.creator_volume_summary import write_volume_summary

        project = _require_project(ctx)
        if req.start_chapter < 1 or req.end_chapter < req.start_chapter:
            raise HTTPException(400, "invalid chapter range")
        out = write_volume_summary(
            project.root,
            start_chapter=req.start_chapter,
            end_chapter=req.end_chapter,
        )
        rel = out.relative_to(project.root).as_posix()
        return CreatorVolumeSummaryGenerateResponse(path=rel, written=True)
