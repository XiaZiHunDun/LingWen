"""Phase 9.45 F34: cascade_runs retention / purge helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

_OLDER_THAN_RE = re.compile(r"^(\d+)([dDhHmM])$")


@dataclass(frozen=True)
class PurgeResult:
    older_than: str
    cutoff_iso: str
    matched: int
    deleted: int
    executed: bool


def parse_older_than(spec: str) -> timedelta:
    """Parse duration like 90d, 12h, 30m."""
    text = spec.strip()
    match = _OLDER_THAN_RE.match(text)
    if not match:
        raise ValueError(
            f"invalid --older-than {spec!r} (expected e.g. 90d, 12h, 30m)"
        )
    amount = int(match.group(1))
    if amount < 1:
        raise ValueError(f"--older-than must be >= 1, got {amount}")
    unit = match.group(2).lower()
    if unit == "d":
        return timedelta(days=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    raise ValueError(f"unsupported duration unit in {spec!r}")


def purge_cascade_runs_older_than(storage, older_than: timedelta, *, execute: bool) -> PurgeResult:
    """Count or delete cascade_runs with started_at older than cutoff."""
    cutoff = datetime.now(timezone.utc) - older_than
    cutoff_iso = cutoff.isoformat()
    matched = storage.count_cascade_runs_started_before(cutoff_iso)
    deleted = 0
    if execute and matched:
        deleted = storage.delete_cascade_runs_started_before(cutoff_iso)
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
