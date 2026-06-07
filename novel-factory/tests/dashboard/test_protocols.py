"""Phase 8.13: per-tier budget extraction helper tests.

Mirror _extract_cost_by_scenario silent-degrade pattern (Phase 8.7):
- getattr(controller, "cost_tracker", None) 兜底无 cost_tracker 属性
- try/except (noqa: BLE001) 异常 → log warning + 返 {} empty dict
- ModelTier enum keys 序列化为 .value (e.g. HAIKU → "haiku")

Phase 8.15: per-tier BUDGET extraction helper (mirror _extract_budget_per_window):
- getattr(master, "budget_service_by_tier", None) 兜底无 service
- try/except 异常 → log warning + 返 3 tier 全 None
- 3 tier 顺序: haiku → sonnet → opus (Enum 顺序, deterministic)
- 返回 dict[tier_name, {"usd": float, "set_at": str} | None] (3 tier 永远 present)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from dashboard.protocols import (
    _extract_budget_by_tier,
    _extract_cost_by_scenario,
    _extract_cost_by_tier,
    _extract_total_cost,
)


class TestExtractCostByTier:
    """Phase 8.13: Mirror _extract_cost_by_scenario silent-degrade pattern."""

    def test_returns_empty_dict_when_no_cost_tracker(self) -> None:
        """Backward compat: controller without cost_tracker attribute → empty dict."""

        class _StubController:
            pass

        assert _extract_cost_by_tier(_StubController()) == {}

    def test_returns_tier_value_keys_and_float_amounts(self) -> None:
        """ModelTier enum keys are serialized via .value; amounts as float."""

        from infra.ai_service.model_tiers import ModelTier

        stub = MagicMock()
        stub.cost_by_tier.return_value = {
            ModelTier.HAIKU: 0.05,
            ModelTier.SONNET: 0.50,
            ModelTier.OPUS: 1.20,
        }

        class _StubController:
            def __init__(self) -> None:
                self.cost_tracker = stub

        result = _extract_cost_by_tier(_StubController())
        assert result == {"haiku": 0.05, "sonnet": 0.50, "opus": 1.20}

    def test_returns_empty_dict_on_cost_tracker_exception(self) -> None:
        """Silent degrade: cost_tracker.cost_by_tier() raises → empty dict + log warning."""

        class _StubController:
            class cost_tracker:
                @staticmethod
                def cost_by_tier():
                    raise RuntimeError("db connection lost")

        result = _extract_cost_by_tier(_StubController())
        assert result == {}


# === Phase 8.15: Per-Tier Budget (helper for budget_by_tier dashboard field) ===

class TestExtractBudgetByTier:
    """Phase 8.15 T5: _extract_budget_by_tier mirror _extract_budget_per_window silent-degrade.

    返回 dict[tier_name, {"usd": float, "set_at": str} | None], 3 tier 永远 present
    (haiku/sonnet/opus, Enum 顺序), 未设 → None, 缺 service → 3 tier 全 None.
    """

    def test_extract_budget_by_tier_no_service_returns_all_none(self) -> None:
        """Phase 8.15: master.budget_service_by_tier = None → 3 tier values 都是 None."""
        # Stub controller 无 budget_service_by_tier 属性
        class _StubMaster:
            pass

        result = _extract_budget_by_tier(_StubMaster())
        assert result == {"haiku": None, "sonnet": None, "opus": None}

    def test_extract_budget_by_tier_with_set_tiers_returns_dict(self, tmp_path: Path) -> None:
        """Phase 8.15: set haiku/opus → 返 haiku+opus dict, sonnet None."""
        from infra.agent_system.budget_persistence import BudgetService
        from infra.ai_service.model_tiers import ModelTier

        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.HAIKU, 0.1)
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        # sonnet 未设

        class _StubMaster:
            def __init__(self) -> None:
                self.budget_service_by_tier = svc

        result = _extract_budget_by_tier(_StubMaster())
        # haiku + opus 返 dict, sonnet = None
        assert isinstance(result["haiku"], dict)
        assert result["haiku"]["usd"] == 0.1
        assert isinstance(result["haiku"]["set_at"], str)
        assert isinstance(result["opus"], dict)
        assert result["opus"]["usd"] == 1.0
        assert isinstance(result["opus"]["set_at"], str)
        assert result["sonnet"] is None

    def test_extract_budget_by_tier_includes_all_three_tiers(self, tmp_path: Path) -> None:
        """Phase 8.15: 3 tier keys (haiku/sonnet/opus) 永远 present, 顺序 Enum 顺序."""
        from infra.agent_system.budget_persistence import BudgetService
        from infra.ai_service.model_tiers import ModelTier

        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.HAIKU, 0.05)
        # sonnet/opus 未设

        class _StubMaster:
            def __init__(self) -> None:
                self.budget_service_by_tier = svc

        result = _extract_budget_by_tier(_StubMaster())
        # 3 keys 永远 present, 顺序 haiku/sonnet/opus (Enum 顺序)
        assert list(result.keys()) == ["haiku", "sonnet", "opus"]

    def test_extract_budget_by_tier_appears_in_workflow_status_response(self, tmp_path: Path) -> None:
        """Phase 8.15: get_active_workflow_status 返 dict 含 budget_by_tier 3 tier dict.

        Mock _last_scheduler/_last_graph 触发 active workflow path (Phase 5+
        run_workflow 写入缓存). Pattern 跟 test_app_workflow_status.py 1:1.
        """
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

        class _StubMaster:
            def __init__(self) -> None:
                self.budget_service_by_tier = svc
                self._last_scheduler = _StubScheduler()
                self._last_graph = _StubGraph()
                self._last_workflow_name = "novel_writing"

        stub = _StubMaster()
        MasterControllerAdapter._controller = stub
        try:
            status = MasterControllerAdapter(stub).get_active_workflow_status()
            # 旧 Phase 6.6.D + 7.6 + 8.7/8.8/8.12/8.13 fields 仍 present
            assert "budget_per_day" in status
            assert "budget_per_week" in status
            # Phase 8.15 新 field
            assert "budget_by_tier" in status
            budget_by_tier = status["budget_by_tier"]
            assert list(budget_by_tier.keys()) == ["haiku", "sonnet", "opus"]
            # opus + sonnet 设了 → dict with usd/set_at
            assert budget_by_tier["opus"]["usd"] == 1.0
            assert budget_by_tier["sonnet"]["usd"] == 0.5
            # haiku 未设 → None
            assert budget_by_tier["haiku"] is None
        finally:
            MasterControllerAdapter._controller = None


# === Phase 8.16: since 透传到 3 _extract_cost_* helper + adapter ===

class TestExtractCostSincePassthrough:
    """Phase 8.16: 3 _extract_cost_* helper 加 since 透传.
    验证 kwarg 透传到 cost_tracker method, default None 走旧 path (0 改)."""

    def test_extract_total_cost_passes_since_to_tracker(self) -> None:
        """_extract_total_cost(since=future) → cost_tracker.total_cost(since=future) 被调."""
        from datetime import datetime, timedelta, timezone

        tracker = MagicMock()
        tracker.total_cost.return_value = 0.0
        controller = MagicMock()
        controller.cost_tracker = tracker
        future = datetime.now(timezone.utc) + timedelta(seconds=1)
        _extract_total_cost(controller, since=future)
        # 验证 since 透传
        tracker.total_cost.assert_called_once_with(since=future)

    def test_extract_cost_by_scenario_passes_since_to_tracker(self) -> None:
        """_extract_cost_by_scenario(since=...) → cost_tracker.cost_by_scenario(since=...) 被调."""
        from datetime import datetime, timedelta, timezone

        tracker = MagicMock()
        tracker.cost_by_scenario.return_value = {}
        controller = MagicMock()
        controller.cost_tracker = tracker
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        _extract_cost_by_scenario(controller, since=one_hour_ago)
        tracker.cost_by_scenario.assert_called_once_with(since=one_hour_ago)

    def test_extract_cost_by_tier_passes_since_to_tracker(self) -> None:
        """_extract_cost_by_tier(since=None) → cost_tracker.cost_by_tier(since=None) 被调 (backward compat)."""
        tracker = MagicMock()
        tracker.cost_by_tier.return_value = {}
        controller = MagicMock()
        controller.cost_tracker = tracker
        _extract_cost_by_tier(controller)  # since 缺省 → None
        tracker.cost_by_tier.assert_called_once_with(since=None)
