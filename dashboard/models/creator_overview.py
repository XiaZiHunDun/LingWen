"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_overview domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Phase 15.0 T1.4: Pydantic v2 + `from __future__ import annotations` means these
# type annotations resolve to strings. Pydantic looks them up in the LOCAL
# module namespace when validating, so we must import the referenced classes
# directly (the dashboard.models package re-exports are not enough on their own).
from dashboard.models.creator import (
    CreatorChapterRow,
    CreatorUiProfile,
    CreatorVolumeDeviation,
    CreatorVolumePlanEntry,
    CreatorVolumeSummary,
)
from dashboard.models.creator_pulse import CreatorVolumePulse


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
    deviation_total_count: int = 0
    alert_count: int = 0
    deviations: list[CreatorVolumeDeviation] = []
    ui_profile: CreatorUiProfile
    volume_pulse: Optional[CreatorVolumePulse] = None

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

class CreatorVolumePlanDiffChange(BaseModel):
    type: str
    label: str
    message: str
    details: list[str] = []

class CreatorOutlineHighlightLine(BaseModel):
    text: str
    highlighted: bool = False

class CreatorVolumePlanDiffResponse(BaseModel):
    has_changes: bool
    changes: list[CreatorVolumePlanDiffChange]
    global_outline_excerpt: str = ""
    global_outline_path: str = ""
    highlight_volume_labels: list[str] = []
    global_outline_lines: list[CreatorOutlineHighlightLine] = []
