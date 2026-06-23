"""Content revision tokens for creator doc conflict detection."""
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
