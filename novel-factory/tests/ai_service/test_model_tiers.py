"""Tests for ai_service.model_tiers (Phase 2.11).

Doc 2 §6.3 + Doc 4 §2: 多模型分级路由
- 简单任务 → HAIKU 4.5 (cost 1/3 of Sonnet)
- 中等任务 → SONNET 4.6 (默认)
- 复杂任务 → OPUS 4.5 (cost 3x of Sonnet)

覆盖:
- ModelTier enum (3 个 tier,str 值)
- MODEL_TIERS 字典含 3 个完整 ModelTierConfig
- SCENARIO_TIER_MAP 覆盖 12 SCENARIOS
- compute_cost() 计算公式
"""
from __future__ import annotations

import pytest

from infra.ai_service.model_tiers import (
    MODEL_TIERS,
    ModelTier,
    ModelTierConfig,
    compute_cost,
)
from infra.prompt_engineering import SCENARIOS
from infra.prompt_engineering.scenarios import SCENARIO_TIER_MAP


class TestModelTierEnum:
    """ModelTier 是 str Enum,3 个值"""

    def test_three_tiers(self):
        assert hasattr(ModelTier, "HAIKU")
        assert hasattr(ModelTier, "SONNET")
        assert hasattr(ModelTier, "OPUS")

    def test_str_values(self):
        assert ModelTier.HAIKU.value == "haiku"
        assert ModelTier.SONNET.value == "sonnet"
        assert ModelTier.OPUS.value == "opus"


class TestModelTierConfig:
    """ModelTierConfig dataclass 字段"""

    def test_config_fields(self):
        cfg = ModelTierConfig(
            tier=ModelTier.SONNET,
            model_name="claude-sonnet-4-6",
            input_cost_per_1m=3.0,
            output_cost_per_1m=15.0,
            max_context_tokens=200_000,
        )
        assert cfg.tier == ModelTier.SONNET
        assert cfg.model_name == "claude-sonnet-4-6"
        assert cfg.input_cost_per_1m == 3.0
        assert cfg.output_cost_per_1m == 15.0
        assert cfg.max_context_tokens == 200_000


class TestModelTiersRegistry:
    """MODEL_TIERS 字典含完整 3 个 tier"""

    def test_has_three_tiers(self):
        assert len(MODEL_TIERS) == 3
        assert ModelTier.HAIKU in MODEL_TIERS
        assert ModelTier.SONNET in MODEL_TIERS
        assert ModelTier.OPUS in MODEL_TIERS

    def test_haiku_cheapest(self):
        haiku = MODEL_TIERS[ModelTier.HAIKU]
        sonnet = MODEL_TIERS[ModelTier.SONNET]
        opus = MODEL_TIERS[ModelTier.OPUS]
        # HAIKU input cost < SONNET < OPUS
        assert haiku.input_cost_per_1m < sonnet.input_cost_per_1m
        assert sonnet.input_cost_per_1m < opus.input_cost_per_1m
        # Output 同理
        assert haiku.output_cost_per_1m < sonnet.output_cost_per_1m
        assert sonnet.output_cost_per_1m < opus.output_cost_per_1m

    def test_each_tier_has_model_name(self):
        for tier, cfg in MODEL_TIERS.items():
            assert cfg.tier == tier
            assert isinstance(cfg.model_name, str)
            assert len(cfg.model_name) > 0


class TestScenarioTierMap:
    """SCENARIO_TIER_MAP 覆盖 12 SCENARIOS"""

    def test_covers_all_scenarios(self):
        for s in SCENARIOS:
            assert s in SCENARIO_TIER_MAP, f"scenario {s} missing from SCENARIO_TIER_MAP"

    def test_all_values_are_tiers(self):
        for s, tier in SCENARIO_TIER_MAP.items():
            assert tier in ModelTier, f"scenario {s} maps to invalid tier {tier}"

    def test_simple_tasks_use_haiku(self):
        # Factual checks + simple extractions → HAIKU
        assert SCENARIO_TIER_MAP["worldview_check"] == ModelTier.HAIKU
        assert SCENARIO_TIER_MAP["character_consistency"] == ModelTier.HAIKU
        assert SCENARIO_TIER_MAP["hook_extraction"] == ModelTier.HAIKU
        assert SCENARIO_TIER_MAP["ai_trace_removal"] == ModelTier.HAIKU

    def test_complex_tasks_use_opus(self):
        # Structural/creative reasoning → OPUS
        assert SCENARIO_TIER_MAP["outline_review"] == ModelTier.OPUS
        assert SCENARIO_TIER_MAP["subplot_suggest"] == ModelTier.OPUS

    def test_writing_uses_sonnet(self):
        # Generation tasks → SONNET (balanced)
        assert SCENARIO_TIER_MAP["chapter_writing"] == ModelTier.SONNET
        assert SCENARIO_TIER_MAP["chapter_outline"] == ModelTier.SONNET


class TestComputeCost:
    """compute_cost(input_tokens, output_tokens, tier) → USD"""

    def test_basic_cost(self):
        # 1M input + 1M output at Sonnet rates
        cost = compute_cost(1_000_000, 1_000_000, ModelTier.SONNET)
        # cost = 3.0 + 15.0 = 18.0
        sonnet = MODEL_TIERS[ModelTier.SONNET]
        expected = sonnet.input_cost_per_1m + sonnet.output_cost_per_1m
        assert cost == pytest.approx(expected)

    def test_zero_tokens_zero_cost(self):
        cost = compute_cost(0, 0, ModelTier.OPUS)
        assert cost == 0.0

    def test_small_token_count(self):
        # 1000 input + 500 output at Haiku rates
        cost = compute_cost(1000, 500, ModelTier.HAIKU)
        haiku = MODEL_TIERS[ModelTier.HAIKU]
        expected = 1000 / 1_000_000 * haiku.input_cost_per_1m + 500 / 1_000_000 * haiku.output_cost_per_1m
        assert cost == pytest.approx(expected)

    def test_haiku_cheaper_than_opus(self):
        # Same tokens, haiku < opus
        cost_h = compute_cost(100_000, 50_000, ModelTier.HAIKU)
        cost_o = compute_cost(100_000, 50_000, ModelTier.OPUS)
        assert cost_h < cost_o


class TestImportContract:
    """Public API 完整性"""

    def test_top_level_imports(self):
        from infra.ai_service import (
            MODEL_TIERS,
            ModelTier,
            ModelTierConfig,
            compute_cost,
        )
        assert MODEL_TIERS is not None
        assert ModelTier is not None
        assert ModelTierConfig is not None
        assert callable(compute_cost)
