"""Unit tests for infra.studio_batch_streamer SSE publisher (Phase 24).

Covers publish/subscribe/unsubscribe fan-out, queue cap (drop oldest),
and the SSE event serialization contract.
"""

import asyncio
import json

import pytest

from infra import studio_batch_streamer
from infra.studio_batch_streamer import publish, subscribe, unsubscribe

JOB = "job-test-123"


@pytest.fixture(autouse=True)
def _reset_registry():
    """Isolate the module-level subscriber registry between tests."""
    studio_batch_streamer._SUBSCRIBERS.clear()
    yield
    studio_batch_streamer._SUBSCRIBERS.clear()


def _payloads(queue: asyncio.Queue, count: int) -> list[dict]:
    """Drain ``count`` SSE messages from ``queue``, returning parsed data payloads."""
    rows = []
    for _ in range(count):
        data = queue.get_nowait().decode("utf-8")
        line = next(line for line in data.splitlines() if line.startswith("data: "))
        rows.append(json.loads(line[len("data: ") :]))
    return rows


def test_publish_with_no_subscribers_is_noop():
    """publish() to a job with no subscribers must not raise and must not fan out."""
    publish(JOB, "job_state", {"status": "running"})
    assert JOB not in studio_batch_streamer._SUBSCRIBERS


@pytest.mark.asyncio
async def test_subscribe_creates_queue_and_receives_published_events():
    queue = subscribe(JOB)
    assert queue in studio_batch_streamer._SUBSCRIBERS[JOB]

    publish(JOB, "job_state", {"status": "running"})
    data = (await asyncio.wait_for(queue.get(), timeout=1.0)).decode("utf-8")

    assert "event: job_state" in data
    assert '"status": "running"' in data


@pytest.mark.asyncio
async def test_publish_to_multiple_subscribers_fans_out():
    queue_a = subscribe(JOB)
    queue_b = subscribe(JOB)

    publish(JOB, "chapter_completed", {"chapter_num": 3})

    data_a = await asyncio.wait_for(queue_a.get(), timeout=1.0)
    data_b = await asyncio.wait_for(queue_b.get(), timeout=1.0)
    assert data_a == data_b


@pytest.mark.asyncio
async def test_unsubscribe_removes_subscriber():
    keep = subscribe(JOB)
    drop = subscribe(JOB)

    unsubscribe(JOB, drop)
    assert drop not in studio_batch_streamer._SUBSCRIBERS[JOB]
    assert keep in studio_batch_streamer._SUBSCRIBERS[JOB]

    unsubscribe(JOB, keep)
    assert JOB not in studio_batch_streamer._SUBSCRIBERS


@pytest.mark.asyncio
async def test_queue_overflow_drops_oldest():
    queue = subscribe(JOB)
    for seq in range(101):  # cap is 100 → the oldest event must be dropped
        publish(JOB, "job_state", {"seq": seq})

    payloads = _payloads(queue, 100)
    assert payloads[0]["seq"] == 1  # seq 0 was dropped for overflow
    assert payloads[-1]["seq"] == 100
    assert queue.qsize() == 0
