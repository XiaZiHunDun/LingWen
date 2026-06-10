"""Phase 9.13: CVG WebSocket support — CvgConnectionManager + broadcast helper.

Mirror dashboard/ws.py::ConnectionManager 1:1, 专用 CVG 实时推送 (跟 /api/ws/workflows
1:1 被动模式, 0 background poll task, CVG 事件 push-only).

事件类型 (Spec 4.2.3):
- ripple_created: 新 ripple 写入 RippleStorage (Phase 9.11/9.12 CLI trigger)
- ripple_status_changed: apply/reject 状态变化
- pong: heartbeat reply (跟 /api/ws/workflows 1:1, client send ping)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

EVENT_RIPPLE_CREATED = "ripple_created"
EVENT_RIPPLE_STATUS_CHANGED = "ripple_status_changed"
EVENT_PONG = "pong"

# Module-level singleton manager (跟 useWorkflowSocket module-level 1:1)
_manager: "CvgConnectionManager | None" = None


def _get_manager() -> "CvgConnectionManager":
    global _manager
    if _manager is None:
        _manager = CvgConnectionManager()
    return _manager


def broadcast(event: dict[str, Any]) -> None:
    """Module-level broadcast helper (storage layer lazy import 用).

    Synchronous wrapper around async manager.broadcast (asyncio.ensure_future
    if loop running, else schedule directly). 跟 Phase 9.13 storage
    _broadcast_ripple_event 1:1 — broadcast failure 永不 throw.
    """
    try:
        manager = _get_manager()
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast(event))
        else:
            loop.run_until_complete(manager.broadcast(event))
    except Exception as e:  # noqa: BLE001
        logger.debug("cvg broadcast skipped: %s", e)


class CvgConnectionManager:
    """Phase 9.13: WebSocket 连接管理器 (CVG 专用).

    跟 dashboard.ws.ConnectionManager 1:1 mirror: 3 method (connect/disconnect/
    broadcast) + 1 helper (send_to) + connection_count property. 无 background
    poll task (CVG 事件 push-only, 跟 /api/ws/workflows 1:1 passive 模式).
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("cvg ws connected (total=%d)", len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        logger.info("cvg ws disconnected (total=%d)", len(self._connections))

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """向所有 client 发送 event, 失败 client 自动清理 (跟 ConnectionManager 1:1)."""
        if not self._connections:
            return
        # 复制避免迭代时变
        async with self._lock:
            targets = list(self._connections)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception as e:  # noqa: BLE001
                logger.warning("cvg ws broadcast failed, removing: %s", e)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    async def send_to(self, ws: WebSocket, event: dict[str, Any]) -> None:
        """单发(握手时用, 跟 ConnectionManager.send_to 1:1)."""
        try:
            await ws.send_json(event)
        except Exception as e:  # noqa: BLE001
            logger.warning("cvg ws send_to failed: %s", e)
            await self.disconnect(ws)
