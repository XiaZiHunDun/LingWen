"""Phase 9.13: WebSocket /api/ws/cvg + CvgConnectionManager (跟 /api/ws/workflows 1:1).

Spec 4.2.3: 3 message types (ripple_created / ripple_status_changed / pong).
Mirror dashboard/ws.py::ConnectionManager 1:1, 但 CVG 专用 + 0 background poll
(CVG 事件 push-only, 跟 /api/ws/workflows 1:1 passive 模式).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from dashboard.app import create_app
from dashboard.cvg_ws import (
    EVENT_PONG,
    EVENT_RIPPLE_CREATED,
    EVENT_RIPPLE_STATUS_CHANGED,
    CvgConnectionManager,
    broadcast,
)
from infra.cross_volume.storage import RippleStorage


def _make_mock_ws() -> MagicMock:
    """Mock WebSocket that records sent JSON in ws.sent (跟 ConnectionManager 测试 1:1).

    accept() + send_json() are async (FastAPI WebSocket), so use AsyncMock for those.
    send_json 的副作用: 同步 append 到 ws.sent 列表,便于 assertion.
    """
    ws = MagicMock(spec=WebSocket)
    ws.sent = []

    async def _send_json_async(event):
        ws.sent.append(event)

    ws.send_json = AsyncMock(side_effect=_send_json_async)
    ws.accept = AsyncMock()
    return ws


# ==================== TestCvgConnectionManager ====================


class TestCvgConnectionManager:
    """CvgConnectionManager 单元测试 (跟 dashboard.ws.ConnectionManager 1:1)."""

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        manager = CvgConnectionManager()
        ws = _make_mock_ws()
        await manager.connect(ws)
        assert ws in manager._connections
        assert manager.connection_count == 1
        await manager.disconnect(ws)
        assert ws not in manager._connections
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_all_connections(self):
        manager = CvgConnectionManager()
        ws1, ws2 = _make_mock_ws(), _make_mock_ws()
        await manager.connect(ws1)
        await manager.connect(ws2)
        event = {"type": "ripple_status_changed", "data": {"ripple_id": "r1"}}
        await manager.broadcast(event)
        assert ws1.sent == [event]
        assert ws2.sent == [event]

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self):
        manager = CvgConnectionManager()
        ws_good = _make_mock_ws()
        ws_dead = _make_mock_ws()
        ws_dead.send_json.side_effect = RuntimeError("connection closed")
        await manager.connect(ws_good)
        await manager.connect(ws_dead)
        await manager.broadcast({"type": "ping", "data": {}})
        assert ws_good in manager._connections
        assert ws_dead not in manager._connections

    @pytest.mark.asyncio
    async def test_send_to_single_connection(self):
        manager = CvgConnectionManager()
        ws = _make_mock_ws()
        await manager.connect(ws)
        event = {"type": "ripple_created", "data": {"ripple_id": "r2"}}
        await manager.send_to(ws, event)
        assert ws.sent == [event]

    def test_event_type_constants(self):
        assert EVENT_RIPPLE_CREATED == "ripple_created"
        assert EVENT_RIPPLE_STATUS_CHANGED == "ripple_status_changed"
        assert EVENT_PONG == "pong"

    def test_broadcast_module_helper_importable(self):
        """Phase 9.13: module-level broadcast() helper (storage layer lazy import 用)."""
        from dashboard import cvg_ws

        assert hasattr(cvg_ws, "broadcast")
        assert callable(cvg_ws.broadcast)
        # 不应抛 (no event loop running 时优雅降级)
        broadcast({"type": "ripple_created", "data": {"ripple_id": "r-test"}})


# ==================== TestCvgWebSocketEndpoint ====================


class TestCvgWebSocketEndpoint:
    """WebSocket /api/ws/cvg endpoint 注册 + 握手测试."""

    def test_ws_endpoint_registered(self, tmp_path, monkeypatch):
        from dashboard import app as app_module

        storage = RippleStorage(db_path=tmp_path / "test.db")
        monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
        app = create_app()
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/ws/cvg" in routes

    def test_ws_cvg_handshake_sends_pong_on_ping(self, tmp_path, monkeypatch):
        from dashboard import app as app_module

        storage = RippleStorage(db_path=tmp_path / "test.db")
        monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
        app = create_app()
        ws_routes = [r for r in app.routes if hasattr(r, "path") and r.path == "/api/ws/cvg"]
        assert len(ws_routes) == 1

    def test_ws_cvg_live_ping_pong(self, tmp_path, monkeypatch):
        """Live WS: client send {type: ping} → server reply {type: pong}."""
        from dashboard import app as app_module

        storage = RippleStorage(db_path=tmp_path / "test.db")
        monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
        app = create_app()
        with TestClient(app) as client:
            with client.websocket_connect("/api/ws/cvg") as ws:
                ws.send_json({"type": "ping"})
                reply = ws.receive_json()
                assert reply == {"type": EVENT_PONG}
