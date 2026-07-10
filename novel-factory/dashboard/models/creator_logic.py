"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_logic domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorLogicCheckIssue(BaseModel):
    severity: str
    chapter: int = 0
    paragraph: Optional[int] = None
    line: Optional[int] = None
    title: str = ""
    message: str = ""

class CreatorLogicCheckResponse(BaseModel):
    passed: bool
    fail_severity: Optional[str] = None
    creation_mode: str = "companion"
    chapters_checked: int = 0
    total_issues: int = 0
    issue_counts: dict[str, int] = {}
    p0_count: int = 0
    p0_only: bool = False
    chapter: Optional[int] = None
    issues: list[CreatorLogicCheckIssue] = []
