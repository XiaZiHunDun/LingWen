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

    def generate_with_usage(self, prompt: str, **kwargs):
        self.calls.append({"prompt": prompt, "kwargs": kwargs})
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
