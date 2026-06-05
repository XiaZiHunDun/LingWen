"""Tests for chat_with_usage API (Phase 8.6).

3 tests: AgentBase (TieredRouter new path + AIRouter fallback) + fallback mode.
"""
from __future__ import annotations

from typing import Any

import pytest


class _TieredRouterStub:
    """Stub 模拟 TieredRouter (有 generate_with_usage)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(self, prompt: str, **kwargs) -> str:
        return "old-path text"

    def generate_with_usage(self, *args, **kwargs):
        # 灵活签名: AgentBase 走全 kwargs (prompt=..., temperature=...),
        # MasterController 走 (scenario, prompt) 位置参数。
        # 真实 TieredRouter.generate_with_usage(self, scenario, prompt, **kwargs) 形状。
        self.calls.append({"args": args, "kwargs": kwargs})
        return "new-path text", {"input_tokens": 42, "output_tokens": 24}


class _LegacyRouterStub:
    """Stub 模拟旧 AIRouter (无 generate_with_usage)."""

    def generate(self, prompt: str, **kwargs) -> str:
        return "legacy text"


class TestAgentBaseChatWithUsage:
    """agents/base.py: AgentBase.chat_with_usage 用 hasattr fallback."""

    def test_uses_new_method_when_router_has_it(self) -> None:
        """Router 有 generate_with_usage → 走新方法, 返 real usage."""
        from infra.agent_system.agents.base import AgentBase

        router = _TieredRouterStub()
        agent = AgentBase(router=router)  # type: ignore[arg-type]
        text, usage = agent.chat_with_usage("test prompt", temperature=0.5)

        assert text == "new-path text"
        assert usage == {"input_tokens": 42, "output_tokens": 24}
        assert len(router.calls) == 1
        # Verify kwargs passthrough
        assert router.calls[0]["kwargs"]["temperature"] == 0.5

    def test_falls_back_to_estimate_when_router_lacks_method(self) -> None:
        """Router 无 generate_with_usage (旧 AIRouter) → 调 chat() + len()//4 估算."""
        from infra.agent_system.agents.base import AgentBase

        router = _LegacyRouterStub()
        agent = AgentBase(router=router)  # type: ignore[arg-type]
        text, usage = agent.chat_with_usage("test prompt")

        assert text == "legacy text"
        # 估算 fallback: 跟 Phase 8.5 公式一致
        assert usage == {
            "input_tokens": len("test prompt") // 4,
            "output_tokens": len("legacy text") // 4,
        }

    def test_fallback_mode_returns_estimate(self) -> None:
        """_fallback_mode (router=None) → 返 _fallback_response + 估算."""
        from infra.agent_system.agents.base import AgentBase

        agent = AgentBase(router=None)
        text, usage = agent.chat_with_usage("test prompt")

        assert text.startswith("[FALLBACK]")
        assert usage["input_tokens"] == len("test prompt") // 4
        assert usage["output_tokens"] == len(text) // 4


class TestMasterControllerChatWithUsage:
    """master_controller.py: MasterController.chat_with_usage public API."""

    def test_falls_back_to_estimate_when_router_lacks_method(self) -> None:
        """_router 是旧 AIRouter (无 generate_with_usage) → 走估算 fallback."""
        from infra.agent_system.master_controller import MasterController

        # Use MasterController.__new__ to bypass __init__ (跟 Phase 7.1 / 8.5 模式)
        master = MasterController.__new__(MasterController)
        master._router = _LegacyRouterStub()  # type: ignore[attr-defined]

        text, usage = master.chat_with_usage("chapter_writing", "test prompt")
        assert text == "legacy text"
        assert usage == {
            "input_tokens": len("test prompt") // 4,
            "output_tokens": len("legacy text") // 4,
        }

    def test_uses_router_new_method_when_available(self) -> None:
        """_router 有 generate_with_usage → 走新方法, 返 real usage."""
        from infra.agent_system.master_controller import MasterController

        master = MasterController.__new__(MasterController)
        router = _TieredRouterStub()
        master._router = router  # type: ignore[attr-defined]

        text, usage = master.chat_with_usage("chapter_writing", "test prompt")
        assert text == "new-path text"
        assert usage == {"input_tokens": 42, "output_tokens": 24}
        assert len(router.calls) == 1


class TestEndToEndChatWithUsage:
    """E2E: MasterController + TieredRouter + stub provider chain."""

    def test_real_usage_flows_through_full_chain(self) -> None:
        """Master.chat_with_usage → TieredRouter → Provider → 返 SDK real usage."""
        from infra.agent_system.master_controller import MasterController
        from infra.ai_service.model_tiers import ModelTier
        from infra.ai_service.tiered_router import TieredRouter

        class _FullChainProvider:
            """Stub provider 返 real usage (模拟 SDK 行为)."""

            def __init__(self) -> None:
                self._call_count = 0

            def generate(self, prompt: str, **kwargs) -> str:
                self._call_count += 1
                return f"response #{self._call_count}"

            def generate_with_usage(self, prompt: str, **kwargs):
                self._call_count += 1
                return (
                    f"response #{self._call_count}",
                    {"input_tokens": 7, "output_tokens": 11},
                )

        provider = _FullChainProvider()
        providers = {tier: provider for tier in ModelTier}
        router = TieredRouter(providers=providers)

        master = MasterController.__new__(MasterController)
        master._router = router  # type: ignore[attr-defined]

        # End-to-end: Master → TieredRouter → Provider
        text, usage = master.chat_with_usage("chapter_writing", "end to end test")
        assert text == "response #1"
        assert usage == {"input_tokens": 7, "output_tokens": 11}
        # Provider.generate_with_usage 被调 1 次 (没走旧 generate)
        assert provider._call_count == 1

    def test_scenario_routing_resolved_correctly(self) -> None:
        """scenario → TieredRouter 正确路由到对应 tier 的 provider."""
        from infra.agent_system.master_controller import MasterController
        from infra.ai_service.model_tiers import ModelTier
        from infra.ai_service.tiered_router import TieredRouter

        # 不同 tier 返不同 usage, 验证 routing
        class _TierAwareProvider:
            def __init__(self, tier: ModelTier) -> None:
                self._tier = tier

            def generate(self, prompt: str, **kwargs) -> str:
                return f"{self._tier.value} text"

            def generate_with_usage(self, prompt: str, **kwargs):
                return (
                    f"{self._tier.value} text",
                    {"input_tokens": self._tier.value, "output_tokens": 0},
                )

        providers = {tier: _TierAwareProvider(tier) for tier in ModelTier}
        router = TieredRouter(providers=providers)

        master = MasterController.__new__(MasterController)
        master._router = router  # type: ignore[attr-defined]

        # chapter_writing → SONNET tier (per SCENARIO_TIER_MAP)
        text, usage = master.chat_with_usage("chapter_writing", "test")
        assert text == "sonnet text"
        assert usage["input_tokens"] == "sonnet"
