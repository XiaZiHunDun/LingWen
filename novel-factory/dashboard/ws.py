"""
Dashboard WebSocket support (Phase 6.4).

设计:
- ConnectionManager 管理活跃 WS 连接
- start_broadcast_task 后台 1s 轮询 controller 状态变化并 broadcast
- broadcast 事件类型:
  - connected (握手,推初始 snapshot)
  - workflow.status (active workflow 状态变化)
  - decision.snapshot (pending decisions 列表变化)
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import WebSocket

from dashboard.protocols import MasterControllerLike

logger = logging.getLogger(__name__)


# === Event types ===

EVENT_CONNECTED = "connected"
EVENT_WORKFLOW_STATUS = "workflow.status"
EVENT_DECISION_SNAPSHOT = "decision.snapshot"

POLL_INTERVAL_SECONDS = 1.0


class ConnectionManager:
    """WebSocket 连接管理器

    Thread-safe-ish (asyncio 单线程,但 broadcast 跨 await)
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("ws connected (total=%d)", len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        logger.info("ws disconnected (total=%d)", len(self._connections))

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """向所有 client 发送 event,失败 client 自动清理"""
        if not self._connections:
            return
        # 复制避免迭代时变
        async with self._lock:
            targets = list(self._connections)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception as e:
                logger.warning("ws broadcast failed, removing: %s", e)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    async def send_to(self, ws: WebSocket, event: dict[str, Any]) -> None:
        """单发(握手时用)"""
        try:
            await ws.send_json(event)
        except Exception as e:
            logger.warning("ws send_to failed: %s", e)
            await self.disconnect(ws)


def _events_equal(a: Any, b: Any) -> bool:
    """简单 deep-equal 用来检测 state 变化"""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(_events_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_events_equal(x, y) for x, y in zip(a, b))
    return a == b


async def start_broadcast_task(
    manager: ConnectionManager,
    controller: MasterControllerLike,
    stop_event: Optional[asyncio.Event] = None,
    poll_interval: float = POLL_INTERVAL_SECONDS,
) -> asyncio.Task:
    """启动后台任务:轮询 controller 状态,broadcast 变化

    Args:
        manager: ConnectionManager 实例
        controller: MasterControllerLike 实例
        stop_event: 外部信号 (设置后任务退出);None 则用 asyncio.create_task 内部 cancel
        poll_interval: 轮询间隔(秒),默认 1.0

    Returns:
        asyncio.Task 句柄
    """
    return asyncio.create_task(
        _broadcast_loop(manager, controller, stop_event, poll_interval)
    )


async def _broadcast_loop(
    manager: ConnectionManager,
    controller: MasterControllerLike,
    stop_event: Optional[asyncio.Event],
    poll_interval: float,
) -> None:
    """轮询 + broadcast 循环

    状态用 controller.get_active_workflow_status() / list_pending_decisions()
    比较 cache,变化时 broadcast。
    """
    last_workflow: Optional[dict] = None
    last_decisions: Optional[list] = None

    logger.info("ws broadcast task started (interval=%.1fs)", poll_interval)
    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                logger.info("ws broadcast task stopped by event")
                return
            try:
                cur_workflow = controller.get_active_workflow_status()
                cur_decisions = controller.list_pending_decisions()
            except Exception as e:
                logger.warning("ws poll controller failed: %s", e)
                await asyncio.sleep(poll_interval)
                continue

            if last_workflow is None or not _events_equal(last_workflow, cur_workflow):
                await manager.broadcast({
                    "type": EVENT_WORKFLOW_STATUS,
                    "payload": cur_workflow,
                })
                last_workflow = cur_workflow

            if last_decisions is None or not _events_equal(last_decisions, cur_decisions):
                await manager.broadcast({
                    "type": EVENT_DECISION_SNAPSHOT,
                    "payload": cur_decisions,
                })
                last_decisions = cur_decisions

            await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
        logger.info("ws broadcast task cancelled")
        raise
