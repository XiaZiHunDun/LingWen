"""E2E 集成测试 helpers (Phase 7)

目标:把 MasterController 的 router 注入点封装为可复用 fixture,
让 test_master_controller_e2e_real_llm.py 集中精力写业务断言。

设计:
- StubProvider 继承 AIProvider,记录所有 generate() calls,返回固定 response
- make_stub_router() 构造 AIRouter,3 个 provider 槽位都注册 StubProvider
- make_master_with_router(state_dir, router) 构造 MasterController(state_dir=state_dir, router=router)
  不替换任何 master.* 方法,完全走生产路径
- 同时显式传入 MasterControllerConfig(空 providers,env_var 无关),
  避免 load_default_config() 在没有 API key 时抛 RuntimeError
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from infra.agent_system.agent_config import MasterControllerConfig
from infra.agent_system.master_controller import MasterController
from infra.ai_service.base import AIProvider, ProviderConfig
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
) -> MasterController:
    """构造 MasterController,注入测试 router,不替换任何 master 方法。"""
    return MasterController(
        state_dir=str(state_dir),
        router=router,
        config=_minimal_config(str(state_dir)),
    )
