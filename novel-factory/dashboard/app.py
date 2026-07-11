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
# ==================== Helpers (Phase 15.0 T1.3: moved to dashboard/helpers/) ====================
# app.py / create_app closure references these helpers — re-export them here
# so the existing top-level call sites (e.g. _default_storage in tests) keep working.
from dashboard.helpers.cvg import (  # noqa: F401
    _audit_to_response,
    _build_reference_graph_response,
    _edge_to_dict_for_response,
    _node_to_dict_for_response,
    _ripple_impact_score,
    _ripple_list_items,
    _ripple_to_detail,
    _ripple_to_list_item,
    _validate_max_depth_v9_20,
    _validate_max_nodes_cap,
    cvg_manager,
)
from dashboard.helpers.decision import _decision_to_response  # noqa: F401
from dashboard.helpers.misc import _maybe_mount_dashboard_ui  # noqa: F401
from dashboard.helpers.reading_power_db import ReadingPowerDB  # noqa: F401
from dashboard.helpers.time_window import _parse_time_window  # noqa: F401
from dashboard.helpers.workflow import (  # noqa: F401
    _list_workflow_yamls,
    _workflow_result_to_response,
)
from dashboard.models import *  # noqa: F401,F403

# Phase 15.0 T1.4: routes are defined in dashboard/routes/*.py and registered
# via register_all_routes() at the end of create_app(). Each register_X takes
# (app, ctx) where ctx is a RoutesContext dataclass that bundles the closure
# dependencies (db, master_controller, manager, limiter, production_records_root,
# cvg_storage).
from dashboard.routes import RoutesContext, register_all_routes  # noqa: E402

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

    def _cvg_storage() -> RippleStorage:
        """Phase 15.0 T1.4: closure-callable wrapper around the module-level
        `_default_storage` singleton. Routes use `_app_module._default_storage()`
        for monkeypatch compat, but the `RoutesContext` dataclass expects a
        no-arg callable that returns the singleton, so we provide one here."""
        return _default_storage()

    ctx = RoutesContext(
        db=db,
        master_controller=master_controller,
        manager=manager,
        limiter=limiter,
        production_records_root=_production_records_root,
        cvg_storage=_cvg_storage,
    )

    # ==================== Endpoints ====================
    # Phase 15.0 T1.4: all 167 inline @app routes were moved to
    # dashboard/routes/*.py; each module's `register_X(app, ctx)` is called
    # once below via register_all_routes.
    register_all_routes(app, ctx)

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
