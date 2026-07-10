"""
Reading Power Dashboard - FastAPI Backend

This module provides a REST API for the Reading Power Dashboard,
serving hook and coolpoint data + MasterController 决策/工作流 API (Phase 6).

Phase 6 新增:
- /api/decisions/* (pending, all, resolve, defer, cancel)
- /api/workflows/* (list, run, resume, active)
- master_controller kwarg (Protocol 注入,默认 None)
"""

import asyncio
import csv
import io
import json
import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from infra.agent_system.agent_config import load_project_env

load_project_env()

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Phase 13.0 T2 H2: middleware — CORS + GZip + slowapi 限流 (100/min default, 10/min mutation)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from dashboard.cascade_notifier import (
    notify_cascade_cancel,  # Phase 9.21: cascade cancel WS push
    set_main_event_loop,  # Phase 9.66: worker-thread WS schedule
    set_ws_manager,  # Phase 9.16: cascade WS push injector
)
from dashboard.cvg_ws import EVENT_PONG, CvgConnectionManager
from dashboard.protocols import (
    CascadeBroadcastLogResponse,  # Phase 9.44 F33
    CascadeCancelPayload,  # Phase 9.21
    CascadeCancelRequest,  # Phase 9.21
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,
    MasterControllerLike,
    ReferenceGraphResponse,
    RippleActionRequest,
    RippleActionResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleListItemResponse,
    RippleRollbackRequest,
    RippleStatsResponse,
    _extract_cost_by_day,
    _extract_cost_by_day_per_tier,
    _extract_cost_by_scenario,
    _extract_cost_by_tier,
    _extract_total_cost,
)
from dashboard.ws import (
    EVENT_CONNECTED,
    ConnectionManager,
    start_broadcast_task,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.scoring import compute_impact_score
from infra.cross_volume.storage import AuditEntry, ConflictError, RippleStorage

# ==================== Middleware / Rate Limiter ====================
# Phase 13.0 T2 H2: slowapi Limiter singleton (module-level, key=IP, default 100/min)
# Per-endpoint stricter limits applied via @limiter.limit("10/minute") on mutation routes
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# ==================== Pydantic Models (Phase 15.0 T1.1: moved to dashboard/models/) ====================
from dashboard.models import *  # noqa: F401,F403

# ==================== Helpers (Phase 15.0 T1.3: moved to dashboard/helpers/) ====================
# app.py / create_app closure references these helpers — re-export them here
# so the existing top-level call sites (e.g. _default_storage in tests) keep working.
from dashboard.helpers.cvg import (  # noqa: F401
    cvg_manager,
    _ripple_impact_score,
    _ripple_to_list_item,
    _ripple_list_items,
    _ripple_to_detail,
    _audit_to_response,
    _node_to_dict_for_response,
    _edge_to_dict_for_response,
    _build_reference_graph_response,
    _validate_max_depth_v9_20,
    _validate_max_nodes_cap,
)
from dashboard.helpers.decision import _decision_to_response  # noqa: F401
from dashboard.helpers.misc import _maybe_mount_dashboard_ui  # noqa: F401
from dashboard.helpers.reading_power_db import ReadingPowerDB  # noqa: F401
from dashboard.helpers.time_window import _parse_time_window  # noqa: F401
from dashboard.helpers.workflow import (  # noqa: F401
    _list_workflow_yamls,
    _workflow_result_to_response,
)

# Phase 15.0 T1.3: CVG storage singleton stays module-level in dashboard.app so tests
# can monkeypatch app_module._default_storage / _default_storage_instance / _DEFAULT_CVG_DB_PATH
# (reader + globals must be co-located for setattr to take effect).
_DEFAULT_CVG_DB_PATH = Path(__file__).parent.parent / ".state" / "cross_volume.db"
_default_storage_instance: "RippleStorage | None" = None


def _default_storage() -> "RippleStorage":
    """Phase 9.13: singleton RippleStorage for cvg endpoints.

    Lazy init: first call creates RippleStorage, subsequent calls return cached.
    """
    global _default_storage_instance
    if _default_storage_instance is None:
        from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph
        from infra.cross_volume.storage import RippleStorage

        storage = RippleStorage(db_path=_DEFAULT_CVG_DB_PATH)
        if storage._graph is None:
            storage._graph = CrossVolumeReferenceGraph(storage)
        _default_storage_instance = storage
    return _default_storage_instance


def create_app(
    db_path: Optional[Path] = None,
    master_controller: Optional[MasterControllerLike] = None,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        db_path: Optional custom path to reading_power.db
        master_controller: Optional MasterControllerLike 实现 (Phase 6)
            - None: decision/workflow endpoints 返回 503
            - Stub (测试用):满足 Protocol 的轻量对象
            - MasterControllerAdapter(MasterController()): 生产

    Returns:
        Configured FastAPI application instance
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Phase 6.4: 启动/停止 WS broadcast 任务"""
        task: Optional[asyncio.Task] = None
        digest_task: Optional[asyncio.Task] = None
        set_main_event_loop(asyncio.get_running_loop())
        if master_controller is not None:
            task = await start_broadcast_task(manager, master_controller)
        from infra.creator_onboarding_digest_background import start_digest_background_task

        digest_task = start_digest_background_task()
        try:
            yield
        finally:
            if digest_task is not None:
                digest_task.cancel()
                try:
                    await digest_task
                except asyncio.CancelledError:
                    pass
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    # manager 是 closure-scoped,供 lifespan 和 endpoint 共享
    manager = ConnectionManager()
    # Phase 9.16: cascade notifier 注入 ws_manager (service-locator 模式)
    set_ws_manager(manager.broadcast)

    app = FastAPI(
        title="Reading Power Dashboard API",
        description="REST API for the LingWen Reading Power Dashboard",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Phase 13.0 T2 H2/H4 dedupe: slowapi 的 _route_limits 是 module-level global
    # 但 apply_ripple 等 mutation routes 在本函数内部 def → 每次 create_app() 重新装饰 → 累计路由 limit
    # → 一次请求 hit() 多次 → 限流数字错乱。生产环境 create_app 只调一次 (影响 0),测试 / 反复 init 安全。
    limiter._route_limits.clear()
    limiter._Limiter__marked_for_limiting.clear()
    limiter._dynamic_route_limits.clear()

    # Phase 13.0 T2 H2: middleware stack — CORS (本地全开) + GZip ≥1KB + slowapi rate limit
    # add_middleware 是 reverse-stack:LIFO — 越后注册越外层;CORS 最外层 (响应所有 cross-origin)
    # 注: allow_credentials=False (CORS 规范禁 *+credentials);本地 Studio 无 cookie/auth,不需要 credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Use init_if_missing=False to avoid trying to create directories for non-existent paths
    db = ReadingPowerDB(db_path, init_if_missing=False)

    def _production_records_root() -> Path:
        """Env override, then active project pilot_records, else legacy infra/.state."""
        from infra.agent_system.production_records import default_pilot_records_dir
        from infra.studio_registry import active_project, pilot_records_dir_for

        env = os.environ.get("LINGWEN_PILOT_RECORDS_DIR", "").strip()
        if env:
            return Path(env)

        project = active_project()
        if project is not None:
            return pilot_records_dir_for(project)
        return default_pilot_records_dir()

    def _require_controller() -> MasterControllerLike:
        """Require master_controller,否则 503"""
        if master_controller is None:
            raise HTTPException(
                status_code=503,
                detail="master_controller not configured for this dashboard instance",
            )
        return master_controller

    # ==================== Endpoints ====================

    @app.get("/api/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", service="reading-power-dashboard")

    @app.get("/api/overview", response_model=OverviewResponse)
    def get_overview() -> OverviewResponse:
        """Get overview statistics from reading_power.db."""
        if not db.exists():
            return OverviewResponse(
                total_chapters=0,
                total_hooks=0,
                avg_hook_strength=0.0,
                total_coolpoints=0,
                avg_coolpoint_density=0.0,
            )
        if db.is_empty():
            return OverviewResponse(
                total_chapters=0,
                total_hooks=0,
                avg_hook_strength=0.0,
                total_coolpoints=0,
                avg_coolpoint_density=0.0,
            )

        stats = db.get_overview_stats()
        if stats is None:
            return OverviewResponse(
                total_chapters=0,
                total_hooks=0,
                avg_hook_strength=0.0,
                total_coolpoints=0,
                avg_coolpoint_density=0.0,
            )

        return OverviewResponse(
            total_chapters=stats["total_chapters"],
            total_hooks=stats["total_hooks"],
            avg_hook_strength=stats["avg_hook_strength"],
            total_coolpoints=stats["total_coolpoints"],
            avg_coolpoint_density=stats["avg_coolpoint_density"],
        )

    @app.get("/api/chapters", response_model=ChaptersResponse)
    def get_chapters(range: str = "1-30") -> ChaptersResponse:
        """
        Get chapter data for a specified range.

        Args:
            range: Chapter range in format "start-end" (e.g., "1-30")
        """
        try:
            parts = range.split("-")
            if len(parts) != 2:
                raise ValueError("Range must be in format 'start-end'")
            start_chapter = int(parts[0])
            end_chapter = int(parts[1])
            if start_chapter > end_chapter:
                raise ValueError("Start chapter must be <= end chapter")
        except (ValueError, IndexError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid range parameter: {range}. Use format '1-30'. Error: {e}",
            )

        if not db.exists():
            return ChaptersResponse(chapters=[])

        chapters = db.get_chapters_range(start_chapter, end_chapter)
        return ChaptersResponse(
            chapters=[
                ChapterData(
                    chapter=ch["chapter"],
                    hook_count=ch["hook_count"],
                    hook_strength_avg=ch["hook_strength_avg"],
                    coolpoint_count=ch["coolpoint_count"],
                    coolpoint_density=ch["coolpoint_density"],
                )
                for ch in chapters
            ]
        )

    @app.get("/api/production-records", response_model=ProductionRecordsResponse)
    def get_production_records(
        chapter_num: Optional[int] = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
    ) -> ProductionRecordsResponse:
        """Phase 9.82 F74: read pilot/batch JSON from infra/.state/pilot_records."""
        from infra.agent_system.production_records import (
            list_production_records,
        )

        root = _production_records_root()
        items = list_production_records(root, chapter_num=chapter_num, limit=limit)
        return ProductionRecordsResponse(
            records_dir=str(root),
            records=[
                ProductionRecordResponse(**item.to_dict()) for item in items
            ],
        )

    @app.get("/api/production-records/rollup", response_model=ProductionRollupResponse)
    def get_production_records_rollup(
        limit: int = Query(default=100, ge=1, le=200),
    ) -> ProductionRollupResponse:
        """Phase 9.89 F81: deduplicated cost + batch list for Analytics."""
        from infra.agent_system.production_records import (
            rollup_production_records,
        )

        data = rollup_production_records(_production_records_root(), limit=limit)
        return ProductionRollupResponse(
            **{
                **data,
                "batches": [
                    ProductionBatchRollupResponse(**row) for row in data["batches"]
                ],
            }
        )

    @app.get("/api/production-records/trend", response_model=ProductionCostTrendResponse)
    def get_production_records_trend(
        limit: int = Query(default=100, ge=1, le=200),
    ) -> ProductionCostTrendResponse:
        """Phase 9.96 F87: time-ordered cost trend for Analytics mini chart."""
        from infra.agent_system.production_records import (
            production_cost_trend,
        )

        data = production_cost_trend(_production_records_root(), limit=limit)
        return ProductionCostTrendResponse(
            **{
                **data,
                "points": [
                    ProductionCostTrendPointResponse(**row) for row in data["points"]
                ],
            }
        )

    # ==================== Phase 6: Decision Endpoints ====================

    @app.get("/api/decisions/pending", response_model=list[DecisionResponse])
    def get_pending_decisions() -> list[DecisionResponse]:
        """列出 PENDING 决策 (按 priority desc + due_at asc)"""
        ctrl = _require_controller()
        return [_decision_to_response(d) for d in ctrl.list_pending_decisions()]

    @app.get("/api/decisions/all", response_model=list[DecisionResponse])
    def get_all_decisions() -> list[DecisionResponse]:
        """列出全部决策 (含 RESOLVED/DEFERRED/CANCELLED)"""
        ctrl = _require_controller()
        queue = ctrl.get_decision_queue()
        return [_decision_to_response(d) for d in queue.all_decisions()]

    @app.post(
        "/api/decisions/{decision_id}/resolve",
        response_model=DecisionResponse,
    )
    def resolve_decision(decision_id: str, body: ResolveDecisionRequest) -> DecisionResponse:
        """解决决策 (PENDING → RESOLVED)"""
        ctrl = _require_controller()
        try:
            d = ctrl.resolve_decision(
                decision_id, body.option, resolved_by=body.resolved_by
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _decision_to_response(d)

    @app.post(
        "/api/decisions/{decision_id}/defer",
        response_model=DecisionResponse,
    )
    def defer_decision(decision_id: str, body: DeferDecisionRequest) -> DecisionResponse:
        """推迟决策 (PENDING → DEFERRED)"""
        ctrl = _require_controller()
        try:
            d = ctrl.defer_decision(decision_id, reason=body.reason)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _decision_to_response(d)

    @app.post(
        "/api/decisions/{decision_id}/cancel",
        response_model=DecisionResponse,
    )
    def cancel_decision(decision_id: str, body: CancelDecisionRequest) -> DecisionResponse:
        """取消决策 (PENDING → CANCELLED)"""
        ctrl = _require_controller()
        try:
            d = ctrl.cancel_decision(decision_id, reason=body.reason)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _decision_to_response(d)

    # ==================== Phase 9.13: CVG Ripple Endpoints ====================

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
        storage = _default_storage()
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
        storage = _default_storage()
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
        storage = _default_storage()
        return _build_reference_graph_response(
            storage,
            volume=volume,
            dimension=dimension,
            limit=limit,
        )

    @app.get("/api/cvg/ripples/{ripple_id}", response_model=RippleDetailResponse)
    def get_ripple_detail(ripple_id: str) -> RippleDetailResponse:
        """Phase 9.13: 单个 ripple 详情。"""
        storage = _default_storage()
        ripple = storage.get_ripple_by_id(ripple_id)
        if ripple is None:
            raise HTTPException(
                status_code=404, detail=f"ripple {ripple_id} not found"
            )
        return _ripple_to_detail(ripple, storage)

    @app.post("/api/cvg/ripples/{ripple_id}/apply", response_model=RippleActionResponse)
    @limiter.limit("10/minute")  # Phase 13.0 T2 H4: mutation 限流 10/min (slowapi introspects Request)
    def apply_ripple(
        request: Request,  # injected by FastAPI; required for slowapi key_func (IP-based)
        ripple_id: str,
        body: RippleActionRequest | None = None,
    ) -> RippleActionResponse:
        """Phase 9.13: 应用 ripple (PENDING → APPLIED)。
        Phase 9.14: 加 Optional body (RippleActionRequest), 不传 body 仍 work (backward compat)。
        """
        storage = _default_storage()
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
        storage = _default_storage()
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
        storage = _default_storage()
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
        storage = _default_storage()
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
        storage = _default_storage()
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

    def _validate_max_depth(max_depth: int | None) -> int | None:
        """Phase 9.19: validate max_depth. Returns depth int if live BFS needed, None if persisted.

        Raises HTTPException 400 if max_depth is out of range.
        """
        if max_depth is not None and max_depth != 0:
            if max_depth < 0 or max_depth > 10:
                raise HTTPException(400, "max_depth must be 0 (persisted) or 1..10")
            return max_depth
        return None  # use persisted path

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

        Phase 9.19: optional max_depth query param (1..10) re-runs BFS live
        without persisting. max_depth=0 or absent returns persisted cascade
        (backward compat).
        Phase 9.32 F16: optional max_nodes_cap (1..1000, default 100) on live BFS.
        """
        storage = _default_storage()
        nodes_cap = _validate_max_nodes_cap(max_nodes_cap)

        # Phase 9.19: validate max_depth if provided
        live_depth = _validate_max_depth(max_depth)
        if live_depth is not None:
            # Re-run BFS live — returns CascadedRipple (not persisted)
            try:
                cascade = storage.preview_cascade(
                    ripple_id, max_depth=live_depth, max_nodes_cap=nodes_cap,
                )
            except ValueError as e:
                raise HTTPException(400, str(e))
        else:
            # Backward compat: use persisted cascade
            cascade = storage.get_cascade_by_ripple_id(ripple_id)
            if cascade is None:
                raise HTTPException(404, f"No cascade computed for ripple {ripple_id}")

        # ReferenceNode/Edge → dict via helper (Pydantic ignores extras like
        # created_at / created_by / confidence / evidence not in schemas)
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

        Phase 9.19: optional max_depth query param (1..10) re-runs BFS live without
        persisting. max_depth=0 or absent returns persisted cascade (backward compat).
        Phase 9.32 F16: optional max_nodes_cap on live BFS.
        Computes aggregate counts (affected chapters/characters/settings, estimated
        changes) from the BFS result. No LLM calls — pure aggregation.
        """
        storage = _default_storage()
        nodes_cap = _validate_max_nodes_cap(max_nodes_cap)

        # Phase 9.19: validate max_depth if provided
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

        # ReferenceNode.dimension: "character" | "foreshadow" | "setting" | "plot_point"
        # Map to modal chip categories: chapter = plot_point+foreshadow (per-chapter events),
        # character = character, setting = setting.
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
    # Additive: new /api/ripples/cascade/{ripple_id}[/runs] namespace. The existing
    # /api/cvg/ripples/{ripple_id}/cascade endpoint stays Phase 9.19 (0 改) — see
    # the regression test_cascade_endpoints.py suite. persist=false (default) on
    # the new endpoint preserves Phase 9.19 response shape (CascadeResponse with
    # trigger_ripple_id, no 'id' / 'ripple_id' / 'status' keys).

    @app.get(
        "/api/ripples/cascade/{ripple_id}",
        response_model=None,  # branch: CascadeResponse (default) | CascadeRunResponse (persist=true)
    )
    def get_ripple_cascade_v9_20(
        ripple_id: str,
        max_depth: int | None = Query(default=None),
        max_nodes_cap: int | None = Query(default=None),
        persist: bool = Query(default=False),
    ):
        """Phase 9.20: get cascade with optional persist to cascade_runs.

        persist=False (default): return Phase 9.19 CascadeResponse (trigger_ripple_id,
            no 'id' / 'ripple_id' / 'status' keys). Computes live BFS when max_depth
            is provided (1..10), else returns persisted cascade from ripple_cascade.
        persist=True: re-run BFS live, persist run to cascade_runs table, return
            CascadeRunResponse with id/ripple_id/max_depth/depth_reached/algorithm/
            started_at/completed_at/status/cascade_nodes/cascade_edges/cascade_actions.

        Raises:
            404: ripple not found (persist path) or no persisted cascade (default path)
            400: max_depth out of range (persist path requires 1..10; default path
                 accepts 1..10 for live BFS or None/0 for persisted)
        """
        storage = _default_storage()
        nodes_cap = _validate_max_nodes_cap(max_nodes_cap)

        if persist:
            # Phase 9.20: live BFS + record + return CascadeRunResponse.
            # persist path requires explicit max_depth (no persisted-cascade fallback).
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

        # Phase 9.19 path (mirror get_ripple_cascade exactly for backward compat).
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
        """Phase 9.20: list historical cascade runs for a ripple (latest first).
        Phase 9.23: add 4 query params (status, min_depth, max_depth, algorithm).

        limit: max rows (1..200, default 50).
        offset: pagination offset (≥0, default 0).
        status: optional filter ('running'/'completed'/'cancelled'/'failed').
        min_depth: optional min max_depth filter (1..10, inclusive).
        max_depth: optional max max_depth filter (1..10, inclusive).
        algorithm: optional algorithm filter ('v1' or 'v2_weighted').

        Returns:
            list of CascadeRunResponse, ordered by id DESC (newest first).
        """
        storage = _default_storage()
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
        storage = _default_storage()
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

        Body: {"reason": str (optional)}
        Returns: updated CascadeRunResponse (status='cancelled', completed_at = cancel time)
        Raises: 404 if run_id not found
        Side-effect: WS push 'cascade.cancel' event (best-effort, if flipped)
        """
        storage = _default_storage()
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
        storage = _default_storage()
        rows = storage.get_cascade_broadcast_logs(
            ripple_id, limit=limit, offset=offset
        )
        return [CascadeBroadcastLogResponse.from_dataclass(r) for r in rows]

    # ==================== Phase 6: Workflow Endpoints ====================

    @app.get("/api/workflows/list", response_model=list[WorkflowListItem])
    def list_workflows() -> list[WorkflowListItem]:
        """列出 infra/got/workflows/*.yaml"""
        return _list_workflow_yamls()

    @app.post(
        "/api/workflows/run",
        response_model=WorkflowStatusResponse,
    )
    def run_workflow(body: RunWorkflowRequest) -> WorkflowStatusResponse:
        """运行工作流 (Phase 4-5: 会扫描 DECISION 节点暂停)"""
        ctrl = _require_controller()
        try:
            result = ctrl.run_workflow(
                workflow_name=body.workflow_name,
                start_nodes=body.start_nodes,
                initial_inputs=body.initial_inputs,
                max_backtracks=body.max_backtracks,
                base_dir=body.base_dir,
                cost_budget_usd=body.cost_budget_usd,  # Phase 8.8 NEW
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            if "no active workflow" in str(e):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:  # noqa: BLE001
            # WorkflowError / MaxStepsExceeded 等
            err_type = type(e).__name__
            if "WorkflowError" in err_type or "workflow load" in str(e).lower():
                raise HTTPException(status_code=422, detail=f"workflow load failed: {e}")
            if "MaxSteps" in err_type:
                raise HTTPException(status_code=500, detail=f"max steps: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        # Phase 8.7: 修 Phase 8.5 gap — 透传 cost_by_scenario + total_cost_usd
        # Phase 8.13: 增 cost_by_tier 透传 (haiku/sonnet/opus breakdown)
        # getattr 兜底 _controller 字段 (测试 stub 可能没,fallback 用 ctrl 自身)
        inner_ctrl = getattr(ctrl, "_controller", ctrl)
        return _workflow_result_to_response(
            result,
            cost_by_scenario=_extract_cost_by_scenario(inner_ctrl),
            cost_by_tier=_extract_cost_by_tier(inner_ctrl),  # Phase 8.13
            cost_by_day=_extract_cost_by_day(inner_ctrl),  # Phase 8.23
            cost_by_day_per_tier=_extract_cost_by_day_per_tier(inner_ctrl),  # Phase 9.28 F12
            total_cost_usd=_extract_total_cost(inner_ctrl),
        )

    @app.post(
        "/api/workflows/resume",
        response_model=WorkflowStatusResponse,
    )
    def resume_workflow(body: ResumeWorkflowRequest) -> WorkflowStatusResponse:
        """恢复 DECISION 暂停的工作流"""
        ctrl = _require_controller()
        try:
            result = ctrl.resume_workflow(
                body.decision_id, body.option, resolved_by=body.resolved_by
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"decision not found: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            if "no active workflow" in str(e):
                raise HTTPException(status_code=409, detail=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e))
        # Phase 8.7: 修 Phase 8.5 gap — 透传 cost_by_scenario + total_cost_usd
        # Phase 8.13: 增 cost_by_tier 透传
        inner_ctrl = getattr(ctrl, "_controller", ctrl)
        return _workflow_result_to_response(
            result,
            cost_by_scenario=_extract_cost_by_scenario(inner_ctrl),
            cost_by_tier=_extract_cost_by_tier(inner_ctrl),  # Phase 8.13
            cost_by_day=_extract_cost_by_day(inner_ctrl),  # Phase 8.23
            cost_by_day_per_tier=_extract_cost_by_day_per_tier(inner_ctrl),  # Phase 9.28 F12
            total_cost_usd=_extract_total_cost(inner_ctrl),
        )

    @app.get("/api/workflows/active", response_model=WorkflowStatusResponse)
    def get_active_workflow(
        time_window: str = Query("all", description="7d|30d|all (Phase 8.16)"),
    ) -> WorkflowStatusResponse:
        """当前活跃工作流状态 (Phase 5+).
        Phase 8.16: 加 time_window query param (7d|30d|all, default all), 透传 since
        到 3 _extract_cost helper. since=None (all) 走旧 path 保 backward compat.
        Invalid time_window → silent fallback to None (跟 Phase 8.13 silent degrade)."""
        if master_controller is None:
            return WorkflowStatusResponse(is_active=False, workflow_name=None)
        since = _parse_time_window(time_window)
        return WorkflowStatusResponse(
            **master_controller.get_active_workflow_status(since=since)
        )

    # ==================== Phase 8.12 T5: Budget Endpoints ====================

    @app.get("/api/budgets")
    async def get_budgets() -> dict[str, Any]:
        """Phase 8.12 T5: 返 3 档 current budget + status

        Returns:
            dict with keys: per_run, per_day, per_week
            每个 value 是 dict {status, budget_usd, used_usd, used_pct} 或 {} (无 budget)
        """
        from dashboard.protocols import (
            MasterControllerAdapter,
            _extract_budget_per_window,
            _extract_budget_status,
        )
        controller = MasterControllerAdapter._controller
        return {
            "per_run": _extract_budget_status(controller),
            "per_day": _extract_budget_per_window(controller, "day"),
            "per_week": _extract_budget_per_window(controller, "week"),
        }

    @app.put("/api/budgets/{scope}")
    async def set_budget(scope: str, req: BudgetSetRequest) -> dict[str, Any]:
        """Phase 8.12 T5: 设置 day/week budget (per-run 不暴露, run 启动时传)

        Args:
            scope: 'day' or 'week' (其他 scope 返 400)
            req: BudgetSetRequest {usd: float, ge=0 le=10000}

        Returns:
            dict with keys: ok, scope, usd

        Raises:
            400: scope not in ('day', 'week')
            422: usd < 0 or usd > 10000 (Pydantic validation)
            503: budget_service not initialized on controller
        """
        if scope not in ("day", "week"):
            raise HTTPException(400, "scope must be 'day' or 'week'")
        from dashboard.protocols import MasterControllerAdapter
        controller = MasterControllerAdapter._controller
        service = getattr(controller, "budget_service", None)
        if service is None:
            raise HTTPException(503, "budget service not initialized")
        service.set(scope, req.usd, run_id=None)
        return {"ok": True, "scope": scope, "usd": req.usd}

    # ==================== Phase 8.15 T6: Per-Tier Budget Endpoints ====================

    @app.get("/api/budgets/by-tier")
    async def get_budgets_by_tier() -> dict[str, Any]:
        """Phase 8.15 T6: 返 3 tier current budget entries (haiku/sonnet/opus).

        跟 GET /api/budgets 同 pattern, 调 _extract_budget_by_tier helper
        (Phase 8.15 T5 已实现, silent-degrade, 3 tier 永远 present).

        Returns:
            dict with keys: haiku, sonnet, opus (Enum 顺序, deterministic)
            每个 value 是 dict {usd, set_at} 或 None (无 budget set)
        """
        from dashboard.protocols import (
            MasterControllerAdapter,
            _extract_budget_by_tier,
        )
        controller = MasterControllerAdapter._controller
        return _extract_budget_by_tier(controller)

    @app.put("/api/budgets/by-tier/{tier}")
    async def set_budget_by_tier(tier: str, req: BudgetTierSetRequest) -> dict[str, Any]:
        """Phase 8.15 T6: 设置 tier budget (haiku/sonnet/opus 各自).

        跟 PUT /api/budgets/{scope} 同 pattern, 调 BudgetService.set_by_tier
        (Phase 8.15 T2 已实现). tier validation 用 ModelTier enum 防非法输入.

        Args:
            tier: 'haiku' | 'sonnet' | 'opus' (其他返 404)
            req: BudgetTierSetRequest {usd: float, ge=0 le=10000}

        Returns:
            dict with keys: ok, tier, usd

        Raises:
            404: tier not in ('haiku','sonnet','opus') (ModelTier ValueError)
            422: usd < 0 or usd > 10000 (Pydantic validation)
            503: budget_service_by_tier not initialized on controller
        """
        from dashboard.protocols import MasterControllerAdapter
        from infra.ai_service.model_tiers import ModelTier

        try:
            tier_enum = ModelTier(tier)
        except ValueError:
            raise HTTPException(
                404, f"invalid tier: {tier!r}, must be 'haiku'/'sonnet'/'opus'"
            )
        controller = MasterControllerAdapter._controller
        service = getattr(controller, "budget_service_by_tier", None)
        if service is None:
            raise HTTPException(503, "tier budget service not initialized")
        service.set_by_tier(tier_enum, req.usd)
        return {"ok": True, "tier": tier, "usd": req.usd}

    # ==================== Phase 10.04: Studio multi-project ====================

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
        from infra.studio_registry import active_project, project_summary

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
        return StudioSummaryResponse(**project_summary(project))

    @app.get("/api/creator/overview", response_model=CreatorOverviewResponse)
    def creator_overview_endpoint() -> CreatorOverviewResponse:
        from infra.creator_dashboard import creator_overview
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOverviewResponse(**creator_overview(project))

    @app.post("/api/creator/logic-check", response_model=CreatorLogicCheckResponse)
    def creator_logic_check_endpoint(chapter: Optional[int] = None) -> CreatorLogicCheckResponse:
        from infra.creator_logic_check import run_creator_logic_check
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")

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
        from infra.studio_batch_runner import list_batch_jobs_for_slug
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        jobs = list_batch_jobs_for_slug(project.slug, limit=5)
        from infra.creator_batch_history import enrich_batch_history_job

        return CreatorBatchHistoryResponse(jobs=[enrich_batch_history_job(row) for row in jobs])

    @app.get("/api/creator/batch-history/export", response_model=CreatorBatchHistoryExportResponse)
    def creator_batch_history_export_endpoint() -> CreatorBatchHistoryExportResponse:
        from infra.studio_batch_runner import list_batch_jobs_for_slug
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        jobs = list_batch_jobs_for_slug(project.slug, limit=20)
        from infra.creator_batch_history import enrich_batch_history_job

        enriched = [enrich_batch_history_job(row) for row in jobs]
        return CreatorBatchHistoryExportResponse(count=len(enriched), jobs=enriched)

    @app.post("/api/creator/volume-plan/diff", response_model=CreatorVolumePlanDiffResponse)
    def creator_volume_plan_diff_endpoint(
        body: CreatorVolumePlanSaveRequest,
    ) -> CreatorVolumePlanDiffResponse:
        from infra.creator_volume_plan import volume_plan_diff_payload
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        draft = [v.model_dump() for v in body.volumes]
        result = volume_plan_diff_payload(project.root, draft)
        return CreatorVolumePlanDiffResponse(**result)

    @app.get("/api/creator/onboarding", response_model=CreatorOnboardingResponse)
    def creator_onboarding_endpoint() -> CreatorOnboardingResponse:
        from infra.creator_onboarding import onboarding_wizard_payload
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingResponse(**onboarding_wizard_payload(project))

    @app.put("/api/creator/onboarding/progress", response_model=CreatorOnboardingProgressResponse)
    def creator_onboarding_progress_put(
        req: CreatorOnboardingProgressRequest,
    ) -> CreatorOnboardingProgressResponse:
        from infra.creator_onboarding import save_onboarding_progress_from_ui
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = save_onboarding_progress_from_ui(
            project,
            desired_completed_step_ids=req.completed_step_ids,
            step_notes=req.step_notes,
        )
        return CreatorOnboardingProgressResponse(**result)

    @app.put("/api/creator/onboarding/wizard-dismiss", response_model=CreatorOnboardingResponse)
    def creator_onboarding_wizard_dismiss() -> CreatorOnboardingResponse:
        from infra.creator_onboarding import dismiss_onboarding_wizard_panel
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingResponse(**dismiss_onboarding_wizard_panel(project))

    @app.put("/api/creator/onboarding/wizard-collapse", response_model=CreatorOnboardingResponse)
    def creator_onboarding_wizard_collapse(
        req: CreatorWizardPanelCollapsedRequest,
    ) -> CreatorOnboardingResponse:
        from infra.creator_onboarding import save_onboarding_wizard_panel_collapsed
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingResponse(
            **save_onboarding_wizard_panel_collapsed(project, collapsed=req.collapsed),
        )

    @app.put(
        "/api/creator/onboarding/notes",
        response_model=CreatorOnboardingProgressResponse,
    )
    def creator_onboarding_notes_put(
        req: CreatorOnboardingNotesRequest,
    ) -> CreatorOnboardingProgressResponse:
        from infra.creator_onboarding import save_onboarding_notes_from_ui
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = save_onboarding_notes_from_ui(project, step_notes=req.step_notes)
        return CreatorOnboardingProgressResponse(**result)

    @app.get(
        "/api/creator/diff-collab-notes",
        response_model=CreatorDiffCollabNotesResponse,
    )
    def creator_diff_collab_notes_get() -> CreatorDiffCollabNotesResponse:
        from infra.creator_diff_collab import diff_collab_notes_payload
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        payload = diff_collab_notes_payload(project.root)
        return CreatorDiffCollabNotesResponse(**payload)

    @app.put(
        "/api/creator/diff-collab-notes",
        response_model=CreatorDiffCollabNotesResponse,
    )
    def creator_diff_collab_notes_put(
        req: CreatorDiffCollabNotesRequest,
    ) -> CreatorDiffCollabNotesResponse:
        from infra.creator_diff_collab import (
            diff_collab_notes_payload,
            load_diff_collab_notes,
            merge_diff_collab_notes,
            save_diff_collab_notes,
        )
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        merged = merge_diff_collab_notes(load_diff_collab_notes(project.root), req.notes)
        save_diff_collab_notes(project.root, merged)
        return CreatorDiffCollabNotesResponse(**diff_collab_notes_payload(project.root))

    @app.post(
        "/api/creator/onboarding/progress/apply-share",
        response_model=CreatorOnboardingProgressResponse,
    )
    def creator_onboarding_progress_apply_share(
        req: CreatorOnboardingProgressRequest,
    ) -> CreatorOnboardingProgressResponse:
        from infra.creator_onboarding import apply_wizard_share_done
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = apply_wizard_share_done(
            project,
            done_step_ids=req.completed_step_ids,
            step_notes=req.step_notes or {},
        )
        return CreatorOnboardingProgressResponse(**result)

    @app.get(
        "/api/creator/onboarding/notifications",
        response_model=CreatorOnboardingNotificationsResponse,
    )
    def creator_onboarding_notifications_get(
        handle: Optional[str] = None,
    ) -> CreatorOnboardingNotificationsResponse:
        from infra.creator_onboarding_notifications import (
            list_notification_handles,
            list_onboarding_notifications,
        )
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        rows = list_onboarding_notifications(project.root, handle=handle)
        unread = sum(1 for row in rows if not row.get("read"))
        return CreatorOnboardingNotificationsResponse(
            notifications=[CreatorOnboardingNotification(**row) for row in rows],
            unread=unread,
            handles=list_notification_handles(project.root),
        )

    @app.post(
        "/api/creator/onboarding/notifications/ack",
        response_model=CreatorOnboardingNotificationsAckResponse,
    )
    def creator_onboarding_notifications_ack(
        req: CreatorOnboardingNotificationsAckRequest,
    ) -> CreatorOnboardingNotificationsAckResponse:
        from infra.creator_onboarding_notifications import ack_onboarding_notifications
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = ack_onboarding_notifications(
            project.root,
            notification_ids=req.notification_ids,
            all_notifications=req.all_notifications,
            handle=req.handle,
        )
        return CreatorOnboardingNotificationsAckResponse(**result)

    @app.get(
        "/api/creator/onboarding/notifications/digest",
        response_model=CreatorOnboardingNotificationDigestResponse,
    )
    def creator_onboarding_notifications_digest(
        handle: Optional[str] = None,
        unread_only: bool = True,
    ) -> CreatorOnboardingNotificationDigestResponse:
        from infra.creator_onboarding_notifications import build_notification_digest
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        digest = build_notification_digest(
            project.root,
            handle=handle,
            unread_only=unread_only,
        )
        return CreatorOnboardingNotificationDigestResponse(**digest)

    @app.get(
        "/api/creator/onboarding/notifications/digest/schedule",
        response_model=CreatorOnboardingDigestScheduleConfig,
    )
    def creator_onboarding_digest_schedule_get() -> CreatorOnboardingDigestScheduleConfig:
        from infra.creator_onboarding_digest_schedule import load_digest_schedule
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingDigestScheduleConfig(**load_digest_schedule(project.root))

    @app.put(
        "/api/creator/onboarding/notifications/digest/schedule",
        response_model=CreatorOnboardingDigestScheduleConfig,
    )
    def creator_onboarding_digest_schedule_put(
        req: CreatorOnboardingDigestScheduleSaveRequest,
    ) -> CreatorOnboardingDigestScheduleConfig:
        from infra.creator_onboarding_digest_schedule import save_digest_schedule
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        saved = save_digest_schedule(
            project.root,
            enabled=req.enabled,
            interval_hours=req.interval_hours,
            channels=req.channels,
            handle_channels=req.handle_channels,
            quiet_hours_start=req.quiet_hours_start,
            quiet_hours_end=req.quiet_hours_end,
            handle_quiet_hours=req.handle_quiet_hours,
            channel_retry_config=req.channel_retry_config,
        )
        return CreatorOnboardingDigestScheduleConfig(**saved)

    @app.get(
        "/api/creator/onboarding/notifications/digest/dead-letter",
        response_model=CreatorOnboardingDigestDeadLetterResponse,
    )
    def creator_onboarding_digest_dead_letter() -> CreatorOnboardingDigestDeadLetterResponse:
        from infra.creator_onboarding_digest_schedule import load_digest_dead_letter
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        data = load_digest_dead_letter(project.root)
        return CreatorOnboardingDigestDeadLetterResponse(
            item_count=data["item_count"],
            items=[CreatorOnboardingDigestRetryItem(**row) for row in data["items"]],
        )

    @app.post(
        "/api/creator/onboarding/notifications/digest/dead-letter/replay",
        response_model=CreatorOnboardingDigestDeadLetterReplayResponse,
    )
    def creator_onboarding_digest_dead_letter_replay(
        req: CreatorOnboardingDigestDeadLetterReplayRequest,
    ) -> CreatorOnboardingDigestDeadLetterReplayResponse:
        from infra.creator_onboarding_digest_schedule import replay_digest_dead_letter
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        try:
            result = replay_digest_dead_letter(project.root, index=req.index)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorOnboardingDigestDeadLetterReplayResponse(**result)

    @app.get(
        "/api/creator/onboarding/notifications/digest/stats",
        response_model=CreatorOnboardingDigestDispatchStats,
    )
    def creator_onboarding_digest_stats() -> CreatorOnboardingDigestDispatchStats:
        from infra.creator_onboarding_digest_schedule import load_digest_dispatch_stats
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingDigestDispatchStats(**load_digest_dispatch_stats(project.root))

    @app.get(
        "/api/creator/onboarding/notifications/digest/retry-queue",
        response_model=CreatorOnboardingDigestRetryQueueResponse,
    )
    def creator_onboarding_digest_retry_queue() -> CreatorOnboardingDigestRetryQueueResponse:
        from infra.creator_onboarding_digest_schedule import load_digest_retry_queue
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        data = load_digest_retry_queue(project.root)
        return CreatorOnboardingDigestRetryQueueResponse(
            item_count=data["item_count"],
            items=[CreatorOnboardingDigestRetryItem(**row) for row in data["items"]],
        )

    @app.post(
        "/api/creator/onboarding/notifications/digest/retry",
        response_model=CreatorOnboardingDigestRetryProcessResponse,
    )
    def creator_onboarding_digest_retry_process() -> CreatorOnboardingDigestRetryProcessResponse:
        from infra.creator_onboarding_digest_schedule import process_digest_retries
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = process_digest_retries(project.root)
        return CreatorOnboardingDigestRetryProcessResponse(**result)

    @app.post(
        "/api/creator/onboarding/notifications/digest/dispatch",
        response_model=CreatorOnboardingDigestDispatchResponse,
    )
    def creator_onboarding_digest_dispatch(
        force: bool = False,
    ) -> CreatorOnboardingDigestDispatchResponse:
        from infra.creator_onboarding_digest_schedule import dispatch_scheduled_digest
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = dispatch_scheduled_digest(project.root, force=force)
        return CreatorOnboardingDigestDispatchResponse(
            sent=bool(result.get("sent")),
            skipped=bool(result.get("skipped")),
            reason=result.get("reason"),
            last_sent_at=result.get("last_sent_at"),
        )

    @app.get(
        "/api/creator/onboarding/webhook",
        response_model=CreatorOnboardingWebhookConfig,
    )
    def creator_onboarding_webhook_get() -> CreatorOnboardingWebhookConfig:
        from infra.creator_onboarding_webhook import load_webhook_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingWebhookConfig(**load_webhook_config(project.root))

    @app.put(
        "/api/creator/onboarding/webhook",
        response_model=CreatorOnboardingWebhookConfig,
    )
    def creator_onboarding_webhook_put(
        req: CreatorOnboardingWebhookSaveRequest,
    ) -> CreatorOnboardingWebhookConfig:
        from infra.creator_onboarding_webhook import save_webhook_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        try:
            saved = save_webhook_config(
                project.root,
                url=req.url,
                enabled=req.enabled,
                mention_handles=req.mention_handles,
                signing_secret=req.signing_secret,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorOnboardingWebhookConfig(**saved)

    @app.get(
        "/api/creator/onboarding/email",
        response_model=CreatorOnboardingEmailConfig,
    )
    def creator_onboarding_email_get() -> CreatorOnboardingEmailConfig:
        from infra.creator_onboarding_email import load_email_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorOnboardingEmailConfig(**load_email_config(project.root))

    @app.put(
        "/api/creator/onboarding/email",
        response_model=CreatorOnboardingEmailConfig,
    )
    def creator_onboarding_email_put(
        req: CreatorOnboardingEmailSaveRequest,
    ) -> CreatorOnboardingEmailConfig:
        from infra.creator_onboarding_email import save_email_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        try:
            saved = save_email_config(
                project.root,
                enabled=req.enabled,
                to_addresses=req.to_addresses,
                mention_handles=req.mention_handles,
                smtp_host=req.smtp_host,
                smtp_port=req.smtp_port,
                smtp_user=req.smtp_user,
                smtp_password=req.smtp_password,
                smtp_use_tls=req.smtp_use_tls,
                from_address=req.from_address,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return CreatorOnboardingEmailConfig(**saved)

    @app.get("/api/creator/volume-plan", response_model=CreatorVolumePlanResponse)
    def creator_volume_plan_get() -> CreatorVolumePlanResponse:
        from infra.creator_volume_plan import volume_plan_payload
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorVolumePlanResponse(**volume_plan_payload(project.root))

    @app.get(
        "/api/creator/volume-plan/templates",
        response_model=CreatorVolumeTemplateListResponse,
    )
    def creator_volume_plan_templates() -> CreatorVolumeTemplateListResponse:
        from infra.creator_volume_templates import list_volume_templates
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        data = export_template_approval_audit(project.root)
        return CreatorVolumeTemplateApprovalAuditExportResponse(**data)

    @app.get(
        "/api/creator/volume-plan/templates/approvals/sla-config",
        response_model=CreatorVolumeTemplateApprovalSlaConfig,
    )
    def creator_volume_plan_template_approval_sla_get() -> CreatorVolumeTemplateApprovalSlaConfig:
        from infra.creator_template_approvals import load_approval_sla_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorVolumeTemplateApprovalSlaConfig(**load_approval_sla_config(project.root))

    @app.put(
        "/api/creator/volume-plan/templates/approvals/sla-config",
        response_model=CreatorVolumeTemplateApprovalSlaConfig,
    )
    def creator_volume_plan_template_approval_sla_put(
        req: CreatorVolumeTemplateApprovalSlaConfig,
    ) -> CreatorVolumeTemplateApprovalSlaConfig:
        from infra.creator_template_approvals import save_approval_sla_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorVolumeTemplateApprovalChainConfig(**load_approval_chain_config(project.root))

    @app.put(
        "/api/creator/volume-plan/templates/approvals/chain-config",
        response_model=CreatorVolumeTemplateApprovalChainConfig,
    )
    def creator_volume_plan_template_approval_chain_put(
        req: CreatorVolumeTemplateApprovalChainConfig,
    ) -> CreatorVolumeTemplateApprovalChainConfig:
        from infra.creator_template_approvals import save_approval_chain_config
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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

    @app.get(
        "/api/creator/chapters/{chapter_num}",
        response_model=CreatorChapterPreviewResponse,
    )
    def creator_chapter_preview_endpoint(
        chapter_num: int,
        full: bool = False,
    ) -> CreatorChapterPreviewResponse:
        from infra.creator_dashboard import creator_chapter_preview
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        if req.start_chapter < 1 or req.end_chapter < req.start_chapter:
            raise HTTPException(400, "invalid chapter range")
        out = write_volume_summary(
            project.root,
            start_chapter=req.start_chapter,
            end_chapter=req.end_chapter,
        )
        rel = out.relative_to(project.root).as_posix()
        return CreatorVolumeSummaryGenerateResponse(path=rel, written=True)

    @app.get("/api/creator/models", response_model=CreatorModelsResponse)
    def creator_models_get() -> CreatorModelsResponse:
        from infra.creator_models import list_creator_models_payload

        return CreatorModelsResponse(**list_creator_models_payload())

    @app.get("/api/creator/preferences", response_model=CreatorPreferencesResponse)
    def creator_preferences_get() -> CreatorPreferencesResponse:
        from infra.creator_preferences import creator_preferences_payload
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorPublishPlatformsResponse(
            slug=project.slug,
            platforms=list_publish_platforms(project),
        )

    @app.get("/api/creator/publish/history", response_model=CreatorPublishHistoryResponse)
    def creator_publish_history(
        limit: int = Query(10, ge=1, le=30),
    ) -> CreatorPublishHistoryResponse:
        from infra.creator_publish import list_creator_publish_history
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorPublishHistoryResponse(**list_creator_publish_history(project, limit=limit))

    @app.get("/api/creator/settings-docs", response_model=CreatorSettingsDocsResponse)
    def creator_settings_docs_get() -> CreatorSettingsDocsResponse:
        from infra.creator_settings_docs import creator_settings_docs_payload
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorSettingsDocsResponse(**creator_settings_docs_payload(project))

    @app.put("/api/creator/settings-docs", response_model=CreatorSettingsDocsResponse)
    def creator_settings_docs_put(
        req: CreatorSettingsDocsSaveRequest,
    ) -> CreatorSettingsDocsResponse:
        from infra.creator_revision import CreatorDocConflictError
        from infra.creator_settings_docs import save_creator_settings_docs
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        result = apply_all_merge_preset_fixes(project.root)
        return CreatorMergePresetApplyAllFixesResponse(**result)

    @app.get(
        "/api/creator/settings-docs/merge-preferences/preset-packages/toposort",
        response_model=CreatorMergePresetToposortResponse,
    )
    def creator_settings_merge_preset_toposort() -> CreatorMergePresetToposortResponse:
        from infra.creator_merge_preferences import toposort_merge_preset_packages
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorMergePresetToposortResponse(**toposort_merge_preset_packages(project.root))

    @app.post(
        "/api/creator/settings-docs/merge-preferences/preset-packages/toposort/apply",
        response_model=CreatorMergePresetToposortApplyResponse,
    )
    def creator_settings_merge_preset_toposort_apply() -> CreatorMergePresetToposortApplyResponse:
        from infra.creator_merge_preferences import apply_toposort_merge_preset_order
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        return CreatorSettingsHistoryResponse(**settings_history_payload(project))

    @app.post("/api/creator/settings-docs/restore", response_model=CreatorSettingsDocsResponse)
    def creator_settings_history_restore(
        req: CreatorSettingsRestoreRequest,
    ) -> CreatorSettingsDocsResponse:
        from infra.creator_settings_history import restore_settings_snapshot
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        try:
            return CreatorSettingsDocsResponse(
                **restore_settings_snapshot(project, req.snapshot_id),
            )
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/studio/quality", response_model=StudioQualityResponse)
    def studio_quality_dashboard() -> StudioQualityResponse:
        from infra.studio_registry import active_project, quality_summary

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
        return StudioQualityResponse(**quality_summary(project))

    @app.get("/api/studio/quality-report", response_model=StudioQualityReportResponse)
    def studio_quality_report() -> StudioQualityReportResponse:
        from infra.studio_registry import active_project, quality_report_summary

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
        data = quality_report_summary(project)
        return StudioQualityReportResponse(slug=project.slug, **data)

    @app.get("/api/studio/prose-diff", response_model=StudioProseDiffResponse)
    def studio_prose_diff() -> StudioProseDiffResponse:
        from infra.studio_registry import active_project, prose_diff_summary

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
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
        from infra.studio_registry import active_project, prose_judge_summary

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
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
        from infra.studio_registry import (
            active_project,
            batch_command,
            production_preflight,
        )

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
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
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active studio project")
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

    # ==================== Phase 6.4: WebSocket Endpoint ====================

    @app.websocket("/api/ws/workflows")
    async def ws_workflows(ws: WebSocket) -> None:
        """实时推送工作流状态变化

        事件类型:
        - connected (握手):{type, snapshot: <active workflow dict>}
        - workflow.status:{type, payload: <active workflow dict>}
        - decision.snapshot:{type, payload: <pending decisions list>}

        master_controller 缺失时拒绝连接 (close 1011)。
        """
        if master_controller is None:
            await ws.close(code=1011, reason="master_controller not configured")
            return

        await manager.connect(ws)
        try:
            # 握手:推初始 snapshot
            initial_workflow = master_controller.get_active_workflow_status()
            initial_decisions = master_controller.list_pending_decisions()
            await manager.send_to(ws, {
                "type": EVENT_CONNECTED,
                "snapshot": initial_workflow,
                "pending_decisions": initial_decisions,
            })
            # 阻塞等 client 关闭 (server 不主动 send 客户端消息)
            while True:
                try:
                    await ws.receive_text()
                except WebSocketDisconnect:
                    break
        finally:
            await manager.disconnect(ws)

    # ==================== Phase 9.13: CVG WebSocket Endpoint ====================

    @app.websocket("/api/ws/cvg")
    async def ws_cvg(ws: WebSocket) -> None:
        """实时推送 ripple 变化 (跟 /api/ws/workflows 1:1 被动模式).

        事件类型 (Spec 4.2.3):
        - ripple_created: 新 ripple 写入 (Phase 9.11/9.12 CLI trigger)
        - ripple_status_changed: apply/reject 状态变化
        - pong: heartbeat reply (client send ping → server reply pong)
        """
        await cvg_manager.connect(ws)
        try:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "ping":
                    await ws.send_json({"type": EVENT_PONG})
        except WebSocketDisconnect:
            await cvg_manager.disconnect(ws)

    # ==================== Phase 6.3: Mermaid Graph Endpoint ====================

    @app.get(
        "/api/workflows/{workflow_name}/mermaid",
        response_model=WorkflowMermaidResponse,
    )
    def get_workflow_mermaid(
        workflow_name: str,
        include_status: bool = False,
    ) -> WorkflowMermaidResponse:
        """渲染工作流 YAML 为 mermaid 字符串 (供前端 mermaid.js 渲染)

        流程:
        1. load_workflow(name) → ThoughtGraph
        2. 可选:若 include_status=true 且有活跃工作流 → 拿 executions 染色
        3. render_mermaid(graph, executions=...) → mermaid 字符串
        4. 返回 {workflow_name, mermaid, node_count, has_decision_nodes,
                 status_applied, node_statuses}

        Query:
            include_status (bool, default False): true → 叠加当前活跃工作流
                节点状态染色 (Phase 6.6.D,修正 Phase 6.3 染色启用缺失)

        Raises:
            404: workflow YAML 不存在
            422: workflow 解析/验证失败
        """
        from datetime import datetime, timezone

        from infra.got.data_structures import NodeExecution, NodeStatus, NodeType
        from infra.got.visualizer import render_mermaid
        from infra.got.workflow_loader import (
            WorkflowError,
            WorkflowNotFoundError,
            load_workflow,
        )

        try:
            graph = load_workflow(workflow_name)
        except WorkflowNotFoundError:
            raise HTTPException(status_code=404, detail=f"workflow not found: {workflow_name}")
        except WorkflowError as e:
            raise HTTPException(status_code=422, detail=f"workflow load failed: {e}")

        # Phase 6.6.D: 叠加 status 染色 (默认关闭,保后向兼容)
        status_applied = False
        node_statuses: dict[str, str] = {}
        executions: dict[str, NodeExecution] = {}
        if include_status:
            try:
                ctrl = _require_controller()
                active = ctrl.get_active_workflow_status()
                if active.get("is_active"):
                    raw = active.get("executions", {}) or {}
                    for nid, st in raw.items():
                        try:
                            executions[nid] = NodeExecution(
                                node_id=nid,
                                status=NodeStatus(st),
                                started_at=datetime.now(timezone.utc),
                            )
                        except ValueError:
                            # 非法 status 字符串 → 跳过
                            continue
                    node_statuses = dict(raw)
                    status_applied = True
            except Exception:
                # 染色失败 → graceful degradation
                pass

        mermaid_str = render_mermaid(graph, executions=executions, include_classdef=True)
        has_decision = any(
            graph.get_node(nid).type == NodeType.DECISION
            for nid in graph.node_ids()
        )
        return WorkflowMermaidResponse(
            workflow_name=workflow_name,
            mermaid=mermaid_str,
            node_count=len(list(graph.node_ids())),
            has_decision_nodes=has_decision,
            status_applied=status_applied,
            node_statuses=node_statuses,
        )

    _maybe_mount_dashboard_ui(app)
    return app



# ==================== App Instance ====================


# Note: app is created lazily to avoid issues with testing and reimport
# Use create_app() to get the application instance


# ==================== Main Entry Point ====================


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("DASHBOARD_PORT", "8765"))
    dev_mode = os.environ.get("LINGWEN_DASHBOARD_DEV", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if dev_mode:
        from dashboard.e2e_stub_controller import E2EStubController
        from infra.cross_volume.e2e_seed import ensure_e2e_fixtures

        ensure_e2e_fixtures()
        state_dir = Path(__file__).resolve().parent.parent / "infra" / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        app = create_app(master_controller=E2EStubController(state_dir=str(state_dir)))
    else:
        app = create_app()
    uvicorn.run(app, host=host, port=port)
