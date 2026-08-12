"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_history domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorBatchHistoryItem(BaseModel):
    job_id: str
    slug: str
    start_chapter: int
    end_chapter: int
    budget_usd: float = 0.0
    mode: str = "canon"
    status: str
    started_at: str
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None
    failure_reason: Optional[str] = None

class CreatorBatchHistoryResponse(BaseModel):
    jobs: list[CreatorBatchHistoryItem] = []

class CreatorBatchHistoryExportResponse(BaseModel):
    schema_version: str = "1"
    count: int = 0
    jobs: list[CreatorBatchHistoryItem] = []
