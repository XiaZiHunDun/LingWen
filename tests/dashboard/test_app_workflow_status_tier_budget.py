"""Phase 8.15 T6: per-tier budget endpoints + WorkflowStatusResponse.budget_by_tier.

6 tests:
1. GET /api/budgets/by-tier → 3 tier dict (haiku/sonnet/opus, 顺序 Enum 顺序)
2. PUT /api/budgets/by-tier/opus usd=1.0 → service.set_by_tier called, returns ok
3. PUT /api/budgets/by-tier/invalid → 404 (tier not in enum)
4. PUT usd=-0.01 → 422 (Pydantic ge=0 兜底)
5. PUT /api/budgets/by-tier/opus with service=None → 503 (Phase 8.12 same pattern)
6. GET /api/workflows/active 返 dict 含 budget_by_tier field (3 keys)

Pattern 跟 tests/agent_system/test_dashboard_budget_endpoints.py 1:1 mirror
(Phase 8.12 _make_test_client + MasterControllerAdapter._controller singleton).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


def _make_test_client(tmp_path: Path) -> tuple[TestClient, Any]:
    """构造 TestClient + tier budget_service 注入 (master 必备 budget_service_by_tier attr).

    Pattern 跟 tests/agent_system/test_dashboard_budget_endpoints.py 1:1 mirror.
    """
    from dashboard.app import create_app
    from dashboard.protocols import MasterControllerAdapter
    from infra.agent_system.budget_persistence import BudgetService

    service = BudgetService(db_path=tmp_path / "test.db")
    service.init_db()

    controller = MagicMock()
    controller.budget_service = None
    controller.budget_service_by_tier = service  # Phase 8.15 T6
    controller.cost_tracker = None
    controller._current_budget_usd = None
    controller._current_run_id = None

    # Inject into adapter singleton (class-level _controller)
    MasterControllerAdapter._controller = controller

    app = create_app()
    return TestClient(app), service


class TestBudgetByTierEndpoints:
    """Phase 8.15 T6: GET/PUT /api/budgets/by-tier + budget_by_tier response field."""

    def test_get_budget_by_tier_endpoint_returns_dict(self, tmp_path: Path) -> None:
        """GET /api/budgets/by-tier 返 3 tier dict (haiku/sonnet/opus, Enum 顺序)."""
        client, service = _make_test_client(tmp_path)
        # 设 opus + sonnet (haiku 未设)
        service.set_by_tier(__import__("infra.ai_service.model_tiers", fromlist=["ModelTier"]).ModelTier.OPUS, 1.0)
        response = client.get("/api/budgets/by-tier")
        assert response.status_code == 200
        data = response.json()
        # 3 keys 永远 present, 顺序 haiku/sonnet/opus (Enum 顺序, T5 helper 已保)
        assert list(data.keys()) == ["haiku", "sonnet", "opus"]
        # opus 设了 → dict with usd/set_at; haiku/sonnet → None
        assert isinstance(data["opus"], dict)
        assert data["opus"]["usd"] == 1.0
        assert isinstance(data["opus"]["set_at"], str)
        assert data["haiku"] is None
        assert data["sonnet"] is None

    def test_set_budget_by_tier_endpoint_calls_service(self, tmp_path: Path) -> None:
        """PUT /api/budgets/by-tier/opus usd=1.0 → service.set_by_tier called, 返 ok."""
        client, service = _make_test_client(tmp_path)
        response = client.put("/api/budgets/by-tier/opus", json={"usd": 1.0})
        assert response.status_code == 200
        body = response.json()
        assert body == {"ok": True, "tier": "opus", "usd": 1.0}
        # Verify persisted via service (mirror test_put_budgets_day_persists)
        from infra.ai_service.model_tiers import ModelTier
        current = service.get_by_tier(ModelTier.OPUS)
        assert current is not None
        assert current.usd == 1.0
        assert current.tier == ModelTier.OPUS

    def test_set_budget_by_tier_endpoint_rejects_invalid_tier(self, tmp_path: Path) -> None:
        """PUT /api/budgets/by-tier/invalid → 404 (tier 不在 haiku/sonnet/opus)."""
        client, _ = _make_test_client(tmp_path)
        response = client.put("/api/budgets/by-tier/invalid", json={"usd": 1.0})
        assert response.status_code == 404

    def test_set_budget_by_tier_endpoint_rejects_negative_usd(self, tmp_path: Path) -> None:
        """PUT usd=-0.01 → 422 (Pydantic ge=0 validation, 跟 Phase 8.12 同 pattern)."""
        client, _ = _make_test_client(tmp_path)
        response = client.put("/api/budgets/by-tier/opus", json={"usd": -0.01})
        assert response.status_code == 422

    def test_set_budget_by_tier_endpoint_returns_503_when_service_none(
        self, tmp_path: Path
    ) -> None:
        """PUT /api/budgets/by-tier/opus → 503 (master.budget_service_by_tier = None)."""
        from dashboard.app import create_app
        from dashboard.protocols import MasterControllerAdapter

        master = MagicMock()
        master.budget_service = None
        master.budget_service_by_tier = None  # 503 触发: service 未配
        master.cost_tracker = None

        MasterControllerAdapter._controller = master
        try:
            app = create_app()
            client = TestClient(app)
            response = client.put("/api/budgets/by-tier/opus", json={"usd": 1.0})
            assert response.status_code == 503
        finally:
            MasterControllerAdapter._controller = None

    def test_workflow_status_response_includes_budget_by_tier_field(self, tmp_path: Path) -> None:
        """GET /api/workflows/active 返 dict 含 budget_by_tier 3 keys (T5 helper 透传, T6 补 model Field)."""
        from dashboard.app import create_app
        from dashboard.protocols import MasterControllerAdapter
        from infra.agent_system.budget_persistence import BudgetService
        from infra.ai_service.model_tiers import ModelTier

        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        svc.set_by_tier(ModelTier.SONNET, 0.5)
        # haiku 未设

        class _StubGraph:
            def node_ids(self):
                return []

            def has_execution(self, nid):
                return False

            def get_execution(self, nid):
                return None

            def get_node(self, nid):
                return None

        class _StubSummary:
            steps = 0

        class _StubScheduler:
            _summary = _StubSummary()

        master = MagicMock()
        master.budget_service = None
        master.budget_service_by_tier = svc
        master.cost_tracker = None
        master._current_budget_usd = None
        master._current_run_id = None
        master._last_scheduler = _StubScheduler()
        master._last_graph = _StubGraph()
        master._last_workflow_name = "novel_writing"

        adapter = MasterControllerAdapter(master)
        app = create_app(db_path=tmp_path / "rp.db", master_controller=adapter)
        client = TestClient(app)
        response = client.get("/api/workflows/active")
        assert response.status_code == 200
        body = response.json()
        # Phase 8.15 T6: budget_by_tier field 正式 present 在 response
        assert "budget_by_tier" in body
        budget_by_tier = body["budget_by_tier"]
        assert list(budget_by_tier.keys()) == ["haiku", "sonnet", "opus"]
        assert budget_by_tier["opus"]["usd"] == 1.0
        assert budget_by_tier["sonnet"]["usd"] == 0.5
        assert budget_by_tier["haiku"] is None
