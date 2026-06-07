"""Tests for CostTrackerDB (Phase 8.5)

Doc 4 §11 Phase 8.5: SQLite 持久化 CostRecord (mirror ReadingPowerDB pattern).

测试目标:
- DB schema 创建 + 索引
- record / records / total_cost / cost_by_scenario / cost_by_tier 行为
- persistence: close conn 后重新 open DB 还能读到 (DB file on disk)
- 幂等性: init_db 调多次不报错
- 路径: 默认 db_path 在 infra/.state/cost_tracker.db
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from infra.agent_system.cost_persistence import CostTrackerDB
from infra.ai_service.cost_tracker import CostRecord
from infra.ai_service.model_tiers import ModelTier


class TestCostTrackerDB:
    """CostTrackerDB 行为 — mirror ReadingPowerDB test patterns"""

    def test_init_db_creates_table(self, tmp_path: Path) -> None:
        """DB 不存在 → 调 init_db → cost_records table 存在"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        with sqlite3.connect(str(tmp_path / "test.db")) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cost_records'"
            )
            assert cursor.fetchone() is not None, "cost_records table should exist after init_db()"

    def test_record_persists_to_db(self, tmp_path: Path) -> None:
        """record 1 条 → records() 返回 1 条 + 字段对齐"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        rec = db.record("chapter_writing", ModelTier.SONNET, 1000, 500)
        records = db.records()
        assert len(records) == 1
        assert isinstance(records[0], CostRecord)
        assert records[0].scenario == "chapter_writing"
        assert records[0].tier == ModelTier.SONNET
        assert records[0].input_tokens == 1000
        assert records[0].output_tokens == 500
        # SONNET 费率: $3/1M input + $15/1M output
        # 1000/1M * 3 + 500/1M * 15 = 0.003 + 0.0075 = 0.0105
        assert records[0].cost_usd == pytest.approx(0.0105, abs=1e-9)
        # timestamp 是 UTC datetime
        assert rec.timestamp.tzinfo is not None

    def test_total_cost_aggregates_correctly(self, tmp_path: Path) -> None:
        """record 3 条 (不同 scenario/tier) → total_cost() 等于 3 条 sum"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        # HAIKU 1000+500 = 0.001 + 0.0025 = 0.0035
        db.record("hook_extraction", ModelTier.HAIKU, 1000, 500)
        # SONNET 2000+1000 = 0.006 + 0.015 = 0.021
        db.record("chapter_writing", ModelTier.SONNET, 2000, 1000)
        # OPUS 100+100 = 0.0015 + 0.0075 = 0.009
        db.record("outline_review", ModelTier.OPUS, 100, 100)
        assert db.total_cost() == pytest.approx(0.0035 + 0.021 + 0.009, abs=1e-9)

    def test_cost_by_scenario_groups_correctly(self, tmp_path: Path) -> None:
        """2 scenario 各 2 条 → cost_by_scenario() 返 2 keys"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        db.record("chapter_writing", ModelTier.SONNET, 1000, 500)  # 0.0105
        db.record("chapter_writing", ModelTier.SONNET, 100, 50)    # 0.00105
        db.record("chapter_review", ModelTier.SONNET, 200, 100)    # 0.0021
        db.record("chapter_review", ModelTier.SONNET, 300, 150)    # 0.00315
        groups = db.cost_by_scenario()
        assert set(groups.keys()) == {"chapter_writing", "chapter_review"}
        assert groups["chapter_writing"] == pytest.approx(0.0105 + 0.00105, abs=1e-9)
        assert groups["chapter_review"] == pytest.approx(0.0021 + 0.00315, abs=1e-9)

    def test_cost_by_tier_groups_correctly(self, tmp_path: Path) -> None:
        """HAIKU 1 + SONNET 2 → cost_by_tier() 返 2 keys"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        db.record("hook_extraction", ModelTier.HAIKU, 1000, 500)  # 0.0035
        db.record("chapter_writing", ModelTier.SONNET, 1000, 500)  # 0.0105
        db.record("chapter_review", ModelTier.SONNET, 200, 100)    # 0.0021
        groups = db.cost_by_tier()
        assert set(groups.keys()) == {ModelTier.HAIKU, ModelTier.SONNET}
        assert groups[ModelTier.HAIKU] == pytest.approx(0.0035, abs=1e-9)
        assert groups[ModelTier.SONNET] == pytest.approx(0.0105 + 0.0021, abs=1e-9)

    def test_records_survives_reopen(self, tmp_path: Path) -> None:
        """record → close conn → 重新 open DB → records 还在 (持久化验证)"""
        db_path = tmp_path / "persist.db"
        db1 = CostTrackerDB(db_path=db_path)
        db1.init_db()
        db1.record("chapter_writing", ModelTier.SONNET, 1000, 500)

        # 重新 open — 模拟 "process restart" 场景
        db2 = CostTrackerDB(db_path=db_path)
        records = db2.records()
        assert len(records) == 1
        assert records[0].scenario == "chapter_writing"
        assert records[0].input_tokens == 1000
        assert records[0].output_tokens == 500
        assert records[0].cost_usd == pytest.approx(0.0105, abs=1e-9)

    def test_init_db_idempotent(self, tmp_path: Path) -> None:
        """调 2 次 init_db 不报错 (CREATE TABLE IF NOT EXISTS)"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        db.init_db()  # 第二次不报错
        # 仍可写
        db.record("chapter_writing", ModelTier.SONNET, 100, 50)
        assert len(db.records()) == 1

    def test_db_path_under_state_dir(self) -> None:
        """默认 db_path 在 infra/.state/cost_tracker.db (gitignored)"""
        # 不传 db_path — 用默认 _DB_PATH
        from infra.agent_system.cost_persistence import _DB_PATH

        assert _DB_PATH.name == "cost_tracker.db"
        # 父目录 = infra/.state (跟 reading_power.db / workflow.db 错开)
        assert _DB_PATH.parent.name == ".state"
        assert _DB_PATH.parent.parent.name == "infra"


class TestCostTrackerDBSinceFilter:
    """Phase 8.16: total_cost / cost_by_scenario / cost_by_tier 加 since 透传
    (SQL WHERE timestamp >= ?). since=None 走旧 path (0 改)."""

    def test_total_cost_with_since_filters_old_records(self, tmp_path: Path) -> None:
        """since=future → SQL WHERE 排除全部 records, total=0.0"""
        from datetime import datetime, timedelta, timezone

        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        db.record("chapter_writing", ModelTier.SONNET, 1000, 500)  # 0.0105
        future = datetime.now(timezone.utc) + timedelta(seconds=1)
        assert db.total_cost(since=future) == 0.0

    def test_cost_by_scenario_with_since_returns_recent(self, tmp_path: Path) -> None:
        """since=1h ago → 全部新近 records >= since → 走全量"""
        from datetime import datetime, timedelta, timezone

        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        db.record("chapter_writing", ModelTier.SONNET, 1000, 500)  # 0.0105
        db.record("hook_extraction", ModelTier.HAIKU, 100, 50)     # 0.00035
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        by_scenario = db.cost_by_scenario(since=one_hour_ago)
        assert by_scenario == {
            "chapter_writing": pytest.approx(0.0105, abs=1e-9),
            "hook_extraction": pytest.approx(0.00035, abs=1e-9),
        }

    def test_cost_by_tier_with_since_none_returns_all(self, tmp_path: Path) -> None:
        """backward compat: since=None → 走旧 SQL (no WHERE), 返全量"""
        db = CostTrackerDB(db_path=tmp_path / "test.db")
        db.init_db()
        db.record("a", ModelTier.SONNET, 100, 50)
        db.record("b", ModelTier.OPUS, 100, 50)
        by_tier = db.cost_by_tier(since=None)
        assert set(by_tier.keys()) == {ModelTier.SONNET, ModelTier.OPUS}
