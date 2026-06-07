"""Tests for AgentComputeFn 3-tier budget check (Phase 8.12) + per-tier (Phase 8.15)

Phase 8.8 仅 check _current_budget_usd (per-run in-memory 累积).
Phase 8.12 在 AgentComputeFn.__init__ 加 budget_service kwarg,
在 __call__ 现有 check_budget 之后加 check_all_scopes
(per-run / per-day / per-week 3 档).
Phase 8.15 在 AgentComputeFn.__init__ 加 budget_service_by_tier kwarg,
在 __call__ 现有 check_all_scopes 之后加 check_all_tiers
(per-tier haiku/sonnet/opus 3 档).

契约 (Phase 8.15):
- budget_service_by_tier=None → 旧 Phase 8.12 path 0 改 (backward compat)
- 任一 tier 超阈 → raise CostBudgetExceeded(scope='tier', tier=<that tier>)
- 顺序: total (Phase 8.8) → run/day/week (Phase 8.12) → tier (Phase 8.15),
  total 先 raise 不走到 tier check (deterministic ordering).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from infra.agent_system.got_bridge import AgentComputeFn
from infra.ai_service.cost_tracker import CostBudgetExceeded, CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.got.data_structures import NodeType, ThoughtNode
from infra.got.scheduler import ComputeResult


def _make_node(scenario: str) -> ThoughtNode:
    """构造一个 GENERATION 节点 (含 prompt_scenario)."""
    return ThoughtNode(
        node_id="n1",
        type=NodeType.GENERATION,
        name="test_node",
        description="budget test node",
        prompt_scenario=scenario,
    )


def _make_compute(
    master: Any, cost_tracker: CostTracker, budget_service: Any
) -> AgentComputeFn:
    """构造一个 AgentComputeFn (含 cost_tracker + budget_service)."""
    return AgentComputeFn(
        master=master,
        cost_tracker=cost_tracker,
        budget_service=budget_service,
    )


class TestAgentComputeFnBudget:
    """AgentComputeFn 3-tier budget enforcement"""

    def test_compute_fn_checks_per_run_scope(self, tmp_path: Path) -> None:
        """set per-run budget 0.1, total_cost 0.15 → raise(scope='run')"""
        from infra.agent_system.budget_persistence import BudgetService

        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("run", 0.1, run_id="r1")

        master = MagicMock()
        master._current_budget_usd = 0.1
        master._current_run_id = "r1"
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # 喂 cost_tracker record 到 total > 0.1
        # SONNET pricing: $3/1M input + $15/1M output → 4M+2M = $0.012 + $0.030 = $0.042
        # 用 10M+5M = $0.03 + $0.075 = $0.105 > 0.1
        tracker.record("chapter_writing", ModelTier.SONNET, 10_000_000, 5_000_000)
        compute = _make_compute(master, tracker, service)

        with pytest.raises(CostBudgetExceeded) as exc:
            compute(_make_node("chapter_writing"), {"chapter_num": 1})
        assert exc.value.scope == "run"

    def test_compute_fn_checks_per_day_scope(self, tmp_path: Path) -> None:
        """set per-day 0.5, total_cost > 0.5 → raise(scope='day')"""
        from infra.agent_system.budget_persistence import BudgetService

        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("day", 0.5)

        master = MagicMock()
        master._current_budget_usd = None  # Phase 8.8 path 不限制
        master._current_run_id = "r1"
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # 喂 cost_tracker record 到 total > 0.5
        # 50M+25M SONNET = $0.15 + $0.375 = $0.525 > 0.5
        tracker.record("chapter_writing", ModelTier.SONNET, 50_000_000, 25_000_000)
        compute = _make_compute(master, tracker, service)

        with pytest.raises(CostBudgetExceeded) as exc:
            compute(_make_node("chapter_writing"), {"chapter_num": 1})
        assert exc.value.scope == "day"

    def test_compute_fn_checks_per_week_scope(self, tmp_path: Path) -> None:
        """set per-week 2.0, total_cost > 2.0 → raise(scope='week')"""
        from infra.agent_system.budget_persistence import BudgetService

        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("week", 2.0)

        master = MagicMock()
        master._current_budget_usd = None
        master._current_run_id = "r1"
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # 喂 cost_tracker record 到 total > 2.0
        # 200M+100M SONNET = $0.6 + $1.5 = $2.1 > 2.0
        tracker.record("chapter_writing", ModelTier.SONNET, 200_000_000, 100_000_000)
        compute = _make_compute(master, tracker, service)

        with pytest.raises(CostBudgetExceeded) as exc:
            compute(_make_node("chapter_writing"), {"chapter_num": 1})
        assert exc.value.scope == "week"

    def test_compute_fn_no_budget_service_unchanged(
        self, tmp_path: Path
    ) -> None:
        """budget_service=None, 旧 Phase 8.8 path 0 改 (check_budget 仍工作)"""
        master = MagicMock()
        master._current_budget_usd = 0.0001  # 极小, cost_tracker > 立即超
        master._current_run_id = None
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # SONNET 1000+500 = $0.000003 + $0.0000075 = > 0.0001
        tracker.record("chapter_writing", ModelTier.SONNET, 1000, 500)
        compute = _make_compute(master, tracker, budget_service=None)

        with pytest.raises(CostBudgetExceeded) as exc:
            compute(_make_node("chapter_writing"), {"chapter_num": 1})
        # Phase 8.8 raise (默认 scope='run')
        assert exc.value.scope == "run"

    def test_compute_fn_default_scope_run_backward_compat(self) -> None:
        """Phase 8.8 raise 不带 scope → 等价 scope='run' (default)"""
        # 验证 CostBudgetExceeded 不传 scope 时 default = 'run'
        exc = CostBudgetExceeded(used_usd=0.2, budget_usd=0.1, scenario="test")
        assert exc.scope == "run"

    def test_compute_fn_window_expired_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """set day 昨天 → window 失效 → 不 raise (即使 cost > budget)"""
        from infra.agent_system.budget_persistence import BudgetService

        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        # 直接插一行 set_at = 昨天
        with sqlite3.connect(str(tmp_path / "test.db")) as conn:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            conn.execute(
                "INSERT INTO budgets (scope, usd, run_id, set_at) VALUES (?, ?, ?, ?)",
                ("day", 0.0001, None, yesterday),
            )
            conn.commit()

        master = MagicMock()
        master._current_budget_usd = None  # Phase 8.8 不限制
        master._current_run_id = "r1"
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # cost > 0.0001 budget, 但 window 失效 → 不 raise
        tracker.record("chapter_writing", ModelTier.SONNET, 1000, 500)
        compute = _make_compute(master, tracker, service)

        # 不 raise 即 pass (window 失效, check_all_scopes 不 throw)
        result = compute(_make_node("chapter_writing"), {"chapter_num": 1})
        assert result.fail is False


# === Phase 8.15: Per-Tier Budget ===
from infra.agent_system.budget_persistence import BudgetService
from infra.ai_service.cost_tracker import CostBudgetExceeded
from infra.ai_service.model_tiers import ModelTier


class TestAgentComputeFnByTier:
    """Phase 8.15: AgentComputeFn 调 check_all_tiers (跟 check_all_scopes 同位置)."""

    def test_compute_fn_tier_budget_none_compat(self, tmp_path: Path) -> None:
        """Phase 8.15: budget_service_by_tier=None 跳过 check, backward compat."""
        from infra.agent_system.got_bridge import AgentComputeFn
        from infra.agent_system.master_controller import MasterController

        master = MasterController.__new__(MasterController)  # bypass __init__
        compute = AgentComputeFn(master, cost_tracker=None, budget_service_by_tier=None)
        # 没有 raise 即可
        assert compute._budget_service_by_tier is None

    def test_compute_fn_with_tier_budget_service_checks_tiers(
        self, tmp_path: Path
    ) -> None:
        """Phase 8.15: 注入 budget_service_by_tier 后, compute 调 check_all_tiers.

        通过 compute.__call__ 走完整 path: stub handler 喂 cost,
        tier budget 设小, 期望 raise(scope='tier', tier=OPUS)。
        """
        master = MagicMock()
        master._current_budget_usd = None  # Phase 8.8 path 不限制
        master._current_run_id = "r1"
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # OPUS pricing: $15/1M input + $75/1M output
        # 喂 cost_tracker record 到 total > 0.1 (设 OPUS tier budget 0.1)
        # 10M+5M OPUS = $0.15 + $0.375 = $0.525 > 0.1
        tracker.record("chapter_writing", ModelTier.OPUS, 10_000_000, 5_000_000)

        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.init_db()
        svc.set_by_tier(ModelTier.OPUS, 0.1)  # tier budget 极小, 必超

        compute = AgentComputeFn(
            master, cost_tracker=tracker, budget_service_by_tier=svc
        )

        with pytest.raises(CostBudgetExceeded) as exc:
            compute(_make_node("chapter_writing"), {"chapter_num": 1})
        assert exc.value.scope == "tier"
        assert exc.value.tier == ModelTier.OPUS

    def test_compute_fn_tier_budget_raise_propagates(self, tmp_path: Path) -> None:
        """Phase 8.15: check_all_tiers raise CostBudgetExceeded(scope='tier', tier=X)."""
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.init_db()
        svc.set_by_tier(ModelTier.SONNET, 0.5)
        ct = CostTracker()
        # 喂 cost_tracker record 到 total > 0.5
        # 100M+50M SONNET = $0.3 + $0.75 = $1.05 > 0.5
        ct.record("audit", ModelTier.SONNET, 100_000_000, 50_000_000)
        with pytest.raises(CostBudgetExceeded) as exc_info:
            svc.check_all_tiers(ct.cost_by_tier())
        assert exc_info.value.tier == ModelTier.SONNET
        assert "tier=sonnet" in str(exc_info.value)

    def test_compute_fn_tier_budget_checked_after_total_check(
        self, tmp_path: Path
    ) -> None:
        """Phase 8.15: total budget 先 raise, 不走到 tier check (顺序保).

        Phase 8.8 CostTracker.check_budget 走 _current_budget_usd (total cap);
        Phase 8.12 check_all_scopes 走 run/day/week (total cost 比对);
        Phase 8.15 check_all_tiers 走 haiku/sonnet/opus (cost_by_tier 比对).

        Ordering invariant: total → run/day/week → tier (跟 Phase 8.12 顺序同栈).
        若 total 必超, 验证 raise(scope='run', default) 而非 tier.
        """
        from infra.agent_system.got_bridge import AgentComputeFn

        master = MagicMock()
        master._current_budget_usd = 0.0001  # 总 cap 极小, 必超
        master._current_run_id = "r1"
        master.write_chapter_with_usage = MagicMock(
            return_value=({"content": "x"}, {"input_tokens": 100, "output_tokens": 50})
        )

        tracker = CostTracker()
        # SONNET 100K+50K = $0.0003 + $0.00075 = $0.00105 > 0.0001 (超!)
        tracker.record("chapter_writing", ModelTier.SONNET, 100_000, 50_000)

        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.init_db()
        svc.set_by_tier(ModelTier.OPUS, 100.0)  # tier budget 极宽松, 0 raise

        compute = AgentComputeFn(
            master,
            cost_tracker=tracker,
            budget_service=svc,
            budget_service_by_tier=svc,
        )

        with pytest.raises(CostBudgetExceeded) as exc:
            compute(_make_node("chapter_writing"), {"chapter_num": 1})
        # Phase 8.8 raise (default scope='run'), 不走到 tier check
        assert exc.value.scope == "run"
