"""Tests for dashboard budget endpoints (Phase 8.12)

GET /api/budgets → 3 tier dict
PUT /api/budgets/{day,week} → 接受 usd 持久化
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


def _make_test_client(tmp_path: Path) -> tuple[TestClient, Any]:
    """构造 TestClient + budget_service 注入"""
    from infra.agent_system.budget_persistence import BudgetService
    from dashboard.app import create_app
    from dashboard.protocols import MasterControllerAdapter

    service = BudgetService(db_path=tmp_path / "test.db")
    service.init_db()

    controller = MagicMock()
    controller.budget_service = service
    controller.cost_tracker = None
    controller._current_budget_usd = None
    controller._current_run_id = None

    # Inject into adapter singleton (class-level _controller)
    MasterControllerAdapter._controller = controller

    # 使用 create_app() 工厂 (dashboard/app.py 用 lazy app 模式)
    app = create_app()
    return TestClient(app), service


class TestDashboardBudgetEndpoints:
    """GET /api/budgets + PUT /api/budgets/{day,week}"""

    def test_get_budgets_returns_3_tiers(self, tmp_path: Path) -> None:
        """GET /api/budgets 返 per_run/per_day/per_week 3 dict"""
        client, service = _make_test_client(tmp_path)
        service.set("day", 0.5)
        service.set("week", 2.0)
        # No per-run set (controller has no current_run_id wired)
        response = client.get("/api/budgets")
        assert response.status_code == 200
        data = response.json()
        assert "per_run" in data
        assert "per_day" in data
        assert "per_week" in data
        # day/week 应有 status
        assert data["per_day"]["budget_usd"] == 0.5
        assert data["per_week"]["budget_usd"] == 2.0

    def test_put_budgets_day_persists(self, tmp_path: Path) -> None:
        """PUT /api/budgets/day usd=0.5 → 后续 GET 返 0.5"""
        client, service = _make_test_client(tmp_path)
        response = client.put("/api/budgets/day", json={"usd": 0.5})
        assert response.status_code == 200
        assert response.json()["ok"] is True
        # Verify persisted in DB
        current = service.get_current("day")
        assert current is not None
        assert current.usd == 0.5

    def test_put_budgets_week_persists(self, tmp_path: Path) -> None:
        """PUT /api/budgets/week usd=2.0 → 后续 GET 返 2.0"""
        client, service = _make_test_client(tmp_path)
        response = client.put("/api/budgets/week", json={"usd": 2.0})
        assert response.status_code == 200
        current = service.get_current("week")
        assert current is not None
        assert current.usd == 2.0

    def test_put_budgets_validates_scope(self, tmp_path: Path) -> None:
        """PUT /api/budgets/month → 400 (invalid scope)"""
        client, _ = _make_test_client(tmp_path)
        response = client.put("/api/budgets/month", json={"usd": 1.0})
        assert response.status_code == 400

    def test_put_budgets_validates_usd_negative(self, tmp_path: Path) -> None:
        """PUT day usd=-1 → 422 (Pydantic ge=0)"""
        client, _ = _make_test_client(tmp_path)
        response = client.put("/api/budgets/day", json={"usd": -1})
        assert response.status_code == 422

    def test_get_budgets_when_none_set_returns_null_per_tier(
        self, tmp_path: Path
    ) -> None:
        """0 budget 全 null/empty, 0 错"""
        client, _ = _make_test_client(tmp_path)
        response = client.get("/api/budgets")
        assert response.status_code == 200
        data = response.json()
        # 3 tier 都 empty/null (无 budget set)
        assert data["per_run"] in ({}, None)
        assert data["per_day"] in ({}, None)
        assert data["per_week"] in ({}, None)
