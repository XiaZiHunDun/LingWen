"""E2E 集成测试 helpers (Phase 7)

目标:把 MasterController 的 router 注入点封装为可复用 fixture,
让 test_master_controller_stub_router_e2e.py 集中精力写业务断言。

设计:
- StubProvider 继承 AIProvider,记录所有 generate() calls,返回固定 response
- make_stub_router() 构造 AIRouter,3 个 provider 槽位都注册 StubProvider
- make_master_with_router(state_dir, router) 构造 MasterController(state_dir=state_dir, router=router)
  不替换任何 master.* 方法,完全走生产路径
- 同时显式传入 MasterControllerConfig(空 providers,env_var 无关),
  避免 load_default_config() 在没有 API key 时抛 RuntimeError
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Optional, Union

from infra.agent_system.agent_config import MasterControllerConfig
from infra.agent_system.master_controller import MasterController
from infra.ai_service.base import AIProvider, ProviderConfig
from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.router import AIRouter


class StubProvider(AIProvider):
    """Test stub — 记录所有 generate() calls,返回固定 response 或抛错。"""

    def __init__(self, name: str, response: Union[str, Exception] = "ok"):
        super().__init__(ProviderConfig(api_key="stub-key", model=name))
        self._name = name
        self._response = response
        self.calls: list[dict] = []

    def get_provider_name(self) -> str:
        return self._name

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append({"prompt": prompt, "kwargs": dict(kwargs)})
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    def embed(self, text: str):
        return [0.0]

    def batch_generate(self, prompts, **kwargs):
        return [self.generate(p, **kwargs) for p in prompts]


def make_stub_router() -> tuple[AIRouter, dict[str, StubProvider]]:
    """构造 AIRouter,3 个 provider 槽位都注册 StubProvider。

    Returns:
        (router, {"anthropic": StubProvider, "openai": StubProvider, "minimax": StubProvider})
    """
    providers = {
        "anthropic": StubProvider("anthropic", "anthropic-response"),
        "openai": StubProvider("openai", "openai-response"),
        "minimax": StubProvider("minimax", "minimax-response"),
    }
    router = AIRouter(
        config={},
        primary_provider="anthropic",
        enable_failover=False,
    )
    for name, prov in providers.items():
        router.register_provider(name, prov)
    # AIRouter.__init__ 在 config={} 时会忽略 primary_provider 参数(整表达式返回 None),
    # 显式调 set_primary() 修正 type_mapping["general"] + _primary_provider
    router.set_primary("anthropic")
    return router, providers


def make_stub_router_with_responses(
    responses: dict[str, Union[str, Exception]],
) -> tuple[AIRouter, dict[str, StubProvider]]:
    """构造 AIRouter,每个 provider 用独立 response (string 或 Exception)。"""
    primary = list(responses.keys())[0]
    router = AIRouter(
        config={},
        primary_provider=primary,
        enable_failover=False,
    )
    providers: dict[str, StubProvider] = {}
    for name, resp in responses.items():
        providers[name] = StubProvider(name, resp)
        router.register_provider(name, providers[name])
    router.set_primary(primary)
    return router, providers


def _minimal_config(state_dir: str) -> MasterControllerConfig:
    """构造最小 MasterControllerConfig — providers 为空,因为 router 由我们注入。

    load_default_config() 在缺少 API key 时会 RuntimeError,本 fixture 不需要
    真实凭据,所以直接构造一个空 providers 的 config。
    """
    return MasterControllerConfig(
        state_dir=state_dir,
        primary_provider="anthropic",
        enable_failover=False,
        providers={},
    )


def make_master_with_router(
    state_dir: Path,
    router: AIRouter,
    cost_tracker: Optional[CostTracker] = None,
) -> MasterController:
    """构造 MasterController,注入测试 router,不替换任何 master 方法。

    Phase 8.5: cost_tracker 默认 None 兜底,旧 14 e2e tests 零修改。
    """
    return MasterController(
        state_dir=str(state_dir),
        router=router,
        config=_minimal_config(str(state_dir)),
        cost_tracker=cost_tracker,
    )


# ==================== Phase 8.2: Multi-Provider Real LLM Matrix ====================

_PROVIDER_REGISTRY = {
    "anthropic": {
        "class_path": "infra.ai_service.anthropic_provider.AnthropicProvider",
        "env_var": "ANTHROPIC_API_KEY",
        "default_model": "claude-haiku-4-5-20251001",
    },
    "openai": {
        "class_path": "infra.ai_service.openai_provider.OpenAIProvider",
        "env_var": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "minimax": {
        "class_path": "infra.ai_service.minimax_provider.MiniMaxProvider",
        "env_var": "MINIMAX_API_KEY",
        "default_model": "MiniMax-M2.7",
    },
}


def _make_real_router(provider_name: str) -> AIRouter:
    """Phase 8.2: 构造单 provider 的 AIRouter (multi-provider matrix).

    Phase 8 只测 Anthropic, Phase 8.2 加 OpenAI + MiniMax 跨 provider 验证
    Phase 7.5 polish_merge 评分在多 provider 都能走 LLM 路径. 抽到 _e2e_helpers.py
    是因为现在 3 个 provider 共用同一个 helper, 分散在多个 test 文件会重复代码.

    Args:
        provider_name: "anthropic" / "openai" / "minimax" (lowercase, 跟
                        @register_provider 注册名一致)

    Returns:
        AIRouter with single provider, primary=provider_name, enable_failover=False

    Raises:
        ValueError: 不支持的 provider_name
        KeyError: 缺少对应 env var (e.g. OPENAI_API_KEY not set)
        ImportError: 依赖未装 (e.g. openai 包缺失)
    """
    if provider_name not in _PROVIDER_REGISTRY:
        raise ValueError(
            f"Unsupported provider_name: {provider_name!r}. "
            f"Supported: {list(_PROVIDER_REGISTRY.keys())}"
        )
    spec = _PROVIDER_REGISTRY[provider_name]
    api_key = os.environ.get(spec["env_var"])
    if not api_key:
        raise KeyError(
            f"Provider {provider_name!r} requires env var {spec['env_var']!r} "
            f"to be set"
        )

    # Lazy import 避免循环 + 允许 provider 缺依赖时 (e.g. openai 包未装) fail gracefully
    module_path, class_name = spec["class_path"].rsplit(".", 1)
    module = importlib.import_module(module_path)
    provider_cls = getattr(module, class_name)

    provider = provider_cls(ProviderConfig(
        api_key=api_key,
        model=spec["default_model"],
        timeout=180,  # 1 LLM call 留 180s headroom
        max_retries=1,  # fail-fast
    ))
    return AIRouter(
        config={provider_name: provider.config},
        primary_provider=provider_name,
        enable_failover=False,  # 单 provider, 失败立即 raise
    )
