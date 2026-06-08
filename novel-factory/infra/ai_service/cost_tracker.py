"""成本追踪 — Phase 2.13 + Phase 8.8 budget alarm

Doc 2 §6.3: 每次 LLM 调用记录 (scenario, tier, tokens, cost),支持维度聚合。

Phase 8.8 新增:
- CostBudgetExceeded exception
- CostTracker.check_budget() 同步检查总成本是否超阈值

设计:
- CostRecord: 不可变单次记录 (含时间戳)
- CostTracker: 内存累积器,按 scenario/tier 聚合
- 与 TieredRouter 注入点配合 (record(scenario, tier, in, out) → CostRecord)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .model_tiers import ModelTier, compute_cost


@dataclass(frozen=True)
class CostRecord:
    """单次 LLM 调用的成本记录 (frozen)

    Attributes:
        scenario: 12 SCENARIOS 之一
        tier: 实际使用的 ModelTier (降级后可能与 SCENARIO_TIER_MAP 不同)
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        cost_usd: USD 成本 (基于 tier 费率)
        timestamp: 记录时间 (UTC)
    """

    scenario: str
    tier: ModelTier
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CostRecord({self.scenario!r}, {self.tier.value}, "
            f"in={self.input_tokens}, out={self.output_tokens}, "
            f"${self.cost_usd:.4f})"
        )


class CostBudgetExceeded(Exception):
    """Phase 8.8: raised by CostTracker.check_budget when total_cost() > budget_usd.
    Phase 8.12: 扩 scope field (default 'run' 保 backward compat, Phase 8.8/8.9/8.10
                tests 0 改; 新 BudgetService.check_all_scopes 显式传 'run'/'day'/'week').
    Phase 8.15: 扩 tier field (default None 保 backward compat; 新
                BudgetService.check_all_tiers 传 scope='tier'+tier=ModelTier.X).

    Attributes are exposed for caller introspection (no re-parsing of message).
    Strictly greater than triggers (equal is OK).
    """

    def __init__(
        self,
        used_usd: float,
        budget_usd: float,
        scenario: str | None = None,
        scope: str = "run",  # 'run'|'day'|'week'|'tier'  (Phase 8.12 +1, Phase 8.15 +1)
        tier: ModelTier | None = None,  # NEW Phase 8.15 (default None, 旧 tests 0 改)
    ) -> None:
        self.used_usd = used_usd
        self.budget_usd = budget_usd
        self.scenario = scenario
        self.scope = scope
        self.tier = tier  # NEW Phase 8.15
        scenario_msg = f" (last scenario: {scenario})" if scenario else ""
        scope_msg = f" [scope={scope}]" if scope != "run" else ""
        tier_msg = f" [tier={tier.value}]" if scope == "tier" and tier else ""  # NEW Phase 8.15
        super().__init__(
            f"Cost budget exceeded: ${used_usd:.4f} / ${budget_usd:.4f}{scope_msg}{tier_msg}{scenario_msg}"
        )


class CostTracker:
    """成本追踪器 (内存累积)

    用法:
        tracker = CostTracker()
        rec = tracker.record("chapter_writing", ModelTier.SONNET, 1000, 500)
        # rec.cost_usd 自动按 SONNET 费率计算
        # tracker.cost_by_scenario() → {"chapter_writing": 0.0105}
    """

    def __init__(self) -> None:
        self._records: list[CostRecord] = []

    def record(
        self,
        scenario: str,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
    ) -> CostRecord:
        """记录一次调用,自动算 cost

        Args:
            scenario: 12 SCENARIOS 之一
            tier: 实际使用的 ModelTier
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数

        Returns:
            CostRecord (已自动填 cost_usd)

        Raises:
            ValueError: tokens 为负
        """
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError(
                f"tokens must be non-negative: input={input_tokens}, output={output_tokens}"
            )
        cost = compute_cost(input_tokens, output_tokens, tier)
        rec = CostRecord(
            scenario=scenario,
            tier=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
        self._records.append(rec)
        return rec

    def records(self) -> list[CostRecord]:
        """全部记录 (按时间顺序)"""
        return list(self._records)

    def total_cost(self, since: Optional[datetime] = None) -> float:
        """总成本 (USD). Phase 8.16: since 透传 (additive, default None 走旧 path)."""
        records = self._records if since is None else [
            r for r in self._records if r.timestamp >= since
        ]
        return sum(r.cost_usd for r in records)

    def total_tokens(self) -> tuple[int, int]:
        """总 (input, output) tokens"""
        in_t = sum(r.input_tokens for r in self._records)
        out_t = sum(r.output_tokens for r in self._records)
        return in_t, out_t

    def cost_by_scenario(self, since: Optional[datetime] = None) -> dict[str, float]:
        """按 scenario 聚合成本. Phase 8.16: since 透传 (additive, default None 走旧 path)."""
        records = self._records if since is None else [
            r for r in self._records if r.timestamp >= since
        ]
        result: dict[str, float] = {}
        for r in records:
            result[r.scenario] = result.get(r.scenario, 0.0) + r.cost_usd
        return result

    def cost_by_tier(self, since: Optional[datetime] = None) -> dict[ModelTier, float]:
        """按 tier 聚合成本. Phase 8.16: since 透传 (additive, default None 走旧 path)."""
        records = self._records if since is None else [
            r for r in self._records if r.timestamp >= since
        ]
        result: dict[ModelTier, float] = {}
        for r in records:
            result[r.tier] = result.get(r.tier, 0.0) + r.cost_usd
        return result

    def cost_by_day(self, since: Optional[datetime] = None) -> dict[str, float]:
        """Phase 8.23: 按 UTC 日期 (YYYY-MM-DD) 聚合 cost_usd, 给 dashboard trend chart.
        跟 cost_by_scenario/tier 同 since 透传 (additive, default None 走旧 path).

        Returns:
            dict[date_str, total_usd] — date_str 是 'YYYY-MM-DD' 格式.
            Python 3.7+ dict 保 insertion order, 记录按时间顺序插入 → 返回值按 date 升序
            (同一天多条 records 合并; 不同天按时间序).
        """
        records = self._records if since is None else [
            r for r in self._records if r.timestamp >= since
        ]
        result: dict[str, float] = {}
        for r in records:
            day = r.timestamp.date().isoformat()  # UTC date 'YYYY-MM-DD'
            result[day] = result.get(day, 0.0) + r.cost_usd
        return result

    def count_by_scenario(self) -> dict[str, int]:
        """按 scenario 计数"""
        result: dict[str, int] = {}
        for r in self._records:
            result[r.scenario] = result.get(r.scenario, 0) + 1
        return result

    def reset(self) -> None:
        """清空所有记录"""
        self._records.clear()

    def check_budget(self, budget_usd: Optional[float]) -> None:
        """Phase 8.8: enforce hard cap on cumulative cost. No-op when budget_usd is None.

        Raises CostBudgetExceeded if self.total_cost() > budget_usd.
        Strictly greater than (equal is OK, only over-budget triggers).

        Args:
            budget_usd: 阈值 (USD)。None 表示 unlimited,不抛。

        Raises:
            CostBudgetExceeded: 累计 cost > 阈值
        """
        if budget_usd is None:
            return  # unlimited
        used = self.total_cost()
        if used > budget_usd:
            last_scenario = self._records[-1].scenario if self._records else None
            raise CostBudgetExceeded(
                used_usd=used, budget_usd=budget_usd, scenario=last_scenario
            )
