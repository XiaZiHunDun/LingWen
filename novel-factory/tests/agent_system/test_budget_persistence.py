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


# === Phase 8.15: Per-Tier Budget ===
from infra.ai_service.cost_tracker import CostBudgetExceeded
from infra.ai_service.model_tiers import ModelTier


class TestBudgetByTierPersistence:
    """Phase 8.15: BudgetService per-tier methods (4 new methods)."""

    def test_set_by_tier_inserts_row(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService, TierBudgetEntry
        svc = BudgetService(db_path=tmp_path / "b.db")
        entry = svc.set_by_tier(ModelTier.OPUS, 1.0)
        assert isinstance(entry, TierBudgetEntry)
        assert entry.tier == ModelTier.OPUS
        assert entry.usd == 1.0
        assert entry.id > 0

    def test_set_by_tier_negative_usd_raises(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        with pytest.raises(ValueError, match="usd must be non-negative"):
            svc.set_by_tier(ModelTier.OPUS, -0.01)

    def test_get_by_tier_returns_latest(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        svc.set_by_tier(ModelTier.OPUS, 2.0)  # 后 set 覆盖 (current)
        entry = svc.get_by_tier(ModelTier.OPUS)
        assert entry is not None
        assert entry.usd == 2.0  # latest

    def test_get_by_tier_returns_none_if_unset(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        assert svc.get_by_tier(ModelTier.OPUS) is None

    def test_list_by_tiers_returns_current_per_tier(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        svc.set_by_tier(ModelTier.OPUS, 2.0)  # 2nd set
        entries = svc.list_by_tiers()
        # 只返 current per tier (history 1 个, current 1 个)
        opus_entries = [e for e in entries if e.tier == ModelTier.OPUS]
        assert len(opus_entries) == 1
        assert opus_entries[0].usd == 2.0

    def test_check_all_tiers_no_exceed_no_raise(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        svc.check_all_tiers({ModelTier.OPUS: 0.5})  # 0.5 < 1.0 ok

    def test_check_all_tiers_raises_on_first_exceed(self, tmp_path):
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        with pytest.raises(CostBudgetExceeded) as exc_info:
            svc.check_all_tiers({ModelTier.OPUS: 1.5})
        assert exc_info.value.scope == "tier"
        assert exc_info.value.tier == ModelTier.OPUS
        assert "tier=opus" in str(exc_info.value)

    def test_check_all_tiers_haiku_checked_first(self, tmp_path):
        """Phase 8.15: deterministic 顺序 haiku → sonnet → opus (Enum 顺序)."""
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.HAIKU, 0.1)
        svc.set_by_tier(ModelTier.SONNET, 0.5)
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        with pytest.raises(CostBudgetExceeded) as exc_info:
            svc.check_all_tiers({
                ModelTier.HAIKU: 0.5,   # 超
                ModelTier.SONNET: 1.0,  # 超
                ModelTier.OPUS: 2.0,    # 超
            })
        # 第 1 个超阈 raise (haiku), 后续不检查
        assert exc_info.value.tier == ModelTier.HAIKU

    def test_check_all_tiers_skips_unset(self, tmp_path):
        """Phase 8.15: 未设 tier 跳过, 不抛 (跟 run/day/week check_all_scopes 同)."""
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set_by_tier(ModelTier.OPUS, 1.0)
        # 只设 opus, haiku/sonnet 未设, cost_by_tier 含这 3 档 → 只 check opus
        svc.check_all_tiers({
            ModelTier.HAIKU: 999.0,  # 未设, 跳过
            ModelTier.SONNET: 999.0,  # 未设, 跳过
            ModelTier.OPUS: 0.5,  # 0.5 < 1.0 ok
        })

    def test_tier_budget_persistence_independent_from_run_day_week(self, tmp_path):
        """Phase 8.15: tier budget 跟 run/day/week budget 共存同一 DB 不同表."""
        from infra.agent_system.budget_persistence import BudgetService
        svc = BudgetService(db_path=tmp_path / "b.db")
        svc.set("run", 5.0)  # Phase 8.12 旧
        svc.set_by_tier(ModelTier.OPUS, 1.0)  # Phase 8.15 新
        # 互不干扰
        assert svc.get_current("run").usd == 5.0
        assert svc.get_by_tier(ModelTier.OPUS).usd == 1.0
