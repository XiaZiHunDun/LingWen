"""Tests for generate_with_usage API (Phase 8.6).

3 default impl tests.
"""
from __future__ import annotations

from typing import Any, List
from unittest.mock import MagicMock

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


class TestAnthropicProviderGenerateWithUsage:
    """anthropic_provider.py: override returns real usage from SDK."""

    def test_returns_real_input_output_tokens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub anthropic SDK → response.usage.input_tokens=100, output_tokens=50."""
        from infra.ai_service import anthropic_provider

        # Stub anthropic.Anthropic class
        fake_client = MagicMock()
        fake_response = MagicMock()
        fake_response.usage.input_tokens = 100
        fake_response.usage.output_tokens = 50
        # response.content[0].text (跟 generate() 同)
        text_block = MagicMock()
        text_block.text = "Generated text"
        fake_response.content = [text_block]
        fake_client.messages.create.return_value = fake_response

        # Patch anthropic.Anthropic constructor
        monkeypatch.setattr(anthropic_provider.anthropic, "Anthropic",
                            lambda **kw: fake_client)

        config = ProviderConfig(api_key="sk-test", model="claude-test")
        provider = anthropic_provider.AnthropicProvider(config)
        text, usage = provider.generate_with_usage("Hello Claude")

        assert text == "Generated text"
        assert usage == {"input_tokens": 100, "output_tokens": 50}
        # 不走 len()//4 估算
        assert usage["input_tokens"] != len("Hello Claude") // 4


class TestOpenAIProviderGenerateWithUsage:
    """openai_provider.py: override returns real usage from SDK (prompt/completion tokens)."""

    def test_returns_real_prompt_completion_tokens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub openai SDK → response.usage.prompt_tokens=80, completion_tokens=40."""
        from infra.ai_service import openai_provider

        fake_client = MagicMock()
        fake_response = MagicMock()
        fake_response.usage.prompt_tokens = 80
        fake_response.usage.completion_tokens = 40
        # response.choices[0].message.content (跟 generate() 同)
        fake_response.choices = [MagicMock(message=MagicMock(content="OpenAI text"))]
        fake_client.chat.completions.create.return_value = fake_response

        # Patch openai.OpenAI constructor
        monkeypatch.setattr(openai_provider.openai, "OpenAI",
                            lambda **kw: fake_client)

        config = ProviderConfig(api_key="sk-test", model="gpt-test")
        provider = openai_provider.OpenAIProvider(config)
        text, usage = provider.generate_with_usage("Hello GPT")

        # 映射 prompt_tokens → input_tokens, completion_tokens → output_tokens
        assert text == "OpenAI text"
        assert usage == {"input_tokens": 80, "output_tokens": 40}
        assert usage["input_tokens"] != len("Hello GPT") // 4


class TestMiniMaxProviderGenerateWithUsage:
    """minimax_provider.py: override returns real usage (Anthropic-compatible)."""

    def test_returns_real_input_output_tokens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub anthropic SDK (MiniMax 走 Anthropic 兼容) → usage.input/output_tokens."""
        from infra.ai_service import minimax_provider

        fake_client = MagicMock()
        fake_response = MagicMock()
        fake_response.usage.input_tokens = 200
        fake_response.usage.output_tokens = 100
        # response.content[0].type='text' (跟 generate() 同)
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "M2.7 text"
        fake_response.content = [text_block]
        fake_client.messages.create.return_value = fake_response

        # Patch anthropic.Anthropic constructor (minimax 走 anthropic SDK)
        monkeypatch.setattr(minimax_provider.anthropic, "Anthropic",
                            lambda **kw: fake_client)

        config = ProviderConfig(api_key="sk-test", model="MiniMax-M2.7")
        provider = minimax_provider.MiniMaxProvider(config)
        text, usage = provider.generate_with_usage("Hello M2.7")

        assert text == "M2.7 text"
        assert usage == {"input_tokens": 200, "output_tokens": 100}
        assert usage["input_tokens"] != len("Hello M2.7") // 4
