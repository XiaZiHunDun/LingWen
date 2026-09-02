"""Pydantic v2 DTOs for the workspace bounded context (write chapter)."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict


class ChapterDTO(BaseModel):
    """Chapter write/read response shape.

    Mirrors ``apps/studio_api/routes/chapters.py`` response shape.
    """

    model_config = ConfigDict(extra="ignore")

    id: int | None = None  # optional for write/create flow (mirrors ProposalDTO pattern)
    project_slug: str
    chapter_number: int
    title: str
    content: str
    word_count: int = 0
    last_modified: str | None = None


class SceneDTO(BaseModel):
    """Scene (sub-chapter unit, TipTap document) shape."""

    model_config = ConfigDict(extra="ignore")

    id: str  # UUID
    chapter_id: int
    order: int
    content: str  # TipTap JSON-serialized
    word_count: int = 0


class AnnotationDTO(BaseModel):
    """User/agent annotation on a scene."""

    model_config = ConfigDict(extra="ignore")

    id: str  # UUID
    scene_id: str
    kind: Literal["comment", "highlight", "revision_note"]
    body: str
    author: str | None = None
    created_at: str | None = None


class ConflictDTO(BaseModel):
    """Conflict snapshot when concurrent writes detected."""

    model_config = ConfigDict(extra="ignore")

    chapter_id: int
    base_revision: int
    head_revision: int
    conflicting_content: str
    resolution_hint: str | None = None
