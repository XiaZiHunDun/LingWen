"""Pydantic v2 DTOs for the quality bounded context (prose judge + scoring)."""

from __future__ import annotations

from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field


class QualityScoreDTO(BaseModel):
    """Quality score for a chapter or batch.

    Mirrors ``apps/studio_api/routes/studio.py::fetch_quality`` response shape.
    """

    model_config = ConfigDict(extra="ignore")

    chapter_id: str | None = None
    overall_score: float = Field(ge=0.0, le=1.0)
    dimensions: Mapping[str, float]  # e.g. {"consistency": 0.9, "prose": 0.8}
    computed_at: str | None = None
    model: str | None = None  # which LLM/judge produced this


class ProseJudgeDTO(BaseModel):
    """Single judge verdict on prose quality."""

    model_config = ConfigDict(extra="ignore")

    chapter_id: str
    verdict: Literal["pass", "revise", "rewrite"]
    rationale: str
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] | None = None


class ProseDiffDTO(BaseModel):
    """Diff between two prose versions (revision tracking)."""

    model_config = ConfigDict(extra="ignore")

    chapter_id: str
    base_revision: int
    head_revision: int
    additions: int = 0
    deletions: int = 0
    diff_summary: str | None = None
