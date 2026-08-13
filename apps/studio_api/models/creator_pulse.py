"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_pulse domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorVolumePulseRow(BaseModel):
    label: str
    start_chapter: int
    end_chapter: int
    written: int
    total_chapters: int
    progress_pct: float = 0.0
    locked: bool = False
    status: str = "ok"
    deviation_count: int = 0
    headline: str = ""

class CreatorVolumePulseSummary(BaseModel):
    name: str
    excerpt: str = ""

class CreatorVolumePulse(BaseModel):
    volume_count: int = 0
    alert_count: int = 0
    warn_count: int = 0
    overall_status: str = "ok"
    alerts_only: bool = False
    volumes: list[CreatorVolumePulseRow] = []
    latest_summary: Optional[CreatorVolumePulseSummary] = None
