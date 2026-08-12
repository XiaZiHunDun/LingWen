"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (creator_agent domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatorAgentScope(BaseModel):
    type: str
    chapter: Optional[int] = None
    selection_text: Optional[str] = None

class CreatorAgentPlanRequest(BaseModel):
    action: str
    action_label: str
    scope: CreatorAgentScope
    body_draft: Optional[str] = None
    style_strength: int = 1
    allow_worldbuilding_fill: bool = False
    goal_tag: Optional[str] = None
    execution_mode: str = "preview"
    lens: str = "author"
    provider_mode: str = "auto"

class CreatorAgentCandidate(BaseModel):
    id: str
    label: str
    direction: str
    text: str

class CreatorAgentAdviceItem(BaseModel):
    id: str
    text: str

class CreatorAgentAnnotation(BaseModel):
    id: str
    level: str = "info"
    text: str
    paragraph: Optional[int] = None

class CreatorAgentPlanResponse(BaseModel):
    advice_only: bool = False
    candidates: list[CreatorAgentCandidate] = Field(default_factory=list)
    advice: list[CreatorAgentAdviceItem] = Field(default_factory=list)
    annotations: list[CreatorAgentAnnotation] = Field(default_factory=list)
    status_line: str = ""
    provider: str = "mock"
    base_excerpt: str = ""
    memory_hints: list[str] = Field(default_factory=list)
    lens: str = "author"
