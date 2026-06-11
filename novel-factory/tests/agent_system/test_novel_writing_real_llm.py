"""Phase 8: Real LLM E2E — 验证 polish_merge S1-S8 评分在生产路径下产出真实分数.

默认 SKIP (无 ANTHROPIC_API_KEY), opt-in 跑:
    export ANTHROPIC_API_KEY=sk-ant-...
    pytest tests/agent_system/test_novel_writing_real_llm.py -v

成本: HAIKU × 6 LLM calls ≈ $0.005-0.020 per test.

跟 tests/agent_system/test_master_controller_stub_router_e2e.py 区别:
- test_master_controller_stub_router_e2e.py: 用 StubProvider 注入 mock router 跑生产路径
- test_novel_writing_real_llm.py (本文件): 真实 Anthropic API 调用
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.agent_system._e2e_helpers import _make_real_router, make_master_with_router

_REQUIRES_ANTHROPIC_KEY = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Phase 8 real LLM test requires ANTHROPIC_API_KEY env var",
)
_REQUIRES_OPENAI_KEY = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="Phase 8.2 real LLM test requires OPENAI_API_KEY env var",
)
_REQUIRES_MINIMAX_KEY = pytest.mark.skipif(
    not os.environ.get("MINIMAX_API_KEY"),
    reason="Phase 8.2 real LLM test requires MINIMAX_API_KEY env var",
)


def _assert_s1_s8_score_dict(scores: dict, label: str) -> None:
    """验证 S1-S8 评分 dict 合法: 8 keys + int + 0-10 范围"""
    assert set(scores.keys()) == {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"}, (
        f"{label} keys 不完整: {set(scores.keys())}"
    )
    for s1_s8, score in scores.items():
        assert isinstance(score, int), (
            f"{label}[{s1_s8}] 应为 int, 实际 {type(score).__name__}: {score!r}"
        )
        assert 0 <= score <= 10, f"{label}[{s1_s8}]={score} 超出 0-10 范围"


@_REQUIRES_ANTHROPIC_KEY
class TestNovelWritingRealLLM:
    """Phase 8: novel_writing.yaml 7 节点端到端, 验证 polish_merge S1-S8 真实评分."""

    def test_novel_writing_yaml_polish_merge_produces_s1_s8_scores(self, tmp_path: Path) -> None:
        """novel_writing.yaml 端到端跑通, 验证 polish_merge.output 含 S1-S8 真实评分.

        跑 6 LLM calls: write + audit + 2 emotional_pacing + 1 ai_trace_removal + 1 polish_merge.
        """
        router = _make_real_router("anthropic")
        master = make_master_with_router(state_dir=tmp_path, router=router)

        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,  # 短内容加速 HAIKU 处理
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },
            max_backtracks=0,  # fail fast, 不重试 (避免 6×2=12 LLM calls 成本 +10x)
        )

        # 1. workflow 跑通
        summary = result["summary"]
        assert summary.completed >= 6, f"期望 ≥6 节点完成, 实际 {summary.completed}"
        assert summary.failed == 0, f"期望 0 失败, 实际 {summary.failed}"

        # 2. polish_merge 节点走 LLM 路径 (非 fallback)
        merge_exec = result["executions"]["polish_merge"]
        merge_output = merge_exec.output
        assert merge_output["fallback"] is None, (
            f"polish_merge 应走 LLM 路径, 但 fallback={merge_output['fallback']!r}. "
            f"可能上游 polish variant 内容相同导致 identical fallback"
        )

        # 3. S1-S8 8 维评分真实
        _assert_s1_s8_score_dict(merge_output["scores_a"], "scores_a")
        _assert_s1_s8_score_dict(merge_output["scores_b"], "scores_b")

        # 4. winner + totals 合理
        assert merge_output["winner"] in merge_output["_labels"], (
            f"winner={merge_output['winner']!r} 不在 _labels={merge_output['_labels']!r}"
        )
        assert 0.0 <= merge_output["scores_total_a"] <= 10.0
        assert 0.0 <= merge_output["scores_total_b"] <= 10.0
        assert abs(
            merge_output["scores_total_a"]
            - merge_output["scores_total_b"]
            - merge_output["scores_delta"]
        ) < 1e-6, (
            f"scores_delta={merge_output['scores_delta']} 不等于 "
            f"total_a - total_b={merge_output['scores_total_a'] - merge_output['scores_total_b']}"
        )

        # 5. labels 透传 (Phase 7.6 dashboard 雷达图依赖)
        assert merge_output["_labels"] == ["polish_emotional_pacing", "polish_ai_trace_removal"]


@_REQUIRES_ANTHROPIC_KEY
class TestPolishMergeSynthesisRealLLM:
    """Phase 8: 直接调 polish_merge_synthesis, 1 LLM call 快速验证 Phase 7.5 核心 (~5-10s)."""

    def test_polish_merge_synthesis_with_distinct_contents(self, tmp_path: Path) -> None:
        """2 个不同内容 → 走 LLM 评分路径, 产出 S1-S8 真实分数.

        单独跑: pytest -k PolishMergeSynthesis 5-10s 验证 Phase 7.5 核心.
        """
        router = _make_real_router("anthropic")
        master = make_master_with_router(state_dir=tmp_path, router=router)

        # 2 个不同内容 (短段落, ~400 chars each)
        content_a = "少年握紧拳头, 眼中燃烧着不甘。寒风刺骨, 但他咬牙前行。" * 20
        content_b = "林夕深吸一口气, 心中暗自立下誓言。纵然前路艰险, 亦不退缩。" * 20

        result = master.polish_merge_synthesis(
            content_a, content_b, labels=("emotional", "motivation"),
        )

        # 跟 TestNovelWritingRealLLM 同样的 5 步断言
        assert result.get("fallback") is None, (
            f"polish_merge_synthesis 应走 LLM 路径, 但 fallback={result['fallback']!r}"
        )
        _assert_s1_s8_score_dict(result["scores_a"], "scores_a")
        _assert_s1_s8_score_dict(result["scores_b"], "scores_b")
        assert result["winner"] in result["_labels"]
        assert 0.0 <= result["scores_total_a"] <= 10.0
        assert 0.0 <= result["scores_total_b"] <= 10.0
        assert abs(
            result["scores_total_a"] - result["scores_total_b"] - result["scores_delta"]
        ) < 1e-6
        assert result["_labels"] == ["emotional", "motivation"]


# ==================== Phase 8.2: Multi-Provider Matrix ====================


@_REQUIRES_OPENAI_KEY
class TestNovelWritingRealLLMOpenAI:
    """Phase 8.2: OpenAI 真实 LLM E2E 验证 polish_merge 跨 provider 兼容.

    跟 TestPolishMergeSynthesisRealLLM (Anthropic) 同样的 9 步断言.
    Cost: gpt-4o-mini 1 LLM call ≈ $0.001-0.003 (7-8x cheaper than HAIKU).

    跑: export OPENAI_API_KEY=sk-...; pytest tests/agent_system/test_novel_writing_real_llm.py -k OpenAI -v
    """

    def test_polish_merge_synthesis_with_distinct_contents(self, tmp_path: Path) -> None:
        """OpenAI: 2 个不同内容 → 走 LLM 评分路径, 产出 S1-S8 真实分数."""
        router = _make_real_router("openai")
        master = make_master_with_router(state_dir=tmp_path, router=router)

        content_a = "少年握紧拳头, 眼中燃烧着不甘。寒风刺骨, 但他咬牙前行。" * 20
        content_b = "林夕深吸一口气, 心中暗自立下誓言。纵然前路艰险, 亦不退缩。" * 20

        result = master.polish_merge_synthesis(
            content_a, content_b, labels=("emotional", "motivation"),
        )

        # 9 步断言 (跟 TestPolishMergeSynthesisRealLLM 一致)
        assert result.get("fallback") is None, (
            f"polish_merge_synthesis (OpenAI) 应走 LLM 路径, 但 fallback={result['fallback']!r}"
        )
        _assert_s1_s8_score_dict(result["scores_a"], "scores_a")
        _assert_s1_s8_score_dict(result["scores_b"], "scores_b")
        assert result["winner"] in result["_labels"]
        assert 0.0 <= result["scores_total_a"] <= 10.0
        assert 0.0 <= result["scores_total_b"] <= 10.0
        assert abs(
            result["scores_total_a"] - result["scores_total_b"] - result["scores_delta"]
        ) < 1e-6
        assert result["_labels"] == ["emotional", "motivation"]


@_REQUIRES_MINIMAX_KEY
class TestNovelWritingRealLLMMiniMax:
    """Phase 8.2: MiniMax 真实 LLM E2E 验证 polish_merge 跨 provider 兼容.

    跟 TestPolishMergeSynthesisRealLLM (Anthropic) 同样的 9 步断言.
    Cost: MiniMax M2.7 单价未知, 1 LLM call 预计 < $0.01.

    跑: export MINIMAX_API_KEY=...; pytest tests/agent_system/test_novel_writing_real_llm.py -k MiniMax -v
    """

    def test_polish_merge_synthesis_with_distinct_contents(self, tmp_path: Path) -> None:
        """MiniMax: 2 个不同内容 → 走 LLM 评分路径, 产出 S1-S8 真实分数."""
        router = _make_real_router("minimax")
        master = make_master_with_router(state_dir=tmp_path, router=router)

        content_a = "少年握紧拳头, 眼中燃烧着不甘。寒风刺骨, 但他咬牙前行。" * 20
        content_b = "林夕深吸一口气, 心中暗自立下誓言。纵然前路艰险, 亦不退缩。" * 20

        result = master.polish_merge_synthesis(
            content_a, content_b, labels=("emotional", "motivation"),
        )

        # 9 步断言 (跟 TestPolishMergeSynthesisRealLLM 一致)
        assert result.get("fallback") is None, (
            f"polish_merge_synthesis (MiniMax) 应走 LLM 路径, 但 fallback={result['fallback']!r}"
        )
        _assert_s1_s8_score_dict(result["scores_a"], "scores_a")
        _assert_s1_s8_score_dict(result["scores_b"], "scores_b")
        assert result["winner"] in result["_labels"]
        assert 0.0 <= result["scores_total_a"] <= 10.0
        assert 0.0 <= result["scores_total_b"] <= 10.0
        assert abs(
            result["scores_total_a"] - result["scores_total_b"] - result["scores_delta"]
        ) < 1e-6
        assert result["_labels"] == ["emotional", "motivation"]


@_REQUIRES_ANTHROPIC_KEY
class TestNovelWritingBudgetRealLLM:
    """Phase 8.9: real LLM e2e opt-in tests 验证 cost_budget_usd 硬中止触阈.

    复用 Phase 8/8.1/8.2 opt-in pattern (skipif ANTHROPIC_API_KEY + _make_real_router +
    make_master_with_router). 默认 SKIP, opt-in 跑:
        export ANTHROPIC_API_KEY=sk-ant-...
        pytest tests/agent_system/test_novel_writing_real_llm.py::TestNovelWritingBudgetRealLLM -v
    成本: HAIKU × ~5 LLM calls × 2 tests ≈ $0.025-0.05 per run, ~30-60s per test.
    """

    def test_run_workflow_under_budget_passes(self, tmp_path: Path) -> None:
        """Phase 8.9: real LLM run with generous budget, 验证 success + cost < budget + finally reset."""
        from infra.ai_service.cost_tracker import CostTracker
        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=_make_real_router("anthropic"),
            cost_tracker=cost_tracker,
        )
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,  # 短内容加速 HAIKU 处理
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },  # 跟 Phase 8 现有 pattern (L63-74) 完全一致
            cost_budget_usd=0.10,  # 10x 预期 $0.005-0.020
            max_backtracks=0,
        )

        summary = result["summary"]
        # 1. 完整跑通
        assert summary.completed >= 5, f"期望 ≥5 completed (5 LLM 节点), 实际 {summary.completed}"
        assert summary.failed == 0, f"期望 0 failed (under-budget), 实际 {summary.failed}"
        # 2. cost 在预算内
        total_cost = cost_tracker.total_cost()
        assert 0 < total_cost < 0.10, f"期望 0 < cost < 0.10, 实际 {total_cost}"
        # 3. finally reset
        assert master._current_budget_usd is None, (
            f"期望 finally reset to None, 实际 {master._current_budget_usd}"
        )

    def test_run_workflow_over_budget_raises(self, tmp_path: Path) -> None:
        """Phase 8.9: real LLM run with sub-cent budget, 验证 CostBudgetExceeded + FAILED + finally reset."""
        from infra.ai_service.cost_tracker import CostBudgetExceeded, CostTracker
        _ = CostBudgetExceeded  # 文档化: workflow 内部抛此异常, scheduler 捕获后转 FAILED
        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=_make_real_router("anthropic"),
            cost_tracker=cost_tracker,
        )
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },  # 跟 Phase 8 现有 pattern 一致
            cost_budget_usd=0.0001,  # sub-cent, 必超
            max_backtracks=0,
        )

        summary = result["summary"]
        # 1. 至少 1 node FAILED (触阈那个)
        assert summary.failed >= 1, (
            f"期望 ≥1 FAILED, 实际 completed={summary.completed} failed={summary.failed}"
        )
        # 2. workflow 中止, 不全跑 (Phase 7.4 = 7 节点)
        total = summary.completed + summary.failed
        assert total < 7, f"期望 total < 7 (workflow 被中止), 实际 {total}"
        # 3. cost 累加 > budget (触阈发生)
        assert cost_tracker.total_cost() > 0.0001
        # 4. finally reset 在 raise 后仍生效
        assert master._current_budget_usd is None, (
            f"期望 finally reset after raise, 实际 {master._current_budget_usd}"
        )
        # 5. 至少 1 笔 record 写入
        assert len(cost_tracker.records()) >= 1


@_REQUIRES_OPENAI_KEY
class TestNovelWritingBudgetRealLLMOpenAI:
    """Phase 8.10: OpenAI gpt-4o-mini real LLM e2e 验证 cost_budget_usd 触阈.

    复用 Phase 8.9 pattern (skipif OPENAI_API_KEY + _make_real_router("openai") +
    make_master_with_router + inline 7-key initial_inputs dict). 默认 SKIP, opt-in 跑:
        export OPENAI_API_KEY=sk-...
        pytest tests/agent_system/test_novel_writing_real_llm.py::TestNovelWritingBudgetRealLLMOpenAI -v
    成本: gpt-4o-mini × ~5 LLM calls × 2 tests ≈ $0.005-0.015 per run, ~30-60s per test.
    """

    def test_run_workflow_under_budget_passes(self, tmp_path: Path) -> None:
        """Phase 8.10: OpenAI gpt-4o-mini generous budget, 验证 success + cost < budget + finally reset."""
        from infra.ai_service.cost_tracker import CostTracker
        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=_make_real_router("openai"),
            cost_tracker=cost_tracker,
        )
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,  # 短内容加速 gpt-4o-mini 处理
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },  # 跟 Phase 8 现有 pattern (L63-74) + Phase 8.9 L248-259 完全一致
            cost_budget_usd=0.10,  # 10x 预期 $0.001-0.010 (gpt-4o-mini 7-8x cheaper)
            max_backtracks=0,
        )

        summary = result["summary"]
        # 1. 完整跑通
        assert summary.completed >= 5, f"期望 ≥5 completed (5 LLM 节点), 实际 {summary.completed}"
        assert summary.failed == 0, f"期望 0 failed (under-budget), 实际 {summary.failed}"
        # 2. cost 在预算内
        total_cost = cost_tracker.total_cost()
        assert 0 < total_cost < 0.10, f"期望 0 < cost < 0.10, 实际 {total_cost}"
        # 3. finally reset
        assert master._current_budget_usd is None, (
            f"期望 finally reset to None, 实际 {master._current_budget_usd}"
        )

    def test_run_workflow_over_budget_raises(self, tmp_path: Path) -> None:
        """Phase 8.10: OpenAI gpt-4o-mini sub-cent budget, 验证 CostBudgetExceeded + FAILED + finally reset."""
        from infra.ai_service.cost_tracker import CostBudgetExceeded, CostTracker
        _ = CostBudgetExceeded  # 文档化: workflow 内部抛此异常, scheduler 捕获后转 FAILED
        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=_make_real_router("openai"),
            cost_tracker=cost_tracker,
        )
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },  # 跟 Phase 8 现有 pattern 一致
            cost_budget_usd=0.0001,  # sub-cent, 必超
            max_backtracks=0,
        )

        summary = result["summary"]
        # 1. 至少 1 node FAILED (触阈那个)
        assert summary.failed >= 1, (
            f"期望 ≥1 FAILED, 实际 completed={summary.completed} failed={summary.failed}"
        )
        # 2. workflow 中止, 不全跑 (Phase 7.4 = 7 节点)
        total = summary.completed + summary.failed
        assert total < 7, f"期望 total < 7 (workflow 被中止), 实际 {total}"
        # 3. cost 累加 > budget (触阈发生)
        assert cost_tracker.total_cost() > 0.0001
        # 4. finally reset 在 raise 后仍生效
        assert master._current_budget_usd is None, (
            f"期望 finally reset after raise, 实际 {master._current_budget_usd}"
        )
        # 5. 至少 1 笔 record 写入
        assert len(cost_tracker.records()) >= 1


@_REQUIRES_MINIMAX_KEY
class TestNovelWritingBudgetRealLLMMiniMax:
    """Phase 8.10: MiniMax M2.7 real LLM e2e 验证 cost_budget_usd 触阈.

    复用 Phase 8.9 pattern (skipif MINIMAX_API_KEY + _make_real_router("minimax") +
    make_master_with_router + inline 7-key initial_inputs dict). 默认 SKIP, opt-in 跑:
        export MINIMAX_API_KEY=...
        pytest tests/agent_system/test_novel_writing_real_llm.py::TestNovelWritingBudgetRealLLMMiniMax -v
    成本: MiniMax M2.7 × ~5 LLM calls × 2 tests ≈ $0.01-0.05 per run, ~30-60s per test.
    """

    def test_run_workflow_under_budget_passes(self, tmp_path: Path) -> None:
        """Phase 8.10: MiniMax M2.7 generous budget, 验证 success + cost < budget + finally reset."""
        from infra.ai_service.cost_tracker import CostTracker
        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=_make_real_router("minimax"),
            cost_tracker=cost_tracker,
        )
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,  # 短内容加速 M2.7 处理
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },  # 跟 Phase 8 现有 pattern (L63-74) + Phase 8.9 L248-259 完全一致
            cost_budget_usd=0.10,  # 2x 预期 <$0.05 (M2.7 单价 <$0.01/call)
            max_backtracks=0,
        )

        summary = result["summary"]
        # 1. 完整跑通
        assert summary.completed >= 5, f"期望 ≥5 completed (5 LLM 节点), 实际 {summary.completed}"
        assert summary.failed == 0, f"期望 0 failed (under-budget), 实际 {summary.failed}"
        # 2. cost 在预算内
        total_cost = cost_tracker.total_cost()
        assert 0 < total_cost < 0.10, f"期望 0 < cost < 0.10, 实际 {total_cost}"
        # 3. finally reset
        assert master._current_budget_usd is None, (
            f"期望 finally reset to None, 实际 {master._current_budget_usd}"
        )

    def test_run_workflow_over_budget_raises(self, tmp_path: Path) -> None:
        """Phase 8.10: MiniMax M2.7 sub-cent budget, 验证 CostBudgetExceeded + FAILED + finally reset."""
        from infra.ai_service.cost_tracker import CostBudgetExceeded, CostTracker
        _ = CostBudgetExceeded  # 文档化: workflow 内部抛此异常, scheduler 捕获后转 FAILED
        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=_make_real_router("minimax"),
            cost_tracker=cost_tracker,
        )
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {"chapters": [{
                    "num": 1, "title": "第一章 测试", "events": ["e1"],
                    "word_count_target": 800,
                }]},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },  # 跟 Phase 8 现有 pattern 一致
            cost_budget_usd=0.0001,  # sub-cent, 必超
            max_backtracks=0,
        )

        summary = result["summary"]
        # 1. 至少 1 node FAILED (触阈那个)
        assert summary.failed >= 1, (
            f"期望 ≥1 FAILED, 实际 completed={summary.completed} failed={summary.failed}"
        )
        # 2. workflow 中止, 不全跑 (Phase 7.4 = 7 节点)
        total = summary.completed + summary.failed
        assert total < 7, f"期望 total < 7 (workflow 被中止), 实际 {total}"
        # 3. cost 累加 > budget (触阈发生)
        assert cost_tracker.total_cost() > 0.0001
        # 4. finally reset 在 raise 后仍生效
        assert master._current_budget_usd is None, (
            f"期望 finally reset after raise, 实际 {master._current_budget_usd}"
        )
        # 5. 至少 1 笔 record 写入
        assert len(cost_tracker.records()) >= 1
