"""
Phase 15.0 T1.4: /api/cvg/* + /api/ripples/cascade/* + /api/cascade/runs routes.

Also registers the /api/ws/cvg WebSocket endpoint.

Extracted from dashboard/app.py create_app closure (was at app.py lines 444-969).

Note on _default_storage / monkeypatch:
tests monkeypatch `dashboard.app._default_storage` via `monkeypatch.setattr(app_module, "_default_storage", lambda: storage)`.
Because the patch is on the module, this route module must look up `_default_storage`
through the module object (not a captured reference) for the patch to take effect.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from dashboard import app as _app_module  # for monkeypatch-compatible _default_storage lookup
from dashboard.cascade_notifier import notify_cascade_cancel
from dashboard.cvg_ws import EVENT_PONG, CvgConnectionManager
from dashboard.helpers.cvg import (
    _audit_to_response,
    _build_reference_graph_response,
    _edge_to_dict_for_response,
    _node_to_dict_for_response,
    _ripple_list_items,
    _ripple_to_detail,
    _validate_max_depth,
    _validate_max_depth_v9_20,
    _validate_max_nodes_cap,
    cvg_manager,
)
from dashboard.models import (
    CascadeBroadcastLogResponse,
    CascadeCancelPayload,
    CascadeCancelRequest,
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,
    ReferenceGraphResponse,
    RippleActionRequest,
    RippleActionResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleListItemResponse,
    RippleRollbackRequest,
    RippleStatsResponse,
)
from dashboard.routes.ctx import RoutesContext


def register_cvg(app: FastAPI, ctx: RoutesContext) -> None:

    @app.get("/api/cvg/ripples", response_model=list[RippleListItemResponse])
    def list_ripples(
        status_filter: Optional[str] = Query(
            None, alias="status", pattern="^(pending|confirmed|applied|rejected|failed)$"
        ),
        volume: Optional[int] = Query(None, ge=1, le=3),
        sort_by: Optional[str] = Query(
            None,
            pattern="^(created_at|impact_score)$",
            description="Phase 9.59 F50: sort order (default created_at desc via storage)",
        ),
        min_score: Optional[float] = Query(
            None, ge=0.0, description="Phase 9.59 F50: minimum impact_score filter"
        ),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ) -> list[RippleListItemResponse]:
        """Phase 9.13: 列出 ripples (status/volume 过滤 + 分页)。
        Phase 9.59 F50: optional sort_by impact_score + min_score filter.
        """
        storage = _app_module._default_storage()
        ripples = storage.get_ripples(
            status=status_filter, volume=volume, limit=limit, offset=offset
        )
        items = _ripple_list_items(ripples, storage)
        if min_score is not None:
            items = [i for i in items if i.impact_score >= min_score]
        if sort_by == "impact_score":
            items.sort(key=lambda i: i.impact_score, reverse=True)
        return items

    @app.get("/api/cvg/ripples/stats", response_model=RippleStatsResponse)
    def get_ripple_stats() -> RippleStatsResponse:
        """Phase 9.13: ripples 统计 (count by status + by volume)。"""
        storage = _app_module._default_storage()
        all_ripples = storage.get_ripples(limit=200)
        by_status: dict[str, int] = {}
        by_volume: dict[str, int] = {}
        for r in all_ripples:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_volume[str(r.trigger_volume)] = by_volume.get(str(r.trigger_volume), 0) + 1
        return RippleStatsResponse(
            total=len(all_ripples), by_status=by_status, by_volume=by_volume
        )

    @app.get("/api/cvg/reference-graph", response_model=ReferenceGraphResponse)
    def get_reference_graph(
        volume: Optional[int] = Query(None, ge=1, le=99),
        dimension: Optional[str] = Query(
            None,
            pattern="^(character|foreshadow|setting|plot_point)$",
        ),
        limit: int = Query(200, ge=1, le=500),
    ) -> ReferenceGraphResponse:
        """Phase 9.41 F30: persisted reference graph for dashboard ImpactGraph."""
        storage = _app_module._default_storage()
        return _build_reference_graph_response(
            storage,
            volume=volume,
            dimension=dimension,
            limit=limit,
        )

    @app.get("/api/cvg/ripples/{ripple_id}", response_model=RippleDetailResponse)
    def get_ripple_detail(ripple_id: str) -> RippleDetailResponse:
        """Phase 9.13: 单个 ripple 详情。"""
        storage = _app_module._default_storage()
        ripple = storage.get_ripple_by_id(ripple_id)
        if ripple is None:
            raise HTTPException(
                status_code=404, detail=f"ripple {ripple_id} not found"
            )
        return _ripple_to_detail(ripple, storage)

    @app.post("/api/cvg/ripples/{ripple_id}/apply", response_model=RippleActionResponse)
    @ctx.limiter.limit("10/minute")  # Phase 13.0 T2 H4: mutation 限流 10/min
    def apply_ripple(
        request: Request,
        ripple_id: str,
        body: RippleActionRequest | None = None,
    ) -> RippleActionResponse:
        """Phase 9.13: 应用 ripple (PENDING → APPLIED)。
        Phase 9.14: 加 Optional body (RippleActionRequest), 不传 body 仍 work (backward compat)。
        """
        from infra.cross_volume.storage import ConflictError
        storage = _app_module._default_storage()
        actor = body.actor if body and body.actor else "user"
        origin = body.origin if body and body.origin else "ui"
        try:
            ripple = storage.update_ripple_status(
                ripple_id, "applied", actor=actor, origin=origin
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"ripple {ripple_id} not found"
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except ConflictError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return RippleActionResponse(
            ripple_id=ripple_id,
            status="applied",
            actor=actor,
            applied_at=ripple.applied_at,
        )

    @app.post("/api/cvg/ripples/{ripple_id}/reject", response_model=RippleActionResponse)
    def reject_ripple(
        ripple_id: str,
        body: RippleActionRequest | None = None,
    ) -> RippleActionResponse:
        """Phase 9.13: 拒绝 ripple (PENDING → REJECTED)。
        Phase 9.14: 加 Optional body (RippleActionRequest), 不传 body 仍 work (backward compat)。
        """
        from infra.cross_volume.storage import ConflictError
        storage = _app_module._default_storage()
        actor = body.actor if body and body.actor else "user"
        origin = body.origin if body and body.origin else "ui"
        try:
            ripple = storage.update_ripple_status(
                ripple_id, "rejected", actor=actor, origin=origin
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"ripple {ripple_id} not found"
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except ConflictError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return RippleActionResponse(
            ripple_id=ripple_id,
            status="rejected",
            actor=actor,
            applied_at=ripple.applied_at,
        )

    # ==================== Phase 9.14: audit + rollback endpoints ====================

    @app.get(
        "/api/cvg/ripples/{ripple_id}/audit",
        response_model=list[RippleAuditEntryResponse],
    )
    def get_ripple_audit(
        ripple_id: str,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ) -> list[RippleAuditEntryResponse]:
        """Phase 9.14: time-ordered audit history (newest first)."""
        storage = _app_module._default_storage()
        if storage.get_ripple_by_id(ripple_id) is None:
            raise HTTPException(404, f"ripple {ripple_id} not found")
        entries = storage.get_audit_history(ripple_id, limit=limit, offset=offset)
        return [_audit_to_response(e) for e in entries]

    @app.get("/api/cvg/ripples/{ripple_id}/audit/export")
    def export_ripple_audit(
        ripple_id: str,
        export_format: str = Query(
            "json",
            alias="format",
            pattern="^(json|csv)$",
        ),
        limit: int = Query(500, ge=1, le=2000),
        offset: int = Query(0, ge=0),
    ) -> Response:
        """Phase 9.60 F51: export ripple audit log as JSON or CSV."""
        storage = _app_module._default_storage()
        if storage.get_ripple_by_id(ripple_id) is None:
            raise HTTPException(404, f"ripple {ripple_id} not found")
        entries = storage.get_audit_history(ripple_id, limit=limit, offset=offset)
        rows = [_audit_to_response(e).model_dump(mode="json") for e in entries]
        if export_format == "json":
            body = json.dumps(rows, ensure_ascii=False, indent=2)
            return Response(content=body, media_type="application/json")
        output = io.StringIO()
        fieldnames = [
            "id", "ripple_id", "action", "prev_status", "new_status",
            "actor", "origin", "reason", "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return Response(content=output.getvalue(), media_type="text/csv")

    @app.post(
        "/api/cvg/ripples/{ripple_id}/rollback",
        response_model=RippleDetailResponse,
    )
    def rollback_ripple(
        ripple_id: str,
        request: RippleRollbackRequest,
    ) -> RippleDetailResponse:
        """Phase 9.14: reverse an apply/reject (status → pending + audit)."""
        storage = _app_module._default_storage()
        try:
            ripple = storage.rollback_ripple(
                ripple_id,
                actor=request.actor,
                origin=request.origin,
                reason=request.reason,
            )
        except KeyError:
            raise HTTPException(404, f"ripple {ripple_id} not found")
        except ValueError as e:
            raise HTTPException(422, str(e))
        return _ripple_to_detail(ripple, storage)

    # ==================== Phase 9.15: Cascade BFS endpoints (T4) ====================

    @app.get(
        "/api/cvg/ripples/{ripple_id}/cascade",
        response_model=CascadeResponse,
    )
    def get_ripple_cascade(
        ripple_id: str,
        max_depth: int | None = Query(default=None),
        max_nodes_cap: int | None = Query(default=None),
    ) -> CascadeResponse:
        """Phase 9.15: return the persisted cascade BFS result for a single ripple.
        Phase 9.19: optional max_depth query param re-runs BFS live.
        Phase 9.32 F16: optional max_nodes_cap.
        """
        storage = _app_module._default_storage()
        nodes_cap = _validate_max_nodes_cap(max_nodes_cap)
        live_depth = _validate_max_depth(max_depth)
        if live_depth is not None:
            try:
                cascade = storage.preview_cascade(
                    ripple_id, max_depth=live_depth, max_nodes_cap=nodes_cap,
                )
            except ValueError as e:
                raise HTTPException(400, str(e))
        else:
            cascade = storage.get_cascade_by_ripple_id(ripple_id)
            if cascade is None:
                raise HTTPException(404, f"No cascade computed for ripple {ripple_id}")

        cascade_nodes = [
            CascadeNodeResponse(**_node_to_dict_for_response(n))
            for n in cascade.cascade_nodes
        ]
        cascade_edges = [
            CascadeEdgeResponse(**_edge_to_dict_for_response(e))
            for e in cascade.cascade_edges
        ]
        return CascadeResponse(
            trigger_ripple_id=cascade.trigger_ripple_id,
            cascade_nodes=cascade_nodes,
            cascade_edges=cascade_edges,
            cascade_actions=list(cascade.cascade_actions),
            depth_reached=cascade.depth_reached,
            generated_at=cascade.generated_at,
            bfs_algorithm_version=cascade.bfs_algorithm_version,
        )

    @app.get(
        "/api/cvg/ripples/{ripple_id}/cascade/preview",
        response_model=CascadePreviewResponse,
    )
    def get_ripple_cascade_preview(
        ripple_id: str,
        max_depth: int | None = Query(default=None),
        max_nodes_cap: int | None = Query(default=None),
    ) -> CascadePreviewResponse:
        """Phase 9.15: return a dry-run preview summary for the apply confirmation modal.
        Phase 9.19: optional max_depth.
        Phase 9.32 F16: optional max_nodes_cap.
        """
        storage = _app_module._default_storage()
        nodes_cap = _validate_max_nodes_cap(max_nodes_cap)
        live_depth = _validate_max_depth(max_depth)
        if live_depth is not None:
            try:
                cascade = storage.preview_cascade(
                    ripple_id, max_depth=live_depth, max_nodes_cap=nodes_cap,
                )
            except ValueError as e:
                raise HTTPException(400, str(e))
        else:
            cascade = storage.get_cascade_by_ripple_id(ripple_id)
            if cascade is None:
                raise HTTPException(404, f"No cascade computed for ripple {ripple_id}")

        affected_characters = sum(
            1 for n in cascade.cascade_nodes if n.dimension == "character"
        )
        affected_settings = sum(
            1 for n in cascade.cascade_nodes if n.dimension == "setting"
        )
        affected_chapters = sum(
            1 for n in cascade.cascade_nodes
            if n.dimension in ("plot_point", "foreshadow")
        )
        estimated_changes = len(cascade.cascade_actions)
        return CascadePreviewResponse(
            ripple_id=ripple_id,
            affected_chapter_count=affected_chapters,
            affected_character_count=affected_characters,
            affected_setting_count=affected_settings,
            estimated_change_count=estimated_changes,
            cascade_node_count=len(cascade.cascade_nodes),
            cascade_edge_count=len(cascade.cascade_edges),
            max_depth=cascade.depth_reached,
        )

    # ==================== Phase 9.20: Cascade Runs Endpoints (T2) ====================

    @app.get(
        "/api/ripples/cascade/{ripple_id}",
        response_model=None,
    )
    def get_ripple_cascade_v9_20(
        ripple_id: str,
        max_depth: int | None = Query(default=None),
        max_nodes_cap: int | None = Query(default=None),
        persist: bool = Query(default=False),
    ):
        """Phase 9.20: get cascade with optional persist to cascade_runs.

        persist=False (default): return Phase 9.19 CascadeResponse.
        persist=True: live BFS + record + return CascadeRunResponse.
        """
        storage = _app_module._default_storage()
        nodes_cap = _validate_max_nodes_cap(max_nodes_cap)

        if persist:
            validated_depth = _validate_max_depth_v9_20(max_depth)
            try:
                cascaded = storage.preview_cascade(
                    ripple_id, max_depth=validated_depth, max_nodes_cap=nodes_cap,
                )
            except KeyError:
                raise HTTPException(404, f"Ripple {ripple_id} not found")
            except ValueError as e:
                raise HTTPException(400, str(e))
            run_id = storage.record_cascade_run(
                ripple_id, cascaded, max_depth=validated_depth
            )
            run = storage.get_cascade_run_by_id(run_id)
            return CascadeRunResponse.from_dataclass(run).model_dump(mode="json")

        live_depth = _validate_max_depth(max_depth)
        if live_depth is not None:
            try:
                cascade = storage.preview_cascade(
                    ripple_id, max_depth=live_depth, max_nodes_cap=nodes_cap,
                )
            except ValueError as e:
                raise HTTPException(400, str(e))
        else:
            cascade = storage.get_cascade_by_ripple_id(ripple_id)
            if cascade is None:
                raise HTTPException(404, f"No cascade computed for ripple {ripple_id}")
        cascade_nodes = [
            CascadeNodeResponse(**_node_to_dict_for_response(n))
            for n in cascade.cascade_nodes
        ]
        cascade_edges = [
            CascadeEdgeResponse(**_edge_to_dict_for_response(e))
            for e in cascade.cascade_edges
        ]
        return CascadeResponse(
            trigger_ripple_id=cascade.trigger_ripple_id,
            cascade_nodes=cascade_nodes,
            cascade_edges=cascade_edges,
            cascade_actions=list(cascade.cascade_actions),
            depth_reached=cascade.depth_reached,
            generated_at=cascade.generated_at,
            bfs_algorithm_version=cascade.bfs_algorithm_version,
        )

    @app.get(
        "/api/ripples/cascade/{ripple_id}/runs",
        response_model=list[CascadeRunResponse],
    )
    def get_ripple_cascade_runs(
        ripple_id: str,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        status: str | None = Query(default=None, pattern="^(running|completed|cancelled|failed)$"),
        min_depth: int | None = Query(default=None, ge=1, le=10),
        max_depth: int | None = Query(default=None, ge=1, le=10),
        algorithm: str | None = Query(default=None, pattern="^(v1|v2_weighted)$"),
    ) -> list[CascadeRunResponse]:
        """Phase 9.20: list historical cascade runs for a ripple.
        Phase 9.23: 4 filter query params.
        """
        storage = _app_module._default_storage()
        runs = storage.get_cascade_runs(
            ripple_id, limit=limit, offset=offset,
            status=status, min_depth=min_depth, max_depth=max_depth, algorithm=algorithm,
        )
        return [CascadeRunResponse.from_dataclass(r) for r in runs]

    @app.get(
        "/api/cascade/runs",
        response_model=list[CascadeRunResponse],
    )
    def list_all_cascade_runs(
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        status: str | None = Query(default=None, pattern="^(running|completed|cancelled|failed)$"),
        min_depth: int | None = Query(default=None, ge=1, le=10),
        max_depth: int | None = Query(default=None, ge=1, le=10),
        algorithm: str | None = Query(default=None, pattern="^(v1|v2_weighted)$"),
        ripple_id: str | None = Query(default=None, min_length=1),
        since_days: int | None = Query(default=None, ge=1, le=3650),
    ) -> list[CascadeRunResponse]:
        """Phase 9.46 F35: global cascade_runs list across all ripples."""
        storage = _app_module._default_storage()
        runs = storage.list_all_cascade_runs(
            limit=limit,
            offset=offset,
            status=status,
            min_depth=min_depth,
            max_depth=max_depth,
            algorithm=algorithm,
            ripple_id=ripple_id,
            since_days=since_days,
        )
        return [CascadeRunResponse.from_dataclass(r) for r in runs]

    @app.post(
        "/api/ripples/cascade/{ripple_id}/runs/{run_id}/cancel",
        response_model=CascadeRunResponse,
    )
    def post_ripple_cascade_run_cancel(
        ripple_id: str,
        run_id: int,
        body: CascadeCancelRequest = CascadeCancelRequest(),
    ) -> CascadeRunResponse:
        """Phase 9.21: cancel a persisted cascade run.
        Side-effect: WS push 'cascade.cancel' event (best-effort, if flipped).
        """
        storage = _app_module._default_storage()
        try:
            flipped = storage.cancel_cascade_run(run_id, reason=body.reason)
        except KeyError:
            raise HTTPException(404, f"Cascade run {run_id} not found")
        run = storage.get_cascade_run_by_id(run_id)
        if flipped:
            notify_cascade_cancel(CascadeCancelPayload(
                run_id=run_id,
                ripple_id=ripple_id,
                reason=body.reason,
            ))
        return CascadeRunResponse.from_dataclass(run)

    @app.get(
        "/api/ripples/cascade/{ripple_id}/broadcast-log",
        response_model=list[CascadeBroadcastLogResponse],
    )
    def get_ripple_cascade_broadcast_log(
        ripple_id: str,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> list[CascadeBroadcastLogResponse]:
        """Phase 9.44 F33: list persisted cascade WS broadcast latency history."""
        storage = _app_module._default_storage()
        rows = storage.get_cascade_broadcast_logs(
            ripple_id, limit=limit, offset=offset
        )
        return [CascadeBroadcastLogResponse.from_dataclass(r) for r in rows]

    # ==================== Phase 9.13: CVG WebSocket endpoint ====================

    @app.websocket("/api/ws/cvg")
    async def cv_ws_endpoint(websocket: WebSocket):
        """Phase 9.13: CVG WebSocket — broadcasts cascade events for ImpactGraph.vue.
        Phase 9.21: cascade.cancel WS push (notify_cascade_cancel).
        """
        await cvg_manager.connect(websocket)
        try:
            while True:
                msg = await websocket.receive_json()
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": EVENT_PONG})
        except WebSocketDisconnect:
            await cvg_manager.disconnect(websocket)
