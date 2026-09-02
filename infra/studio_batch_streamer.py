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

_TERMINAL_EVENTS = frozenset(
    {EVENT_JOB_COMPLETED, EVENT_JOB_FAILED, EVENT_JOB_CANCELLED}
)

# Per-job subscriber registry: job_id -> list[asyncio.Queue].
_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}

# Cap per-queue buffered events to prevent unbounded growth.
_MAX_QUEUE = 100


def format_event(event_type: str, payload: dict[str, Any]) -> bytes:
    """Serialize an event as one SSE message (``event:`` + ``data:`` frame)."""
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


def is_terminal_event(event_type: str) -> bool:
    return event_type in _TERMINAL_EVENTS


def subscribe(job_id: str) -> asyncio.Queue:
    """Create a new subscriber queue for ``job_id`` and return it."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
    _SUBSCRIBERS.setdefault(job_id, []).append(queue)
    return queue


def unsubscribe(job_id: str, queue: asyncio.Queue) -> None:
    """Remove ``queue`` from ``job_id``'s subscriber list; drop empty jobs."""
    subscribers = _SUBSCRIBERS.get(job_id)
    if not subscribers:
        return
    try:
        subscribers.remove(queue)
    except ValueError:
        pass
    if not subscribers:
        _SUBSCRIBERS.pop(job_id, None)


def publish(job_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Non-blocking fire-and-forget publish to every subscriber of ``job_id``.

    Subscribers whose queue is full have their oldest event dropped so the
    newest state always flows through.
    """
    subscribers = _SUBSCRIBERS.get(job_id)
    if not subscribers:
        return  # no subscribers; nothing to do
    data = format_event(event_type, payload)
    for queue in list(subscribers):
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            # Drop oldest, enqueue newest (keep the freshest state marching on).
            try:
                queue.get_nowait()
                queue.put_nowait(data)
            except Exception:
                pass