"""JSONL append-only illustration event audit (Phase 98).

Layout: <project_root>/.lingwen/illustration_audit.jsonl (one event per line)

Best-effort: audit failures NEVER block generation. The log is for
post-hoc inspection only (e.g. "did user bypass confirm?", "which chapter
has the most cleanup activity?").

Invariants:
- I090 (Phase 98): audit_log.record_event is the only entry point for
  illustration event logging (pipeline / storage call only this).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from lingwen_illustrations.metadata import IllustrationMetadata

EventType = Literal["generation", "regeneration", "cleanup", "deletion"]


def _audit_path(project_root: Path) -> Path:
    return project_root / ".lingwen" / "illustration_audit.jsonl"


def record_event(
    project_root: Path,
    *,
    event: EventType,
    asset_meta: IllustrationMetadata | None = None,
    confirmed: bool | None = None,
    bypassed: bool = False,
    extra: dict | None = None,
    id: str | None = None,  # NEW (Phase 99). None → omit from payload.
) -> None:
    """Append JSONL event. Best-effort: OSError silently swallowed.

    Args:
        project_root: Project root path.
        event: Event type (generation/regeneration/cleanup/deletion).
        asset_meta: Optional asset metadata for ID/type/chapter_num capture.
        confirmed: Whether user confirmed the action (None if N/A).
        bypassed: Whether confirmation was required but skipped.
        extra: Additional context fields merged into the JSONL record.
        id: Optional ULID; when provided, written into payload so SSE+JSONL
            share the same id for since_id reconciliation (Phase 99 I091).
    """
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "asset_id": asset_meta.id if asset_meta else None,
        "asset_type": asset_meta.type if asset_meta else None,
        "chapter_num": asset_meta.chapter_num if asset_meta else None,
        "confirmed": confirmed,
        "bypassed": bypassed,
        **(extra or {}),
    }
    if id is not None:
        payload["id"] = id  # NEW (Phase 99)
    target = _audit_path(project_root)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass  # best-effort, never raise


def read_history(
    project_root: Path,
    *,
    since_id: str | None = None,
    limit: int = 20,
) -> tuple[list[dict], bool]:
    """Parse JSONL audit log, return latest N events newer than since_id.

    Phase 99: returns (events, has_more) where events is sorted most-recent
    first by ULID lexicographic order (= time order), and has_more is True
    if more rows exist beyond limit. Corrupt lines are silently skipped.
    Returns ([], False) if the file does not exist or cannot be read.
    """
    target = _audit_path(project_root)
    if not target.exists():
        return [], False
    rows: list[dict] = []
    try:
        with target.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # corrupt line, skip
                row_id = row.get("id", "")
                if since_id is not None and row_id <= since_id:
                    continue  # older or equal, skip
                rows.append(row)
    except OSError:
        return [], False
    rows.sort(key=lambda r: r.get("id", ""), reverse=True)
    has_more = len(rows) > limit
    return rows[:limit], has_more


__all__ = ["EventType", "record_event", "read_history"]
