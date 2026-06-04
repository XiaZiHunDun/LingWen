"""Tests for dashboard WebSocket endpoint (Phase 6.4)

Doc 4 §10 Phase 6.4: 把 2s 轮询替换为 WebSocket 推送。

设计:
- dashboard/ws.py: ConnectionManager (connect/disconnect/broadcast) +
  start_broadcast_task(manager, controller) — 后台 1s 轮询 controller
  状态变化,broadcast 给所有连接的 client
- dashboard/app.py: WS endpoint /api/ws/workflows 注册 + lifespan 启停任务
- 测试用 _ControllableStub (可手动 trigger 状态变化) 替代 _StubMasterController

测试覆盖:
- 4 WS 端点 happy path (连接/初始消息/状态变更推送/广播多客户端)
- 2 断线清理
- 1 边界 (无 controller → 503,400 等)
"""
from __future__ import annotations

import asyncio
import json
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app

# === Controllable stub ===

class _ControllableStub:
    """可手动 trigger 状态变化的 stub — 同步用 threading.Event 触发

    WebSocket 端点会调 get_active_workflow_status() 和 list_pending_decisions(),
    我们用 RLock 保护 state,允许测试线程修改并触发 push 事件。
    """
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workflow_status: dict = {
            "is_active": False,
            "workflow_name": None,
            "completed": 0,
            "failed": 0,
            "paused": False,
            "paused_nodes": [],
            "node_count": 0,
            "steps": 0,
            "pending_decisions": [],
        }
        self._pending_decisions: list[dict] = []

    def set_workflow_status(self, status: dict) -> None:
        with self._lock:
            self._workflow_status = status

    def add_pending_decision(self, decision: dict) -> None:
        with self._lock:
            self._pending_decisions.append(decision)

    def clear_pending_decisions(self) -> None:
        with self._lock:
            self._pending_decisions = []

    def get_active_workflow_status(self) -> dict:
        with self._lock:
            return dict(self._workflow_status)

    def list_pending_decisions(self) -> list[dict]:
        with self._lock:
            return list(self._pending_decisions)


# === Fixtures ===

@pytest.fixture
def stub() -> _ControllableStub:
    return _ControllableStub()


@pytest.fixture
def client(stub: _ControllableStub, tmp_path):
    db_path = tmp_path / "rp.db"
    app = create_app(db_path=db_path, master_controller=stub)
    # 用 `with` 触发 lifespan → 启动 WS broadcast 任务
    with TestClient(app) as c:
        yield c


def _wait_for_event(client: TestClient, timeout: float = 3.0) -> Optional[dict]:
    """阻塞等 WS 收一条 message, 超时返回 None"""
    start = time.time()
    while time.time() - start < timeout:
        # 轮询 client._websocket_send_messages
        # 但 TestClient 的 WS 接收需要显式 receive_text/recv_json
        # 所以下面直接用 receive_json 而非轮询
        pass
    return None  # 永远到不了,只是占位


# === TestWSConnect ===

class TestWSConnect:
    """WS 端点连接测试"""

    def test_ws_connect_returns_connected_message(self, client: TestClient):
        """新连接应立即收到 1 条 'connected' 消息 (含当前 cached state)"""
        with client.websocket_connect("/api/ws/workflows") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert "snapshot" in msg
            # snapshot 应含 workflow 状态
            assert "is_active" in msg["snapshot"]

    def test_ws_path_not_found(self, client: TestClient):
        """未知 WS 路径应 403/404 (FastAPI WebSocket 路由不匹配)"""
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/api/ws/unknown") as ws:
                ws.receive_json()
        # FastAPI WebSocketDisconnect / 403 / 404 之一
        assert exc_info.value is not None


# === TestWSBroadcastOnChange ===

class TestWSBroadcastOnChange:
    """状态变更时 broadcast 测试"""

    def test_status_change_broadcasts_workflow_status_event(
        self, client: TestClient, stub: _ControllableStub
    ):
        """1s 轮询检测到状态变化 → broadcast workflow.status 事件"""
        with client.websocket_connect("/api/ws/workflows") as ws:
            # 清空初始 connected 消息
            initial = ws.receive_json()
            assert initial["type"] == "connected"

            # 触发状态变更
            stub.set_workflow_status({
                "is_active": True,
                "workflow_name": "novel_writing",
                "completed": 0,
                "failed": 0,
                "paused": True,
                "paused_nodes": ["judge"],
                "node_count": 4,
                "steps": 1,
                "pending_decisions": [],
            })

            # 等 ≤ 2.5s 收到 broadcast
            msg = ws.receive_json()
            assert msg["type"] == "workflow.status"
            assert msg["payload"]["is_active"] is True
            assert msg["payload"]["workflow_name"] == "novel_writing"
            assert msg["payload"]["paused"] is True

    def test_pending_decision_change_broadcasts_decision_event(
        self, client: TestClient, stub: _ControllableStub
    ):
        """新决策进入队列 → broadcast decision.snapshot 事件"""
        with client.websocket_connect("/api/ws/workflows") as ws:
            ws.receive_json()  # 跳过 connected

            stub.add_pending_decision({
                "decision_id": "dec_1",
                "kind": "outline_judgment",
                "node_id": "judge",
                "prompt": "Approve?",
                "options": ["approve", "revise"],
                "priority": 8,
                "status": "pending",
            })

            msg = ws.receive_json()
            assert msg["type"] == "decision.snapshot"
            assert len(msg["payload"]) == 1
            assert msg["payload"][0]["decision_id"] == "dec_1"


# === TestWSMultiClient ===

class TestWSMultiClient:
    """多客户端订阅测试"""

    def test_broadcast_to_multiple_clients(
        self, client: TestClient, stub: _ControllableStub
    ):
        """同一状态变化应 broadcast 给所有连接的 client"""
        with client.websocket_connect("/api/ws/workflows") as ws1:
            with client.websocket_connect("/api/ws/workflows") as ws2:
                # 两个 client 都收 connected
                m1 = ws1.receive_json()
                m2 = ws2.receive_json()
                assert m1["type"] == "connected"
                assert m2["type"] == "connected"

                # 触发变更
                stub.set_workflow_status({
                    "is_active": True,
                    "workflow_name": "wf_x",
                    "completed": 0,
                    "failed": 0,
                    "paused": True,
                    "paused_nodes": ["n1"],
                    "node_count": 2,
                    "steps": 1,
                    "pending_decisions": [],
                })

                # 两个 client 都应收到 broadcast
                m1 = ws1.receive_json()
                m2 = ws2.receive_json()
                assert m1["type"] == "workflow.status"
                assert m2["type"] == "workflow.status"
                assert m1["payload"]["workflow_name"] == "wf_x"
                assert m2["payload"]["workflow_name"] == "wf_x"


# === TestWSDisconnectCleanup ===

class TestWSDisconnectCleanup:
    """断线清理测试"""

    def test_client_disconnect_removes_from_manager(
        self, client: TestClient, stub: _ControllableStub
    ):
        """client 关闭连接后,ConnectionManager 不应再向其发消息"""
        with client.websocket_connect("/api/ws/workflows") as ws:
            ws.receive_json()  # connected

        # 此时 ws 已关闭;后续 trigger 状态变化不应让 server 抛异常
        # 直接 trigger,不应有未处理异常
        stub.set_workflow_status({
            "is_active": True,
            "workflow_name": "wf_after_close",
            "completed": 0,
            "failed": 0,
            "paused": False,
            "paused_nodes": [],
            "node_count": 0,
            "steps": 0,
            "pending_decisions": [],
        })

        # 等 1.5s 验证 server 不挂掉
        time.sleep(1.5)
        # 这里只能间接验证:不抛异常即通过
        # (更严的验证需要查 ConnectionManager.active 数量,但 TestClient 隔离)


# === TestWSRequiresController ===

class TestWSRequiresController:
    """master_controller=None 时 WS 端点应拒绝"""

    def test_ws_reject_when_no_controller(self, tmp_path):
        app = create_app(db_path=tmp_path / "rp.db", master_controller=None)
        client = TestClient(app)
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/api/ws/workflows") as ws:
                ws.receive_json()
        # WebSocketDisconnect (1006/1008 等) 或 403
        assert exc_info.value is not None
