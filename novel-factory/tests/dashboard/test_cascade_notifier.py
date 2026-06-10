"""Phase 9.16: dashboard/cascade_notifier.py async-broadcast fix + helper tests.

Spec: 2026-06-10-phase9.16-cascade-weighted-realtime-design.md (commit 4fc7ed0).
Plan: 2026-06-10-phase9.16-cascade-weighted-realtime.md (commit 5a47f27).

T3 暴露: 既有实现 sync 调 _ws_manager(envelope), 但 ConnectionManager.broadcast
是 async def → coroutine 丢弃, 推送永不生效 (e2e test 通过仅因绕开 broken
broadcast 直接调 dev-mode handler). 修复: 跟 dashboard/cvg_ws.broadcast
1:1 (asyncio.ensure_future if loop running else run_until_complete), 加
pytest-asyncio RED test 覆盖。
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from dashboard import cascade_notifier


@pytest.fixture(autouse=True)
def _reset_ws_manager():
    """Each test starts with a clean module-level singleton."""
    cascade_notifier.set_ws_manager(None)
    yield
    cascade_notifier.set_ws_manager(None)


def _make_async_mock_ws() -> AsyncMock:
    """AsyncMock for ConnectionManager.broadcast (跟 test_cvg_ws 1:1)."""
    return AsyncMock()


class TestCascadeNotifierAsyncBroadcast:
    """T3 fix RED test: notify_cascade_update 必须 await async broadcast."""

    def test_notify_awaits_async_broadcast(self):
        """notify_cascade_update 必须真的 await async broadcast (不能丢弃 coroutine).

        RED 当前: 同步调 _ws_manager(envelope) → coroutine 丢弃 → side_effect
        永不执行, list 永远空. 修复后 (asyncio.ensure_future / loop detection):
        coroutine scheduled, side_effect 真正执行, list 收到 envelope.
        """
        side_effect_calls: list[dict] = []

        async def _async_broadcast(envelope: dict) -> None:
            side_effect_calls.append(envelope)

        mock_ws = AsyncMock(side_effect=_async_broadcast)
        cascade_notifier.set_ws_manager(mock_ws)

        async def _run():
            cascade_notifier.notify_cascade_update(
                {
                    "ripple_id": "r1",
                    "cascade_node_count": 3,
                    "cascade_edge_count": 2,
                    "depth_reached": 2,
                    "bfs_algorithm_version": "v2_weighted",
                }
            )
            # Allow scheduled task to complete
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        asyncio.run(_run())

        # broadcast side_effect 真的执行了 (不是仅仅被调)
        assert len(side_effect_calls) == 1, (
            f"async broadcast never awaited; side_effect_calls={side_effect_calls}"
        )
        envelope = side_effect_calls[0]
        assert envelope["type"] == "cascade.update"
        assert envelope["payload"]["ripple_id"] == "r1"

    def test_notify_skips_when_ws_manager_none(self):
        """无 ws_manager 注入 → logger.debug skip, 不抛错 (跟 cvg_ws 1:1)."""
        # No set_ws_manager call → _ws_manager is None
        cascade_notifier.notify_cascade_update({"ripple_id": "r1"})
        # No exception, no log error (verified via no throw)

    def test_notify_swallows_broadcast_exception(self):
        """broadcast 抛错 → logger.warning 不 propagate (跟 9.14 record_audit 1:1)."""
        mock_ws = MagicMock(side_effect=RuntimeError("connection closed"))
        cascade_notifier.set_ws_manager(mock_ws)

        # Should not raise (best-effort)
        cascade_notifier.notify_cascade_update({"ripple_id": "r1"})

    def test_envelope_shape_matches_spec(self):
        """Envelope format: {type: 'cascade.update', payload: {ripple_id, ...}} 1:1 spec."""
        captured: list[dict] = []

        def _capture_sync(envelope: dict) -> None:
            captured.append(envelope)

        cascade_notifier.set_ws_manager(_capture_sync)
        cascade_notifier.notify_cascade_update(
            {
                "ripple_id": "r42",
                "cascade_node_count": 5,
                "cascade_edge_count": 4,
                "depth_reached": 3,
                "bfs_algorithm_version": "v2_weighted",
            }
        )
        # Sync mock: no loop needed, call happens immediately
        assert len(captured) == 1
        assert captured[0]["type"] == "cascade.update"
        assert captured[0]["payload"]["ripple_id"] == "r42"
        assert captured[0]["payload"]["bfs_algorithm_version"] == "v2_weighted"
