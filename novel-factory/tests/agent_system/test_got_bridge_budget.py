"""Tests for AgentComputeFn 3-tier budget check (Phase 8.12)

Phase 8.8 仅 check _current_budget_usd (per-run in-memory 累积).
Phase 8.12 在 AgentComputeFn.__init__ 加 budget_service kwarg,
在 __call__ 现有 check_budget 之后加 check_all_scopes
(per-run / per-day / per-week 3 档).

契约:
- budget_service=None → 旧 Phase 8.8 path 0 改 (backward compat)
- 任一档超阈 → raise CostBudgetExceeded(scope=<that scope>)
- per-day / per-week window 失效 (set_at 已过 UTC day/week) → 不 raise
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from infra.ai_service.cost_tracker import CostBudgetExceeded, CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.agent_system.got_bridge import AgentComputeFn
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
