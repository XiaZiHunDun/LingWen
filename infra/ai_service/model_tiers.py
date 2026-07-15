"""多模型分级 — Phase 2.11

Doc 2 §6.3 + Doc 4 §2: 简单任务 → HAIKU 4.5,中等 → SONNET 4.6,复杂 → OPUS 4.5。

设计原则:
- ModelTier: str Enum,序列化友好 (.value == "haiku"/"sonnet"/"opus")
- ModelTierConfig: 模型静态信息 (model_name, cost, max_context)
- MODEL_TIERS: 全 3 tier 完整注册
- compute_cost: 标准成本计算 (input/output tokens → USD)

成本参考 (Claude 4.x, USD / 1M tokens):
- HAIKU 4.5:  $1 input / $5 output
- SONNET 4.6: $3 input / $15 output
- OPUS 4.5:   $15 input / $75 output
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelTier(str, Enum):
    """模型分级 (str Enum,便于 JSON 序列化)"""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


@dataclass(frozen=True)
class ModelTierConfig:
    """单 tier 静态配置

    Attributes:
        tier: ModelTier
        model_name: LLM 模型名 (e.g. "claude-haiku-4-5-20251001")
        input_cost_per_1m: 输入成本 USD / 1M tokens
        output_cost_per_1m: 输出成本 USD / 1M tokens
        max_context_tokens: 最大上下文窗口
    """

    tier: ModelTier
    model_name: str
    input_cost_per_1m: float
    output_cost_per_1m: float
    max_context_tokens: int


# 3 tier 完整注册 (per Doc 2 §6.3)
MODEL_TIERS: dict[ModelTier, ModelTierConfig] = {
    ModelTier.HAIKU: ModelTierConfig(
        tier=ModelTier.HAIKU,
        model_name="claude-haiku-4-5-20251001",
        input_cost_per_1m=1.0,
        output_cost_per_1m=5.0,
        max_context_tokens=200_000,
    ),
    ModelTier.SONNET: ModelTierConfig(
        tier=ModelTier.SONNET,
        model_name="claude-sonnet-4-6",
        input_cost_per_1m=3.0,
        output_cost_per_1m=15.0,
        max_context_tokens=200_000,
    ),
    ModelTier.OPUS: ModelTierConfig(
        tier=ModelTier.OPUS,
        model_name="claude-opus-4-7",
        input_cost_per_1m=15.0,
        output_cost_per_1m=75.0,
        max_context_tokens=200_000,
    ),
}


def compute_cost(input_tokens: int, output_tokens: int, tier: ModelTier) -> float:
    """计算单次调用的 USD 成本

    Args:
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        tier: 使用的模型 tier

    Returns:
        USD 成本 (浮点)
    """
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError(f"tokens must be non-negative: input={input_tokens}, output={output_tokens}")
    cfg = MODEL_TIERS[tier]
    return (
        input_tokens / 1_000_000 * cfg.input_cost_per_1m
        + output_tokens / 1_000_000 * cfg.output_cost_per_1m
    )
