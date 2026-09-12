"""lingwen-studio-batch-streamer — canonical studio batch SSE streamer package.

Phase 47 P3-ARCHDEBT: relocated from infra/studio_batch_streamer.py (131 LOC).
TRUE LEAF (0 workspace deps; stdlib only).
"""

from __future__ import annotations

from lingwen_studio_batch_streamer.service import (
    EVENT_CHAPTER_COMPLETED,
    EVENT_CHAPTER_STARTED,
    EVENT_JOB_CANCELLED,
    EVENT_JOB_COMPLETED,
    EVENT_JOB_FAILED,
    EVENT_JOB_STATE,
    KNOWN_EVENT_TYPES,
    format_event,
    is_terminal_event,
    publish,
    subscribe,
    unsubscribe,
)

__all__ = [
    # Event type constants
    "EVENT_JOB_STATE",
    "EVENT_CHAPTER_STARTED",
    "EVENT_CHAPTER_COMPLETED",
    "EVENT_JOB_COMPLETED",
    "EVENT_JOB_FAILED",
    "EVENT_JOB_CANCELLED",
    "KNOWN_EVENT_TYPES",
    # Public functions
    "format_event",
    "is_terminal_event",
    "subscribe",
    "unsubscribe",
    "publish",
]