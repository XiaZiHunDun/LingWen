"""Phase 8.13 + 8.16: WorkflowStatusResponse.cost_by_tier 透传 + time_window query param.

Mirror TestCostByScenarioExtraction.test_workflow_status_response_includes_cost_by_scenario
(Phase 8.7, tests/dashboard/test_decision_api.py:772) — 走真实 FastAPI endpoint,
用 create_app(master_controller=adapter) 注入 stub controller (带 cost_tracker),
验证 GET /api/workflows/active 响应包含 cost_by_tier 字段.

Phase 8.16 增: time_window=7d|30d|all query param, 透传 since 到
MasterControllerAdapter.get_active_workflow_status (Task 3 路径).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from dashboard.protocols import MasterControllerAdapter
from infra.agent_system import master_controller as mc_mod
from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier


class TestWorkflowStatusResponseCostByTier:
    """Phase 8.13: GET /api/workflows/active 暴露 cost_by_tier 字段."""

    def test_status_response_includes_cost_by_tier_when_workflow_active(
        self, tmp_path: Path
    ) -> None:
        """Active workflow → cost_by_tier 透传 (非空 dict, ModelTier.value 序列化)."""
        master = mc_mod.MasterController.__new__(mc_mod.MasterController)
        cost_tracker = CostTracker()
        # 混合 tier 触发 cost_by_tier() 有 2+ keys
        cost_tracker.record("chapter_writing", ModelTier.SONNET, 100, 50)
        cost_tracker.record("polish_merge", ModelTier.HAIKU, 200, 100)
        cost_tracker.record("review", ModelTier.OPUS, 50, 25)
        master.cost_tracker = cost_tracker

        # 注入 _last_* 缓存 (get_active_workflow_status 需要)
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

        master._last_scheduler = _StubScheduler()
        master._last_graph = _StubGraph()
        master._last_workflow_name = "novel_writing"

        adapter = MasterControllerAdapter(master)
        app = create_app(db_path=tmp_path / "rp.db", master_controller=adapter)
        client = TestClient(app)

        response = client.get("/api/workflows/active")
        assert response.status_code == 200
        body = response.json()
        # 字段存在 + ModelTier.value 序列化 (HAIKU → "haiku")
        assert "cost_by_tier" in body
        assert body["cost_by_tier"] == {"sonnet": pytest.approx(0.00105), "haiku": pytest.approx(0.0007), "opus": pytest.approx(0.002625)}
        # 验证 3 tier 都非 0
        assert all(v > 0 for v in body["cost_by_tier"].values())


class TestWorkflowStatusTimeWindow:
    """Phase 8.16: GET /api/workflows/active?time_window=7d|30d|all
    透传 since 到 _extract_cost helper. 5 测试: 7d/30d/all/default/invalid
    silent fallback."""

    def _make_master_with_cost_tracker(self, tmp_path: Path):
        """复用 TestWorkflowStatusResponseCostByTier 的 _make_master pattern."""
        from dashboard.protocols import MasterControllerAdapter
        from infra.agent_system import master_controller as mc_mod
        from infra.ai_service.cost_tracker import CostTracker
        from infra.ai_service.model_tiers import ModelTier

        master = mc_mod.MasterController.__new__(mc_mod.MasterController)
        cost_tracker = CostTracker()
        cost_tracker.record("chapter_writing", ModelTier.SONNET, 100, 50)
        master.cost_tracker = cost_tracker

        class _StubGraph:
            def node_ids(self): return []
            def has_execution(self, nid): return False
            def get_execution(self, nid): return None
            def get_node(self, nid): return None
        class _StubSummary: steps = 0
        class _StubScheduler: _summary = _StubSummary()
        master._last_scheduler = _StubScheduler()
        master._last_graph = _StubGraph()
        master._last_workflow_name = "novel_writing"

        adapter = MasterControllerAdapter(master)
        from dashboard.app import create_app
        app = create_app(db_path=tmp_path / "rp.db", master_controller=adapter)
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_time_window_7d_returns_full_cost_when_records_recent(
        self, tmp_path: Path
    ) -> None:
        """time_window=7d + 全部 records 新近 → 返全量 cost (走 since 透传, 不破坏 7d 内数据)."""
        client = self._make_master_with_cost_tracker(tmp_path)
        response = client.get("/api/workflows/active?time_window=7d")
        assert response.status_code == 200
        body = response.json()
        # 全部 records 是新近, 7d 窗口应包含全部
        assert body["total_cost_usd"] > 0
        assert "chapter_writing" in body["cost_by_scenario"]

    def test_time_window_30d_returns_full_cost(self, tmp_path: Path) -> None:
        """time_window=30d → 返全量 cost (同 7d path, 验证 30d 也透传)."""
        client = self._make_master_with_cost_tracker(tmp_path)
        response = client.get("/api/workflows/active?time_window=30d")
        assert response.status_code == 200
        body = response.json()
        assert body["total_cost_usd"] > 0
        assert "chapter_writing" in body["cost_by_scenario"]

    def test_time_window_all_returns_cost(self, tmp_path: Path) -> None:
        """time_window=all → since=None → 走旧 path, 返全量 cost."""
        client = self._make_master_with_cost_tracker(tmp_path)
        response = client.get("/api/workflows/active?time_window=all")
        assert response.status_code == 200
        body = response.json()
        assert body["total_cost_usd"] > 0

    def test_time_window_default_omitted_returns_cost(self, tmp_path: Path) -> None:
        """time_window 缺省 (omitted) → default 'all' → since=None → 走旧 path."""
        client = self._make_master_with_cost_tracker(tmp_path)
        response = client.get("/api/workflows/active")
        assert response.status_code == 200
        body = response.json()
        assert body["total_cost_usd"] > 0

    def test_time_window_invalid_silently_falls_back_to_all(
        self, tmp_path: Path
    ) -> None:
        """time_window=invalid → _parse_time_window silent fallback to None → 走旧 path.
        不抛 422, 0 破旧 caller 用错 URL 行为 (跟 Phase 8.13 silent degrade)."""
        client = self._make_master_with_cost_tracker(tmp_path)
        response = client.get("/api/workflows/active?time_window=invalid_value")
        assert response.status_code == 200
        body = response.json()
        # 仍能返 cost (走 since=None 旧 path)
        assert body["total_cost_usd"] > 0
