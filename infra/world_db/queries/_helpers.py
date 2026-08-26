"""Shared helpers for world_db query modules.

Centralizes:
- ISO-8601 UTC timestamp generation (avoids drift across modules)
- SQLite row → dict conversion with per-table JSON column decoding
- Base class for optimistic-concurrency revision conflicts
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone


def now_iso() -> str:
    """Current time as ISO-8601 UTC string with trailing 'Z'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row_to_dict(
    row: sqlite3.Row | None,
    json_fields: tuple[str, ...] = (),
) -> dict | None:
    """Convert a sqlite3.Row into a dict, decoding listed columns as JSON.

    Returns None when row is None. For each name in ``json_fields``, if the
    column is present and truthy, its string value is parsed with json.loads.
    """
    if row is None:
        return None
    d = dict(row)
    for field in json_fields:
        if d.get(field):
            d[field] = json.loads(d[field])
    return d


class RevisionConflict(Exception):
    """Base class for optimistic-concurrency revision mismatches.

    Subclasses carry more specific semantics (e.g. character vs lore) but
    callers may also catch ``RevisionConflict`` for generic handling.
    """
