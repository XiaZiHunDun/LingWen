"""多模型分级路由 — Phase 2.12

Doc 2 §6.3 + Doc 4 §2: 任务复杂度 → tier → 模型 → 实际调用 + 降级。

设计:
- TieredRouter 接受 {ModelTier: AIProvider} 字典 (3 个 tier 必备)
- route(scenario): scenario → tier → model_name
- generate(scenario, prompt): 调该 tier provider;失败时自动降级 (OPUS → SONNET → HAIKU)
- disable_downgrade: 关闭降级 (失败直接抛错,用于 A/B 测试)
- CostTracker 注入点 (Phase 2.13 接入)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from .base import AIProvider, AIProviderError
from .model_tiers import MODEL_TIERS, ModelTier


# CostTracker 抽象 (Phase 2.13 接入)
class _CostTrackerLike(Protocol):
    def record(self, scenario: str, tier: ModelTier, input_tokens: int, output_tokens: int) -> None: ...


class TieredRouterError(AIProviderError):
    """TieredRouter 错误 (scenario 未知/所有 tier 失败)"""


@dataclass
class _CallRecord:
    """单次 generate 调用记录 (供 CostTracker 注入)"""

    scenario: str
    tier: ModelTier
    model_name: str
    prompt: str
    response: str


class TieredRouter:
    """按 scenario 自动选 tier + 失败时降级

    Args:
        providers: {ModelTier: AIProvider} 字典 (3 个 tier 必备)
        cost_tracker: 可选 CostTracker 注入
    """

    # 降级顺序 (高 → 低)
    DOWNGRADE_ORDER: tuple[ModelTier, ...] = (ModelTier.OPUS, ModelTier.SONNET, ModelTier.HAIKU)

    def __init__(
        self,
        providers: dict[ModelTier, AIProvider],
        cost_tracker: Optional[_CostTrackerLike] = None,
    ) -> None:
        missing = set(self.DOWNGRADE_ORDER) - set(providers.keys())
        if missing:
            raise TieredRouterError(
                f"missing tier providers: {sorted(missing, key=lambda t: t.value)}"
            )
        self._providers: dict[ModelTier, AIProvider] = dict(providers)
        self._cost_tracker = cost_tracker
        # 降级开关 (True=启用降级,默认)
        self.disable_downgrade: bool = False

    def get_provider(self, tier: ModelTier) -> AIProvider:
        """获取指定 tier 的 provider"""
        if tier not in self._providers:
            raise TieredRouterError(f"tier {tier.value} not registered")
        return self._providers[tier]

    def route(self, scenario: str) -> tuple[ModelTier, str]:
        """scenario → (tier, model_name)

        Args:
            scenario: 12 SCENARIOS 之一

        Returns:
            (tier, model_name) 元组

        Raises:
            TieredRouterError: scenario 不在 SCENARIO_TIER_MAP
        """
        # 延迟导入避免循环
        from infra.prompt_engineering.scenarios import SCENARIO_TIER_MAP

        if scenario not in SCENARIO_TIER_MAP:
            raise TieredRouterError(
                f"unknown scenario: {scenario!r}; expected one of {sorted(SCENARIO_TIER_MAP)}"
            )
        tier = SCENARIO_TIER_MAP[scenario]
        return tier, MODEL_TIERS[tier].model_name

    def get_tier_for_scenario(self, scenario: str) -> ModelTier:
        """便捷方法: 只返回 tier"""
        tier, _ = self.route(scenario)
        return tier

    def generate(self, scenario: str, prompt: str, **kwargs) -> str:
        """按 scenario 路由并生成,失败时降级

        Args:
            scenario: 12 SCENARIOS 之一
            prompt: 输入提示词
            **kwargs: 传给底层 provider 的额外参数

        Returns:
            生成的文本

        Raises:
            TieredRouterError: scenario 未知/所有 tier 失败
        """
        primary_tier, _ = self.route(scenario)
        # 降级链: 起点 = primary_tier,降级方向 = 越来越便宜
        downgrade_chain = self._build_downgrade_chain(primary_tier)
        last_error: Optional[Exception] = None

        for tier in downgrade_chain:
            provider = self._providers[tier]
            try:
                response = provider.generate(prompt, **kwargs)
                # 成功后通知 cost_tracker (若注入)
                self._notify_tracker(scenario, tier, prompt, response)
                return response
            except Exception as exc:
                last_error = exc
                if self.disable_downgrade:
                    break
                continue

        raise TieredRouterError(
            f"all tiers failed for scenario {scenario!r}: {last_error}"
        )

    def _build_downgrade_chain(self, start_tier: ModelTier) -> tuple[ModelTier, ...]:
        """从 start_tier 开始的降级链 (高 → 低)"""
        idx = self.DOWNGRADE_ORDER.index(start_tier)
        return self.DOWNGRADE_ORDER[idx:]

    def _notify_tracker(
        self, scenario: str, tier: ModelTier, prompt: str, response: str
    ) -> None:
        """通知 cost_tracker (若注入)"""
        if self._cost_tracker is None:
            return
        # 简单估算: 1 token ≈ 4 chars (英文/中文混合体)
        input_tokens = len(prompt) // 4
        output_tokens = len(response) // 4
        self._cost_tracker.record(scenario, tier, input_tokens, output_tokens)
