"""Unit tests for lingwen_illustrations.notifications (Phase 99).

Covers:
- subscribe/unsubscribe lifecycle
- format_event SSE wire format
- queue-full drop-oldest
- ULID monotonic
- publish 0-subscribers no-op
- NotificationEvent dataclass
- project_slug isolation
"""
from __future__ import annotations

import asyncio
import json
import re

import pytest

from lingwen_illustrations import notifications
from lingwen_illustrations.notifications import (
    NotificationEvent,
    EventType,
    format_event,
    new_event_id,
    publish,
    subscribe,
    unsubscribe,
)


def _make_event(project_slug: str = "星陨纪元", **overrides) -> NotificationEvent:
    base = dict(
        id=new_event_id(),
        project_slug=project_slug,
        event_type="generation",
        asset_id="ch12-cover-v3",
        asset_type="cover",
        chapter_num=None,
        style_preset="水墨写意",
        provider="minimax",
        ts="2026-09-18T07:12:34.567890+00:00",
        extra={"auto_generate": True},
    )
    base.update(overrides)
    return NotificationEvent(**base)


def test_publish_with_zero_subscribers_is_noop() -> None:
    """publish() must not raise when no subscriber exists for the project."""
    event = _make_event()
    publish(event)


def test_subscribe_returns_queue_and_unsubscribe_removes_it() -> None:
    slug = "project-A"
    q = subscribe(slug)
    assert isinstance(q, asyncio.Queue)
    unsubscribe(slug, q)
    event = _make_event(project_slug=slug)
    publish(event)
    assert q.empty()


def test_publish_delivers_to_subscriber_queue() -> None:
    slug = "project-B"
    q = subscribe(slug)
    try:
        event = _make_event(project_slug=slug, asset_id="abc")
        publish(event)
        assert not q.empty()
        data = q.get_nowait()
        assert isinstance(data, bytes)
        text = data.decode("utf-8")
        assert text.startswith("event: generation\ndata: ")
        assert text.endswith("\n\n")
        payload_str = text.removeprefix("event: generation\ndata: ").removesuffix("\n\n")
        payload = json.loads(payload_str)
        assert payload["asset_id"] == "abc"
        assert payload["project_slug"] == slug
    finally:
        unsubscribe(slug, q)


def test_publish_drops_oldest_when_queue_full() -> None:
    slug = "project-C"
    q = asyncio.Queue(maxsize=2)
    notifications._SUBSCRIBERS.setdefault(slug, []).append(q)
    try:
        e1 = _make_event(project_slug=slug, id="01HZX7K0000000000000000000")
        e2 = _make_event(project_slug=slug, id="01HZX7K0000000000000000001")
        e3 = _make_event(project_slug=slug, id="01HZX7K0000000000000000002")
        publish(e1)
        publish(e2)
        publish(e3)
        assert q.qsize() == 2
        first = json.loads(q.get_nowait().decode("utf-8").removeprefix("event: generation\ndata: ").removesuffix("\n\n"))
        assert first["id"] == "01HZX7K0000000000000000001"
        second = json.loads(q.get_nowait().decode("utf-8").removeprefix("event: generation\ndata: ").removesuffix("\n\n"))
        assert second["id"] == "01HZX7K0000000000000000002"
    finally:
        notifications._SUBSCRIBERS.pop(slug, None)


def test_publish_isolates_per_project_slug() -> None:
    slug_a = "project-D"
    slug_b = "project-E"
    qa = subscribe(slug_a)
    qb = subscribe(slug_b)
    try:
        event_a = _make_event(project_slug=slug_a)
        publish(event_a)
        assert not qa.empty()
        assert qb.empty()
        qa.get_nowait()
    finally:
        unsubscribe(slug_a, qa)
        unsubscribe(slug_b, qb)


def test_format_event_emits_sse_wire_format() -> None:
    event = _make_event(asset_id="x1")
    data = format_event(event)
    assert isinstance(data, bytes)
    text = data.decode("utf-8")
    assert text.startswith(f"event: {event.event_type}\n")
    assert "data: " in text
    assert text.endswith("\n\n")


def test_new_event_id_is_ulid_string_and_monotonic() -> None:
    id1 = new_event_id()
    id2 = new_event_id()
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert len(id1) == 26
    assert id1 < id2
    ulid_pattern = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
    assert ulid_pattern.match(id1)
    assert ulid_pattern.match(id2)


def test_notification_event_is_frozen() -> None:
    event = _make_event()
    with pytest.raises(Exception):
        event.asset_id = "tampered"


def test_event_type_literal_includes_all_four() -> None:
    from typing import get_args
    values = get_args(EventType)
    assert set(values) == {"generation", "regeneration", "cleanup", "deletion"}