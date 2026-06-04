"""Tests for ai_service.tiered_router (Phase 2.12).

Doc 2 §6.3: 任务复杂度 → tier → 模型 → 实际调用。
- TieredRouter.route(scenario) → (ModelTier, model_name)
- TieredRouter.generate(scenario, prompt) → str
  - 解析 scenario → tier → model_name
  - 调底层 AIRouter/Provider 生成
  - 失败时自动 downgrade (OPUS → SONNET → HAIKU)
- 注入 AIRouter (解耦)
- 调用 CostTracker 记录 (Phase 2.13 配合)
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

import pytest

from infra.ai_service.base import AIProvider, AIProviderError, ProviderConfig
from infra.ai_service.model_tiers import (
    MODEL_TIERS,
    ModelTier,
    ModelTierConfig,
)
from infra.ai_service.tiered_router import (
    TieredRouter,
    TieredRouterError,
)
from infra.prompt_engineering import SCENARIO_TIER_MAP


class _StubProvider(AIProvider):
    """测试用 provider,只记录被调用 + 返回固定内容或抛错"""

    def __init__(self, name: str, response: str = "ok", raise_exc: Optional[Exception] = None):
        super().__init__(ProviderConfig(api_key="stub-key", model=name))
        self._name = name
        self._response = response
        self._raise = raise_exc
        self.calls: list[str] = []

    def get_provider_name(self) -> str:
        return self._name

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append(prompt)
        if self._raise:
            raise self._raise
        return self._response

    def embed(self, text: str):  # pragma: no cover
        return [0.0]

    def batch_generate(self, prompts, **kwargs):  # pragma: no cover
        return [self.generate(p) for p in prompts]


def _make_router(
    tier_responses: dict[ModelTier, str | Exception],
) -> tuple[TieredRouter, dict[ModelTier, _StubProvider]]:
    """构造 TieredRouter,每个 tier 一个 stub provider"""
    providers: dict[ModelTier, _StubProvider] = {}
    for tier, resp in tier_responses.items():
        if isinstance(resp, Exception):
            providers[tier] = _StubProvider(MODEL_TIERS[tier].model_name, raise_exc=resp)
        else:
            providers[tier] = _StubProvider(MODEL_TIERS[tier].model_name, response=resp)
    router = TieredRouter(providers)
    return router, providers


class TestTieredRouterInit:
    """TieredRouter 接受 {tier: provider} 字典"""

    def test_three_tiers_required(self):
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        assert router.get_tier_for_scenario("chapter_writing") == ModelTier.SONNET

    def test_missing_tier_raises(self):
        # 缺 OPUS → 报错
        with pytest.raises(TieredRouterError):
            TieredRouter({
                ModelTier.HAIKU: MagicMock(),
                ModelTier.SONNET: MagicMock(),
            })


class TestRouteByScenario:
    """route(scenario) → (tier, model_name)"""

    def test_simple_task_uses_haiku(self, tmp_path):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        tier, model = router.route("hook_extraction")
        assert tier == ModelTier.HAIKU
        assert model == "claude-haiku-4-5-20251001"

    def test_writing_uses_sonnet(self, tmp_path):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        tier, model = router.route("chapter_writing")
        assert tier == ModelTier.SONNET
        assert model == "claude-sonnet-4-6"

    def test_creative_uses_opus(self, tmp_path):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        tier, model = router.route("subplot_suggest")
        assert tier == ModelTier.OPUS
        assert model == "claude-opus-4-7"

    def test_unknown_scenario_raises(self, tmp_path):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        with pytest.raises(TieredRouterError):
            router.route("unknown_scenario")


class TestGenerateByScenario:
    """generate(scenario, prompt) → str, 自动选 tier"""

    def test_simple_task_calls_haiku(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "haiku-output",
            ModelTier.SONNET: "sonnet-output",
            ModelTier.OPUS: "opus-output",
        })
        result = router.generate("hook_extraction", "test prompt")
        assert result == "haiku-output"
        assert len(providers[ModelTier.HAIKU].calls) == 1
        # 其它 tier 不应被调用
        assert len(providers[ModelTier.SONNET].calls) == 0
        assert len(providers[ModelTier.OPUS].calls) == 0

    def test_writing_calls_sonnet(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        result = router.generate("chapter_writing", "test")
        assert result == "s"
        assert len(providers[ModelTier.SONNET].calls) == 1

    def test_creative_calls_opus(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        result = router.generate("subplot_suggest", "test")
        assert result == "o"
        assert len(providers[ModelTier.OPUS].calls) == 1


class TestDowngradeOnFailure:
    """高 tier 失败时,自动降级到下一 tier"""

    def test_opus_fails_downgrade_to_sonnet(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "haiku-output",
            ModelTier.SONNET: "sonnet-output",
            ModelTier.OPUS: AIProviderError("opus down"),
        })
        # subplot_suggest 原本是 OPUS,失败 → 降级 SONNET
        result = router.generate("subplot_suggest", "test")
        assert result == "sonnet-output"
        assert len(providers[ModelTier.OPUS].calls) == 1
        assert len(providers[ModelTier.SONNET].calls) == 1

    def test_opus_and_sonnet_fail_downgrade_to_haiku(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "haiku-output",
            ModelTier.SONNET: AIProviderError("sonnet down"),
            ModelTier.OPUS: AIProviderError("opus down"),
        })
        result = router.generate("subplot_suggest", "test")
        assert result == "haiku-output"
        # 3 个 tier 都试了
        assert len(providers[ModelTier.OPUS].calls) == 1
        assert len(providers[ModelTier.SONNET].calls) == 1
        assert len(providers[ModelTier.HAIKU].calls) == 1

    def test_all_tiers_fail_raises(self):
        router, _ = _make_router({
            ModelTier.HAIKU: AIProviderError("haiku down"),
            ModelTier.SONNET: AIProviderError("sonnet down"),
            ModelTier.OPUS: AIProviderError("opus down"),
        })
        with pytest.raises(TieredRouterError):
            router.generate("subplot_suggest", "test")

    def test_no_downgrade_when_disabled(self):
        """disable_downgrade=True: 失败不降级,直接抛错"""
        router, providers = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: AIProviderError("opus down"),
        })
        router.disable_downgrade = True
        with pytest.raises(TieredRouterError):
            router.generate("subplot_suggest", "test")
        # 其它 tier 不应被调用
        assert len(providers[ModelTier.HAIKU].calls) == 0
        assert len(providers[ModelTier.SONNET].calls) == 0


class TestScenarioMap:
    """12 SCENARIOS 全部覆盖"""

    def test_all_scenarios_route(self):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        for scenario in SCENARIO_TIER_MAP:
            tier, _ = router.route(scenario)
            assert tier == SCENARIO_TIER_MAP[scenario]


class TestImportContract:
    """Public API 完整性"""

    def test_top_level_imports(self):
        from infra.ai_service import TieredRouter, TieredRouterError
        assert TieredRouter is not None
        assert issubclass(TieredRouterError, Exception)
