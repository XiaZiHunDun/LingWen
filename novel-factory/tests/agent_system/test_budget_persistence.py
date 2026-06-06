"""Tests for BudgetService (Phase 8.12)

Per-run / per-day / per-week budget persistence. Append-only `budgets` table.
Per-day = UTC 00:00-23:59, per-week = Mon-Sun.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

from infra.agent_system.budget_persistence import BudgetService


class TestBudgetService:
    """BudgetService 行为 — mirror CostTrackerDB patterns"""

    def test_init_db_creates_table_and_indices(self, tmp_path: Path) -> None:
        """init_db → budgets table + 2 indices 存在"""
        db = tmp_path / "test.db"
        service = BudgetService(db_path=db)
        service.init_db()
        with sqlite3.connect(str(db)) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'"
            ).fetchall()
            assert len(tables) == 1
            indices = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='budgets'"
            ).fetchall()
            index_names = {row[0] for row in indices}
            assert any("scope" in n for n in index_names)
            assert any("run_id" in n for n in index_names)

    def test_set_scope_run_inserts_with_run_id(self, tmp_path: Path) -> None:
        """set('run', 0.1, 'abc') → 1 行, scope/run_id/usd 正确"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("run", 0.1, run_id="abc123")
        with sqlite3.connect(str(tmp_path / "test.db")) as conn:
            row = conn.execute(
                "SELECT scope, usd, run_id FROM budgets"
            ).fetchone()
        assert row[0] == "run"
        assert row[1] == 0.1
        assert row[2] == "abc123"

    def test_set_scope_day_week_run_id_none(self, tmp_path: Path) -> None:
        """set('day', 0.5) / set('week', 2.0) → run_id NULL"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("day", 0.5)
        service.set("week", 2.0)
        with sqlite3.connect(str(tmp_path / "test.db")) as conn:
            rows = conn.execute(
                "SELECT scope, usd, run_id FROM budgets ORDER BY id"
            ).fetchall()
        assert rows[0] == ("day", 0.5, None)
        assert rows[1] == ("week", 2.0, None)

    def test_get_current_returns_latest_for_scope(self, tmp_path: Path) -> None:
        """set 2 次同 scope → get_current 返最后一次"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("day", 0.5)
        service.set("day", 1.0)
        current = service.get_current("day")
        assert current is not None
        assert current.usd == 1.0

    def test_get_current_returns_none_when_no_row(self, tmp_path: Path) -> None:
        """0 行 → get_current 返 None"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        assert service.get_current("day") is None
        assert service.get_current("week") is None
        assert service.get_current("run", run_id="missing") is None

    def test_get_current_run_filters_by_run_id(self, tmp_path: Path) -> None:
        """2 run 各 set → get_current(scope='run', run_id='r1') 只返 r1"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("run", 0.1, run_id="r1")
        service.set("run", 0.2, run_id="r2")
        r1 = service.get_current("run", run_id="r1")
        r2 = service.get_current("run", run_id="r2")
        assert r1 is not None and r1.usd == 0.1
        assert r2 is not None and r2.usd == 0.2

    def test_check_all_scopes_per_run_exceeded(self, tmp_path: Path) -> None:
        """per-run set 0.1, total_cost 0.15 → raise CostBudgetExceeded(scope='run')"""
        from infra.ai_service.cost_tracker import CostBudgetExceeded
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("run", 0.1, run_id="r1")
        with pytest.raises(CostBudgetExceeded) as exc:
            service.check_all_scopes(total_cost_usd=0.15, current_run_id="r1")
        assert exc.value.scope == "run"
        assert exc.value.used_usd == 0.15
        assert exc.value.budget_usd == 0.1

    def test_check_all_scopes_per_day_within_window(self, tmp_path: Path) -> None:
        """set 0.5 今日, total_cost 0.3 → pass (no raise)"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("day", 0.5)
        # 不 raise = pass
        service.check_all_scopes(total_cost_usd=0.3, current_run_id="r1")

    def test_check_all_scopes_per_day_outside_window(self, tmp_path: Path) -> None:
        """set 0.5 昨日, total_cost 0.3 → pass (window 失效)"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        # 直接插一行 set_at = 昨天
        with sqlite3.connect(str(tmp_path / "test.db")) as conn:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            conn.execute(
                "INSERT INTO budgets (scope, usd, run_id, set_at) VALUES (?, ?, ?, ?)",
                ("day", 0.5, None, yesterday),
            )
            conn.commit()
        # 不 raise = pass (window 失效, 不 check)
        service.check_all_scopes(total_cost_usd=0.3, current_run_id="r1")

    def test_check_all_scopes_per_week_within_window(self, tmp_path: Path) -> None:
        """set 2.0 本周, total_cost 1.5 → pass"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("week", 2.0)
        service.check_all_scopes(total_cost_usd=1.5, current_run_id="r1")

    def test_check_all_scopes_priority_run_over_day_over_week(
        self, tmp_path: Path
    ) -> None:
        """3 档都设, total_cost 超 per-run → raise(scope='run') 不管 day/week"""
        from infra.ai_service.cost_tracker import CostBudgetExceeded
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("run", 0.1, run_id="r1")
        service.set("day", 10.0)
        service.set("week", 20.0)
        with pytest.raises(CostBudgetExceeded) as exc:
            service.check_all_scopes(total_cost_usd=0.15, current_run_id="r1")
        assert exc.value.scope == "run"

    def test_list_runs_returns_recent_distinct(self, tmp_path: Path) -> None:
        """set 3 run (r1/r2/r3) → list_runs(limit=2) 返 2 最新"""
        service = BudgetService(db_path=tmp_path / "test.db")
        service.init_db()
        service.set("run", 0.1, run_id="r1")
        service.set("run", 0.2, run_id="r2")
        service.set("run", 0.3, run_id="r3")
        runs = service.list_runs(limit=2)
        assert len(runs) == 2
        assert "r3" in runs
        assert "r2" in runs
        assert "r1" not in runs
