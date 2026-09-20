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
- record_failure(project_slug, error, *, project_root, threshold) — caller passes
  both project_root + threshold so notifications module stays yaml-free
- record_success(project_slug) — resets counter
- Threshold crossing emits 1 severity=warning notification; counter stays
  elevated until record_success() resets it (sustained-failure visibility)
"""
from __future__ import annotations

import asyncio
import json
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

# Phase 102: consecutive failure counter (in-memory, lost on restart — Phase 99 trade-off).
# I095: only record_failure/record_success may mutate these dicts.
_consecutive_failures: dict[str, int] = {}
# Tracks whether we have already emitted a threshold warning for the current
# sustained-failure window. Reset to False by record_success() so the next
# failure streak can warn again.
_warning_emitted: dict[str, bool] = {}


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


# Phase 102 I095: record_failure / record_success — _consecutive_failures state machine.
# Caller (pipeline) passes project_root + threshold so notifications module stays yaml-free,
# consistent with audit_log.record_event signature (pipeline knows project_root + has
# already loaded settings).


def record_failure(
    project_slug: str,
    error: BaseException,
    *,
    project_root: Path,
    threshold: int,
) -> None:
    """Increment consecutive failure counter; emit warning when count >= threshold.

    Idempotent on threshold crossing: after warning emit, does NOT reset counter.
    Counter stays elevated until record_success() is called. This surfaces a
    sustained-failure pattern to the user without spamming them.

    Caller pattern (in pipeline.dispatch_with_fallback):
        settings = _load_illustration_settings(project_root)
        threshold = settings.get("notify_threshold", 3)
        try:
            ... attempt ...
        except Exception as e:
            notifications.record_failure(
                slug, e, project_root=project_root, threshold=threshold,
            )
            raise
        else:
            notifications.record_success(slug)
    """
    _consecutive_failures[project_slug] = _consecutive_failures.get(project_slug, 0) + 1
    count = _consecutive_failures[project_slug]
    if count >= threshold and not _warning_emitted.get(project_slug, False):
        _warning_emitted[project_slug] = True
        _emit_failure_warning(project_slug, count, error, project_root)


def record_success(project_slug: str) -> None:
    """Reset counter to 0 on any successful illustration event.

    Called from pipeline on successful generation/regeneration.
    No project_root needed — counter state is in-memory only.
    """
    _consecutive_failures[project_slug] = 0
    _warning_emitted[project_slug] = False


def _emit_failure_warning(
    project_slug: str,
    count: int,
    error: BaseException,
    project_root: Path,
) -> None:
    """Emit severity=warning notification; ULID shared with audit_log (I091 invariant)."""
    event_id = str(ulid.ULID())
    audit_log.record_event(
        project_root,
        event="generation",
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
        event_type="generation",
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
]
