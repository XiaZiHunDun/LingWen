"""Tests for ai_service.cost_tracker (Phase 2.13).

Doc 2 §6.3: 每 scenario/tier 调用后记录成本,支持按维度聚合。

API:
- CostRecord frozen dataclass: (scenario, tier, input_tokens, output_tokens, cost_usd, timestamp)
- CostTracker:
  - record(scenario, tier, input_tokens, output_tokens) → CostRecord
  - total_cost() → USD 总额
  - cost_by_scenario() → dict[scenario, USD]
  - cost_by_tier() → dict[ModelTier, USD]
  - count_by_scenario() → dict[scenario, int]
  - reset() 清空
  - records() 全部记录列表
"""
from __future__ import annotations

from datetime import datetime

import pytest

from infra.ai_service.cost_tracker import CostRecord, CostTracker
from infra.ai_service.model_tiers import ModelTier, compute_cost


class TestCostRecord:
    """CostRecord 不可变 + 字段语义"""

    def test_frozen_immutable(self):
        r = CostRecord(
            scenario="chapter_writing",
            tier=ModelTier.SONNET,
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.0105,
        )
        with pytest.raises((AttributeError, Exception)):
            r.scenario = "other"  # type: ignore[misc]

    def test_fields_accessible(self):
        r = CostRecord(
            scenario="s",
            tier=ModelTier.HAIKU,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.0001,
        )
        assert r.scenario == "s"
        assert r.tier == ModelTier.HAIKU
        assert r.input_tokens == 100
        assert r.output_tokens == 50
        assert r.cost_usd == 0.0001


class TestCostTrackerBasic:
    """基本 record + 查询"""

    def test_empty_tracker(self):
        tracker = CostTracker()
        assert tracker.records() == []
        assert tracker.total_cost() == 0.0

    def test_record_one_call(self):
        tracker = CostTracker()
        rec = tracker.record("chapter_writing", ModelTier.SONNET, 1_000_000, 1_000_000)
        assert rec.scenario == "chapter_writing"
        assert rec.tier == ModelTier.SONNET
        # cost = 3 + 15 = 18
        assert rec.cost_usd == pytest.approx(18.0)

    def test_total_cost_after_multiple(self):
        tracker = CostTracker()
        tracker.record("chapter_writing", ModelTier.SONNET, 1_000_000, 1_000_000)
        tracker.record("hook_extraction", ModelTier.HAIKU, 100_000, 50_000)
        # 18 + 0.1*1 + 0.05*5 = 18 + 0.1 + 0.25 = 18.35
        haiku_cost = compute_cost(100_000, 50_000, ModelTier.HAIKU)
        expected = 18.0 + haiku_cost
        assert tracker.total_cost() == pytest.approx(expected)


class TestCostAggregation:
    """按 scenario / tier 维度聚合"""

    def test_cost_by_scenario(self):
        tracker = CostTracker()
        tracker.record("chapter_writing", ModelTier.SONNET, 1_000_000, 0)
        tracker.record("chapter_writing", ModelTier.SONNET, 0, 1_000_000)
        tracker.record("hook_extraction", ModelTier.HAIKU, 0, 1_000_000)
        by_scenario = tracker.cost_by_scenario()
        # chapter_writing: 3 + 15 = 18; hook_extraction: 5
        assert by_scenario["chapter_writing"] == pytest.approx(18.0)
        assert by_scenario["hook_extraction"] == pytest.approx(5.0)

    def test_cost_by_tier(self):
        tracker = CostTracker()
        tracker.record("a", ModelTier.SONNET, 1_000_000, 0)  # 3
        tracker.record("b", ModelTier.SONNET, 0, 1_000_000)  # 15
        tracker.record("c", ModelTier.OPUS, 1_000_000, 0)    # 15
        by_tier = tracker.cost_by_tier()
        assert by_tier[ModelTier.SONNET] == pytest.approx(18.0)
        assert by_tier[ModelTier.OPUS] == pytest.approx(15.0)
        assert ModelTier.HAIKU not in by_tier  # 没有 haiku 调用

    def test_count_by_scenario(self):
        tracker = CostTracker()
        tracker.record("chapter_writing", ModelTier.SONNET, 100, 50)
        tracker.record("chapter_writing", ModelTier.SONNET, 100, 50)
        tracker.record("hook_extraction", ModelTier.HAIKU, 100, 50)
        counts = tracker.count_by_scenario()
        assert counts["chapter_writing"] == 2
        assert counts["hook_extraction"] == 1


class TestCostTrackerReset:
    """reset() 清空记录"""

    def test_reset_clears_records(self):
        tracker = CostTracker()
        tracker.record("a", ModelTier.SONNET, 1000, 500)
        assert len(tracker.records()) == 1
        tracker.reset()
        assert tracker.records() == []
        assert tracker.total_cost() == 0.0


class TestCostTrackerEdgeCases:
    """边界场景"""

    def test_zero_tokens(self):
        tracker = CostTracker()
        rec = tracker.record("test", ModelTier.OPUS, 0, 0)
        assert rec.cost_usd == 0.0

    def test_negative_tokens_raises(self):
        tracker = CostTracker()
        with pytest.raises(ValueError):
            tracker.record("test", ModelTier.SONNET, -100, 0)
        with pytest.raises(ValueError):
            tracker.record("test", ModelTier.SONNET, 0, -100)


class TestImportContract:
    """Public API 完整性"""

    def test_top_level_imports(self):
        from infra.ai_service import CostRecord, CostTracker
        assert CostRecord is not None
        assert CostTracker is not None

    def test_cost_record_repr_contains_scenario(self):
        r = CostRecord(
            scenario="chapter_writing",
            tier=ModelTier.SONNET,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
        )
        text = repr(r)
        assert "chapter_writing" in text
        assert "sonnet" in text


class TestCheckBudget:
    """Phase 8.8: CostTracker.check_budget() enforces hard cap on cumulative cost.

    - check_budget(None) → no-op (unlimited)
    - check_budget(0.0) with any cost → raise
    - check_budget(very_large) → no-op
    - check_budget(very_small) → raise
    - exact equal → no raise (strict >)
    """

    def test_check_budget_none_always_passes(self):
        tracker = CostTracker()
        # Record 大量 cost, budget=None 不该 raise
        tracker.record("s1", ModelTier.OPUS, 1_000_000, 1_000_000)  # cost = $15 + $75 = $90
        tracker.check_budget(None)  # 不抛

    def test_check_budget_under_threshold_passes(self):
        tracker = CostTracker()
        # cost = $10.5 (1M SONNET input $3 + 500K SONNET output $7.5)
        tracker.record("s1", ModelTier.SONNET, 1_000_000, 500_000)
        # budget = $20.0, used = $10.5, OK
        tracker.check_budget(20.0)

    def test_check_budget_over_threshold_raises(self):
        from infra.ai_service.cost_tracker import CostBudgetExceeded

        tracker = CostTracker()
        # 制造 $90 cost
        tracker.record("s1", ModelTier.OPUS, 1_000_000, 1_000_000)
        # budget = $0.001, used = $90, raise
        with pytest.raises(CostBudgetExceeded) as exc_info:
            tracker.check_budget(0.001)
        # Attributes exposed for caller introspection
        assert exc_info.value.used_usd == pytest.approx(90.0)
        assert exc_info.value.budget_usd == 0.001
        assert exc_info.value.scenario == "s1"
        # Message also informative
        assert "exceeded" in str(exc_info.value).lower()

    def test_check_budget_exact_threshold_passes(self):
        tracker = CostTracker()
        # cost = $90 (OPUS 1M+1M)
        tracker.record("s1", ModelTier.OPUS, 1_000_000, 1_000_000)
        used = tracker.total_cost()
        # 严格 > 触发,等号 OK
        tracker.check_budget(used)  # 应该不抛


class TestCostBudgetExceededMessage:
    """Phase 8.12: CostBudgetExceeded.__str__ scope_msg backward compat.

    - scope='run' (default) → message 0 含 [scope=run] (Phase 8.8/8.9/8.10 message 0 改)
    - scope='day' / scope='week' → message 含 [scope=day] / [scope=week] 帮 ops 区分
    """

    def test_cost_budget_exceeded_message_includes_scope(self) -> None:
        """Phase 8.12: scope='day' or 'week' appears in message, default 'run' does not"""
        from infra.ai_service.cost_tracker import CostBudgetExceeded

        # Default 'run' scope → no [scope=run] in message
        exc_default = CostBudgetExceeded(
            used_usd=0.15, budget_usd=0.10, scenario="chapter_writing"
        )
        assert exc_default.scope == "run"
        assert "[scope=run]" not in str(exc_default)
        assert "(last scenario: chapter_writing)" in str(exc_default)

        # Explicit 'day' scope → [scope=day] appears
        exc_day = CostBudgetExceeded(used_usd=0.6, budget_usd=0.5, scope="day")
        assert exc_day.scope == "day"
        assert "[scope=day]" in str(exc_day)

        # Explicit 'week' scope → [scope=week] appears
        exc_week = CostBudgetExceeded(used_usd=2.1, budget_usd=2.0, scope="week")
        assert exc_week.scope == "week"
        assert "[scope=week]" in str(exc_week)


class TestCostTrackerSinceFilter:
    """Phase 8.16: total_cost / cost_by_scenario / cost_by_tier 加 since 透传
    过滤 timestamp < since 的 records. since=None 走旧 path (0 改)."""

    def test_total_cost_with_since_filters_old_records(self) -> None:
        """since=now → 旧 records 全过滤, total=0.0"""
        from datetime import datetime, timedelta, timezone

        tracker = CostTracker()
        tracker.record("s1", ModelTier.SONNET, 1000, 500)  # 0.0105
        # since=now+1s (未来) → 全部 records 都在 since 之前
        future = datetime.now(timezone.utc) + timedelta(seconds=1)
        assert tracker.total_cost(since=future) == 0.0

    def test_cost_by_scenario_with_since_returns_only_recent(self) -> None:
        """since=now-1h → 全部 records 仍 >= since (新近插入) → 走全量"""
        from datetime import datetime, timedelta, timezone

        tracker = CostTracker()
        tracker.record("chapter_writing", ModelTier.SONNET, 1_000, 500)  # 0.0105
        tracker.record("hook_extraction", ModelTier.HAIKU, 100, 50)     # 0.00035
        # 1h 前 → 全部 records 都在 since 之后
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        by_scenario = tracker.cost_by_scenario(since=one_hour_ago)
        assert by_scenario == {
            "chapter_writing": pytest.approx(0.0105),
            "hook_extraction": pytest.approx(0.00035),
        }

    def test_cost_by_tier_with_since_none_returns_all(self) -> None:
        """backward compat: since=None 走旧 path, 返全部 records 聚合"""
        tracker = CostTracker()
        tracker.record("a", ModelTier.SONNET, 100, 50)
        tracker.record("b", ModelTier.OPUS, 100, 50)
        by_tier = tracker.cost_by_tier(since=None)
        assert ModelTier.SONNET in by_tier
        assert ModelTier.OPUS in by_tier


class TestCostTrackerCostByDay:
    """Phase 8.23: cost_by_day() 按 UTC 日期 (YYYY-MM-DD) 聚合 USD
    给 dashboard trend chart. 跟 cost_by_scenario/tier 同 since 透传."""

    def test_cost_by_day_groups_by_utc_date(self) -> None:
        """3 records 跨 2 天 → 2 keys, 各天 sum 正确"""
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch

        tracker = CostTracker()
        # Patch CostRecord.timestamp 来制造 2 天的 records
        day1 = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 6, 2, 14, 0, 0, tzinfo=timezone.utc)
        # 直接插预制 timestamp 的 records (绕过 record() 调 datetime.now)
        from infra.ai_service.cost_tracker import CostRecord
        from infra.ai_service.model_tiers import compute_cost
        tracker._records.append(CostRecord(
            scenario="chapter_writing", tier=ModelTier.SONNET,
            input_tokens=1000, output_tokens=500, cost_usd=0.0105,
            timestamp=day1,
        ))
        tracker._records.append(CostRecord(
            scenario="hook_extraction", tier=ModelTier.HAIKU,
            input_tokens=100, output_tokens=50, cost_usd=0.00035,
            timestamp=day1,
        ))
        tracker._records.append(CostRecord(
            scenario="chapter_review", tier=ModelTier.SONNET,
            input_tokens=500, output_tokens=250, cost_usd=0.00525,
            timestamp=day2,
        ))
        by_day = tracker.cost_by_day()
        assert by_day == {
            "2026-06-01": pytest.approx(0.0105 + 0.00035, abs=1e-9),
            "2026-06-02": pytest.approx(0.00525, abs=1e-9),
        }

    def test_cost_by_day_with_since_filters_old_records(self) -> None:
        """since=future → 全部 records 都在 since 之前 → 返 {} (0 个 keys)"""
        from datetime import datetime, timedelta, timezone

        tracker = CostTracker()
        tracker.record("chapter_writing", ModelTier.SONNET, 1000, 500)
        future = datetime.now(timezone.utc) + timedelta(seconds=1)
        assert tracker.cost_by_day(since=future) == {}

    def test_cost_by_day_empty_tracker_returns_empty_dict(self) -> None:
        """backward compat: 空 tracker → 返 {}, 不抛"""
        tracker = CostTracker()
        assert tracker.cost_by_day() == {}
        assert tracker.cost_by_day(since=None) == {}
