"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (studio domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


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
