"""Content revision tokens for creator doc conflict detection.

Migrated from infra/creator_revision.py in Phase 126 v16.2.0.
New location: packages/lingwen-creator/src/lingwen_creator/shared/revision.py
Used by settings/docs, volume/plan, volume/templates — see spec §2.1.
"""
from __future__ import annotations

import hashlib


class CreatorDocConflictError(Exception):
    """Raised when on-disk content changed since the client loaded it."""

    def __init__(self, message: str, *, fields: list[str] | None = None):
        super().__init__(message)
        self.fields = fields or []


def content_revision(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
