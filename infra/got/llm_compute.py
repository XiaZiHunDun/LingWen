"""真实 LLM compute_fn — Phase 2.12a

Doc 4 §3.4: 用 TieredRouter 替代 mock lambda,GoTScheduler 调真实 LLM。

API:
- LLMComputeFn(tiered_router, cost_tracker=None, prompt_builder=None)
  - 实现 ComputeFn 协议: __call__(node, inputs) → ComputeResult
  - 默认 scenario: node.prompt_scenario
  - 默认 prompt_builder: 拼装 node + inputs → str
  - 失败 → ComputeResult(fail=True, error=...),不抛异常
  - 成功 → ComputeResult(output=str, cost_tokens=估算)

设计:
- 与 ComputeFn 协议 (Callable[[ThoughtNode, dict], ComputeResult]) 完全兼容
- 直接传 GoTScheduler(compute_fn=llm_compute) 即可使用
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol

from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.tiered_router import TieredRouter

from .data_structures import ThoughtNode
from .scheduler import ComputeResult

# Type aliases
PromptBuilder = Callable[[ThoughtNode, dict[str, Any]], str]


def default_prompt_builder(node: ThoughtNode, inputs: dict[str, Any]) -> str:
    """默认 prompt builder: JSON 序列化 inputs + node 信息"""
    parts = [
        f"## Node: {node.node_id} ({node.name})",
        f"Type: {node.type.value}",
        f"Description: {node.description}",
    ]
    if node.prompt_scenario:
        parts.append(f"Scenario: {node.prompt_scenario}")
    if node.token_budget:
        parts.append(f"Token budget: {node.token_budget}")
    parts.append("")
    parts.append("## Inputs (JSON)")
    parts.append(json.dumps(inputs, ensure_ascii=False, indent=2))
    parts.append("")
    parts.append("请基于以上上下文,生成节点输出。")
    return "\n".join(parts)


# CostTracker Protocol (避免循环)
class _CostTrackerLike(Protocol):
    def record(self, scenario: str, tier, input_tokens: int, output_tokens: int) -> Any: ...


class LLMComputeFn:
    """真实 LLM compute_fn 适配器 (与 ComputeFn 协议兼容)

    用法:
        router = TieredRouter({...})
        tracker = CostTracker()
        llm_compute = LLMComputeFn(router, cost_tracker=tracker)
        scheduler = GoTScheduler(graph, compute_fn=llm_compute)
        summary = scheduler.run(start_nodes=["root"])
    """

    def __init__(
        self,
        tiered_router: TieredRouter,
        cost_tracker: Optional[CostTracker] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ) -> None:
        self._router = tiered_router
        self._cost_tracker = cost_tracker
        self._prompt_builder = prompt_builder or default_prompt_builder

    def __call__(self, node: ThoughtNode, inputs: dict[str, Any]) -> ComputeResult:
        """执行节点 — 调 LLM, 包装为 ComputeResult

        失败不抛异常,统一返回 ComputeResult(fail=True, error=...),
        让 GoTScheduler 走标准 backtrack 路径。
        """
        scenario = node.prompt_scenario
        if not scenario:
            return ComputeResult(
                fail=True,
                error=f"node {node.node_id!r} has no prompt_scenario; cannot route",
            )

        # 构造 prompt
        try:
            prompt = self._prompt_builder(node, inputs)
        except Exception as exc:
            return ComputeResult(
                fail=True,
                error=f"prompt_builder failed: {exc}",
            )

        # 调 LLM
        try:
            output = self._router.generate(scenario, prompt)
        except Exception as exc:
            return ComputeResult(
                fail=True,
                error=f"LLM call failed for scenario {scenario!r}: {exc}",
            )

        # 估算 token (与 TieredRouter._notify_tracker 一致: 1 token ≈ 4 chars)
        input_tokens = len(prompt) // 4
        output_tokens = len(output) // 4

        # LLMComputeFn 自己的 cost_tracker 记录 (供上层汇总)
        # 注意: TieredRouter 可能也记录了一份 (若构造时传入)
        # 这里额外记录是为了让 LLMComputeFn 用户不依赖 TieredRouter 内部状态
        if self._cost_tracker is not None:
            # 降级时,我们不知道实际 tier, 用 primary tier
            # 实际生产中可以扩展 TieredRouter 返回实际 tier
            from infra.ai_service.model_tiers import ModelTier
            from infra.prompt_engineering.scenarios import SCENARIO_TIER_MAP
            try:
                tier = SCENARIO_TIER_MAP[scenario]
            except KeyError:
                tier = ModelTier.SONNET  # fallback
            self._cost_tracker.record(scenario, tier, input_tokens, output_tokens)

        return ComputeResult(
            output=output,
            cost_tokens=input_tokens + output_tokens,
            fail=False,
        )
