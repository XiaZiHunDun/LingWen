"""Pydantic schemas for LLM-backed world-DB proposal extraction.

Phase 118: validates JSON output from the LLM before it is inserted into
the ``proposal`` table. The ``character.update`` payload mirrors the
fields accepted by ``accept_proposal`` in apps/studio_api/routes/world.py.
"""
from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CharacterUpdatePayload(BaseModel):
    """Subset of Character fields accepted by ``character.update`` proposals.

    Each field is optional because the LLM may only emit a partial patch.
    Server-side code (``update_character``) uses COALESCE so omitted fields
    keep their current value.
    """

    name: str | None = None
    canon_level: Literal["Draft", "Secondary", "Primary"] | None = None
    status: str | None = None
    first_chapter: int | None = None
    last_seen_chapter: int | None = None
    attributes: dict | None = None
    aliases: list[str] | None = None
    notes: str | None = None

    @field_validator("aliases")
    @classmethod
    def _strip_aliases(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return [a.strip() for a in v if a and a.strip()]


class ProposalResponse(BaseModel):
    """One proposal returned by the LLM extractor.

    The shape matches the ``proposal`` table columns:
    kind / target_kind / target_id / payload / source / source_context.
    """

    kind: Literal["character.update", "character.create"]
    target_kind: Literal["character", "faction"] | None = None
    target_id: int = 0
    payload: CharacterUpdatePayload
    source: Literal["agent"] = "agent"
    source_context: str | None = None
    confidence: Literal["high", "medium", "low"] = "medium"


class ExtractionResult(BaseModel):
    """Top-level JSON shape returned by the LLM.

    Phase 118 v1: the LLM may return either a bare JSON array of proposals
    or a JSON object with a ``proposals`` key. ``parse_proposals_json``
    normalizes both shapes into ``ExtractionResult.proposals``.
    """

    proposals: list[ProposalResponse] = Field(default_factory=list)


def parse_proposals_json(raw: str) -> list[ProposalResponse]:
    """Parse raw LLM output into a validated list of proposals.

    Accepts:
      - Top-level JSON array of proposal objects
      - JSON object with a ``proposals`` key
      - Markdown-fenced JSON (````json ... ````)

    Raises ``ValueError`` on parse / validation failure with a
    human-readable message. The caller decides whether to surface the
    error to the user or treat it as an empty extraction result.
    """
    text = raw.strip()
    # Strip markdown code fences if present.
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:].lstrip("\n")
    text = text.strip()

    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM output is not valid JSON: {exc}") from exc

    if isinstance(data, list):
        wrapped = {"proposals": data}
    elif isinstance(data, dict) and "proposals" in data:
        wrapped = data
    elif isinstance(data, dict):
        wrapped = {"proposals": [data]}
    else:
        raise ValueError(
            f"unexpected LLM output shape: {type(data).__name__}"
        )

    result = ExtractionResult.model_validate(wrapped)
    return result.proposals
