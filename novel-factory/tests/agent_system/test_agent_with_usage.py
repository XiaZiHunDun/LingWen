"""Phase 8.6.1: 3 production agent *_with_usage 变体方法测试。

3 agents (content_writer/auditor/polisher) 暴露 parallel *_with_usage 方法,
返回 (result, usage) tuple (老 method 仍返回 dict, 0 改保 2120 baseline)。

Stub 设计: _RecordingRouter 实现 generate_with_usage → 调 provider,
跟 TieredRouter 走相同路径 (AgentBase.chat_with_usage hasattr 路由),
让测试断言 真实 usage (vs base.py default impl 走 len()//4 估算)。
"""
from __future__ import annotations

from typing import Any, Dict, Union

import pytest

from infra.agent_system.agents.auditor.tools import AuditorTools
from infra.agent_system.agents.content_writer.tools import ContentWriterTools
from infra.agent_system.agents.polisher.tools import PolisherTools
from infra.ai_service.base import AIProvider, ProviderConfig


class _UsageRecordingProvider(AIProvider):
    """Test stub: 实现 generate_with_usage 返回硬编码 usage."""

    def __init__(
        self,
        response: Union[str, Exception] = "stub response",
        input_tokens: int = 100,
        output_tokens: int = 50,
    ) -> None:
        super().__init__(ProviderConfig(api_key="sk-test", model="stub-model"))
        self._response = response
        self._input = input_tokens
        self._output = output_tokens
        self.usage_calls: list[dict] = []
        self.calls: list[dict] = []

    def get_provider_name(self) -> str:
        return "stub"

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append({"prompt": prompt, "kwargs": dict(kwargs)})
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    def generate_with_usage(self, prompt: str, **kwargs) -> tuple[str, Dict[str, int]]:
        self.usage_calls.append({"prompt": prompt, "kwargs": dict(kwargs)})
        if isinstance(self._response, Exception):
            raise self._response
        return self._response, {"input_tokens": self._input, "output_tokens": self._output}

    def embed(self, text: str):
        return [0.0]

    def batch_generate(self, prompts, **kwargs):
        return [self.generate(p, **kwargs) for p in prompts]


class _RecordingRouter:
    """Stub router 模拟 TieredRouter 路径 (有 generate_with_usage).

    AIRouter 不实现 generate_with_usage (Phase 8.6 设计: legacy path 走
    len()//4 估算), 所以用 _RecordingRouter 走 real path.
    """

    def __init__(self, provider: _UsageRecordingProvider) -> None:
        self._provider = provider

    def generate(self, prompt: str, **kwargs) -> str:
        """旧 path, 让 test 验证 *_with_usage 走新 path 不走这个."""
        return self._provider.generate(prompt, **kwargs)

    def generate_with_usage(self, prompt: str, **kwargs) -> tuple[str, Dict[str, int]]:
        return self._provider.generate_with_usage(prompt, **kwargs)


def _make_router_with_usage_recorder(
    response: Union[str, Exception] = "stub response",
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> tuple[_RecordingRouter, _UsageRecordingProvider]:
    """_RecordingRouter + _UsageRecordingProvider (走 generate_with_usage real path).

    跟 _e2e_helpers.make_stub_router() 区别: 用 _RecordingRouter 而非 AIRouter
    → AgentBase.chat_with_usage hasattr 路由走 real path.
    """
    provider = _UsageRecordingProvider(response, input_tokens, output_tokens)
    router = _RecordingRouter(provider)
    return router, provider


# ==================== ContentWriter ====================


class TestContentWriterUsage:
    """ContentWriterTools.generate_chapter_with_usage 验证 (3 tests)."""

    def test_generate_chapter_with_usage_returns_tuple(self) -> None:
        router, _prov = _make_router_with_usage_recorder("chapter content here")
        writer = ContentWriterTools(router)
        context = {
            "chapter_outline": {"title": "ch1", "events": ["e1"]},
            "characters": [],
            "style_guide": {"tone": "简洁有力"},
        }
        result, usage = writer.generate_chapter_with_usage(
            chapter_num=1, context=context
        )
        assert isinstance(result, dict)
        assert "content" in result
        assert result["content"] == "chapter content here"
        assert isinstance(usage, dict)
        assert usage == {"input_tokens": 100, "output_tokens": 50}

    def test_generate_chapter_with_usage_uses_real_usage(self) -> None:
        """验证 chat_with_usage 被调 1 次 (而非 chat() 估算)."""
        router, prov = _make_router_with_usage_recorder("x")
        writer = ContentWriterTools(router)
        context = {
            "chapter_outline": {"title": "ch1"},
            "characters": [],
            "style_guide": {},
        }
        writer.generate_chapter_with_usage(chapter_num=1, context=context)
        assert len(prov.usage_calls) == 1
        assert len(prov.calls) == 0  # chat() path not taken

    def test_generate_chapter_unchanged_returns_dict(self) -> None:
        """旧 method 签名 0 改, 返回 dict (不返回 tuple)."""
        router, _prov = _make_router_with_usage_recorder("chapter content")
        writer = ContentWriterTools(router)
        context = {
            "chapter_outline": {"title": "ch1"},
            "characters": [],
            "style_guide": {},
        }
        result = writer.generate_chapter(chapter_num=1, context=context)
        assert isinstance(result, dict)
        assert "content" in result
        assert result["content"] == "chapter content"


# ==================== Auditor ====================


class TestAuditorUsage:
    """AuditorTools.audit_chapter_with_usage 验证 (3 tests)."""

    def test_audit_chapter_with_usage_returns_tuple(self) -> None:
        router, _prov = _make_router_with_usage_recorder('{"issues": [], "scores": {}}')
        auditor = AuditorTools(router)
        result, usage = auditor.audit_chapter_with_usage(
            chapter_num=1,
            content="text",
            characters=[],
            context={"timeline": []},
        )
        assert isinstance(result, dict)
        assert isinstance(usage, dict)
        assert usage == {"input_tokens": 100, "output_tokens": 50}

    def test_audit_chapter_with_usage_uses_real_usage(self) -> None:
        router, prov = _make_router_with_usage_recorder('{"issues": []}')
        auditor = AuditorTools(router)
        auditor.audit_chapter_with_usage(
            chapter_num=1, content="t", characters=[], context={}
        )
        assert len(prov.usage_calls) == 1
        assert len(prov.calls) == 0

    def test_audit_chapter_unchanged_returns_dict(self) -> None:
        router, _prov = _make_router_with_usage_recorder('{"issues": []}')
        auditor = AuditorTools(router)
        result = auditor.audit_chapter(
            chapter_num=1, content="t", characters=[], context={}
        )
        assert isinstance(result, dict)


# ==================== Polisher ====================


class TestPolisherUsage:
    """PolisherTools.polish_chapter_with_usage 验证 (3 tests).

    polish_chapter 内部调 2 LLM (optimize_dialogue + adjust_pacing),
    usage 累加 (2x single).
    """

    def test_polish_chapter_with_usage_sums_both_llms(self) -> None:
        """2 LLM 都走 generate_with_usage, usage 累加."""
        router, prov = _make_router_with_usage_recorder("optimized text")
        polisher = PolisherTools(router)
        result, usage = polisher.polish_chapter_with_usage(
            chapter_num=1, content="original text"
        )
        assert isinstance(result, dict)
        assert "content" in result
        # 2 LLM calls (dialogue + pacing) each with 100/50 → 200/100
        assert usage == {"input_tokens": 200, "output_tokens": 100}
        assert len(prov.usage_calls) == 2
        assert len(prov.calls) == 0

    def test_polish_chapter_with_usage_returns_tuple(self) -> None:
        router, _prov = _make_router_with_usage_recorder("x")
        polisher = PolisherTools(router)
        result, usage = polisher.polish_chapter_with_usage(
            chapter_num=1, content="t"
        )
        assert isinstance(result, dict)
        assert isinstance(usage, dict)
        assert set(usage.keys()) == {"input_tokens", "output_tokens"}

    def test_polish_chapter_unchanged_returns_dict(self) -> None:
        """旧 method 签名 0 改, 返回 dict (不返回 tuple)."""
        router, _prov = _make_router_with_usage_recorder("x")
        polisher = PolisherTools(router)
        result = polisher.polish_chapter(chapter_num=1, content="t")
        assert isinstance(result, dict)
        assert "content" in result
        assert "issues" in result
