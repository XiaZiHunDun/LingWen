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
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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


class ProductionRecordResponse(BaseModel):
    """Phase 9.82 F74: pilot/batch record summary (read-only)."""

    record_id: str
    record_type: str
    chapter_num: Optional[int] = None
    chapter_range: Optional[str] = None
    operator: Optional[str] = None
    recorded_at: Optional[str] = None
    provider: Optional[str] = None
    total_cost_usd: Optional[float] = None
    emit_chapter_completed: Optional[bool] = None
    memory_context_source: Optional[str] = None
    stopped_reason: Optional[str] = None
    source_file: str


class ProductionRecordsResponse(BaseModel):
    """List of production records from pilot_records dir."""

    records_dir: str
    records: list[ProductionRecordResponse]


class ProductionBatchRollupResponse(BaseModel):
    """Phase 9.89 F81: batch row in production rollup."""

    record_id: str
    chapter_range: Optional[str] = None
    total_cost_usd: Optional[float] = None
    stopped_reason: Optional[str] = None
    recorded_at: Optional[str] = None
    source_file: str


class ProductionRollupResponse(BaseModel):
    """Phase 9.89 F81: aggregated pilot/batch stats for Analytics."""

    records_dir: str
    record_count: int
    pilot_count: int
    batch_count: int
    total_cost_usd: float
    chapters_with_records: int
    latest_recorded_at: Optional[str] = None
    batches: list[ProductionBatchRollupResponse]


class ProductionCostTrendPointResponse(BaseModel):
    """Phase 9.96 F87: one point on production cost timeline."""

    recorded_at: Optional[str] = None
    record_id: str
    record_type: str
    label: str
    cost_usd: Optional[float] = None
    incremental_cost_usd: float
    cumulative_cost_usd: float


class ProductionCostTrendResponse(BaseModel):
    """Phase 9.96 F87: time-ordered cost series for Analytics chart."""

    records_dir: str
    point_count: int
    total_cost_usd: float
    points: list[ProductionCostTrendPointResponse]


# === Phase 10.04: Studio multi-project models ===


class StudioProjectItem(BaseModel):
    slug: str
    name: str
    role: str
    root: str
    location: str


class StudioProjectsResponse(BaseModel):
    projects: list[StudioProjectItem]
    active_slug: Optional[str] = None


class StudioActiveResponse(BaseModel):
    slug: str
    name: str
    root: str
    role: str


class StudioSetActiveRequest(BaseModel):
    slug: str


class StudioSummaryResponse(BaseModel):
    slug: str
    name: str
    role: str
    root: str
    location: str
    max_chapter: int
    genre: str
    chapter_count: int
    latest_chapter: int
    outline_count: int
    golden_chapters: list[int]
    has_golden_set: bool
    pilot_records_dir: str
    pilot_record_count: int
    pillars_ok: bool
    pillars_path: str
    creation_mode: str = "studio"
    quality_profile: str = "studio_full"


class CreatorChapterRow(BaseModel):
    chapter: int
    has_body: bool
    has_outline: bool
    word_count: int
    excerpt: Optional[str] = None


class CreatorVolumeSummary(BaseModel):
    path: str
    name: str
    excerpt: str


class CreatorVolumePlanEntry(BaseModel):
    label: str
    start_chapter: int
    end_chapter: int
    core_conflict: str = ""
    locked: bool = False
    locked_at: Optional[str] = None


class CreatorVolumeDeviation(BaseModel):
    type: str
    severity: str
    chapter: int
    volume_label: Optional[str] = None
    message: str


class CreatorOverviewResponse(BaseModel):
    slug: str
    name: str
    creation_mode: str
    quality_profile: str
    max_chapter: int
    chapters_written: int
    coverage_pct: float
    chapters: list[CreatorChapterRow]
    volume_summaries: list[CreatorVolumeSummary]
    pillars_excerpt: str
    pillars_path: str
    global_outline_excerpt: str
    global_outline_path: str
    p0_count: Optional[int] = None
    quality_report_available: bool
    companion_check_cmd: str
    advance_batch_hint: str
    notify_per_chapter: bool
    advance_volume_summary: bool
    locked_volume_count: int = 0
    deviation_count: int = 0
    alert_count: int = 0
    deviations: list[CreatorVolumeDeviation] = []


class CreatorVolumePlanResponse(BaseModel):
    slug: str
    global_outline_path: str
    state_path: str
    revision: str
    volumes: list[CreatorVolumePlanEntry]
    locked_volume_count: int
    deviations: list[CreatorVolumeDeviation]
    deviation_count: int
    alert_count: int


class CreatorVolumePlanSaveRequest(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    expected_revision: Optional[str] = None


class CreatorVolumeMergeRequest(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    start_index: int
    end_index: int
    label: Optional[str] = None
    core_conflict: Optional[str] = None


class CreatorVolumeMergeResponse(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    merged_label: str
    merged_range: str


class CreatorVolumeSplitRequest(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    volume_index: int
    split_at_chapter: int
    first_label: Optional[str] = None
    second_label: Optional[str] = None


class CreatorVolumeSplitResponse(BaseModel):
    volumes: list[CreatorVolumePlanEntry]
    first_label: str
    second_label: str
    first_range: str
    second_range: str


class CreatorVolumeTemplateInfo(BaseModel):
    id: str
    name: str
    description: str
    builtin: bool = True
    scope: str = "builtin"
    version_label: Optional[str] = None


class CreatorVolumeTemplateVersionRequest(BaseModel):
    version_label: Optional[str] = None


class CreatorVolumeTemplateVersionResponse(BaseModel):
    id: str
    version_label: Optional[str] = None


class CreatorVolumeFactoryPublishRequest(BaseModel):
    template_id: str


class CreatorVolumeFactoryPublishResponse(BaseModel):
    id: str
    name: str
    description: str


class CreatorVolumeFactoryPullRequest(BaseModel):
    template_ids: list[str]


class CreatorVolumeFactoryPullResponse(BaseModel):
    imported: int
    total: int
    template_ids: list[str]


class CreatorVolumeFactoryDeleteResponse(BaseModel):
    id: str
    deleted: bool


class CreatorVolumeSaveTemplateRequest(BaseModel):
    name: str
    volumes: list[CreatorVolumePlanEntry]
    max_chapter: Optional[int] = None
    description: Optional[str] = None
    version_label: Optional[str] = None


class CreatorVolumeSaveTemplateResponse(BaseModel):
    id: str
    name: str
    description: str


class CreatorVolumeDeleteTemplateResponse(BaseModel):
    id: str
    deleted: bool


class CreatorVolumeRenameTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    version_label: Optional[str] = None


class CreatorVolumeRenameTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    version_label: Optional[str] = None


class CreatorVolumeTemplateExportResponse(BaseModel):
    schema_version: str
    templates: list[dict[str, Any]]
    count: int


class CreatorVolumeTemplateImportRequest(BaseModel):
    templates: list[dict[str, Any]]
    replace: bool = False


class CreatorVolumeTemplateImportResponse(BaseModel):
    imported: int
    total: int
    replaced: bool


class CreatorVolumeTemplateSyncSource(BaseModel):
    slug: str
    name: str
    template_count: int


class CreatorVolumeTemplateSyncSourcesResponse(BaseModel):
    sources: list[CreatorVolumeTemplateSyncSource]


class CreatorVolumeTemplateSyncRequest(BaseModel):
    source_slugs: list[str]


class CreatorVolumeTemplateSyncResponse(BaseModel):
    imported: int
    total: int
    sources: list[str]


class CreatorVolumeTemplateListResponse(BaseModel):
    templates: list[CreatorVolumeTemplateInfo]


class CreatorVolumeApplyTemplateRequest(BaseModel):
    template_id: str
    max_chapter: Optional[int] = None


class CreatorVolumeApplyTemplateResponse(BaseModel):
    template_id: str
    template_name: str
    volumes: list[CreatorVolumePlanEntry]


class CreatorChapterPreviewResponse(BaseModel):
    chapter: int
    has_body: bool
    has_outline: bool
    word_count: int
    body_preview: str
    outline_preview: str
    body_truncated: bool
    outline_truncated: bool


class CreatorSettingsDocsResponse(BaseModel):
    slug: str
    pillars_path: str
    global_outline_path: str
    pillars_text: str
    global_outline_text: str
    pillars_revision: str
    global_outline_revision: str


class CreatorSettingsDocsSaveRequest(BaseModel):
    pillars_text: Optional[str] = None
    global_outline_text: Optional[str] = None
    expected_pillars_revision: Optional[str] = None
    expected_global_outline_revision: Optional[str] = None
    pillars_merge_source: Optional[str] = None
    global_outline_merge_source: Optional[str] = None
    merge_snapshot_id: Optional[str] = None
    pillars_merge_snapshot_id: Optional[str] = None
    global_outline_merge_snapshot_id: Optional[str] = None


class CreatorOnboardingStep(BaseModel):
    id: str
    title: str
    detail: str
    note: str = ""


class CreatorOnboardingResponse(BaseModel):
    slug: str
    creation_mode: str
    mode_label: str
    max_chapter: int
    steps: list[CreatorOnboardingStep]
    checklist_doc: str
    smoke_command: str
    onboarding_doc: str
    completed_step_ids: list[str] = []
    auto_completed_step_ids: list[str] = []
    step_notes: dict[str, str] = {}
    progress_pct: int = 0


class CreatorOnboardingProgressRequest(BaseModel):
    completed_step_ids: list[str] = []
    step_notes: Optional[dict[str, str]] = None


class CreatorOnboardingNotesRequest(BaseModel):
    step_notes: dict[str, str]


class CreatorOnboardingProgressResponse(BaseModel):
    completed_step_ids: list[str]
    auto_completed_step_ids: list[str] = []
    step_notes: dict[str, str] = {}
    progress_pct: int


class CreatorMergePreferencesResponse(BaseModel):
    pillars_merge_source: str
    global_outline_merge_source: str
    merge_snapshot_id: Optional[str] = None
    pillars_merge_snapshot_id: Optional[str] = None
    global_outline_merge_snapshot_id: Optional[str] = None
    uses_global_default: bool = False


class CreatorSettingsDiffPart(BaseModel):
    changed: bool
    lines_added: int
    lines_removed: int
    snippet: list[str]


class CreatorSettingsDiffResponse(BaseModel):
    has_changes: bool
    pillars: CreatorSettingsDiffPart
    global_outline: CreatorSettingsDiffPart


class CreatorSettingsThreeWayPair(BaseModel):
    pillars: CreatorSettingsDiffPart
    global_outline: CreatorSettingsDiffPart


class CreatorSettingsThreeWayResponse(BaseModel):
    has_changes: bool
    pillars: CreatorSettingsDiffPart
    global_outline: CreatorSettingsDiffPart
    has_history: bool = False
    history_snapshot_id: Optional[str] = None
    disk_vs_history: Optional[CreatorSettingsThreeWayPair] = None
    editor_vs_history: Optional[CreatorSettingsThreeWayPair] = None


class CreatorSettingsThreeWayRequest(BaseModel):
    pillars_text: str
    global_outline_text: str
    snapshot_id: Optional[str] = None


class CreatorSettingsMergeFieldPreview(BaseModel):
    source: str
    vs_disk: CreatorSettingsDiffPart
    vs_editor: CreatorSettingsDiffPart


class CreatorSettingsMergePreviewResponse(BaseModel):
    pillars: CreatorSettingsMergeFieldPreview
    global_outline: CreatorSettingsMergeFieldPreview


class CreatorSettingsMergePreviewRequest(BaseModel):
    pillars_text: str
    global_outline_text: str
    pillars_merge_source: str = "editor"
    global_outline_merge_source: str = "editor"
    snapshot_id: Optional[str] = None
    pillars_merge_snapshot_id: Optional[str] = None
    global_outline_merge_snapshot_id: Optional[str] = None


class CreatorSettingsHistorySnapshot(BaseModel):
    id: str
    saved_at: Optional[str] = None
    label: str
    pillars_excerpt: str
    global_outline_excerpt: str
    pillars_lines: int
    global_outline_lines: int


class CreatorSettingsHistoryResponse(BaseModel):
    slug: str
    snapshots: list[CreatorSettingsHistorySnapshot]
    count: int


class CreatorSettingsRestoreRequest(BaseModel):
    snapshot_id: str


class StudioQualityResponse(BaseModel):
    slug: str
    pillars_ok: bool
    pillars_path: str
    require_chapter_outline: bool
    max_chapter: int
    chapters_written: int
    outlines_present: int
    coverage_pct: float
    missing_outlines: list[int]
    missing_bodies: list[int]
    golden_set_status: str
    golden_regression_cmd: str


class StudioQualityReportIssue(BaseModel):
    severity: str
    issue_type: str
    chapter: int
    description: str


class StudioQualityReportChapter(BaseModel):
    chapter: int
    word_count: int
    issue_count: int
    issues: list[StudioQualityReportIssue]


class StudioProseHeatmapChapter(BaseModel):
    chapter: int
    issue_count: int
    prose_p1: int
    prose_total: int
    structural_total: int
    heat: float


class StudioProseHeatmap(BaseModel):
    chapters: list[StudioProseHeatmapChapter]
    max_prose_per_chapter: int = 0
    total_prose_issues: int = 0
    total_prose_p1: int = 0


class StudioQualityReportResponse(BaseModel):
    slug: str
    available: bool
    path: str
    total: int
    p0: int
    p1: int
    p2: int
    p3: int
    generated_at: Optional[str] = None
    chapters: list[StudioQualityReportChapter]
    prose_heatmap: StudioProseHeatmap


class StudioProseDiffTotals(BaseModel):
    p0: int = 0
    p1: int = 0
    total: int = 0
    prose_p1: int = 0
    prose_total: int = 0


class StudioProseDiffChapter(BaseModel):
    chapter: int
    before_prose_p1: int
    after_prose_p1: int
    delta_prose_p1: int
    before_prose_total: int
    after_prose_total: int
    delta_prose_total: int


class StudioProseDiffResponse(BaseModel):
    slug: str
    available: bool
    reason: Optional[str] = None
    snapshot_path: str = ""
    report_path: Optional[str] = None
    save_command: Optional[str] = None
    before_captured_at: Optional[str] = None
    after_captured_at: Optional[str] = None
    total_delta: Optional[StudioProseDiffTotals] = None
    chapters: list[StudioProseDiffChapter] = Field(default_factory=list)
    improved_count: int = 0
    regressed_count: int = 0
    has_regression: bool = False
    net_prose_p1_delta: int = 0


class StudioProseJudgeRating(BaseModel):
    dimension: str
    score: int
    evidence: str
    action: str


class StudioProseJudgeChapter(BaseModel):
    chapter: int
    avg_score: float
    ratings: list[StudioProseJudgeRating]


class StudioProseJudgeSignal(BaseModel):
    chapter: int
    issue_type: Optional[str] = None
    dimension: Optional[str] = None
    judge_score: int
    description: Optional[str] = None
    evidence: Optional[str] = None


class StudioProseJudgeResponse(BaseModel):
    slug: str
    available: bool
    reason: Optional[str] = None
    report_path: str = ""
    generate_command: Optional[str] = None
    source: Optional[str] = None
    judged_at: Optional[str] = None
    golden_chapters: list[int] = Field(default_factory=list)
    weighted_avg: float = 0.0
    chapters: list[StudioProseJudgeChapter] = Field(default_factory=list)
    high_priority_count: int = 0
    false_positive_candidate_count: int = 0
    review_needed_count: int = 0
    high_priority: list[StudioProseJudgeSignal] = Field(default_factory=list)
    false_positive_candidates: list[StudioProseJudgeSignal] = Field(default_factory=list)
    review_needed: list[StudioProseJudgeSignal] = Field(default_factory=list)


class StudioPreflightChapter(BaseModel):
    chapter: int
    ok: bool
    message: str


class StudioPreflightRequest(BaseModel):
    start_chapter: int = Field(ge=1)
    end_chapter: int = Field(ge=1)
    mode: str = "canon"


class StudioPreflightResponse(BaseModel):
    slug: str
    mode: str
    start_chapter: int
    end_chapter: int
    all_ok: bool
    chapters: list[StudioPreflightChapter]
    batch_command: str


class StudioBatchRunRequest(BaseModel):
    start_chapter: int = Field(ge=1)
    end_chapter: int = Field(ge=1)
    mode: str = "canon"
    budget_usd: float = Field(default=0.15, ge=0, le=100)
    skip_preflight: bool = False


class StudioBatchJobResponse(BaseModel):
    job_id: str
    slug: str
    start_chapter: int
    end_chapter: int
    budget_usd: float
    mode: str
    status: str
    pid: Optional[int] = None
    log_path: str
    started_at: str
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None
    log_tail: Optional[str] = None


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


def _maybe_mount_dashboard_ui(app: FastAPI) -> None:
    """Serve built Vue UI from FastAPI (single port for SSH remote / Cursor forward)."""
    flag = os.environ.get("LINGWEN_SERVE_UI", "").strip().lower()
    if flag not in ("1", "true", "yes"):
        return
    dist = Path(__file__).resolve().parent / "frontend" / "dist"
    if not dist.is_dir():
        return
    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="dashboard-assets")

    @app.get("/", include_in_schema=False)
    async def dashboard_index() -> FileResponse:
        return FileResponse(dist / "index.html")


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
    def creator_chapter_preview_endpoint(chapter_num: int) -> CreatorChapterPreviewResponse:
        from infra.creator_dashboard import creator_chapter_preview
        from infra.studio_registry import active_project

        project = active_project()
        if project is None:
            raise HTTPException(404, "no active project")
        try:
            return CreatorChapterPreviewResponse(
                **creator_chapter_preview(project, chapter_num),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

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
