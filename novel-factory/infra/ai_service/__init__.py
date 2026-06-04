"""AI Service 模块

提供统一的AI Provider接口，支持多提供商（OpenAI、Anthropic等）

R3-012: Provider 类型注册化 — 3 个内置 provider 通过
`@register_provider` 装饰器自动注册到 `_PROVIDER_REGISTRY`。
router.py 通过 `get_provider_class(name)` 查找,新增 provider 只需
写一个 `<name>_provider.py` 并加 `@register_provider("name")`,
无需改 router / __init__。
"""

# 触发各 provider 模块的 @register_provider 装饰器
from . import (
    anthropic_provider,  # noqa: F401
    minimax_provider,  # noqa: F401
    openai_provider,  # noqa: F401
)
from .anthropic_provider import AnthropicProvider
from .base import (
    AIProvider,
    AIProviderError,
    APIError,
    NetworkError,
    ProviderConfig,
    ProviderConfigError,
    TimeoutError,
    get_provider_class,
    list_registered_providers,
    register_provider,
)

# Phase 2.11 — 多模型分级路由
from .cost_tracker import CostRecord, CostTracker
from .minimax_provider import MiniMaxProvider
from .model_tiers import MODEL_TIERS, ModelTier, ModelTierConfig, compute_cost

# 显式 re-export provider 类(向后兼容: `from infra.ai_service import OpenAIProvider`)
from .openai_provider import OpenAIProvider

# Phase 2.12 — TieredRouter
from .tiered_router import TieredRouter, TieredRouterError

__all__ = [
    "AIProvider",
    "ProviderConfig",
    "AIProviderError",
    "ProviderConfigError",
    "APIError",
    "NetworkError",
    "TimeoutError",
    "OpenAIProvider",
    "AnthropicProvider",
    "MiniMaxProvider",
    "register_provider",
    "get_provider_class",
    "list_registered_providers",
    # Phase 2.11
    "ModelTier",
    "ModelTierConfig",
    "MODEL_TIERS",
    "compute_cost",
    # Phase 2.12
    "TieredRouter",
    "TieredRouterError",
    # Phase 2.13
    "CostRecord",
    "CostTracker",
]
