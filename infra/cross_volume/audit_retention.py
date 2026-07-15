"""Phase 9.61 F52: ripple_audit retention / purge helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from infra.cross_volume.cascade_retention import PurgeResult, parse_older_than

__all__ = ["PurgeResult", "parse_older_than", "purge_audit_entries_older_than"]


def purge_audit_entries_older_than(
    storage, older_than: timedelta, *, execute: bool
) -> PurgeResult:
    """Count or delete ripple_audit rows with created_at older than cutoff."""
    cutoff = datetime.now(timezone.utc) - older_than
    cutoff_iso = cutoff.isoformat()
    matched = storage.count_audit_entries_created_before(cutoff_iso)
    deleted = 0
    if execute and matched:
        deleted = storage.delete_audit_entries_created_before(cutoff_iso)
    return PurgeResult(
        older_than=_format_timedelta(older_than),
        cutoff_iso=cutoff_iso,
        matched=matched,
        deleted=deleted,
        executed=execute,
    )


def _format_timedelta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds % 86400 == 0:
        return f"{total_seconds // 86400}d"
    if total_seconds % 3600 == 0:
        return f"{total_seconds // 3600}h"
    return f"{total_seconds // 60}m"
