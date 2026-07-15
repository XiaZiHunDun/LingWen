"""Tests for CostBudgetExceeded.tier field (Phase 8.15)

Phase 8.8/8.12: CostBudgetExceeded raised with (used_usd, budget_usd, scenario, scope).
Phase 8.15: adds .tier: ModelTier | None for per-tier budget alarm.
             default None 保 Phase 8.8/8.12 50+ tests 0 改 backward compat.
             新 BudgetService.check_all_tiers 显式传 scope='tier'+tier=ModelTier.X.

测试覆盖:
- tier field default None (backward compat 旧 path)
- tier field 接受 ModelTier (str enum), .value 序列化 in __str__
- scope='tier' + tier → message 含 [tier=opus]
- scope='run' (Phase 8.8/8.12 旧 path) → message 0 tier_msg 0 scope_msg (default 0 变)
"""
from __future__ import annotations

from infra.ai_service.cost_tracker import CostBudgetExceeded
from infra.ai_service.model_tiers import ModelTier


def test_cost_budget_exceeded_tier_default_none():
    """Phase 8.15: tier field default None 保 Phase 8.8/8.12 backward compat."""
    exc = CostBudgetExceeded(used_usd=1.0, budget_usd=0.5, scope="run")
    assert exc.tier is None


def test_cost_budget_exceeded_tier_field_set():
    """Phase 8.15: tier field 接受 ModelTier (str enum 序列化 .value 在 __str__)."""
    exc = CostBudgetExceeded(
        used_usd=1.5, budget_usd=1.0, scope="tier", tier=ModelTier.OPUS,
    )
    assert exc.tier == ModelTier.OPUS
    assert exc.scope == "tier"
    assert "tier=opus" in str(exc)


def test_cost_budget_exceeded_tier_message_no_tier_msg_when_scope_run():
    """Phase 8.15: scope='run' (Phase 8.8/8.12 旧 path) 不出 tier_msg."""
    exc = CostBudgetExceeded(used_usd=1.0, budget_usd=0.5, scope="run")
    msg = str(exc)
    assert "tier=" not in msg  # 旧 path 0 tier_msg
    assert "scope=" not in msg  # scope='run' default 不出 scope_msg
