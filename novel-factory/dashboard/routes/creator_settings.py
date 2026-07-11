"""
Phase 15.0 T1.4: creator settings / merge-presets routes.

Routes:
- /api/creator/settings-docs (GET, PUT, /preview POST, /three-way-preview POST, /merge-preview POST)
- /api/creator/settings-docs/merge-preferences (GET, /global GET, /export GET, /import POST)
- /api/creator/settings-docs/merge-preferences/preset-packages × list, graph, conflicts,
  conflicts/fixes, conflicts/apply-fix, conflicts/apply-all, toposort, toposort/apply,
  import/preview-diff, factory/conflicts, factory/merge-conflicts, import/preflight,
  export, import, factory, factory/publish, factory/pull/preflight, {id}/changelog,
  {id}/changelog/diff, factory/pull, factory/{id} (delete)
- /api/creator/settings-docs/history (GET)
- /api/creator/settings-docs/restore (POST)

Extracted from dashboard/app.py lines 2857-3487.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from dashboard.models import (
    CreatorMergePreferencesExportResponse,
    CreatorMergePreferencesImportRequest,
    CreatorMergePreferencesImportResponse,
    CreatorMergePreferencesResponse,
    CreatorMergePresetApplyAllFixesResponse,
    CreatorMergePresetChangelogDiffChange,
    CreatorMergePresetChangelogDiffResponse,
    CreatorMergePresetChangelogEntry,
    CreatorMergePresetChangelogResponse,
    CreatorMergePresetConflict,
    CreatorMergePresetConflictFix,
    CreatorMergePresetConflictFixApplyRequest,
    CreatorMergePresetConflictFixApplyResponse,
    CreatorMergePresetConflictFixesResponse,
    CreatorMergePresetConflictsResponse,
    CreatorMergePresetFactoryConflictResolveRequest,
    CreatorMergePresetFactoryConflictResolveResponse,
    CreatorMergePresetFactoryConflictResponse,
    CreatorMergePresetFactoryDeleteResponse,
    CreatorMergePresetFactoryPublishRequest,
    CreatorMergePresetFactoryPublishResponse,
    CreatorMergePresetFactoryPullPreflightResponse,
    CreatorMergePresetFactoryPullRequest,
    CreatorMergePresetFactoryPullResponse,
    CreatorMergePresetGraphEdge,
    CreatorMergePresetGraphNode,
    CreatorMergePresetGraphResponse,
    CreatorMergePresetImportDiffPreviewResponse,
    CreatorMergePresetImportPreflightResponse,
    CreatorMergePresetPackage,
    CreatorMergePresetPackagesExportResponse,
    CreatorMergePresetPackagesImportRequest,
    CreatorMergePresetPackagesImportResponse,
    CreatorMergePresetPackagesResponse,
    CreatorMergePresetToposortApplyResponse,
    CreatorMergePresetToposortResponse,
    CreatorSettingsDiffResponse,
    CreatorSettingsDocsResponse,
    CreatorSettingsDocsSaveRequest,
    CreatorSettingsHistoryResponse,
    CreatorSettingsMergePreviewRequest,
    CreatorSettingsMergePreviewResponse,
    CreatorSettingsRestoreRequest,
    CreatorSettingsThreeWayRequest,
    CreatorSettingsThreeWayResponse,
)
from dashboard.routes.ctx import RoutesContext


def _require_project(ctx: RoutesContext):
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        raise HTTPException(404, "no active project")
    return project


def register_creator_settings(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/creator/settings-docs", response_model=CreatorSettingsDocsResponse)
    def creator_settings_docs_get() -> CreatorSettingsDocsResponse:
        from infra.creator_settings_docs import creator_settings_docs_payload

        project = _require_project(ctx)
        return CreatorSettingsDocsResponse(**creator_settings_docs_payload(project))

    @app.put("/api/creator/settings-docs", response_model=CreatorSettingsDocsResponse)
    def creator_settings_docs_put(
        req: CreatorSettingsDocsSaveRequest,
    ) -> CreatorSettingsDocsResponse:
        from infra.creator_revision import CreatorDocConflictError
        from infra.creator_settings_docs import save_creator_settings_docs

        project = _require_project(ctx)
        if req.pillars_text is None and req.global_outline_text is None:
            raise HTTPException(400, "provide pillars_text and/or global_outline_text")
        try:
            return CreatorSettingsDocsResponse(
                **save_creator_settings_docs(
                    project,
                    pillars_text=req.pillars_text,
                    global_outline_text=req.global_outline_text,
                    expected_pillars_revision=req.expected_pillars_revision,
                    expected_global_outline_revision=req.expected_global_outline_revision,
                    pillars_merge_source=req.pillars_merge_source,
                    global_outline_merge_source=req.global_outline_merge_source,
                    merge_snapshot_id=req.merge_snapshot_id,
                    pillars_merge_snapshot_id=req.pillars_merge_snapshot_id,
                    global_outline_merge_snapshot_id=req.global_outline_merge_snapshot_id,
                ),
            )
        except CreatorDocConflictError as exc:
            raise HTTPException(409, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/creator/settings-docs/preview", response_model=CreatorSettingsDiffResponse)
    def creator_settings_docs_preview(
        req: CreatorSettingsDocsSaveRequest,
    ) -> CreatorSettingsDiffResponse:
        from infra.creator_settings_docs import preview_settings_docs_diff

        project = _require_project(ctx)
        if req.pillars_text is None or req.global_outline_text is None:
            raise HTTPException(400, "provide pillars_text and global_outline_text")
        return CreatorSettingsDiffResponse(
            **preview_settings_docs_diff(
                project,
                pillars_text=req.pillars_text,
                global_outline_text=req.global_outline_text,
            ),
        )

    @app.post(
        "/api/creator/settings-docs/three-way-preview",
        response_model=CreatorSettingsThreeWayResponse,
    )
    def creator_settings_three_way_preview(
        req: CreatorSettingsThreeWayRequest,
    ) -> CreatorSettingsThreeWayResponse:
        from infra.creator_settings_docs import preview_settings_three_way

        project = _require_project(ctx)
        return CreatorSettingsThreeWayResponse(
            **preview_settings_three_way(
                project,
                pillars_text=req.pillars_text,
                global_outline_text=req.global_outline_text,
                snapshot_id=req.snapshot_id,
            ),
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences",
        response_model=CreatorMergePreferencesResponse,
    )
    def creator_settings_merge_preferences_get() -> CreatorMergePreferencesResponse:
        from infra.creator_merge_preferences import load_merge_preferences

        project = _require_project(ctx)
        return CreatorMergePreferencesResponse(**load_merge_preferences(project.root))

    @app.get(
        "/api/creator/settings-docs/merge-preferences/global",
        response_model=CreatorMergePreferencesResponse,
    )
    def creator_settings_merge_preferences_global_get() -> CreatorMergePreferencesResponse:
        from infra.creator_merge_preferences import load_global_merge_preferences

        prefs = load_global_merge_preferences()
        prefs["uses_global_default"] = True
        return CreatorMergePreferencesResponse(**prefs)

    @app.get(
        "/api/creator/settings-docs/merge-preferences/export",
        response_model=CreatorMergePreferencesExportResponse,
    )
    def creator_settings_merge_preferences_export() -> CreatorMergePreferencesExportResponse:
        from infra.creator_merge_preferences import export_merge_preferences

        project = _require_project(ctx)
        data = export_merge_preferences(project.root)
        return CreatorMergePreferencesExportResponse(
            schema_version=data["schema_version"],
            project=data["project"],
            global_prefs=data["global"],
        )

    @app.post(
        "/api/creator/settings-docs/merge-preferences/import",
        response_model=CreatorMergePreferencesImportResponse,
    )
    def creator_settings_merge_preferences_import(
        req: CreatorMergePreferencesImportRequest,
    ) -> CreatorMergePreferencesImportResponse:
        from infra.creator_merge_preferences import import_merge_preferences

        project = _require_project(ctx)
        payload = req.model_dump(by_alias=True, exclude_none=True)
        try:
            result = import_merge_preferences(
                project.root,
                payload,
                scope=req.scope,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePreferencesImportResponse(
            scope=result["scope"],
            project=result.get("project"),
            global_prefs=result.get("global"),
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages",
        response_model=CreatorMergePresetPackagesResponse,
    )
    def creator_settings_merge_preset_packages() -> CreatorMergePresetPackagesResponse:
        from infra.creator_merge_preferences import list_merge_preset_packages

        project = _require_project(ctx)
        packages = list_merge_preset_packages(project.root)
        return CreatorMergePresetPackagesResponse(
            packages=[CreatorMergePresetPackage(**row) for row in packages],
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/graph",
        response_model=CreatorMergePresetGraphResponse,
    )
    def creator_settings_merge_preset_graph() -> CreatorMergePresetGraphResponse:
        from infra.creator_merge_preferences import build_merge_preset_graph

        project = _require_project(ctx)
        graph = build_merge_preset_graph(project.root)
        return CreatorMergePresetGraphResponse(
            node_count=graph["node_count"],
            edge_count=graph["edge_count"],
            nodes=[CreatorMergePresetGraphNode(**row) for row in graph["nodes"]],
            edges=[
                CreatorMergePresetGraphEdge(
                    from_pkg=edge["from"],
                    to=edge["to"],
                    relation=edge.get("relation", "depends_on"),
                )
                for edge in graph["edges"]
            ],
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts",
        response_model=CreatorMergePresetConflictsResponse,
    )
    def creator_settings_merge_preset_conflicts() -> CreatorMergePresetConflictsResponse:
        from infra.creator_merge_preferences import detect_merge_preset_conflicts

        project = _require_project(ctx)
        result = detect_merge_preset_conflicts(project.root)
        return CreatorMergePresetConflictsResponse(
            conflict_count=result["conflict_count"],
            conflicts=[CreatorMergePresetConflict(**row) for row in result["conflicts"]],
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes",
        response_model=CreatorMergePresetConflictFixesResponse,
    )
    def creator_settings_merge_preset_conflict_fixes() -> CreatorMergePresetConflictFixesResponse:
        from infra.creator_merge_preferences import suggest_merge_preset_fixes

        project = _require_project(ctx)
        result = suggest_merge_preset_fixes(project.root)
        return CreatorMergePresetConflictFixesResponse(
            fix_count=result["fix_count"],
            fixes=[CreatorMergePresetConflictFix(**row) for row in result["fixes"]],
        )

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix",
        response_model=CreatorMergePresetConflictFixApplyResponse,
    )
    def creator_settings_merge_preset_conflict_apply_fix(
        req: CreatorMergePresetConflictFixApplyRequest,
    ) -> CreatorMergePresetConflictFixApplyResponse:
        from infra.creator_merge_preferences import apply_merge_preset_fix

        project = _require_project(ctx)
        try:
            result = apply_merge_preset_fix(
                project.root,
                package_id=req.package_id,
                action=req.action,
                dependency_id=req.dependency_id,
                version_label=req.version_label,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetConflictFixApplyResponse(**result)

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all",
        response_model=CreatorMergePresetApplyAllFixesResponse,
    )
    def creator_settings_merge_preset_conflict_apply_all() -> CreatorMergePresetApplyAllFixesResponse:
        from infra.creator_merge_preferences import apply_all_merge_preset_fixes

        project = _require_project(ctx)
        result = apply_all_merge_preset_fixes(project.root)
        return CreatorMergePresetApplyAllFixesResponse(**result)

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/toposort",
        response_model=CreatorMergePresetToposortResponse,
    )
    def creator_settings_merge_preset_toposort() -> CreatorMergePresetToposortResponse:
        from infra.creator_merge_preferences import toposort_merge_preset_packages

        project = _require_project(ctx)
        return CreatorMergePresetToposortResponse(**toposort_merge_preset_packages(project.root))

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/toposort/apply",
        response_model=CreatorMergePresetToposortApplyResponse,
    )
    def creator_settings_merge_preset_toposort_apply() -> CreatorMergePresetToposortApplyResponse:
        from infra.creator_merge_preferences import apply_toposort_merge_preset_order

        project = _require_project(ctx)
        try:
            result = apply_toposort_merge_preset_order(project.root)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetToposortApplyResponse(**result)

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff",
        response_model=CreatorMergePresetImportDiffPreviewResponse,
    )
    def creator_settings_merge_preset_import_preview_diff(
        req: CreatorMergePresetPackagesImportRequest,
    ) -> CreatorMergePresetImportDiffPreviewResponse:
        from infra.creator_merge_preferences import preview_merge_preset_import_diff

        project = _require_project(ctx)
        try:
            result = preview_merge_preset_import_diff(project.root, req.model_dump())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetImportDiffPreviewResponse(**result)

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts",
        response_model=CreatorMergePresetFactoryConflictResponse,
    )
    def creator_settings_merge_preset_factory_conflicts() -> CreatorMergePresetFactoryConflictResponse:
        from infra.creator_merge_preferences import detect_factory_merge_preset_conflicts

        project = _require_project(ctx)
        result = detect_factory_merge_preset_conflicts(project.root)
        return CreatorMergePresetFactoryConflictResponse(**result)

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory/merge-conflicts",
        response_model=CreatorMergePresetFactoryConflictResolveResponse,
    )
    def creator_settings_merge_preset_factory_merge_conflicts(
        req: CreatorMergePresetFactoryConflictResolveRequest,
    ) -> CreatorMergePresetFactoryConflictResolveResponse:
        from infra.creator_merge_preferences import resolve_factory_merge_preset_conflict

        project = _require_project(ctx)
        try:
            result = resolve_factory_merge_preset_conflict(
                project.root,
                package_id=req.package_id,
                strategy=req.strategy,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetFactoryConflictResolveResponse(**result)

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/import/preflight",
        response_model=CreatorMergePresetImportPreflightResponse,
    )
    def creator_settings_merge_preset_import_preflight(
        req: CreatorMergePresetPackagesImportRequest,
    ) -> CreatorMergePresetImportPreflightResponse:
        from infra.creator_merge_preferences import preflight_merge_preset_import

        project = _require_project(ctx)
        try:
            result = preflight_merge_preset_import(project.root, req.model_dump())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetImportPreflightResponse(
            would_import=result["would_import"],
            conflict_count=result["conflict_count"],
            conflicts=[CreatorMergePresetConflict(**row) for row in result["conflicts"]],
            blocked=result["blocked"],
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/export",
        response_model=CreatorMergePresetPackagesExportResponse,
    )
    def creator_settings_merge_preset_packages_export() -> CreatorMergePresetPackagesExportResponse:
        from infra.creator_merge_preferences import export_merge_preset_packages

        project = _require_project(ctx)
        data = export_merge_preset_packages(project.root)
        return CreatorMergePresetPackagesExportResponse(**data)

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/import",
        response_model=CreatorMergePresetPackagesImportResponse,
    )
    def creator_settings_merge_preset_packages_import(
        req: CreatorMergePresetPackagesImportRequest,
    ) -> CreatorMergePresetPackagesImportResponse:
        from infra.creator_merge_preferences import import_merge_preset_packages

        project = _require_project(ctx)
        try:
            result = import_merge_preset_packages(
                project.root,
                req.model_dump(),
                replace=req.replace,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetPackagesImportResponse(
            imported=result["imported"],
            total=result["total"],
            replaced=result["replaced"],
            packages=[CreatorMergePresetPackage(**row) for row in result["packages"]],
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory",
        response_model=CreatorMergePresetPackagesResponse,
    )
    def creator_settings_merge_factory_preset_packages() -> CreatorMergePresetPackagesResponse:
        from infra.creator_merge_preferences import list_factory_merge_preset_packages

        packages = list_factory_merge_preset_packages()
        return CreatorMergePresetPackagesResponse(
            packages=[CreatorMergePresetPackage(**row) for row in packages],
        )

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory/publish",
        response_model=CreatorMergePresetFactoryPublishResponse,
    )
    def creator_settings_merge_factory_preset_publish(
        req: CreatorMergePresetFactoryPublishRequest,
    ) -> CreatorMergePresetFactoryPublishResponse:
        from infra.creator_merge_preferences import publish_merge_preset_to_factory

        project = _require_project(ctx)
        try:
            result = publish_merge_preset_to_factory(project.root, req.package_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetFactoryPublishResponse(
            id=result["id"],
            name=result["name"],
            description=result.get("description", ""),
            scope=result.get("scope", "factory"),
        )

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight",
        response_model=CreatorMergePresetFactoryPullPreflightResponse,
    )
    def creator_settings_merge_factory_preset_pull_preflight(
        req: CreatorMergePresetFactoryPullRequest,
    ) -> CreatorMergePresetFactoryPullPreflightResponse:
        from infra.creator_merge_preferences import preflight_factory_merge_preset_pull

        project = _require_project(ctx)
        try:
            result = preflight_factory_merge_preset_pull(project.root, package_ids=req.package_ids)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetFactoryPullPreflightResponse(**result)

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/{package_id}/changelog",
        response_model=CreatorMergePresetChangelogResponse,
    )
    def creator_settings_merge_preset_changelog(
        package_id: str,
        limit: int = 10,
    ) -> CreatorMergePresetChangelogResponse:
        from infra.creator_merge_preferences import list_merge_preset_changelog

        project = _require_project(ctx)
        try:
            result = list_merge_preset_changelog(project.root, package_id=package_id, limit=limit)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetChangelogResponse(
            package_id=result["package_id"],
            entry_count=result["entry_count"],
            entries=[CreatorMergePresetChangelogEntry(**row) for row in result["entries"]],
        )

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/{package_id}/changelog/diff",
        response_model=CreatorMergePresetChangelogDiffResponse,
    )
    def creator_settings_merge_preset_changelog_diff(
        package_id: str,
        entry_index: int = 0,
    ) -> CreatorMergePresetChangelogDiffResponse:
        from infra.creator_merge_preferences import preview_merge_preset_changelog_diff

        project = _require_project(ctx)
        try:
            result = preview_merge_preset_changelog_diff(
                project.root,
                package_id=package_id,
                entry_index=entry_index,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetChangelogDiffResponse(
            package_id=result["package_id"],
            entry_index=result["entry_index"],
            changed_at=result.get("changed_at"),
            action=result.get("action"),
            change_count=result["change_count"],
            changes=[CreatorMergePresetChangelogDiffChange(**row) for row in result["changes"]],
        )

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory/pull",
        response_model=CreatorMergePresetFactoryPullResponse,
    )
    def creator_settings_merge_factory_preset_pull(
        req: CreatorMergePresetFactoryPullRequest,
    ) -> CreatorMergePresetFactoryPullResponse:
        from infra.creator_merge_preferences import pull_factory_merge_presets_to_project

        project = _require_project(ctx)
        try:
            result = pull_factory_merge_presets_to_project(
                project.root,
                package_ids=req.package_ids,
                conflict_strategies=req.conflict_strategies,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetFactoryPullResponse(
            imported=result["imported"],
            skipped=result.get("skipped", 0),
            total=result["total"],
            package_ids=result["package_ids"],
            skipped_package_ids=result.get("skipped_package_ids", []),
        )

    @app.delete(
        "/api/creator/settings-docs/merge-preferences/preset-packages/factory/{package_id}",
        response_model=CreatorMergePresetFactoryDeleteResponse,
    )
    def creator_settings_merge_factory_preset_delete(
        package_id: str,
    ) -> CreatorMergePresetFactoryDeleteResponse:
        from infra.creator_merge_preferences import delete_factory_merge_preset_package

        try:
            result = delete_factory_merge_preset_package(package_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorMergePresetFactoryDeleteResponse(**result)

    @app.post(
        "/api/creator/settings-docs/merge-preview",
        response_model=CreatorSettingsMergePreviewResponse,
    )
    def creator_settings_merge_preview(
        req: CreatorSettingsMergePreviewRequest,
    ) -> CreatorSettingsMergePreviewResponse:
        from infra.creator_settings_docs import preview_settings_merge_strategy

        project = _require_project(ctx)
        try:
            payload = preview_settings_merge_strategy(
                project,
                pillars_text=req.pillars_text,
                global_outline_text=req.global_outline_text,
                pillars_merge_source=req.pillars_merge_source,
                global_outline_merge_source=req.global_outline_merge_source,
                snapshot_id=req.snapshot_id,
                pillars_merge_snapshot_id=req.pillars_merge_snapshot_id,
                global_outline_merge_snapshot_id=req.global_outline_merge_snapshot_id,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorSettingsMergePreviewResponse(**payload)

    @app.get("/api/creator/settings-docs/history", response_model=CreatorSettingsHistoryResponse)
    def creator_settings_history_get() -> CreatorSettingsHistoryResponse:
        from infra.creator_settings_history import settings_history_payload

        project = _require_project(ctx)
        return CreatorSettingsHistoryResponse(**settings_history_payload(project))

    @app.post("/api/creator/settings-docs/restore", response_model=CreatorSettingsDocsResponse)
    def creator_settings_history_restore(
        req: CreatorSettingsRestoreRequest,
    ) -> CreatorSettingsDocsResponse:
        from infra.creator_settings_history import restore_settings_snapshot

        project = _require_project(ctx)
        try:
            return CreatorSettingsDocsResponse(
                **restore_settings_snapshot(project, req.snapshot_id),
            )
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
