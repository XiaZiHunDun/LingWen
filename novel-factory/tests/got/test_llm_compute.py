"""Tests for got.llm_compute (Phase 2.12a — 真实 LLM compute_fn).

Doc 4 §3.4: GoTScheduler 注入真实 LLM 替代 mock compute_fn。

API:
- LLMComputeFn: 适配器,匹配 ComputeFn 协议
  - __init__(tiered_router, cost_tracker=None, prompt_builder=None)
  - __call__(node: ThoughtNode, inputs: dict) → ComputeResult
- 默认 scenario: node.prompt_scenario (ThoughtNode 字段)
- 默认 prompt_builder: JSON dump inputs + node description
- 失败 → ComputeResult(fail=True, error=...)
- 成功 → ComputeResult(output=str, cost_tokens=估算)
"""
from __future__ import annotations

import json
from typing import Any, Optional

import pytest

from infra.ai_service.base import AIProvider, ProviderConfig
from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.ai_service.tiered_router import TieredRouter, TieredRouterError
from infra.got.data_structures import NodeType, ThoughtNode
from infra.got.llm_compute import LLMComputeFn
from infra.got.scheduler import ComputeResult


class _StubProvider(AIProvider):
    """Test stub — 返回固定 response 或抛错"""

    def __init__(self, name: str, response: str = "ok", raise_exc: Optional[Exception] = None):
        super().__init__(ProviderConfig(api_key="stub-key", model=name))
        self._name = name
        self._response = response
        self._raise = raise_exc
        self.calls: list[str] = []

    def get_provider_name(self) -> str:
        return self._name

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append(prompt)
        if self._raise:
            raise self._raise
        return self._response

    def embed(self, text: str):  # pragma: no cover
        return [0.0]

    def batch_generate(self, prompts, **kwargs):  # pragma: no cover
        return [self.generate(p) for p in prompts]


def _make_router(responses: dict[ModelTier, str | Exception]) -> tuple[TieredRouter, dict[ModelTier, _StubProvider]]:
    providers: dict[ModelTier, _StubProvider] = {}
    for tier, resp in responses.items():
        if isinstance(resp, Exception):
            providers[tier] = _StubProvider(f"model-{tier.value}", raise_exc=resp)
        else:
            providers[tier] = _StubProvider(f"model-{tier.value}", response=resp)
    return TieredRouter(providers), providers


def _node(node_id: str = "n1", scenario: Optional[str] = "chapter_writing") -> ThoughtNode:
    return ThoughtNode(
        node_id=node_id,
        type=NodeType.GENERATION,
        name=f"node_{node_id}",
        description=f"测试节点 {node_id}",
        prompt_scenario=scenario,
    )


# === TestLLMComputeFnBasic ===

class TestLLMComputeFnBasic:
    """基本调用:scenario 路由 + 返回 ComputeResult"""

    def test_call_returns_compute_result(self):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s-out", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        result = compute(_node(), {"ch": 100})
        assert isinstance(result, ComputeResult)
        assert result.fail is False
        assert result.output == "s-out"
        assert result.cost_tokens > 0  # 估算了 token

    def test_routes_by_node_scenario(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        # chapter_writing → SONNET
        compute(_node(scenario="chapter_writing"), {})
        assert len(providers[ModelTier.SONNET].calls) == 1
        # subplot_suggest → OPUS
        compute(_node(scenario="subplot_suggest"), {})
        assert len(providers[ModelTier.OPUS].calls) == 1
        # hook_extraction → HAIKU
        compute(_node(scenario="hook_extraction"), {})
        assert len(providers[ModelTier.HAIKU].calls) == 1

    def test_prompt_includes_node_info(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        node = _node(node_id="abc", scenario="chapter_writing")
        compute(node, {"key": "value"})
        prompt = providers[ModelTier.SONNET].calls[0]
        # 默认 prompt builder 应含 node id/description + inputs
        assert "abc" in prompt
        assert "测试节点" in prompt or "node_abc" in prompt

    def test_prompt_includes_inputs(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        compute(_node(), {"chapter": 100, "title": "觉醒"})
        prompt = providers[ModelTier.SONNET].calls[0]
        # inputs 必含 (序列化形式)
        assert "chapter" in prompt
        assert "100" in prompt


# === TestLLMComputeFnFailure ===

class TestLLMComputeFnFailure:
    """失败处理:抛错 → ComputeResult(fail=True, error=...)"""

    def test_all_tiers_fail_returns_failed_result(self):
        router, _ = _make_router({
            ModelTier.HAIKU: ValueError("haiku fail"),
            ModelTier.SONNET: ValueError("sonnet fail"),
            ModelTier.OPUS: ValueError("opus fail"),
        })
        compute = LLMComputeFn(router)
        result = compute(_node(scenario="subplot_suggest"), {})
        # 所有 tier 失败 → 返回 fail, 不抛异常 (compute_fn 协议)
        assert result.fail is True
        assert result.error is not None
        assert "fail" in result.error.lower() or "error" in result.error.lower()

    def test_downgrade_on_partial_failure(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "haiku-recovered",
            ModelTier.SONNET: ValueError("sonnet down"),
            ModelTier.OPUS: ValueError("opus down"),
        })
        compute = LLMComputeFn(router)
        # subplot_suggest 原本是 OPUS,失败 → 降级 → HAIKU 成功
        result = compute(_node(scenario="subplot_suggest"), {})
        assert result.fail is False
        assert result.output == "haiku-recovered"
        assert len(providers[ModelTier.OPUS].calls) == 1
        assert len(providers[ModelTier.SONNET].calls) == 1
        assert len(providers[ModelTier.HAIKU].calls) == 1


# === TestLLMComputeFnScenario ===

class TestLLMComputeFnScenario:
    """scenario 处理:None/未知 → 错误"""

    def test_none_scenario_raises(self):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        result = compute(_node(scenario=None), {})
        # scenario is None → 失败 (无法路由)
        assert result.fail is True
        assert "scenario" in result.error.lower()

    def test_unknown_scenario_fails(self):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        result = compute(_node(scenario="unknown_scenario"), {})
        assert result.fail is True


# === TestLLMComputeFnCostTracker ===

class TestLLMComputeFnCostTracker:
    """注入 CostTracker 时,自动记录"""

    def test_records_to_cost_tracker(self):
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s-out", ModelTier.OPUS: "o",
        })
        tracker = CostTracker()
        compute = LLMComputeFn(router, cost_tracker=tracker)
        compute(_node(scenario="chapter_writing"), {"ch": 100})
        # 1 记录,scenario=chapter_writing
        assert len(tracker.records()) == 1
        rec = tracker.records()[0]
        assert rec.scenario == "chapter_writing"
        assert rec.tier == ModelTier.SONNET
        assert rec.cost_usd > 0

    def test_records_after_successful_downgrade(self):
        """降级成功后,LLMComputeFn 记录 1 条 (用 primary tier 估算成本)"""
        router, _ = _make_router({
            ModelTier.HAIKU: "haiku-recovered",
            ModelTier.SONNET: ValueError("sonnet fail"),
            ModelTier.OPUS: ValueError("opus fail"),
        })
        tracker = CostTracker()
        compute = LLMComputeFn(router, cost_tracker=tracker)
        compute(_node(scenario="subplot_suggest"), {})
        # 1 条记录, tier 用 primary (subplot_suggest → OPUS)
        assert len(tracker.records()) == 1
        rec = tracker.records()[0]
        assert rec.tier == ModelTier.OPUS  # 用 SCENARIO_TIER_MAP 的 primary
        assert rec.scenario == "subplot_suggest"

    def test_no_tracker_no_error(self):
        """不传 cost_tracker 也不报错"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router, cost_tracker=None)
        result = compute(_node(), {})
        assert result.fail is False


# === TestLLMComputeFnCustomPrompt ===

class TestLLMComputeFnCustomPrompt:
    """自定义 prompt_builder"""

    def test_custom_prompt_builder(self):
        router, providers = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })

        def my_builder(node, inputs):
            return f"PROMPT for {node.node_id}: {inputs.get('key', '')}"

        compute = LLMComputeFn(router, prompt_builder=my_builder)
        compute(_node(node_id="xyz"), {"key": "k-value"})
        prompt = providers[ModelTier.SONNET].calls[0]
        assert prompt == "PROMPT for xyz: k-value"


# === TestLLMComputeFnImport ===

class TestLLMComputeFnImport:
    """Public API"""

    def test_top_level_imports(self):
        from infra.got import LLMComputeFn
        assert LLMComputeFn is not None

    def test_callable(self):
        from infra.got import LLMComputeFn
        router, _ = _make_router({
            ModelTier.HAIKU: "h", ModelTier.SONNET: "s", ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        # 必须可调用 (满足 ComputeFn 协议)
        assert callable(compute)
