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

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field

from dashboard.cascade_notifier import (
    notify_cascade_cancel,  # Phase 9.21: cascade cancel WS push
    set_main_event_loop,  # Phase 9.66: worker-thread WS schedule
    set_ws_manager,  # Phase 9.16: cascade WS push injector
)
from dashboard.cvg_ws import EVENT_PONG, CvgConnectionManager
from dashboard.protocols import (
    CascadeCancelPayload,  # Phase 9.21
    CascadeCancelRequest,  # Phase 9.21
    CascadeBroadcastLogResponse,  # Phase 9.44 F33
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,
    MasterControllerLike,
    RippleActionRequest,
    RippleActionResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleListItemResponse,
    RippleRollbackRequest,
    RippleStatsResponse,
    ReferenceGraphResponse,
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

# ==================== Pydantic Models ====================


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str


class OverviewResponse(BaseModel):
    """Overview statistics response model."""

    total_chapters: int
    total_hooks: int
    avg_hook_strength: float
    total_coolpoints: int
    avg_coolpoint_density: float


class ChapterData(BaseModel):
    """Single chapter data model."""

    chapter: int
    hook_count: int
    hook_strength_avg: float
    coolpoint_count: int
    coolpoint_density: float


class ChaptersResponse(BaseModel):
    """Chapters list response model."""

    chapters: list[ChapterData]


# === Phase 6: Decision/Workflow models ===

class DecisionResponse(BaseModel):
    """HumanDecision 序列化(决策面板用)"""
    decision_id: str
    kind: str
    node_id: str
    prompt: str
    options: list[str]
    priority: int
    status: str
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    reason: Optional[str] = None


class ResolveDecisionRequest(BaseModel):
    """解决决策请求"""
    option: str
    resolved_by: str = "human"


class DeferDecisionRequest(BaseModel):
    """推迟决策请求"""
    reason: str = ""


class CancelDecisionRequest(BaseModel):
    """取消决策请求"""
    reason: str = ""


class WorkflowListItem(BaseModel):
    """工作流列表项"""
    name: str
    path: str
    node_count: int
    has_decision_nodes: bool


class RunWorkflowRequest(BaseModel):
    """运行工作流请求"""
    workflow_name: str
    initial_inputs: Optional[dict[str, Any]] = None
    start_nodes: Optional[list[str]] = None
    max_backtracks: int = 2
    base_dir: Optional[str] = None
    cost_budget_usd: Optional[float] = None  # Phase 8.8: budget alarm (None=unlimited)


class ResumeWorkflowRequest(BaseModel):
    """恢复工作流请求"""
    decision_id: str
    option: str
    resolved_by: str = "human"
    # Phase 8.8: 字段保留 (前端可传),但 master.resume_workflow 当前不接 (T3 留 followup)
    # 透传后 _current_budget_usd 仍为 None,resumed run 不受新 budget 影响
    cost_budget_usd: Optional[float] = None  # Phase 8.8: budget alarm (None=清空 budget)


class BudgetSetRequest(BaseModel):
    """Phase 8.12 T5: 设置 day/week budget (per-run 不暴露, run 启动时传)"""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"


class BudgetTierSetRequest(BaseModel):
    """Phase 8.15 T6: 设置 tier budget (haiku/sonnet/opus 各自)."""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    workflow_name: Optional[str] = None
    is_active: bool = False
    completed: int = 0
    failed: int = 0
    paused: bool = False
    paused_nodes: list[str] = Field(default_factory=list)
    node_count: int = 0
    steps: int = 0
    total_cost_usd: float = 0.0  # Phase 8.5: 0.0 if no cost_tracker wired
    pending_decisions: list[dict[str, Any]] = Field(default_factory=list)
    executions: dict[str, str] = Field(default_factory=dict)  # Phase 6.6.D
    score_data: dict[str, dict[str, Any]] = Field(default_factory=dict)  # Phase 7.6: S1-S8 评分数据
    cost_by_scenario: dict[str, float] = Field(default_factory=dict)  # Phase 8.7: by-scenario 累计 USD
    cost_by_tier: dict[str, float] = Field(default_factory=dict)  # Phase 8.13: by-tier 累计 USD (haiku/sonnet/opus)
    cost_by_day: dict[str, float] = Field(default_factory=dict)  # Phase 8.23: trend chart data (YYYY-MM-DD → USD)
    cost_by_day_per_tier: dict[str, dict[str, float]] = Field(  # Phase 9.28 F12
        default_factory=dict
    )
    cost_budget_status: dict[str, Any] = Field(default_factory=dict)  # Phase 8.8 T5: budget alarm 状态
    # Phase 8.12 T5 NEW: per-day / per-week budget status (per-run 仍走 cost_budget_status 旧 path)
    budget_per_day: dict[str, Any] = Field(default_factory=dict)
    budget_per_week: dict[str, Any] = Field(default_factory=dict)
    # Phase 8.15 T6 NEW: per-tier budget status (haiku/sonnet/opus, 跟 run/day/week 完全 orthogonal)
    budget_by_tier: dict[str, dict[str, Any] | None] = Field(default_factory=dict)
    # Phase 9.68 F60: incremental CVG backfill stats after novel_writing (null = skipped/disabled)
    incremental_backfill: dict[str, Any] | None = None
    # Phase 9.74 F66: per-run chapter production summary (chapter_num + memory + backfill)
    production_summary: dict[str, Any] | None = None


class WorkflowMermaidResponse(BaseModel):
    """工作流 mermaid 图响应 (Phase 6.3 + 6.6.D)"""
    workflow_name: str
    mermaid: str
    node_count: int
    has_decision_nodes: bool
    status_applied: bool = False  # Phase 6.6.D: true = 染色基于 active workflow
    node_statuses: dict[str, str] = Field(default_factory=dict)  # Phase 6.6.D


# ==================== Phase 8.16: Time Window Helper ====================

_TIME_WINDOW_DAYS = {"7d": 7, "30d": 30}


def _parse_time_window(window: str) -> Optional[datetime]:
    """Phase 8.16: 翻译 time_window query param → since datetime (UTC).

    Args:
        window: "7d" | "30d" | "all" | 其他 (silent fallback to None)

    Returns:
        datetime (UTC, now-7d 或 now-30d) for "7d"/"30d"
        None for "all" or invalid (silent fallback, 防呆, 跟 Phase 8.13 silent degrade 模式一致)
    """
    if window in _TIME_WINDOW_DAYS:
        return datetime.now(timezone.utc) - timedelta(days=_TIME_WINDOW_DAYS[window])
    return None


# ==================== Database Helper ====================


class ReadingPowerDB:
    """Database handler for reading power data."""

    DB_PATH = Path(__file__).parent.parent / ".state" / "reading_power.db"

    def __init__(self, db_path: Optional[Path] = None, init_if_missing: bool = True):
        self.db_path = db_path or self.DB_PATH
        if init_if_missing:
            self._ensure_db_path()

    def _ensure_db_path(self) -> None:
        """Ensure the database directory exists."""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection with Row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connect(self):
        """Context manager for database connections."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS hooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter TEXT NOT NULL,
                    hook_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    position TEXT NOT NULL,
                    content TEXT NOT NULL,
                    llm_analyzed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chapter, hook_type, position)
                );

                CREATE TABLE IF NOT EXISTS coolpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    density REAL NOT NULL,
                    combo_with TEXT,
                    content TEXT NOT NULL,
                    llm_analyzed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chapter, pattern)
                );

                CREATE TABLE IF NOT EXISTS chapter_summary (
                    chapter TEXT PRIMARY KEY,
                    hook_count INTEGER DEFAULT 0,
                    hook_strength_avg REAL DEFAULT 0.0,
                    coolpoint_count INTEGER DEFAULT 0,
                    coolpoint_density REAL DEFAULT 0.0,
                    reading_power_score REAL DEFAULT 0.0,
                    last_analyzed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS analysis_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter TEXT NOT NULL,
                    analyzer_type TEXT NOT NULL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_hooks_chapter ON hooks(chapter);
                CREATE INDEX IF NOT EXISTS idx_coolpoints_chapter ON coolpoints(chapter);
                CREATE INDEX IF NOT EXISTS idx_chapter_summary_chapter ON chapter_summary(chapter);
            """)

    def update_chapter_summary(
        self,
        chapter: str,
        hook_count: int,
        hook_strength_avg: float,
        coolpoint_count: int,
        coolpoint_density: float,
        reading_power_score: Optional[float] = None,
    ) -> None:
        """Update or insert chapter summary with aggregated metrics."""
        self._init_db()
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chapter_summary
                (chapter, hook_count, hook_strength_avg, coolpoint_count, coolpoint_density,
                 reading_power_score, last_analyzed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chapter) DO UPDATE SET
                    hook_count = excluded.hook_count,
                    hook_strength_avg = excluded.hook_strength_avg,
                    coolpoint_count = excluded.coolpoint_count,
                    coolpoint_density = excluded.coolpoint_density,
                    reading_power_score = COALESCE(excluded.reading_power_score, reading_power_score),
                    last_analyzed_at = excluded.last_analyzed_at,
                    updated_at = excluded.updated_at
                """,
                (
                    chapter,
                    hook_count,
                    hook_strength_avg,
                    coolpoint_count,
                    coolpoint_density,
                    reading_power_score,
                    now,
                    now,
                    now,
                ),
            )

    def exists(self) -> bool:
        """Check if the database file exists."""
        return self.db_path.exists()

    def is_empty(self) -> bool:
        """Check if the database has no data."""
        if not self.exists():
            return True
        self.ensure_tables_exist()
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as cnt FROM chapter_summary"
            ).fetchone()
            return cursor["cnt"] == 0 if cursor else True

    def ensure_tables_exist(self) -> None:
        """Ensure database tables are initialized. Separate from is_empty()."""
        if self.exists():
            self._init_db()

    def get_overview_stats(self) -> Optional[dict]:
        """Get overview statistics from chapter_summary table."""
        if not self.exists():
            return None
        self.ensure_tables_exist()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT chapter) as total_chapters,
                    COALESCE(SUM(hook_count), 0) as total_hooks,
                    COALESCE(AVG(hook_strength_avg), 0.0) as avg_hook_strength,
                    COALESCE(SUM(coolpoint_count), 0) as total_coolpoints,
                    COALESCE(AVG(coolpoint_density), 0.0) as avg_coolpoint_density
                FROM chapter_summary
                """
            ).fetchone()
            return dict(row) if row else None

    def get_chapters_range(
        self, start_chapter: int, end_chapter: int
    ) -> list[dict]:
        """Get chapter data for a range of chapters."""
        if not self.exists():
            return []
        self.ensure_tables_exist()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    CAST(chapter AS INTEGER) as chapter,
                    hook_count,
                    hook_strength_avg,
                    coolpoint_count,
                    coolpoint_density
                FROM chapter_summary
                WHERE CAST(chapter AS INTEGER) BETWEEN ? AND ?
                ORDER BY CAST(chapter AS INTEGER)
                """,
                (start_chapter, end_chapter),
            ).fetchall()
            return [dict(row) for row in rows]


# ==================== Workflow Listing Helper ====================


def _list_workflow_yamls() -> list[WorkflowListItem]:
    """扫描 infra/got/workflows/*.yaml → WorkflowListItem 列表

    简化:不调 workflow_loader,只读 YAML 文本粗略统计
    - node_count: text 中 `- id:` 出现次数
    - has_decision_nodes: text 中是否含 `type: decision`
    """
    wf_dir = Path(__file__).parent.parent / "infra" / "got" / "workflows"
    if not wf_dir.exists():
        return []
    items: list[WorkflowListItem] = []
    for yaml_path in sorted(wf_dir.glob("*.yaml")):
        try:
            text = yaml_path.read_text(encoding="utf-8")
        except OSError:
            continue
        node_count = text.count("- id:")
        has_decision = "type: decision" in text
        items.append(
            WorkflowListItem(
                name=yaml_path.stem,
                path=str(yaml_path.relative_to(wf_dir.parent.parent)),
                node_count=node_count,
                has_decision_nodes=has_decision,
            )
        )
    return items


def _decision_to_response(d: Any) -> DecisionResponse:
    """HumanDecision / dict → DecisionResponse"""
    if hasattr(d, "to_dict"):
        d = d.to_dict()
    return DecisionResponse(
        decision_id=d.get("decision_id", ""),
        kind=d.get("decision_kind") or d.get("kind", ""),
        node_id=d.get("node_id", ""),
        prompt=d.get("prompt", ""),
        options=list(d.get("options", [])),
        priority=d.get("priority", 0),
        status=d.get("status", "pending"),
        context=d.get("context", {}) or {},
        created_at=d.get("created_at"),
        resolution=d.get("resolution"),
        resolved_at=d.get("resolved_at"),
        resolved_by=d.get("resolved_by"),
        reason=d.get("reason"),
    )


# ==================== App Factory ====================


# ==================== Phase 9.13: CVG Ripple Storage Singleton ====================
# Module-level singleton (跟 _default_decision_queue 1:1 pattern);test fixture override
# via monkeypatch.setattr(app_module, "_default_storage", ...)。

_DEFAULT_CVG_DB_PATH = Path(__file__).parent.parent / ".state" / "cross_volume.db"
_default_storage_instance: RippleStorage | None = None

# Phase 9.13: CVG WebSocket connection manager (跟 /api/ws/workflows ConnectionManager 1:1 模式)
cvg_manager = CvgConnectionManager()


def _default_storage() -> RippleStorage:
    """Phase 9.13: singleton RippleStorage for cvg endpoints.

    Lazy init: first call creates RippleStorage, subsequent calls return cached.
    跟 dashboard 内部 _default_decision_queue 1:1 pattern (但 decisions 是 queue,
    CVG 是 SQLite-backed RippleStorage)。
    """
    global _default_storage_instance
    if _default_storage_instance is None:
        _default_storage_instance = RippleStorage(db_path=_DEFAULT_CVG_DB_PATH)
    return _default_storage_instance


def _ripple_impact_score(storage: RippleStorage, r: CrossVolumeRipple) -> float:
    """Phase 9.59 F50: score from direct + persisted cascade (no live BFS)."""
    cascade = storage.get_cascade_by_ripple_id(r.id)
    return compute_impact_score(r, cascade)


def _ripple_to_list_item(r: CrossVolumeRipple, storage: RippleStorage) -> RippleListItemResponse:
    """Phase 9.13: helper to convert CrossVolumeRipple → RippleListItemResponse.

    dimension / relationship_type 暂用 placeholder (Phase 9.14 通过 JOIN reference_nodes
    + reference_edges 填充); source_chapter / target_chapter 暂用 trigger_chapter 占位
    (Phase 9.14 真实化 — 从 affected_nodes 第一个 node 的 chapter 提取)。
    """
    return RippleListItemResponse(
        ripple_id=r.id,
        dimension="unknown",  # TODO: Phase 9.14 JOIN reference_nodes
        relationship_type="mentions",  # TODO: Phase 9.14 JOIN reference_edges
        source_chapter=r.trigger_chapter,
        target_chapter=r.trigger_chapter,
        status=r.status,
        confidence=r.payload.get("confidence", 1),
        created_at=r.created_at,
        impact_score=_ripple_impact_score(storage, r),
        parent_ripple_id=r.parent_ripple_id,
        child_count=storage.count_child_ripples(r.id),
    )


def _ripple_to_detail(r: CrossVolumeRipple, storage: RippleStorage) -> RippleDetailResponse:
    """Phase 9.13: helper to convert CrossVolumeRipple → RippleDetailResponse."""
    return RippleDetailResponse(
        ripple_id=r.id,
        dimension="unknown",
        relationship_type="mentions",
        source_chapter=r.trigger_chapter,
        target_chapter=r.trigger_chapter,
        status=r.status,
        confidence=r.payload.get("confidence", 1),
        created_at=r.created_at,
        impact_score=_ripple_impact_score(storage, r),
        parent_ripple_id=r.parent_ripple_id,
        child_count=storage.count_child_ripples(r.id),
        evidence=r.payload.get("evidence", ""),
        source_payload=r.payload.get("source_payload", {}),
        target_payload=r.payload.get("target_payload", {}),
        edge_payload=r.payload.get("edge_payload", {}),
    )


def _audit_to_response(entry: AuditEntry) -> RippleAuditEntryResponse:
    """Phase 9.14: AuditEntry → RippleAuditEntryResponse."""
    return RippleAuditEntryResponse(
        id=entry.id,
        ripple_id=entry.ripple_id,
        action=entry.action,
        prev_status=entry.prev_status,
        new_status=entry.new_status,
        actor=entry.actor,
        origin=entry.origin,
        reason=entry.reason,
        created_at=entry.created_at,
    )


# === Phase 9.15 T4: cascade BFS → response helpers (locality: kept near endpoints
#  they serve; module-level so the create_app closure can reference them) ===

def _node_to_dict_for_response(node: Any) -> dict:
    """Phase 9.15 T4: ReferenceNode → dict for CascadeNodeResponse(**).

    Converts the dataclass to dict (datetime → isoformat) so Pydantic v2
    can bind the fields it knows and ignore extras (created_at / created_by
    / confidence are 0 改 ReferenceNode 既有字段, schema 不需要它们).
    """
    from dataclasses import asdict, is_dataclass
    if is_dataclass(node):
        d = asdict(node)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(node)


def _edge_to_dict_for_response(edge: Any) -> dict:
    """Phase 9.15 T4: ReferenceEdge → dict for CascadeEdgeResponse(**)."""
    from dataclasses import asdict, is_dataclass
    if is_dataclass(edge):
        d = asdict(edge)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(edge)


def _build_reference_graph_response(
    storage: RippleStorage,
    *,
    volume: int | None = None,
    dimension: str | None = None,
    limit: int = 200,
) -> ReferenceGraphResponse:
    """Phase 9.41 F30: load persisted CVG graph for ImpactGraph.vue."""
    nodes = storage.load_all_nodes()
    edges = storage.load_all_edges()
    if volume is not None:
        nodes = [n for n in nodes if n.volume == volume]
    if dimension is not None:
        nodes = [n for n in nodes if n.dimension == dimension]
    total_node_count = len(nodes)
    total_edge_count = len(edges)
    truncated = total_node_count > limit
    if truncated:
        nodes = nodes[:limit]
    node_ids = {n.id for n in nodes}
    visible_edges = [
        e for e in edges
        if e.from_node_id in node_ids and e.to_node_id in node_ids
    ]
    return ReferenceGraphResponse(
        nodes=[
            CascadeNodeResponse(**_node_to_dict_for_response(n)) for n in nodes
        ],
        edges=[
            CascadeEdgeResponse(**_edge_to_dict_for_response(e)) for e in visible_edges
        ],
        total_node_count=total_node_count,
        total_edge_count=total_edge_count,
        truncated=truncated,
    )


def _validate_max_depth_v9_20(max_depth: int | None) -> int:
    """Phase 9.20: validate max_depth for persist=true path. Returns validated int.

    persist path requires explicit max_depth (1..10). None or 0/negative/>10 → 400.
    Mirrors Phase 9.19 _validate_max_depth contract but requires a non-None return
    (no persisted-cascade fallback — persist always runs live BFS).

    Raises:
        HTTPException 400 if max_depth is None or out of range.
    """
    if max_depth is None:
        raise HTTPException(400, "max_depth is required for persist=true (1..10)")
    if max_depth < 1 or max_depth > 10:
        raise HTTPException(400, "max_depth must be 1..10")
    return max_depth


def _validate_max_nodes_cap(max_nodes_cap: int | None) -> int:
    """Phase 9.32 F16: validate max_nodes_cap for live BFS paths. Returns validated int.

    None → DEFAULT_MAX_NODES_CAP (100, backward compat).
    Raises HTTPException 400 if out of range.
    """
    from infra.cross_volume.reference_graph import DEFAULT_MAX_NODES_CAP, MAX_NODES_CAP_UPPER

    if max_nodes_cap is None:
        return DEFAULT_MAX_NODES_CAP
    if max_nodes_cap < 1 or max_nodes_cap > MAX_NODES_CAP_UPPER:
        raise HTTPException(400, f"max_nodes_cap must be 1..{MAX_NODES_CAP_UPPER}")
    return max_nodes_cap


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
        set_main_event_loop(asyncio.get_running_loop())
        if master_controller is not None:
            task = await start_broadcast_task(manager, master_controller)
        try:
            yield
        finally:
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

    # Use init_if_missing=False to avoid trying to create directories for non-existent paths
    db = ReadingPowerDB(db_path, init_if_missing=False)

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
        items = [_ripple_to_list_item(r, storage) for r in ripples]
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
    def apply_ripple(
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

    return app


def _workflow_result_to_response(
    result: dict[str, Any],
    score_data: dict[str, dict[str, Any]] | None = None,
    cost_by_scenario: dict[str, float] | None = None,  # Phase 8.7
    cost_by_tier: dict[str, float] | None = None,  # Phase 8.13
    cost_by_day: dict[str, float] | None = None,  # Phase 8.23
    cost_by_day_per_tier: dict[str, dict[str, float]] | None = None,  # Phase 9.28 F12
    total_cost_usd: float = 0.0,  # Phase 8.7: 修 Phase 8.5 gap
    budget_by_tier: dict[str, dict[str, Any] | None] | None = None,  # Phase 8.15 T5
) -> WorkflowStatusResponse:
    """run_workflow / resume_workflow 返回 dict → WorkflowStatusResponse

    summary 可能是 dict (adapter 转换后) 或 dataclass (测试 stub 直接返回)

    Phase 8.7: 修 Phase 8.5 gap — 显式接 cost_by_scenario + total_cost_usd params
    透传到 response (不再 hardcoded 0)
    Phase 8.13: 增 cost_by_tier param (additive, default None → empty dict)
    Phase 8.15 T5: 增 budget_by_tier param (additive, default None → empty dict).
    Pydantic v2 默认 extra='ignore', 未在 model 注册的 field 静默忽略; T6 会
    在 WorkflowStatusResponse 加 budget_by_tier Field (Task 6 范围).
    Phase 8.23: 增 cost_by_day param (additive, default None → empty dict)
    给 dashboard trend chart.
    Phase 9.28 F12: 增 cost_by_day_per_tier param (day × tier cross-dim).
    """
    summary = result.get("summary") or {}
    if not isinstance(summary, dict):
        # dataclass → 用 getattr
        paused_nodes = list(getattr(summary, "paused_nodes", []) or [])
        summary_dict = {
            "completed": getattr(summary, "completed", 0),
            "failed": getattr(summary, "failed", 0),
            "paused": getattr(summary, "paused", False),
            "paused_nodes": paused_nodes,
            "node_count": getattr(summary, "node_count", 0),
            "steps": getattr(summary, "steps", 0),
        }
    else:
        summary_dict = summary
    executions = result.get("executions") or {}
    paused_nodes = list(summary_dict.get("paused_nodes", []))
    return WorkflowStatusResponse(
        workflow_name=result.get("workflow_name"),
        is_active=True,
        completed=int(summary_dict.get("completed", 0)),
        failed=int(summary_dict.get("failed", 0)),
        paused=bool(summary_dict.get("paused", False)),
        paused_nodes=paused_nodes,
        node_count=int(summary_dict.get("node_count", len(executions))),
        steps=int(summary_dict.get("steps", 0)),
        pending_decisions=list(result.get("pending_decisions", [])),
        score_data=score_data or {},
        cost_by_scenario=cost_by_scenario or {},  # Phase 8.7
        cost_by_tier=cost_by_tier or {},  # Phase 8.13
        cost_by_day=cost_by_day or {},  # Phase 8.23
        cost_by_day_per_tier=cost_by_day_per_tier or {},  # Phase 9.28 F12
        total_cost_usd=total_cost_usd,  # Phase 8.7: 修 Phase 8.5 gap
        budget_by_tier=budget_by_tier or {},  # Phase 8.15 T5 (Pydantic 暂 ignore, T6 补 model Field)
        incremental_backfill=result.get("incremental_backfill"),  # Phase 9.68 F60
        production_summary=result.get("production_summary"),  # Phase 9.74 F66
    )


# ==================== App Instance ====================


# Note: app is created lazily to avoid issues with testing and reimport
# Use create_app() to get the application instance


# ==================== Main Entry Point ====================


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("DASHBOARD_PORT", "8765"))
    app = create_app()
    uvicorn.run(app, host=host, port=port)
