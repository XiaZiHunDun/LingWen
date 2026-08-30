"""Budget DTOs for the workflows bounded context.

Phase 126 v16.5 #N.9: Extracted from ``apps/studio_api/models/workflow.py``
because BudgetSetRequest / BudgetTierSetRequest are orthogonal to the
workflow bounded context — they're budget-alarm DTOs that happen to share
a module with workflow models for historical reasons.

These DTOs are NOT promoted to ``lingwen_shared`` because:
- They are server-side only (no dashboard surface)
- They are persistence-coupled (Field constraints match the cost_tracker
  SQLite row schema)
- The dashboard does not consume them directly

Endpoints that use these:
- ``POST /workflows/budget`` → BudgetSetRequest (per-day / per-week USD)
- ``POST /workflows/budget/tier`` → BudgetTierSetRequest (per-tier USD)
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BudgetSetRequest(BaseModel):
    """Phase 8.12 T5: 设置 day/week budget (per-run 不暴露, run 启动时传)"""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"


class BudgetTierSetRequest(BaseModel):
    """Phase 8.15 T6: 设置 tier budget (haiku/sonnet/opus 各自)."""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"


__all__ = ["BudgetSetRequest", "BudgetTierSetRequest"]
