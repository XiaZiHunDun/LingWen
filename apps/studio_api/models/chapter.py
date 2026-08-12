"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (chapter domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


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
