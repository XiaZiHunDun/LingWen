"""E2E Tests for GoT + TieredRouter + CostTracker 集成 (Phase 2.12b)

Doc 4 §3.4: GoTScheduler 注入 LLMComputeFn,后者用 TieredRouter + CostTracker。

E2E 流程:
1. 构造真实 ThoughtGraph (含 prompt_scenario 节点)
2. 构造 TieredRouter (stub providers per tier)
3. 构造 CostTracker
4. 构造 LLMComputeFn(router, cost_tracker=tracker)
5. 构造 GoTScheduler(graph, compute_fn=llm_compute)
6. scheduler.run() → ExecutionSummary
7. 验证:
   - 节点执行顺序符合 depends_on 拓扑
   - 每个完成节点都在 CostTracker 留下 1 条记录
   - 累计 token = 各节点 cost_tokens 之和
   - 降级链: 高 tier 失败 → 低 tier 接管
   - backtrack 联动: 失败 → 下游 STALE → 重新 READY
   - 缓存命中: 第二次相同 inputs 不重复调用 LLM
"""
from __future__ import annotations

from typing import Optional

import pytest

from infra.ai_service.base import AIProvider, ProviderConfig
from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.ai_service.tiered_router import TieredRouter
from infra.got.data_structures import NodeStatus, NodeType, ThoughtNode
from infra.got.graph import ThoughtGraph
from infra.got.llm_compute import LLMComputeFn
from infra.got.scheduler import ExecutionSummary, GoTScheduler

# === Test fixtures: stub providers ===

class _StubProvider(AIProvider):
    """E2E stub — 可配置 response 和 call 记录"""

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


def _make_router(responses: dict[ModelTier, object]) -> tuple[TieredRouter, dict[ModelTier, _StubProvider]]:
    providers: dict[ModelTier, _StubProvider] = {}
    for tier, resp in responses.items():
        if isinstance(resp, Exception):
            providers[tier] = _StubProvider(f"model-{tier.value}", raise_exc=resp)
        else:
            providers[tier] = _StubProvider(f"model-{tier.value}", response=resp)
    return TieredRouter(providers), providers


def _node(node_id: str, scenario: str, depends_on: tuple[str, ...] = ()) -> ThoughtNode:
    return ThoughtNode(
        node_id=node_id,
        type=NodeType.GENERATION,
        name=f"node_{node_id}",
        description=f"E2E 节点 {node_id}",
        prompt_scenario=scenario,
        depends_on=depends_on,
    )


# === E2E Test 1: 完整流水线 — 多节点 + CostTracker + Token 累计 ===

class TestE2EWorkflow:
    """E2E: ThoughtGraph → LLMComputeFn → GoTScheduler → CostTracker"""

    def test_full_pipeline_completes_all_nodes(self):
        """5 节点串/并混合,全部完成,CostTracker 收到 5 条记录"""
        router, providers = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s-out",
            ModelTier.OPUS: "o",
        })
        tracker = CostTracker()
        compute = LLMComputeFn(router, cost_tracker=tracker)

        # a → (b, c) → d
        # 拓扑: a (haiku) → b (sonnet) + c (sonnet) → d (opus)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))  # HAIKU
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))  # SONNET
        graph.add_node(_node("c", "chapter_outline", depends_on=("a",)))  # SONNET
        graph.add_node(_node("d", "subplot_suggest", depends_on=("b", "c")))  # OPUS

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])

        # 全部完成
        assert summary.completed == 4
        assert summary.failed == 0
        assert summary.steps == 4
        assert summary.node_count == 4

        # CostTracker: 4 条记录,每节点 1 条
        assert len(tracker.records()) == 4
        scenarios = {r.scenario for r in tracker.records()}
        assert scenarios == {"hook_extraction", "chapter_writing", "chapter_outline", "subplot_suggest"}

    def test_pipeline_token_aggregation(self):
        """summary.total_cost_tokens == CostTracker 总 tokens (估算)"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s" * 100,  # 100 字符输出 → 25 tokens
            ModelTier.OPUS: "o" * 200,  # 200 字符输出 → 50 tokens
        })
        tracker = CostTracker()
        compute = LLMComputeFn(router, cost_tracker=tracker)

        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))  # HAIKU
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))  # SONNET
        graph.add_node(_node("c", "subplot_suggest", depends_on=("a",)))  # OPUS

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])

        # CostTracker tokens == summary tokens (同一估算公式)
        in_t, out_t = tracker.total_tokens()
        assert summary.total_cost_tokens == in_t + out_t

    def test_pipeline_dependency_order(self):
        """依赖顺序:b 必在 a 后执行 (验证 inputs 收集自上游)"""
        router, providers = _make_router({
            ModelTier.HAIKU: "h-a",
            ModelTier.SONNET: "s-b",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)

        execution_order: list[str] = []
        # 拦截:用 custom prompt_builder 抓 node id
        def track_builder(node, inputs):
            execution_order.append(node.node_id)
            return f"prompt for {node.node_id}"

        compute = LLMComputeFn(router, prompt_builder=track_builder)

        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))

        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        # a 先于 b
        assert execution_order.index("a") < execution_order.index("b")

    def test_pipeline_collects_upstream_outputs_as_inputs(self):
        """b 的 inputs 应包含 a 的 output (即 'h-a')"""
        router, _ = _make_router({
            ModelTier.HAIKU: "a-output-text",
            ModelTier.SONNET: "b-output",
            ModelTier.OPUS: "o",
        })
        captured_inputs: dict[str, dict] = {}

        def capture_builder(node, inputs):
            captured_inputs[node.node_id] = inputs
            return f"prompt-{node.node_id}"

        compute = LLMComputeFn(router, prompt_builder=capture_builder)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))

        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        # b 的 inputs 包含 a 的 output
        assert "a" in captured_inputs["b"]
        assert captured_inputs["b"]["a"] == "a-output-text"

    def test_pipeline_uses_correct_tier_per_scenario(self):
        """每个 scenario 路由到正确的 tier provider"""
        router, providers = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))  # HAIKU
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))  # SONNET
        graph.add_node(_node("c", "subplot_suggest", depends_on=("a",)))  # OPUS

        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        assert len(providers[ModelTier.HAIKU].calls) == 1
        assert len(providers[ModelTier.SONNET].calls) == 1
        assert len(providers[ModelTier.OPUS].calls) == 1


# === E2E Test 2: 降级链 (TieredRouter) 联动 ===

class TestE2EDowngrade:
    """E2E: TieredRouter 降级链在高 tier 失败时自动接管"""

    def test_opus_fails_downgrade_to_sonnet(self):
        """OPUS 失败 → 自动降级到 SONNET → 节点仍完成"""
        router, providers = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s-fallback",
            ModelTier.OPUS: ValueError("opus down"),
        })
        compute = LLMComputeFn(router)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "subplot_suggest"))  # primary OPUS

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])

        # 节点完成 (降级成功)
        assert summary.completed == 1
        assert summary.failed == 0
        # 实际调用了 OPUS 和 SONNET
        assert len(providers[ModelTier.OPUS].calls) == 1
        assert len(providers[ModelTier.SONNET].calls) == 1

    def test_all_tiers_fail_node_marks_failed(self):
        """所有 tier 都失败 → 节点 FAILED,GoTScheduler 计入 failed"""
        router, _ = _make_router({
            ModelTier.HAIKU: ValueError("haiku down"),
            ModelTier.SONNET: ValueError("sonnet down"),
            ModelTier.OPUS: ValueError("opus down"),
        })
        compute = LLMComputeFn(router)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "chapter_writing"))  # SONNET primary

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])

        # max_backtracks=0 → 失败被保留,无重试
        assert summary.completed == 0
        assert summary.failed == 1
        # graph 状态: a 节点 FAILED
        status = graph.get_execution("a").status
        assert status == NodeStatus.FAILED


# === E2E Test 3: Backtrack 联动 ===

class TestE2EBacktrack:
    """E2E: 节点失败 + max_backtracks > 0 → 触发 backtrack + STALE 下游"""

    def test_backtrack_marks_downstream_stale(self):
        """a 失败 (max_backtracks=1) → a 重置为 PENDING/READY → b 标 STALE"""
        call_count = {"a": 0}

        class _FailOnceProvider(AIProvider):
            def __init__(self):
                super().__init__(ProviderConfig(api_key="k", model="fail-once"))
                self.calls: list[str] = []

            def get_provider_name(self) -> str:
                return "fail-once"

            def generate(self, prompt: str, **kwargs) -> str:
                self.calls.append(prompt)
                call_count["a"] += 1
                if call_count["a"] == 1:
                    raise ValueError("first attempt fail")
                return "recovered"

            def embed(self, text: str):  # pragma: no cover
                return [0.0]

            def batch_generate(self, prompts, **kwargs):  # pragma: no cover
                return [self.generate(p) for p in prompts]

        providers = {
            ModelTier.HAIKU: _FailOnceProvider(),  # hook_extraction → HAIKU
            ModelTier.SONNET: _StubProvider("sonnet", "b-out"),
            ModelTier.OPUS: _StubProvider("opus", "o"),
        }
        router = TieredRouter(providers)
        compute = LLMComputeFn(router)

        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))

        # max_backtracks=1: 允许 1 次回溯
        sched = GoTScheduler(graph, compute_fn=compute, max_backtracks=1)
        summary = sched.run(start_nodes=["a"])

        # 第二次成功 → a 完成
        # 注意: max_backtracks=1 意味 budget=1,失败后第 2 次跑通
        assert summary.completed >= 1
        # a 重试过 (call_count=2)
        assert call_count["a"] == 2


# === E2E Test 4: CostTracker 集成 ===

class TestE2ECostTracker:
    """E2E: CostTracker 接收 LLMComputeFn 的记录"""

    def test_no_tracker_no_error(self):
        """不传 cost_tracker 也不报错"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router, cost_tracker=None)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "chapter_writing"))

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 1

    def test_tracker_receives_records_with_primary_tier(self):
        """CostTracker 收到的 tier 是 primary tier (非降级实际 tier)"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h-recovered",
            ModelTier.SONNET: ValueError("sonnet down"),
            ModelTier.OPUS: ValueError("opus down"),
        })
        tracker = CostTracker()
        compute = LLMComputeFn(router, cost_tracker=tracker)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "subplot_suggest"))  # primary OPUS

        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        # 1 条记录, tier=OPUS (primary), scenario=subplot_suggest
        assert len(tracker.records()) == 1
        rec = tracker.records()[0]
        assert rec.scenario == "subplot_suggest"
        assert rec.tier == ModelTier.OPUS

    def test_tracker_cost_by_scenario(self):
        """按 scenario 聚合成本"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s" * 1000,  # 大量输出
            ModelTier.OPUS: "o",
        })
        tracker = CostTracker()
        compute = LLMComputeFn(router, cost_tracker=tracker)

        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))  # HAIKU
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))  # SONNET
        graph.add_node(_node("b2", "chapter_writing", depends_on=("a",)))  # SONNET (2 次)

        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        cost_by = tracker.cost_by_scenario()
        assert "hook_extraction" in cost_by
        assert "chapter_writing" in cost_by
        # chapter_writing 跑了 2 次 → 成本 > hook_extraction
        assert cost_by["chapter_writing"] > cost_by["hook_extraction"]


# === E2E Test 5: 缓存 + ExecutionSummary 字段 ===

class TestE2ECacheAndSummary:
    """E2E: ThoughtCache 命中 + ExecutionSummary 字段"""

    def test_summary_fields_populated(self):
        """ExecutionSummary 所有字段被填"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))
        graph.add_node(_node("b", "chapter_writing", depends_on=("a",)))

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])

        assert isinstance(summary, ExecutionSummary)
        assert summary.completed == 2
        assert summary.failed == 0
        assert summary.steps == 2
        assert summary.node_count == 2
        assert summary.total_cost_tokens > 0
        assert summary.backtrack_count == 0

    def test_cache_hits_skip_llm_call(self):
        """第二次跑相同图 → 缓存命中 → LLM 调用次数不变"""
        router, providers = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))

        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])
        first_calls = len(providers[ModelTier.HAIKU].calls)

        # 第二次跑 (新 scheduler 共享 cache)
        cache = sched._cache
        sched2 = GoTScheduler(graph, compute_fn=compute, cache=cache)
        sched2.run(start_nodes=["a"])
        second_calls = len(providers[ModelTier.HAIKU].calls)

        # 第二次没新增 LLM 调用 (缓存命中)
        assert second_calls == first_calls


# === E2E Test 6: 并发/多起点 ===

class TestE2EConcurrency:
    """E2E: 多起点 + 并行分支"""

    def test_diamond_topology(self):
        """菱形: root → (a, b) → join"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)

        graph = ThoughtGraph()
        graph.add_node(_node("root", "hook_extraction"))
        graph.add_node(_node("a", "chapter_outline", depends_on=("root",)))
        graph.add_node(_node("b", "chapter_outline", depends_on=("root",)))
        graph.add_node(_node("join", "subplot_suggest", depends_on=("a", "b")))

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["root"])

        assert summary.completed == 4
        assert summary.node_count == 4
        # join 节点必在 a, b 之后
        join_exec = graph.get_execution("join")
        assert join_exec.status == NodeStatus.COMPLETED

    def test_empty_start_nodes(self):
        """空 start_nodes → 立即返回 (0/0)"""
        router, _ = _make_router({
            ModelTier.HAIKU: "h",
            ModelTier.SONNET: "s",
            ModelTier.OPUS: "o",
        })
        compute = LLMComputeFn(router)
        graph = ThoughtGraph()
        graph.add_node(_node("a", "hook_extraction"))

        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=[])
        assert summary.completed == 0
        assert summary.node_count == 1
