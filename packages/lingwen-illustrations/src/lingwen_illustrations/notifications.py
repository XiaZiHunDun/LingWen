"""In-process async publisher for illustration notification SSE (Phase 99 + Phase 102).

Mirrors lingwen_studio_batch_streamer pattern (Phase 24). In-memory subscriber
registry keyed by project_slug. publish() is non-blocking, fire-and-forget.

I091 (Phase 99): publish() is the only fan-out entry point for illustration
events. record_event (I090) remains audit_log's source of truth. pipeline and
cleanup_route call BOTH (record_event first for durability, publish second
for fan-out) with the SAME id (ULID).

Phase 102 extensions:
- NotificationEvent.severity field ("info" default; "warning" for threshold alerts)
- _consecutive_failures in-memory state machine (I095 invariant)
- record_failure(project_slug, error, *, project_root, threshold, event_type) — caller
  passes project_root + threshold + event_type so notifications module stays yaml-free
- record_success(project_slug, event_type) — resets counter for that (slug, event_type) pair
- Threshold crossing emits 1 severity=warning notification per (slug, event_type) pair;
  counter stays elevated until record_success() resets it (sustained-failure visibility)

Phase 104 extensions:
- _consecutive_failures / _warning_emitted keys widened from str to (str, str) tuple
  (project_slug, event_type). Each event type has independent failure counter.
- record_failure() signature now takes event_type: str kwarg.
- record_success() signature now takes event_type: str positional arg.
- I095 EXTENDED via docstring only — no new invariant introduced.
"""
from __future__ import annotations

import asyncio
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import ulid

from lingwen_illustrations import audit_log  # re-exported for monkeypatch in tests (I095)

EventType = Literal["generation", "regeneration", "cleanup", "deletion"]
Severity = Literal["info", "warning"]  # NEW Phase 102


@dataclass(frozen=True)
class NotificationEvent:
    """One illustration event, used for both SSE push and REST history."""
    id: str
    project_slug: str
    event_type: EventType
    asset_id: str | None
    asset_type: str | None  # "cover" | "chapter" | None
    chapter_num: int | None
    style_preset: str | None
    provider: str | None
    ts: str  # ISO 8601 UTC
    extra: dict[str, Any] | None = None
    severity: Severity = "info"  # NEW Phase 102. "warning" for threshold alerts.


# In-process subscriber registry. Keyed by project_slug.
_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}
_MAX_QUEUE = 100

# Phase 102 + Phase 104: consecutive failure counter (in-memory, lost on restart — Phase 99 trade-off).
# I095 EXTENDED: keys are (project_slug, event_type) tuples, NOT bare project_slug.
# Only record_failure/record_success may mutate these dicts.
_consecutive_failures: dict[tuple[str, str], int] = {}
# Tracks whether we have already emitted a threshold warning for the current
# sustained-failure window per (slug, event_type) pair. Reset to False by
# record_success() so the next failure streak can warn again.
_warning_emitted: dict[tuple[str, str], bool] = {}

# Sentinel for "no warning ever" — partial dict unconfigured keys
# resolve to this in pipeline._resolve_threshold().
INFINITY_THRESHOLD: float = math.inf


def subscribe(project_slug: str) -> asyncio.Queue:
    """Register a new subscriber queue for project_slug."""
    q: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
    _SUBSCRIBERS.setdefault(project_slug, []).append(q)
    return q


def unsubscribe(project_slug: str, q: asyncio.Queue) -> None:
    """Remove subscriber holding q from project_slug's registry."""
    subs = _SUBSCRIBERS.get(project_slug)
    if subs and q in subs:
        subs.remove(q)
        if not subs:
            _SUBSCRIBERS.pop(project_slug, None)


def publish(event: NotificationEvent) -> None:
    """Fire-and-forget fan-out. Drop oldest if queue full."""
    subs = _SUBSCRIBERS.get(event.project_slug)
    if not subs:
        return
    data = format_event(event)
    for q in list(subs):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            try:
                q.get_nowait()
                q.put_nowait(data)
            except Exception:
                pass


def format_event(event: NotificationEvent) -> bytes:
    """Serialize one event as one SSE message."""
    payload = asdict(event)
    return (
        f"event: {event.event_type}\n"
        f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    ).encode("utf-8")


def new_event_id() -> str:
    """Generate a fresh ULID — lexicographically time-sortable, 26 chars."""
    return str(ulid.ULID())


def now_iso() -> str:
    """ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


# Phase 105: _resolve_threshold relocated from pipeline.py. Co-located with the
# counter state machine because the YAML-derived threshold value drives counter
# behavior. Pipeline keeps a back-compat re-export (`pipeline._resolve_threshold`)
# so existing callers and tests are unchanged.
def resolve_threshold(settings: dict, event_type: str) -> int | float:
    """Resolve notify_threshold for specific event_type.

    After Pydantic normalization, settings["notify_threshold"] is dict[str, int]
    where keys are subset of ("generation", "regeneration", "cleanup", "deletion").
    Missing key → INFINITY_THRESHOLD (never warn for that event type).

    Defensive: if int legacy form slips through (shouldn't post-validation),
    returns int directly. If something else (bool, None), returns INFINITY
    to err on the side of "don't warn" rather than crashing callers.

    Phase 104 spec §3. Phase 105 relocated from pipeline.py.
    """
    nt = settings.get("notify_threshold", INFINITY_THRESHOLD)
    if isinstance(nt, bool):
        # bool is subclass of int — exclude truthy acceptance before int check.
        return INFINITY_THRESHOLD
    if isinstance(nt, (int, float)):
        return nt
    if isinstance(nt, dict):
        return nt.get(event_type, INFINITY_THRESHOLD)
    return INFINITY_THRESHOLD  # defensive: non-validated path fallback


# Phase 102 I095: record_failure / record_success — _consecutive_failures state machine.
# Caller (pipeline) passes project_root + threshold so notifications module stays yaml-free,
# consistent with audit_log.record_event signature (pipeline knows project_root + has
# already loaded settings).


def record_failure(
    project_slug: str,
    error: BaseException,
    *,
    project_root: Path | None,
    threshold: int | float,
    event_type: str,
) -> None:
    """Increment consecutive failure counter for (slug, event_type); emit warning when count >= threshold.

    Idempotent on threshold crossing: after warning emit, does NOT reset counter.
    Counter stays elevated until record_success(slug, event_type) is called. This
    surfaces a sustained-failure pattern to the user without spamming them.

    Phase 104: counter keyed per (project_slug, event_type) tuple. Failures in
    different event types do NOT bleed into each other's counters.

    Phase 105: project_root is Path | None. None is allowed when caller cannot
    resolve a real project root (e.g. cleanup_route LoadError on unknown slug).
    audit_log.record_event is skipped when None; publish() still fires for SSE.

    Caller pattern (in pipeline.generate_illustration):
        settings = _load_illustration_settings(project_root)
        threshold = _resolve_threshold(settings, "generation")  # int or inf
        try:
            ... attempt ...
        except Exception as e:
            notifications.record_failure(
                slug, e, project_root=project_root,
                threshold=threshold, event_type="generation",
            )
            raise
        else:
            notifications.record_success(slug, event_type="generation")
    """
    key = (project_slug, event_type)
    _consecutive_failures[key] = _consecutive_failures.get(key, 0) + 1
    count = _consecutive_failures[key]
    if count >= threshold and not _warning_emitted.get(key, False):
        _warning_emitted[key] = True
        _emit_failure_warning(project_slug, count, error, project_root, event_type)


def record_success(project_slug: str, event_type: str) -> None:
    """Reset counter + warning flag for specific (slug, event_type) pair.

    Phase 104: only resets the targeted event_type's counter — other event
    types' counters for the same slug remain unchanged.

    Called from pipeline on successful generation/regeneration.
    No project_root needed — counter state is in-memory only.
    """
    key = (project_slug, event_type)
    _consecutive_failures[key] = 0
    _warning_emitted[key] = False


def _emit_failure_warning(
    project_slug: str,
    count: int,
    error: BaseException,
    project_root: Path | None,
    event_type: str,
) -> None:
    """Emit severity=warning notification; ULID shared with audit_log (I091 invariant).

    Phase 104: event_type passed in (was hardcoded "generation" in Phase 102).
    Phase 105: project_root is Path | None. When None, audit_log.record_event is
    skipped (caller has no real project context, e.g. cleanup_route LoadError on
    missing slug). publish() still fires for SSE fan-out.
    """
    event_id = str(ulid.ULID())
    if project_root is not None:
        audit_log.record_event(
            project_root,
            event=event_type,
            extra={
                "severity": "warning",
                "consecutive_failures": count,
                "last_error": str(error),
                "id": event_id,
            },
        )
    publish(NotificationEvent(
        id=event_id,
        project_slug=project_slug,
        event_type=event_type,
        severity="warning",
        asset_id=None,
        asset_type=None,
        chapter_num=None,
        style_preset=None,
        provider=None,
        ts=now_iso(),
        extra={"consecutive_failures": count, "last_error": str(error)},
    ))


__all__ = [
    "EventType",
    "INFINITY_THRESHOLD",
    "NotificationEvent",
    "Severity",
    "subscribe",
    "unsubscribe",
    "publish",
    "format_event",
    "new_event_id",
    "now_iso",
    "record_failure",
    "record_success",
    "resolve_threshold",  # NEW Phase 105 (relocated from pipeline.py)
]
