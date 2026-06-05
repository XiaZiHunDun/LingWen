"""Tests for generate_with_usage API (Phase 8.6).

3 default impl tests.
"""
from __future__ import annotations

from typing import Any, List

import pytest

from infra.ai_service.base import AIProvider, ProviderConfig


class _StubProvider(AIProvider):
    """Minimal stub: uses default generate_with_usage impl."""

    def __init__(self) -> None:
        # 跟 test_tiered_router / test_registry 模式一致: super().__init__ 走
        # AIProvider._validate_config 默认校验 (api_key 非空 + 是 ProviderConfig).
        # 这测试不需要自定义配置字段, 复用基类校验即可.
        super().__init__(ProviderConfig(api_key="sk-test"))
        self._calls: list[dict[str, Any]] = []

    def generate(self, prompt: str, **kwargs) -> str:
        self._calls.append({"prompt": prompt, "kwargs": kwargs})
        return f"response to: {prompt[:20]}"

    def embed(self, text: str) -> List[float]:
        return [0.0] * 4

    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        return [self.generate(p, **kwargs) for p in prompts]


class TestAIProviderDefault:
    """base.py: AIProvider.generate_with_usage default impl."""

    def test_default_returns_text_and_estimated_usage(self) -> None:
        """Default impl 调 self.generate() + len()//4 估算 (跟 Phase 8.5 一致)."""
        provider = _StubProvider()
        text, usage = provider.generate_with_usage("hello world")
        # Pin API contract: usage dict 必须且仅含这两个 key
        # (downstream Task 5-7 TieredRouter/AgentBase/MasterController 依赖)
        assert set(usage.keys()) == {"input_tokens", "output_tokens"}
        assert text == "response to: hello world"
        assert usage == {"input_tokens": len("hello world") // 4,
                         "output_tokens": len(text) // 4}
        assert isinstance(usage["input_tokens"], int)
        assert isinstance(usage["output_tokens"], int)

    def test_default_passes_kwargs_through(self) -> None:
        """kwargs 透传给 self.generate() (跟 chat() 模式一致)."""
        provider = _StubProvider()
        provider.generate_with_usage("test", temperature=0.5, max_tokens=100)
        assert provider._calls[0]["kwargs"] == {"temperature": 0.5, "max_tokens": 100}

    def test_default_propagates_exception(self) -> None:
        """generate() 失败 → generate_with_usage 透传, 不静默吞错."""

        class _FailProvider(_StubProvider):
            def generate(self, prompt: str, **kwargs) -> str:
                raise RuntimeError("boom")

        provider = _FailProvider()
        with pytest.raises(RuntimeError, match="boom"):
            provider.generate_with_usage("test")
