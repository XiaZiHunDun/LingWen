import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lingwen_storage.events.jsonl_store import JsonlStore, WorkflowEvent


def test_append_and_load(tmp_path: Path):
    """An event appended to a fresh store can be loaded back."""
    store = JsonlStore(tmp_path / "events.jsonl")
    e = WorkflowEvent(
        event_id="01J00000000000000000000000",
        occurred_at=datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc),
        step="STEP_00",
        actor="system",
        correlation_id="c-1",
        payload={"k": "v"},
    )
    store.append(e)
    events = list(store.iter())
    assert len(events) == 1
    assert events[0].event_id == e.event_id
    assert events[0].payload == {"k": "v"}


def test_unicode_payload(tmp_path: Path):
    """Non-ASCII characters in payload are preserved (UTF-8)."""
    store = JsonlStore(tmp_path / "events.jsonl")
    e = WorkflowEvent(
        event_id="01J00000000000000000000001",
        occurred_at=datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc),
        step="STEP_00",
        actor="system",
        correlation_id="c-1",
        payload={"chapter_title": "灵文纪元", "emoji": "🎉"},
    )
    store.append(e)
    events = list(store.iter())
    assert events[0].payload["chapter_title"] == "灵文纪元"
    assert events[0].payload["emoji"] == "🎉"


def test_multiple_events_preserved(tmp_path: Path):
    """Multiple events appended in order are loaded in order."""
    store = JsonlStore(tmp_path / "events.jsonl")
    for i in range(5):
        store.append(
            WorkflowEvent(
                event_id=f"01J0000000000000000000000{i}",
                occurred_at=datetime(2026, 8, 9, 12, 0, i, tzinfo=timezone.utc),
                step="STEP_00",
                actor="system",
                correlation_id=f"c-{i}",
                payload={"i": i},
            )
        )
    events = list(store.iter())
    assert len(events) == 5
    assert [e.payload["i"] for e in events] == [0, 1, 2, 3, 4]


def test_iter_empty_store(tmp_path: Path):
    """An empty (just-created) store yields no events."""
    store = JsonlStore(tmp_path / "events.jsonl")
    assert list(store.iter()) == []


def test_iter_missing_file(tmp_path: Path):
    """Iterating over a path that doesn't exist returns empty."""
    store = JsonlStore(tmp_path / "does-not-exist.jsonl")
    assert list(store.iter()) == []


def test_reload_from_existing_file(tmp_path: Path):
    """A new JsonlStore instance can read events written by another."""
    path = tmp_path / "events.jsonl"
    store1 = JsonlStore(path)
    store1.append(
        WorkflowEvent(
            event_id="01J00000000000000000000001",
            occurred_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
            step="STEP_12",
            actor="writer-a",
            correlation_id="ch001",
            payload={"chapter_id": "ch001"},
        )
    )
    store2 = JsonlStore(path)
    events = list(store2.iter())
    assert len(events) == 1
    assert events[0].step == "STEP_12"


def test_file_created_in_nonexistent_directory(tmp_path: Path):
    """The store creates parent directories as needed."""
    nested = tmp_path / "deeply" / "nested" / "events.jsonl"
    store = JsonlStore(nested)
    e = WorkflowEvent(
        event_id="01J00000000000000000000001",
        occurred_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
        step="STEP_00",
        actor="system",
        correlation_id="c-1",
        payload={},
    )
    store.append(e)
    assert nested.exists()


def test_append_is_durable(tmp_path: Path):
    """After append, the data is on disk (not just buffered)."""
    store = JsonlStore(tmp_path / "events.jsonl")
    e = WorkflowEvent(
        event_id="01J00000000000000000000001",
        occurred_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
        step="STEP_00",
        actor="system",
        correlation_id="c-1",
        payload={"durable": True},
    )
    store.append(e)
    # Read raw bytes from disk
    content = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "durable" in content
    assert "true" in content
