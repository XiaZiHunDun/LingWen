"""In-process async event publisher for batch job SSE streams (Phase 24).

Design:
- module-level, in-memory subscriber registry keyed by ``job_id``
- ``publish`` is a non-blocking, fire-and-forget fan-out to that job's subscribers
- each subscriber holds an ``asyncio.Queue`` (cap ``_MAX_QUEUE`` events, drop oldest
  on overflow) so a slow SSE consumer never back-pressures the batch runner

Lifecycle is owned by the caller/route:
- ``subscribe(job_id) -> queue`` creates subscriber before streaming
- ``unsubscribe(job_id, queue)`` must be called in the generator's ``finally``
- ``format_event`` + terminal helpers mirror the canonical SSE event schema
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

# Canonical SSE event types (Phase 24 design section 2.2).
EVENT_JOB_STATE = "job_state"
EVENT_CHAPTER_STARTED = "chapter_started"
EVENT_CHAPTER_COMPLETED = "chapter_completed"
EVENT_JOB_COMPLETED = "job_completed"
EVENT_JOB_FAILED = "job_failed"
EVENT_JOB_CANCELLED = "job_cancelled"

KNOWN_EVENT_TYPES = frozenset(
    {
        EVENT_JOB_STATE,
        EVENT_CHAPTER_STARTED,
        EVENT_CHAPTER_COMPLETED,
        EVENT_JOB_COMPLETED,
        EVENT_JOB_FAILED,
        EVENT_JOB_CANCELLED,
    }
)

_TERMINAL_EVENTS = frozenset({EVENT_JOB_COMPLETED, EVENT_JOB_FAILED, EVENT_JOB_CANCELLED})

# Per-job subscriber registry: job_id -> list[_Subscriber].
_SUBSCRIBERS: dict[str, list["_Subscriber"]] = {}

# Cap per-queue buffered events to prevent unbounded growth.
_MAX_QUEUE = 100


class _Subscriber:
    """A single SSE subscriber — one asyncio.Queue plus an optional event filter.

    ``event_types`` is ``None`` (deliver everything) or a frozen set of the event
    types this subscriber is willing to receive (Phase 25 server-side filter).
    """

    __slots__ = ("queue", "event_types")

    def __init__(self, queue: asyncio.Queue, event_types: frozenset[str] | None) -> None:
        self.queue = queue
        self.event_types = event_types


def _normalize_filter(event_types) -> frozenset[str] | None:
    """Collapse an event-type iterable to a frozen set; ``None``/empty means "all"."""
    if event_types is None:
        return None
    normalized = frozenset(event_types)
    return normalized or None


def format_event(event_type: str, payload: dict[str, Any]) -> bytes:
    """Serialize an event as one SSE message (``event:`` + ``data:`` frame)."""
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


def is_terminal_event(event_type: str) -> bool:
    return event_type in _TERMINAL_EVENTS


def subscribe(job_id: str, event_types=None) -> asyncio.Queue:
    """Create a new subscriber queue for ``job_id`` and return it.

    ``event_types`` optionally restricts what this subscriber receives: a list of
    event type names. ``None``/empty means deliver all events (Phase 24 behavior).
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
    _SUBSCRIBERS.setdefault(job_id, []).append(_Subscriber(queue, _normalize_filter(event_types)))
    return queue


def unsubscribe(job_id: str, queue: asyncio.Queue) -> None:
    """Remove the subscriber holding ``queue`` from ``job_id``; drop empty jobs."""
    subscribers = _SUBSCRIBERS.get(job_id)
    if not subscribers:
        return
    try:
        for index, subscriber in enumerate(subscribers):
            if subscriber.queue is queue:
                del subscribers[index]
                break
    except ValueError:
        pass
    if not subscribers:
        _SUBSCRIBERS.pop(job_id, None)


def publish(job_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Non-blocking fire-and-forget publish to every subscriber of ``job_id``.

    Subscribers whose ``event_types`` filter excludes ``event_type`` are skipped.
    Subscribers whose queue is full have their oldest event dropped so the
    newest state always flows through.
    """
    subscribers = _SUBSCRIBERS.get(job_id)
    if not subscribers:
        return  # no subscribers; nothing to do
    data = format_event(event_type, payload)
    for subscriber in list(subscribers):
        event_types = subscriber.event_types
        if event_types is not None and event_type not in event_types:
            continue  # subscriber does not want this event type
        queue = subscriber.queue
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            # Drop oldest, enqueue newest (keep the freshest state marching on).
            try:
                queue.get_nowait()
                queue.put_nowait(data)
            except Exception:
                pass
