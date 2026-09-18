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
) -> None:
    """Append JSONL event. Best-effort: OSError silently swallowed.

    Args:
        project_root: Project root path.
        event: Event type (generation/regeneration/cleanup/deletion).
        asset_meta: Optional asset metadata for ID/type/chapter_num capture.
        confirmed: Whether user confirmed the action (None if N/A).
        bypassed: Whether confirmation was required but skipped.
        extra: Additional context fields merged into the JSONL record.
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
    target = _audit_path(project_root)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass  # best-effort, never raise


__all__ = ["EventType", "record_event"]
