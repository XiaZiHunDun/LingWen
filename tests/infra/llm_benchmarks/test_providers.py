"""Tests for infra.llm_benchmarks.providers."""

from __future__ import annotations

import pytest

from infra.llm_benchmarks.providers import (
    MockLLMService,
    anthropic_mock_canned,
    get_provider_llm,
    minimax_mock_canned,
    openai_mock_canned,
)


def test_mock_llm_returns_canned_json_for_known_prompt():
    svc = MockLLMService(canned=openai_mock_canned)
    out = svc.generate(prompt="角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\nfoo", system="x")
    assert out.startswith("{") or out.startswith("[")


def test_mock_llm_returns_empty_proposals_for_unknown_prompt():
    svc = MockLLMService(canned=openai_mock_canned)
    out = svc.generate(prompt="unrecognized prompt shape", system="x")
    assert "proposals" in out


def test_get_provider_llm_returns_mock_when_real_false():
    svc = get_provider_llm("minimax", real=False)
    assert isinstance(svc, MockLLMService)


def test_get_provider_llm_raises_when_minimax_real_no_env(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MINIMAX_API_KEY not set"):
        get_provider_llm("minimax", real=True)


def test_get_provider_llm_raises_not_implemented_for_anthropic_real(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    with pytest.raises(NotImplementedError, match="real anthropic"):
        get_provider_llm("anthropic", real=True)


def test_anthropic_canned_differs_from_openai_canned():
    # Different canned JSON reflects different provider "personality"
    assert anthropic_mock_canned != openai_mock_canned
    assert "minimax" not in anthropic_mock_canned
