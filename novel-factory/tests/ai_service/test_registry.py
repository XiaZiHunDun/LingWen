"""R3-012: Provider Registry 测试

验证:
- 3 个内置 provider 通过 @register_provider 自动注册
- register_provider 装饰器拒绝非 AIProvider 子类
- get_provider_class / list_registered_providers 工作正常
- AIRouter 走 registry 实例化(新增 provider 即可用)
- 向后兼容:`from infra.ai_service import XxxProvider` 仍工作
"""
import pytest
from unittest.mock import patch

from infra.ai_service import (
    AIProvider,
    ProviderConfig,
    register_provider,
    get_provider_class,
    list_registered_providers,
    OpenAIProvider,
    AnthropicProvider,
    MiniMaxProvider,
)
from infra.ai_service.router import AIRouter
from infra.ai_service.base import _PROVIDER_REGISTRY


class TestBuiltinRegistration:
    """3 个内置 provider 应在 import infra.ai_service 时自动注册"""

    def test_openai_registered(self):
        assert get_provider_class("openai") is OpenAIProvider

    def test_anthropic_registered(self):
        assert get_provider_class("anthropic") is AnthropicProvider

    def test_minimax_registered(self):
        assert get_provider_class("minimax") is MiniMaxProvider

    def test_list_includes_builtins(self):
        names = list_registered_providers()
        assert "openai" in names
        assert "anthropic" in names
        assert "minimax" in names

    def test_lookup_is_case_insensitive(self):
        assert get_provider_class("OpenAI") is OpenAIProvider
        assert get_provider_class("ANTHROPIC") is AnthropicProvider

    def test_unknown_returns_none(self):
        assert get_provider_class("does_not_exist") is None


class TestRegisterProviderDecorator:
    """register_provider 装饰器行为"""

    def test_decorator_registers_class(self):
        @register_provider("test_decorator_xyz")
        class _Dummy(AIProvider):
            def generate(self, prompt, **kwargs):
                return ""

            def embed(self, text):
                return []

            def batch_generate(self, prompts, **kwargs):
                return []

        try:
            assert get_provider_class("test_decorator_xyz") is _Dummy
        finally:
            # 清理 — 不污染后续测试
            _PROVIDER_REGISTRY.pop("test_decorator_xyz", None)

    def test_decorator_rejects_non_ai_provider(self):
        with pytest.raises(TypeError) as exc_info:
            @register_provider("bad_target")
            class _NotAProvider:
                pass

        assert "AIProvider" in str(exc_info.value)

    def test_decorator_returns_class_unchanged(self):
        @register_provider("test_return_unchanged")
        class _Dummy(AIProvider):
            def generate(self, prompt, **kwargs):
                return ""

            def embed(self, text):
                return []

            def batch_generate(self, prompts, **kwargs):
                return []

        try:
            # 装饰器应原样返回类(不修改)
            assert _Dummy.__name__ == "_Dummy"
        finally:
            _PROVIDER_REGISTRY.pop("test_return_unchanged", None)

    def test_reregister_overrides(self):
        """重复注册同名 provider 应覆盖(后注册胜出)"""
        @register_provider("test_override")
        class _First(AIProvider):
            def generate(self, prompt, **kwargs):
                return "first"

            def embed(self, text):
                return []

            def batch_generate(self, prompts, **kwargs):
                return []

        @register_provider("test_override")
        class _Second(AIProvider):
            def generate(self, prompt, **kwargs):
                return "second"

            def embed(self, text):
                return []

            def batch_generate(self, prompts, **kwargs):
                return []

        try:
            assert get_provider_class("test_override") is _Second
        finally:
            _PROVIDER_REGISTRY.pop("test_override", None)


class TestRouterUsesRegistry:
    """AIRouter 应通过 registry 实例化 provider"""

    def test_router_instantiates_openai_via_registry(self):
        """配置 openai 时,RailRouter 通过 get_provider_class 拿到 OpenAIProvider"""
        router = AIRouter(
            config={"openai": ProviderConfig(api_key="k")},
            primary_provider="openai",
            enable_failover=False,
        )
        assert isinstance(router._providers["openai"], OpenAIProvider)

    def test_router_instantiates_anthropic_via_registry(self):
        router = AIRouter(
            config={"anthropic": ProviderConfig(api_key="k", model="claude-sonnet-4-20250514")},
            primary_provider="anthropic",
            enable_failover=False,
        )
        assert isinstance(router._providers["anthropic"], AnthropicProvider)

    def test_router_instantiates_minimax_via_registry(self):
        """minimax 也走 registry — 验证 minimax_provider 模块的 @register_provider 生效"""
        router = AIRouter(
            config={"minimax": ProviderConfig(api_key="k")},
            primary_provider="minimax",
            enable_failover=False,
        )
        assert isinstance(router._providers["minimax"], MiniMaxProvider)

    def test_router_uses_newly_registered_provider(self):
        """通过 register_provider 加新 provider,AIRouter 应能直接用

        模拟用户加了一个 'stub' provider(用 stub 模块挡掉真实 API 调用)。
        """
        @register_provider("stub_for_router")
        class _StubProvider(AIProvider):
            def generate(self, prompt, **kwargs):
                return "stub-response"

            def embed(self, text):
                return [0.0]

            def batch_generate(self, prompts, **kwargs):
                return ["stub-response"] * len(prompts)

        try:
            router = AIRouter(
                config={"stub_for_router": ProviderConfig(api_key="k")},
                primary_provider="stub_for_router",
                enable_failover=False,
            )
            assert isinstance(router._providers["stub_for_router"], _StubProvider)
            # 走 router.generate 应返回 stub 的输出
            assert router.generate("hi") == "stub-response"
        finally:
            _PROVIDER_REGISTRY.pop("stub_for_router", None)

    def test_router_unknown_name_via_register_provider_method(self):
        """未注册的名字可用 router.register_provider() 显式注入(向后兼容旧 API)"""
        class _AdHocProvider(AIProvider):
            def generate(self, prompt, **kwargs):
                return "adhoc"

            def embed(self, text):
                return []

            def batch_generate(self, prompts, **kwargs):
                return ["adhoc"] * len(prompts)

        router = AIRouter(
            config={"openai": ProviderConfig(api_key="k")},
            primary_provider="openai",
            enable_failover=False,
        )
        router.register_provider("adhoc", _AdHocProvider(ProviderConfig(api_key="k")))
        assert isinstance(router._providers["adhoc"], _AdHocProvider)
        assert router.generate("hi", provider="adhoc") == "adhoc"


class TestBackwardCompat:
    """旧 import 路径仍工作"""

    def test_package_reexports_openai(self):
        from infra.ai_service import OpenAIProvider as PkgOpenAI
        from infra.ai_service.openai_provider import OpenAIProvider as ModOpenAI
        assert PkgOpenAI is ModOpenAI

    def test_package_reexports_anthropic(self):
        from infra.ai_service import AnthropicProvider as PkgAnthropic
        from infra.ai_service.anthropic_provider import AnthropicProvider as ModAnthropic
        assert PkgAnthropic is ModAnthropic

    def test_package_reexports_minimax(self):
        from infra.ai_service import MiniMaxProvider as PkgMiniMax
        from infra.ai_service.minimax_provider import MiniMaxProvider as ModMiniMax
        assert PkgMiniMax is ModMiniMax

    def test_submodule_imports_still_work(self):
        """tools/*.py 中用过的子模块 import 路径不应被破坏"""
        from infra.ai_service.minimax_provider import MiniMaxProvider
        from infra.ai_service.base import ProviderConfig
        assert MiniMaxProvider is not None
        assert ProviderConfig is not None


class TestAllExports:
    """__all__ 完整性"""

    def test_package_all_includes_registry_helpers(self):
        import infra.ai_service as pkg
        for name in [
            "AIProvider", "ProviderConfig", "AIProviderError",
            "OpenAIProvider", "AnthropicProvider", "MiniMaxProvider",
            "register_provider", "get_provider_class", "list_registered_providers",
        ]:
            assert name in pkg.__all__, f"missing {name!r} in __all__"
