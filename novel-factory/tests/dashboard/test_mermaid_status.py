"""Phase 6.6.D — /mermaid 端点 ?include_status=true 测试

- 默认 false → status_applied=False, node_statuses={}
- true + active workflow → status_applied=True, node_statuses 含各节点状态
- true + 无活跃工作流 → status_applied=False, node_statuses={} (不报错)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app


class _StubMaster:
    """满足 MasterControllerLike 协议 — 控制 get_active_workflow_status 返回"""

    def __init__(self, executions: dict[str, str] | None):
        self._executions = executions

    def get_active_workflow_status(self) -> dict[str, Any]:
        if self._executions is None:
            return {
                "is_active": False,
                "workflow_name": None,
                "pending_decisions": [],
            }
        return {
            "is_active": True,
            "workflow_name": "novel_writing",
            "completed": sum(1 for s in self._executions.values() if s == "completed"),
            "failed": sum(1 for s in self._executions.values() if s == "failed"),
            "paused": False,
            "paused_nodes": [],
            "node_count": len(self._executions),
            "steps": 1,
            "pending_decisions": [],
            "executions": self._executions,
        }


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "rp.db"


class TestMermaidStatusEndpoint:
    """Phase 6.6.D — Mermaid 节点状态染色"""

    def test_mermaid_endpoint_default_does_not_apply_status(self, tmp_db: Path):
        """?include_status 缺省 → status_applied=False, node_statuses={} (保后向兼容)"""
        stub = _StubMaster({"write_chapter": "completed", "review_chapter": "completed"})
        app = create_app(db_path=tmp_db, master_controller=stub)
        client = TestClient(app)

        response = client.get("/api/workflows/novel_writing/mermaid")
        assert response.status_code == 200
        data = response.json()
        assert data["status_applied"] is False
        assert data["node_statuses"] == {}

    def test_mermaid_endpoint_with_include_status_returns_node_statuses(self, tmp_db: Path):
        """?include_status=true + active workflow → status_applied=True + node_statuses 完整"""
        stub = _StubMaster({
            "read_snapshot": "completed",
            "write_chapter": "completed",
            "review_chapter": "running",
            "polish_chapter": "pending",
            "emit_chapter": "pending",
        })
        app = create_app(db_path=tmp_db, master_controller=stub)
        client = TestClient(app)

        response = client.get("/api/workflows/novel_writing/mermaid?include_status=true")
        assert response.status_code == 200
        data = response.json()
        assert data["status_applied"] is True
        assert data["node_statuses"] == {
            "read_snapshot": "completed",
            "write_chapter": "completed",
            "review_chapter": "running",
            "polish_chapter": "pending",
            "emit_chapter": "pending",
        }
        # mermaid 字符串应包含 status-based class 声明
        assert "class read_snapshot node-completed" in data["mermaid"]
        assert "class review_chapter node-running" in data["mermaid"]
        assert "class polish_chapter node-pending" in data["mermaid"]

    def test_mermaid_endpoint_with_no_active_workflow_returns_empty_statuses(self, tmp_db: Path):
        """?include_status=true + 无活跃工作流 → status_applied=False, node_statuses={} (不报错)"""
        stub = _StubMaster(None)  # is_active=False
        app = create_app(db_path=tmp_db, master_controller=stub)
        client = TestClient(app)

        response = client.get("/api/workflows/novel_writing/mermaid?include_status=true")
        assert response.status_code == 200
        data = response.json()
        assert data["status_applied"] is False
        assert data["node_statuses"] == {}
        # 仍返回 valid mermaid 字符串
        assert "graph TD" in data["mermaid"]
