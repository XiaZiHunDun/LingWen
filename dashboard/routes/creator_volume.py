"""
Phase 15.0 T1.4: creator volume routes.

Routes:
- /api/creator/volume-plan (GET, PUT, merge, split, apply-template)
- /api/creator/volume-plan/templates × save / delete / rename / version / changelog / rollback
- /api/creator/volume-plan/templates/approvals × list / history / audit / sla / chain / batch / transfers / snapshot diff-drift
- /api/creator/volume-plan/templates/export, import, sync-sources, sync, factory × list/publish/pull/delete

Extracted from dashboard/app.py lines 1776-2555.
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException

from dashboard.models import (
    CreatorVolumeApplyTemplateRequest,
    CreatorVolumeApplyTemplateResponse,
    CreatorVolumeDeleteTemplateResponse,
    CreatorVolumeFactoryDeleteResponse,
    CreatorVolumeFactoryPublishRequest,
    CreatorVolumeFactoryPublishResponse,
    CreatorVolumeFactoryPullRequest,
    CreatorVolumeFactoryPullResponse,
    CreatorVolumeMergeRequest,
    CreatorVolumeMergeResponse,
    CreatorVolumePlanEntry,
    CreatorVolumePlanResponse,
    CreatorVolumePlanSaveRequest,
    CreatorVolumeRenameTemplateRequest,
    CreatorVolumeRenameTemplateResponse,
    CreatorVolumeSaveTemplateRequest,
    CreatorVolumeSaveTemplateResponse,
    CreatorVolumeSplitRequest,
    CreatorVolumeSplitResponse,
    CreatorVolumeTemplateApproval,
    CreatorVolumeTemplateApprovalAuditExportResponse,
    CreatorVolumeTemplateApprovalBatchRequest,
    CreatorVolumeTemplateApprovalBatchResponse,
    CreatorVolumeTemplateApprovalBatchResult,
    CreatorVolumeTemplateApprovalChainConfig,
    CreatorVolumeTemplateApprovalDriftResponse,
    CreatorVolumeTemplateApprovalHistoryResponse,
    CreatorVolumeTemplateApprovalListResponse,
    CreatorVolumeTemplateApprovalOverdueResponse,
    CreatorVolumeTemplateApprovalRejectRequest,
    CreatorVolumeTemplateApprovalResolveRequest,
    CreatorVolumeTemplateApprovalSlaConfig,
    CreatorVolumeTemplateApprovalSnapshotDiffResponse,
    CreatorVolumeTemplateApprovalSubmitRequest,
    CreatorVolumeTemplateApprovalTransferRequest,
    CreatorVolumeTemplateChangelogEntry,
    CreatorVolumeTemplateChangelogResponse,
    CreatorVolumeTemplateExportResponse,
    CreatorVolumeTemplateImportRequest,
    CreatorVolumeTemplateImportResponse,
    CreatorVolumeTemplateInfo,
    CreatorVolumeTemplateListResponse,
    CreatorVolumeTemplateRollbackRequest,
    CreatorVolumeTemplateRollbackResponse,
    CreatorVolumeTemplateSyncRequest,
    CreatorVolumeTemplateSyncResponse,
    CreatorVolumeTemplateSyncSource,
    CreatorVolumeTemplateSyncSourcesResponse,
    CreatorVolumeTemplateVersionRequest,
    CreatorVolumeTemplateVersionResponse,
)
from dashboard.routes.ctx import RoutesContext


def _require_project(ctx: RoutesContext):
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        raise HTTPException(404, "no active project")
    return project


def register_creator_volume(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/creator/volume-plan", response_model=CreatorVolumePlanResponse)
    def creator_volume_plan_get() -> CreatorVolumePlanResponse:
        from infra.creator_volume_plan import volume_plan_payload

        project = _require_project(ctx)
        return CreatorVolumePlanResponse(**volume_plan_payload(project.root))

    @app.get(
        "/api/creator/volume-plan/templates",
        response_model=CreatorVolumeTemplateListResponse,
    )
    def creator_volume_plan_templates() -> CreatorVolumeTemplateListResponse:
        from infra.creator_volume_templates import list_volume_templates

        project = _require_project(ctx)
        return CreatorVolumeTemplateListResponse(
            templates=[
                CreatorVolumeTemplateInfo(**row)
                for row in list_volume_templates(project.root)
            ],
        )

    @app.post(
        "/api/creator/volume-plan/templates/save",
        response_model=CreatorVolumeSaveTemplateResponse,
    )
    def creator_volume_plan_save_template(
        req: CreatorVolumeSaveTemplateRequest,
    ) -> CreatorVolumeSaveTemplateResponse:
        from infra.creator_volume_templates import save_custom_volume_template
        from infra.paths import ProjectPaths
        from infra.project_config import ProjectConfig

        project = _require_project(ctx)
        paths = ProjectPaths.get(project.root)
        config = ProjectConfig.load(paths)
        max_chapter = req.max_chapter or config.max_chapter
        try:
            saved = save_custom_volume_template(
                project.root,
                name=req.name,
                volumes=[v.model_dump() for v in req.volumes],
                max_chapter=max_chapter,
                description=req.description,
                version_label=req.version_label,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeSaveTemplateResponse(
            id=saved["id"],
            name=saved["name"],
            description=saved.get("description", ""),
        )

    @app.delete(
        "/api/creator/volume-plan/templates/{template_id}",
        response_model=CreatorVolumeDeleteTemplateResponse,
    )
    def creator_volume_plan_delete_template(
        template_id: str,
    ) -> CreatorVolumeDeleteTemplateResponse:
        from infra.creator_volume_templates import delete_custom_volume_template

        project = _require_project(ctx)
        try:
            result = delete_custom_volume_template(project.root, template_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeDeleteTemplateResponse(**result)

    @app.patch(
        "/api/creator/volume-plan/templates/{template_id}",
        response_model=CreatorVolumeRenameTemplateResponse,
    )
    def creator_volume_plan_rename_template(
        template_id: str,
        req: CreatorVolumeRenameTemplateRequest,
    ) -> CreatorVolumeRenameTemplateResponse:
        from infra.creator_volume_templates import rename_custom_volume_template

        project = _require_project(ctx)
        try:
            result = rename_custom_volume_template(
                project.root,
                template_id,
                name=req.name,
                description=req.description,
                version_label=req.version_label,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeRenameTemplateResponse(**result)

    @app.put(
        "/api/creator/volume-plan/templates/{template_id}/version",
        response_model=CreatorVolumeTemplateVersionResponse,
    )
    def creator_volume_plan_template_version(
        template_id: str,
        req: CreatorVolumeTemplateVersionRequest,
    ) -> CreatorVolumeTemplateVersionResponse:
        from infra.creator_volume_templates import (
            set_custom_template_version_label,
            set_factory_template_version_label,
        )

        project = _require_project(ctx)
        tid = template_id.strip().lower()
        try:
            if tid.startswith("factory_"):
                result = set_factory_template_version_label(
                    tid,
                    version_label=req.version_label,
                )
            else:
                result = set_custom_template_version_label(
                    project.root,
                    tid,
                    version_label=req.version_label,
                )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateVersionResponse(**result)

    @app.get(
        "/api/creator/volume-plan/templates/{template_id}/version-changelog",
        response_model=CreatorVolumeTemplateChangelogResponse,
    )
    def creator_volume_plan_template_changelog(
        template_id: str,
    ) -> CreatorVolumeTemplateChangelogResponse:
        from infra.creator_volume_templates import get_template_version_changelog

        project = _require_project(ctx)
        tid = template_id.strip().lower()
        try:
            entries = get_template_version_changelog(
                project.root if tid.startswith("custom_") else None,
                tid,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateChangelogResponse(
            template_id=tid,
            entries=[CreatorVolumeTemplateChangelogEntry(**row) for row in entries],
        )

    @app.post(
        "/api/creator/volume-plan/templates/{template_id}/version-rollback",
        response_model=CreatorVolumeTemplateRollbackResponse,
    )
    def creator_volume_plan_template_rollback(
        template_id: str,
        req: CreatorVolumeTemplateRollbackRequest,
    ) -> CreatorVolumeTemplateRollbackResponse:
        from infra.creator_volume_templates import rollback_template_version

        project = _require_project(ctx)
        tid = template_id.strip().lower()
        try:
            result = rollback_template_version(
                project.root if tid.startswith("custom_") else None,
                tid,
                version_label=req.version_label,
                changelog_index=req.changelog_index,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateRollbackResponse(
            id=result["id"],
            version_label=result.get("version_label"),
            rolled_back_to=result.get("rolled_back_to"),
        )

    @app.get(
        "/api/creator/volume-plan/templates/approvals",
        response_model=CreatorVolumeTemplateApprovalListResponse,
    )
    def creator_volume_plan_template_approvals_list(
        status: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> CreatorVolumeTemplateApprovalListResponse:
        from infra.creator_template_approvals import list_template_approvals

        project = _require_project(ctx)
        rows = list_template_approvals(
            project.root,
            status=status,
            template_id=template_id,
        )
        return CreatorVolumeTemplateApprovalListResponse(
            approvals=[CreatorVolumeTemplateApproval(**row) for row in rows],
        )

    @app.get(
        "/api/creator/volume-plan/templates/approvals/history",
        response_model=CreatorVolumeTemplateApprovalHistoryResponse,
    )
    def creator_volume_plan_template_approval_history(
        limit: int = 20,
    ) -> CreatorVolumeTemplateApprovalHistoryResponse:
        from infra.creator_template_approvals import list_template_approval_history

        project = _require_project(ctx)
        rows = list_template_approval_history(project.root, limit=max(1, min(limit, 50)))
        return CreatorVolumeTemplateApprovalHistoryResponse(
            approvals=[CreatorVolumeTemplateApproval(**row) for row in rows],
        )

    @app.get(
        "/api/creator/volume-plan/templates/approvals/audit-export",
        response_model=CreatorVolumeTemplateApprovalAuditExportResponse,
    )
    def creator_volume_plan_template_approval_audit_export() -> CreatorVolumeTemplateApprovalAuditExportResponse:
        from infra.creator_template_approvals import export_template_approval_audit

        project = _require_project(ctx)
        data = export_template_approval_audit(project.root)
        return CreatorVolumeTemplateApprovalAuditExportResponse(**data)

    @app.get(
        "/api/creator/volume-plan/templates/approvals/sla-config",
        response_model=CreatorVolumeTemplateApprovalSlaConfig,
    )
    def creator_volume_plan_template_approval_sla_get() -> CreatorVolumeTemplateApprovalSlaConfig:
        from infra.creator_template_approvals import load_approval_sla_config

        project = _require_project(ctx)
        return CreatorVolumeTemplateApprovalSlaConfig(**load_approval_sla_config(project.root))

    @app.put(
        "/api/creator/volume-plan/templates/approvals/sla-config",
        response_model=CreatorVolumeTemplateApprovalSlaConfig,
    )
    def creator_volume_plan_template_approval_sla_put(
        req: CreatorVolumeTemplateApprovalSlaConfig,
    ) -> CreatorVolumeTemplateApprovalSlaConfig:
        from infra.creator_template_approvals import save_approval_sla_config

        project = _require_project(ctx)
        saved = save_approval_sla_config(
            project.root,
            timeout_hours=req.timeout_hours,
            email_on_submit=req.email_on_submit,
            email_on_reject=req.email_on_reject,
            email_on_overdue=req.email_on_overdue,
        )
        return CreatorVolumeTemplateApprovalSlaConfig(**saved)

    @app.get(
        "/api/creator/volume-plan/templates/approvals/overdue",
        response_model=CreatorVolumeTemplateApprovalOverdueResponse,
    )
    def creator_volume_plan_template_approval_overdue() -> CreatorVolumeTemplateApprovalOverdueResponse:
        from infra.creator_template_approvals import list_overdue_template_approvals

        project = _require_project(ctx)
        rows = list_overdue_template_approvals(project.root)
        return CreatorVolumeTemplateApprovalOverdueResponse(
            overdue_count=len(rows),
            approvals=[CreatorVolumeTemplateApproval(**row) for row in rows],
        )

    @app.get(
        "/api/creator/volume-plan/templates/approvals/chain-config",
        response_model=CreatorVolumeTemplateApprovalChainConfig,
    )
    def creator_volume_plan_template_approval_chain_get() -> CreatorVolumeTemplateApprovalChainConfig:
        from infra.creator_template_approvals import load_approval_chain_config

        project = _require_project(ctx)
        return CreatorVolumeTemplateApprovalChainConfig(**load_approval_chain_config(project.root))

    @app.put(
        "/api/creator/volume-plan/templates/approvals/chain-config",
        response_model=CreatorVolumeTemplateApprovalChainConfig,
    )
    def creator_volume_plan_template_approval_chain_put(
        req: CreatorVolumeTemplateApprovalChainConfig,
    ) -> CreatorVolumeTemplateApprovalChainConfig:
        from infra.creator_template_approvals import save_approval_chain_config

        project = _require_project(ctx)
        saved = save_approval_chain_config(
            project.root,
            required_steps=req.required_steps,
            step_assignees=req.step_assignees,
            step_assignee_groups=req.step_assignee_groups,
        )
        return CreatorVolumeTemplateApprovalChainConfig(**saved)

    @app.post(
        "/api/creator/volume-plan/templates/{template_id}/version-approval",
        response_model=CreatorVolumeTemplateApproval,
    )
    def creator_volume_plan_template_approval_submit(
        template_id: str,
        req: CreatorVolumeTemplateApprovalSubmitRequest,
    ) -> CreatorVolumeTemplateApproval:
        from infra.creator_template_approvals import submit_template_version_approval

        project = _require_project(ctx)
        try:
            row = submit_template_version_approval(
                project.root,
                template_id,
                version_label=req.version_label,
                submit_note=req.submit_note,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateApproval(**row)

    @app.post(
        "/api/creator/volume-plan/templates/approvals/{approval_id}/approve",
        response_model=CreatorVolumeTemplateApproval,
    )
    def creator_volume_plan_template_approval_approve(
        approval_id: str,
        req: CreatorVolumeTemplateApprovalResolveRequest | None = None,
    ) -> CreatorVolumeTemplateApproval:
        from infra.creator_template_approvals import approve_template_approval

        project = _require_project(ctx)
        body = req or CreatorVolumeTemplateApprovalResolveRequest()
        try:
            row = approve_template_approval(
                project.root,
                approval_id,
                assignee=body.assignee,
                resolve_note=body.resolve_note,
                force=body.force,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateApproval(**{k: v for k, v in row.items() if k != "applied"})

    @app.post(
        "/api/creator/volume-plan/templates/approvals/{approval_id}/reject",
        response_model=CreatorVolumeTemplateApproval,
    )
    def creator_volume_plan_template_approval_reject(
        approval_id: str,
        req: CreatorVolumeTemplateApprovalRejectRequest,
    ) -> CreatorVolumeTemplateApproval:
        from infra.creator_template_approvals import reject_template_approval

        project = _require_project(ctx)
        try:
            row = reject_template_approval(
                project.root,
                approval_id,
                reason=req.reason,
                resolve_note=req.resolve_note,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateApproval(**row)

    @app.post(
        "/api/creator/volume-plan/templates/approvals/{approval_id}/transfer",
        response_model=CreatorVolumeTemplateApproval,
    )
    def creator_volume_plan_template_approval_transfer(
        approval_id: str,
        req: CreatorVolumeTemplateApprovalTransferRequest,
    ) -> CreatorVolumeTemplateApproval:
        from infra.creator_template_approvals import transfer_template_approval

        project = _require_project(ctx)
        try:
            row = transfer_template_approval(
                project.root,
                approval_id,
                to_assignee=req.to_assignee,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateApproval(**row)

    @app.get(
        "/api/creator/volume-plan/templates/approvals/{approval_id}/snapshot-diff",
        response_model=CreatorVolumeTemplateApprovalSnapshotDiffResponse,
    )
    def creator_volume_plan_template_approval_snapshot_diff(
        approval_id: str,
    ) -> CreatorVolumeTemplateApprovalSnapshotDiffResponse:
        from infra.creator_template_approvals import preview_template_approval_snapshot_diff

        project = _require_project(ctx)
        try:
            result = preview_template_approval_snapshot_diff(project.root, approval_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateApprovalSnapshotDiffResponse(**result)

    @app.get(
        "/api/creator/volume-plan/templates/approvals/{approval_id}/snapshot-drift",
        response_model=CreatorVolumeTemplateApprovalDriftResponse,
    )
    def creator_volume_plan_template_approval_snapshot_drift(
        approval_id: str,
    ) -> CreatorVolumeTemplateApprovalDriftResponse:
        from infra.creator_template_approvals import check_approval_snapshot_drift

        project = _require_project(ctx)
        try:
            result = check_approval_snapshot_drift(project.root, approval_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateApprovalDriftResponse(**result)

    @app.post(
        "/api/creator/volume-plan/templates/approvals/batch-approve",
        response_model=CreatorVolumeTemplateApprovalBatchResponse,
    )
    def creator_volume_plan_template_approval_batch_approve(
        req: CreatorVolumeTemplateApprovalBatchRequest,
    ) -> CreatorVolumeTemplateApprovalBatchResponse:
        from infra.creator_template_approvals import batch_approve_template_approvals

        project = _require_project(ctx)
        result = batch_approve_template_approvals(
            project.root,
            req.approval_ids,
            assignee=req.assignee,
            resolve_note=req.resolve_note,
            force=req.force,
        )
        return CreatorVolumeTemplateApprovalBatchResponse(
            approved=result["approved"],
            rejected=0,
            total=result["total"],
            results=[CreatorVolumeTemplateApprovalBatchResult(**row) for row in result["results"]],
        )

    @app.post(
        "/api/creator/volume-plan/templates/approvals/batch-reject",
        response_model=CreatorVolumeTemplateApprovalBatchResponse,
    )
    def creator_volume_plan_template_approval_batch_reject(
        req: CreatorVolumeTemplateApprovalBatchRequest,
    ) -> CreatorVolumeTemplateApprovalBatchResponse:
        from infra.creator_template_approvals import batch_reject_template_approvals

        project = _require_project(ctx)
        result = batch_reject_template_approvals(
            project.root,
            req.approval_ids,
            reason=req.reason,
            resolve_note=req.resolve_note,
        )
        return CreatorVolumeTemplateApprovalBatchResponse(
            approved=0,
            rejected=result["rejected"],
            total=result["total"],
            results=[CreatorVolumeTemplateApprovalBatchResult(**row) for row in result["results"]],
        )

    @app.get(
        "/api/creator/volume-plan/templates/export",
        response_model=CreatorVolumeTemplateExportResponse,
    )
    def creator_volume_plan_export_templates() -> CreatorVolumeTemplateExportResponse:
        from infra.creator_volume_templates import export_custom_volume_templates

        project = _require_project(ctx)
        return CreatorVolumeTemplateExportResponse(
            **export_custom_volume_templates(project.root),
        )

    @app.post(
        "/api/creator/volume-plan/templates/import",
        response_model=CreatorVolumeTemplateImportResponse,
    )
    def creator_volume_plan_import_templates(
        req: CreatorVolumeTemplateImportRequest,
    ) -> CreatorVolumeTemplateImportResponse:
        from infra.creator_volume_templates import import_custom_volume_templates

        project = _require_project(ctx)
        try:
            result = import_custom_volume_templates(
                project.root,
                {"templates": req.templates},
                replace=req.replace,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateImportResponse(**result)

    @app.get(
        "/api/creator/volume-plan/templates/sync-sources",
        response_model=CreatorVolumeTemplateSyncSourcesResponse,
    )
    def creator_volume_plan_template_sync_sources() -> CreatorVolumeTemplateSyncSourcesResponse:
        from infra.creator_volume_templates import list_template_sync_sources

        project = _require_project(ctx)
        return CreatorVolumeTemplateSyncSourcesResponse(
            sources=[
                CreatorVolumeTemplateSyncSource(**row)
                for row in list_template_sync_sources(exclude_slug=project.slug)
            ],
        )

    @app.post(
        "/api/creator/volume-plan/templates/sync",
        response_model=CreatorVolumeTemplateSyncResponse,
    )
    def creator_volume_plan_template_sync(
        req: CreatorVolumeTemplateSyncRequest,
    ) -> CreatorVolumeTemplateSyncResponse:
        from infra.creator_volume_templates import sync_custom_volume_templates_from_projects

        project = _require_project(ctx)
        try:
            result = sync_custom_volume_templates_from_projects(
                project.root,
                source_slugs=req.source_slugs,
                exclude_slug=project.slug,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeTemplateSyncResponse(**result)

    @app.get(
        "/api/creator/volume-plan/templates/factory",
        response_model=CreatorVolumeTemplateListResponse,
    )
    def creator_volume_plan_factory_templates() -> CreatorVolumeTemplateListResponse:
        from infra.creator_volume_templates import list_factory_volume_templates

        return CreatorVolumeTemplateListResponse(
            templates=[
                CreatorVolumeTemplateInfo(**row)
                for row in list_factory_volume_templates()
            ],
        )

    @app.post(
        "/api/creator/volume-plan/templates/factory/publish",
        response_model=CreatorVolumeFactoryPublishResponse,
    )
    def creator_volume_plan_factory_publish(
        req: CreatorVolumeFactoryPublishRequest,
    ) -> CreatorVolumeFactoryPublishResponse:
        from infra.creator_volume_templates import publish_custom_to_factory_library

        project = _require_project(ctx)
        try:
            result = publish_custom_to_factory_library(project.root, req.template_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeFactoryPublishResponse(**result)

    @app.post(
        "/api/creator/volume-plan/templates/factory/pull",
        response_model=CreatorVolumeFactoryPullResponse,
    )
    def creator_volume_plan_factory_pull(
        req: CreatorVolumeFactoryPullRequest,
    ) -> CreatorVolumeFactoryPullResponse:
        from infra.creator_volume_templates import pull_factory_templates_to_project

        project = _require_project(ctx)
        try:
            result = pull_factory_templates_to_project(
                project.root,
                template_ids=req.template_ids,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeFactoryPullResponse(**result)

    @app.delete(
        "/api/creator/volume-plan/templates/factory/{template_id}",
        response_model=CreatorVolumeFactoryDeleteResponse,
    )
    def creator_volume_plan_factory_delete(
        template_id: str,
    ) -> CreatorVolumeFactoryDeleteResponse:
        from infra.creator_volume_templates import delete_factory_volume_template

        try:
            result = delete_factory_volume_template(template_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorVolumeFactoryDeleteResponse(**result)

    @app.post(
        "/api/creator/volume-plan/apply-template",
        response_model=CreatorVolumeApplyTemplateResponse,
    )
    def creator_volume_plan_apply_template(
        req: CreatorVolumeApplyTemplateRequest,
    ) -> CreatorVolumeApplyTemplateResponse:
        from infra.creator_volume_templates import build_volume_template, template_meta
        from infra.paths import ProjectPaths
        from infra.project_config import ProjectConfig

        project = _require_project(ctx)
        paths = ProjectPaths.get(project.root)
        config = ProjectConfig.load(paths)
        max_chapter = req.max_chapter or config.max_chapter
        try:
            built = build_volume_template(req.template_id, max_chapter, project.root)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        tid = req.template_id.strip().lower()
        meta = template_meta(tid, project.root)
        return CreatorVolumeApplyTemplateResponse(
            template_id=tid,
            template_name=meta["name"],
            volumes=[CreatorVolumePlanEntry(**row) for row in built],
        )

    @app.put("/api/creator/volume-plan", response_model=CreatorVolumePlanResponse)
    def creator_volume_plan_put(req: CreatorVolumePlanSaveRequest) -> CreatorVolumePlanResponse:
        from infra.creator_revision import CreatorDocConflictError
        from infra.creator_volume_plan import save_volume_plan, volume_plan_payload

        project = _require_project(ctx)
        try:
            save_volume_plan(
                project.root,
                [v.model_dump() for v in req.volumes],
                expected_revision=req.expected_revision,
            )
        except CreatorDocConflictError as exc:
            raise HTTPException(409, str(exc)) from exc
        return CreatorVolumePlanResponse(**volume_plan_payload(project.root))

    @app.post("/api/creator/volume-plan/merge", response_model=CreatorVolumeMergeResponse)
    def creator_volume_plan_merge(req: CreatorVolumeMergeRequest) -> CreatorVolumeMergeResponse:
        from infra.creator_volume_plan import merge_volume_range

        try:
            merged_volumes, merged = merge_volume_range(
                [v.model_dump() for v in req.volumes],
                req.start_index,
                req.end_index,
                label=req.label,
                core_conflict=req.core_conflict,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        start = merged.start_chapter
        end = merged.end_chapter
        merged_range = f"ch{start:03d}–ch{end:03d}" if start != end else f"ch{start:03d}"
        return CreatorVolumeMergeResponse(
            volumes=[CreatorVolumePlanEntry(**v.to_dict()) for v in merged_volumes],
            merged_label=merged.label,
            merged_range=merged_range,
        )

    @app.post("/api/creator/volume-plan/split", response_model=CreatorVolumeSplitResponse)
    def creator_volume_plan_split(req: CreatorVolumeSplitRequest) -> CreatorVolumeSplitResponse:
        from infra.creator_volume_plan import split_volume

        try:
            split_volumes, first, second = split_volume(
                [v.model_dump() for v in req.volumes],
                req.volume_index,
                req.split_at_chapter,
                first_label=req.first_label,
                second_label=req.second_label,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        def _range(vol) -> str:
            if vol.start_chapter == vol.end_chapter:
                return f"ch{vol.start_chapter:03d}"
            return f"ch{vol.start_chapter:03d}–ch{vol.end_chapter:03d}"

        return CreatorVolumeSplitResponse(
            volumes=[CreatorVolumePlanEntry(**v.to_dict()) for v in split_volumes],
            first_label=first.label,
            second_label=second.label,
            first_range=_range(first),
            second_range=_range(second),
        )
