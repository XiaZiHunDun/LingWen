"""In-process async publisher for illustration notification SSE (Phase 99).

Mirrors lingwen_studio_batch_streamer pattern (Phase 24). In-memory subscriber
registry keyed by project_slug. publish() is non-blocking, fire-and-forget.

I091 (Phase 99): publish() is the only fan-out entry point for illustration
events. record_event (I090) remains audit_log's source of truth. pipeline and
cleanup_route call BOTH (record_event first for durability, publish second
for fan-out) with the SAME id (ULID).
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

import ulid

EventType = Literal["generation", "regeneration", "cleanup", "deletion"]


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


# In-process subscriber registry. Keyed by project_slug.
_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}
_MAX_QUEUE = 100


def subscribe(project_slug: str) -> asyncio.Queue:
    """Register a new subscriber queue for project_slug."""
    q: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
    _SUBSCRIBERS.setdefault(project_slug, []).append(q)
    return q


def unsubscribe(project_slug: str, q: asyncio.Queue) -> None:
    """Remove the subscriber holding q from project_slug's registry."""
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


__all__ = [
    "NotificationEvent",
    "EventType",
    "subscribe",
    "unsubscribe",
    "publish",
    "format_event",
    "new_event_id",
    "now_iso",
]
