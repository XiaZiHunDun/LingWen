"""Tests for infra.agent_system.got_bridge (Phase 3.1 + 3.2 — GoT bridge)

Doc 4 (GoT 适配设计 v1.0) §十一 Phase 3:
MasterController + GoT 整合。本测试验证:
- AgentComputeFn 协议: __call__(node, inputs) → ComputeResult
- scenario → handler 映射完整覆盖 12 SCENARIOS
- handler 失败 → ComputeResult(fail=True, ...)
- 节点无 prompt_scenario → fail
- 未注册 scenario → fail
- build_got_scheduler: 加载 YAML + 构造 GoTScheduler
- MasterController.run_workflow: 委托给 GoT bridge
"""
from __future__ import annotations

from typing import Any, Optional

import pytest

from infra.agent_system.got_bridge import (
    SCENARIO_HANDLERS,
    AgentComputeFn,
    build_got_scheduler,
    registered_scenarios,
    uncovered_scenarios,
)
from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.got.data_structures import NodeStatus, NodeType, ThoughtNode
from infra.got.scheduler import ComputeResult, ExecutionSummary

# === Test fixtures: stub MasterController ===

class _StubMaster:
    """最小 MasterController stub — 不连 API,不读状态"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def write_chapter(self, chapter_num, outline, characters, memory_context, style_guide, use_llm):
        self.calls.append(("write_chapter", {"chapter_num": chapter_num, "use_llm": use_llm}))
        return {"content": f"ch{chapter_num} text", "word_count": 100, "suggestions": []}

    def audit_chapter(self, chapter_num, content, characters, timeline, use_llm):
        self.calls.append(("audit_chapter", {"chapter_num": chapter_num, "content_len": len(content)}))
        return {"chapter": chapter_num, "issues": [], "scores": {"S1": 80}}

    def polish_chapter(self, content: str) -> str:
        self.calls.append(("polish_chapter", {"content_len": len(content)}))
        return content + " [polished]"

    # Phase 7.4: 新增 2 个 variant entry methods (用于 test_got_bridge 路由测试)
    def polish_emotional_pacing(self, content: str) -> str:
        self.calls.append(("polish_emotional_pacing", {"content_len": len(content)}))
        return content + " [emotional]"

    def polish_ai_trace_removal(self, content: str) -> str:
        self.calls.append(("polish_ai_trace_removal", {"content_len": len(content)}))
        return content + " [ai_removed]"

    # Phase 8.6.2: 5 *_with_usage methods — 供 test_got_bridge 验证 tuple return path
    # 返回 max(len(content)) fallback 模拟真实 LLM usage (含 input/output tokens)
    def write_chapter_with_usage(self, chapter_num, outline, characters, memory_context, style_guide, use_llm):
        self.calls.append(("write_chapter_with_usage", {"chapter_num": chapter_num, "use_llm": use_llm}))
        return (
            {"content": f"ch{chapter_num} text", "word_count": 100, "suggestions": []},
            {"input_tokens": 100, "output_tokens": 50},
        )

    def audit_chapter_with_usage(self, chapter_num, content, characters, timeline, use_llm):
        self.calls.append(("audit_chapter_with_usage", {"chapter_num": chapter_num, "content_len": len(content)}))
        return (
            {"chapter": chapter_num, "issues": [], "scores": {"S1": 80}},
            {"input_tokens": 80, "output_tokens": 40},
        )

    def polish_chapter_with_usage(self, chapter_num, content, style_guide=None):
        self.calls.append(("polish_chapter_with_usage", {"content_len": len(content)}))
        return (content + " [polished]", {"input_tokens": 200, "output_tokens": 100})

    def polish_emotional_pacing_with_usage(self, chapter_num, content):
        self.calls.append(("polish_emotional_pacing_with_usage", {"content_len": len(content)}))
        return (content + " [emotional]", {"input_tokens": 200, "output_tokens": 100})

    def polish_ai_trace_removal_with_usage(self, chapter_num, content):
        self.calls.append(("polish_ai_trace_removal_with_usage", {"content_len": len(content)}))
        return (content + " [ai_removed]", {"input_tokens": 100, "output_tokens": 50})

    # Phase 7.5: stub polish_merge_synthesis — 默认走 max(len) 兜底 (不调 LLM)
    def polish_merge_synthesis(self, content_a: str, content_b: str, *, labels=("A", "B")) -> dict:
        """Stub: 模拟 master.polish_merge_synthesis 的 max(len) 兜底 (默认 stub 不调 LLM)"""
        if not content_a or not content_b:
            winner = labels[0] if content_a else labels[1]
            content = content_a or content_b
            return {"content": content, "winner": winner, "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "empty_content"}
        if content_a == content_b:
            return {"content": content_a, "winner": labels[0], "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "identical"}
        winner_label = labels[0] if len(content_a) >= len(content_b) else labels[1]
        content = content_a if winner_label == labels[0] else content_b
        return {"content": content, "winner": winner_label, "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "llm_fail"}

    # Phase 8.7: stub polish_merge_synthesis_with_usage — 跟 5 *_with_usage methods 同模式
    # 返 (max(len) fallback dict, hardcoded 100/50). _handler_polish_merge 改调此方法.
    def polish_merge_synthesis_with_usage(self, content_a, content_b, *, labels=("A", "B")):
        """Phase 8.7: stub 返 (max(len) fallback dict, 100/50 hardcoded)."""
        chosen = content_a if len(content_a) >= len(content_b) else content_b
        winner = labels[0] if len(content_a) >= len(content_b) else labels[1]
        return (
            {
                "content": chosen,
                "winner": winner,
                "scores_a": {}, "scores_b": {},
                "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0,
                "fallback": "stub_max_len",
            },
            {"input_tokens": 100, "output_tokens": 50},
        )

    def generate_outline(self, settings, requirements):
        self.calls.append(("generate_outline", {"settings_keys": list(settings.keys())}))
        return {"chapters": [], "volume": 1}


def _node(node_id: str, scenario: Optional[str]) -> ThoughtNode:
    return ThoughtNode(
        node_id=node_id,
        type=NodeType.GENERATION,
        name=f"node_{node_id}",
        description=f"测试节点 {node_id}",
        prompt_scenario=scenario,
    )


# === TestScenarioCoverage ===

class TestScenarioCoverage:
    """12 SCENARIOS 全部覆盖 AgentComputeFn"""

    def test_all_12_scenarios_registered(self):
        from infra.prompt_engineering.scenarios import SCENARIOS
        assert len(SCENARIOS) == 12
        for s in SCENARIOS:
            assert s in SCENARIO_HANDLERS, f"scenario {s!r} not in SCENARIO_HANDLERS"

    def test_registered_scenarios_returns_tuple(self):
        scenarios = registered_scenarios()
        assert isinstance(scenarios, tuple)
        # Phase 7.4: 12 SCENARIOS + 1 polish_merge (自定义) = 13
        assert len(scenarios) == 13

    def test_uncovered_scenarios_is_empty(self):
        assert uncovered_scenarios() == ()

    def test_handlers_dict_is_mutable_mapping(self):
        # SCENARIO_HANDLERS 是 dict(可扩展),新加 scenario 直接插入
        assert isinstance(SCENARIO_HANDLERS, dict)
        assert "chapter_writing" in SCENARIO_HANDLERS


# === TestAgentComputeFnBasic ===

class TestAgentComputeFnBasic:
    """基本调用:scenario → handler → ComputeResult"""

    def test_chapter_writing_routes_to_write_chapter(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("ch1", "chapter_writing")
        result = compute(node, {"chapter_num": 1, "use_llm": False})
        assert isinstance(result, ComputeResult)
        assert result.fail is False
        assert "ch1 text" in result.output["content"]
        # Phase 8.6.2: handler 调 write_chapter_with_usage 拿真实 usage
        assert master.calls[0][0] == "write_chapter_with_usage"
        assert master.calls[0][1]["chapter_num"] == 1

    def test_chapter_review_routes_to_audit(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("rev1", "chapter_review")
        result = compute(node, {"chapter_num": 1, "content": "abcdefg", "use_llm": False})
        assert result.fail is False
        assert result.output["chapter"] == 1
        # Phase 8.6.2: handler 调 audit_chapter_with_usage 拿真实 usage
        assert master.calls[0][0] == "audit_chapter_with_usage"

    def test_ai_trace_removal_routes_to_polish_ai_trace_removal(self):
        """Phase 7.4: scenario=ai_trace_removal 走新的 polish_ai_trace_removal entry method"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("pol1", "ai_trace_removal")
        result = compute(node, {"content": "raw text"})
        assert result.fail is False
        assert "[ai_removed]" in result.output["content"]
        # Phase 8.6.2: 工厂调 polish_ai_trace_removal_with_usage 拿真实 usage
        assert master.calls[0][0] == "polish_ai_trace_removal_with_usage"

    def test_outline_review_routes_to_generate_outline(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("out1", "outline_review")
        result = compute(node, {"settings": {"genre": "xuanhuan"}, "requirements": {"length": 50}})
        assert result.fail is False
        assert "chapters" in result.output
        assert master.calls[0][0] == "generate_outline"


# === TestAgentComputeFnFailure ===

class TestAgentComputeFnFailure:
    """失败处理:无 scenario / 未注册 / handler 抛错 / 业务失败"""

    def test_none_scenario_passes_through_as_input_node(self):
        """无 prompt_scenario = input/output 节点,旁路返回 inputs 自身 (供下游参考)"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("n1", None)
        inputs = {"key": "value", "n": 42}
        result = compute(node, inputs)
        assert result.fail is False
        assert result.output == inputs
        # master 未被调用
        assert master.calls == []

    def test_unregistered_scenario_returns_fail(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("n1", "totally_made_up_scenario")
        result = compute(node, {})
        assert result.fail is True
        assert "no registered handler" in result.error.lower()

    def test_handler_exception_caught_as_fail(self):
        master = _StubMaster()
        # Phase 8.6.2: handler 调 write_chapter_with_usage, 强行让该 variant 抛错
        def boom(*args, **kwargs):
            raise RuntimeError("upstream error")
        master.write_chapter_with_usage = boom

        compute = AgentComputeFn(master)
        node = _node("n1", "chapter_writing")
        result = compute(node, {"chapter_num": 1})
        assert result.fail is True
        assert "upstream error" in result.error

    def test_business_error_marker_treated_as_fail(self):
        """handler 返回 dict 含 _error 字段 → 业务失败"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        # chapter_writing handler 在 chapter_num=0 时返回 _error
        node = _node("n1", "chapter_writing")
        result = compute(node, {"chapter_num": 0})
        assert result.fail is True
        assert "chapter_num" in result.error


# === TestAgentComputeFnProtocol ===

class TestAgentComputeFnProtocol:
    """满足 ComputeFn 协议 (与 GoTScheduler 兼容)"""

    def test_callable(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        assert callable(compute)

    def test_returns_compute_result_instance(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("n1", "chapter_writing")
        result = compute(node, {"chapter_num": 1})
        assert isinstance(result, ComputeResult)


# === TestBuildGoTScheduler ===

class TestBuildGoTScheduler:
    """build_got_scheduler 工厂:加载 workflow + 构造 scheduler"""

    def test_loads_novel_writing_workflow(self):
        master = _StubMaster()
        scheduler, graph = build_got_scheduler(master, "novel_writing")
        # Phase 7.4: 7 节点 (含 2 个并行 polish + 1 merge) — read_snapshot → write_chapter → review_chapter → polish_emotional_pacing + polish_ai_trace_removal → polish_merge → emit_chapter
        assert len(graph.node_ids()) == 7
        # scheduler 是 GoTScheduler 实例
        from infra.got.scheduler import GoTScheduler
        assert isinstance(scheduler, GoTScheduler)

    def test_scheduler_compute_fn_is_agent_compute(self):
        master = _StubMaster()
        scheduler, _ = build_got_scheduler(master, "novel_writing")
        # 内部 compute_fn 是 AgentComputeFn 实例
        from infra.agent_system.got_bridge import AgentComputeFn
        assert isinstance(scheduler._compute_fn, AgentComputeFn)


# === TestE2EWorkflow ===

class TestE2EWorkflow:
    """E2E: 加载 novel_writing + 跑 write_chapter → review_chapter 链"""

    def test_run_novel_writing_writes_and_reviews(self):
        """stub 模式下完整跑 novel_writing (write_chapter + review_chapter 走 stub)

        通过 initial_inputs 注入 chapter_num=1,让 read_snapshot passthrough 把它传给下游
        """
        master = _StubMaster()
        scheduler, graph = build_got_scheduler(master, "novel_writing", max_backtracks=0)

        # 注入 initial inputs (chapter_num, characters, style_guide)
        initial = {
            "chapter_num": 1,
            "characters": [],
            "style_guide": {},
            "timeline": [],
        }
        # 直接用 GoTScheduler 的 run_with_inputs (若没有就用 run + start_nodes)
        summary = scheduler.run(start_nodes=["read_snapshot"], initial_inputs=initial)
        assert isinstance(summary, ExecutionSummary)

        # write_chapter_with_usage + audit_chapter_with_usage 都被调用
        # Phase 8.6.2: handler 走 *_with_usage variant 拿真实 usage
        called = [c[0] for c in master.calls]
        assert "write_chapter_with_usage" in called
        assert "audit_chapter_with_usage" in called

    def test_review_chapter_receives_write_chapter_output(self):
        """review_chapter 的 content 来自 write_chapter 的 output"""
        master = _StubMaster()
        scheduler, graph = build_got_scheduler(master, "novel_writing", max_backtracks=0)
        initial = {"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []}
        scheduler.run(start_nodes=["read_snapshot"], initial_inputs=initial)

        # 找到 audit_chapter_with_usage 调用,验证 content_len > 0
        audit_call = next(c for c in master.calls if c[0] == "audit_chapter_with_usage")
        assert audit_call[1]["content_len"] > 0

    def test_graph_topology_respected(self):
        """节点执行顺序:read_snapshot → write_chapter → review_chapter → emit_chapter"""
        master = _StubMaster()
        execution_order: list[str] = []

        scheduler, graph = build_got_scheduler(master, "novel_writing", max_backtracks=0)
        original_compute = scheduler._compute_fn

        def tracking_compute(node, inputs):
            execution_order.append(node.node_id)
            return original_compute(node, inputs)

        scheduler._compute_fn = tracking_compute
        initial = {"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []}
        scheduler.run(start_nodes=["read_snapshot"], initial_inputs=initial)

        # 4 个节点都被执行
        assert "read_snapshot" in execution_order
        assert "write_chapter" in execution_order
        assert "review_chapter" in execution_order
        # 顺序:read_snapshot 必在 write_chapter 前
        assert execution_order.index("read_snapshot") < execution_order.index("write_chapter")
        assert execution_order.index("write_chapter") < execution_order.index("review_chapter")


# === TestPolishHandlerRouting (Phase 7.4 NEW) ===

class TestPolishHandlerRouting:
    """Phase 7.4: _handler_polish 拆为 _make_polish_handler 工厂, 按 scenario 路由"""

    def test_emotional_pacing_routes_to_polish_emotional_pacing(self):
        """scenario=emotional_pacing → master.polish_emotional_pacing 被调 (非 polish_chapter)"""
        master = _StubMaster()
        # Phase 8.6.2: 工厂调 polish_emotional_pacing_with_usage, stub 该方法
        master.emotional_pacing_calls = []
        def _stub_emotional_with_usage(chapter_num, content):
            master.emotional_pacing_calls.append(content)
            return content + " [emotional]", {"input_tokens": 0, "output_tokens": 0}
        master.polish_emotional_pacing_with_usage = _stub_emotional_with_usage

        compute = AgentComputeFn(master)
        node = _node("pol1", "emotional_pacing")
        result = compute(node, {"content": "raw text"})
        assert result.fail is False
        assert "[emotional]" in result.output["content"]
        assert len(master.emotional_pacing_calls) == 1
        # 验证 polish_chapter (旧 path) 没被调
        assert not any(call[0] == "polish_chapter" for call in master.calls)

    def test_ai_trace_removal_routes_to_polish_ai_trace_removal(self):
        """scenario=ai_trace_removal → master.polish_ai_trace_removal 被调 (非 polish_chapter)"""
        master = _StubMaster()
        # Phase 8.6.2: 工厂调 polish_ai_trace_removal_with_usage, stub 该方法
        master.ai_trace_calls = []
        def _stub_ai_trace_with_usage(chapter_num, content):
            master.ai_trace_calls.append(content)
            return content + " [ai_removed]", {"input_tokens": 0, "output_tokens": 0}
        master.polish_ai_trace_removal_with_usage = _stub_ai_trace_with_usage

        compute = AgentComputeFn(master)
        node = _node("pol2", "ai_trace_removal")
        result = compute(node, {"content": "raw text"})
        assert result.fail is False
        assert "[ai_removed]" in result.output["content"]
        assert len(master.ai_trace_calls) == 1
        assert not any(call[0] == "polish_chapter" for call in master.calls)

    def test_hook_extraction_still_routes_to_polish_chapter(self):
        """反向: hook_extraction 仍走 master.polish_chapter (向后兼容)"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("pol3", "hook_extraction")
        result = compute(node, {"content": "raw text"})
        assert result.fail is False
        # Phase 8.6.2: 工厂调 polish_chapter_with_usage
        assert master.calls[0][0] == "polish_chapter_with_usage"


# === TestPolishMergeHandler (Phase 7.4 NEW) ===

class TestPolishMergeHandler:
    """Phase 7.4: _handler_polish_merge 按 max(len) 合并多个上游 content"""

    def test_polish_merge_picks_longer_content(self):
        """输入 2 个上游, 返 max(len(content)) 版本"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("merge1", "polish_merge")
        inputs = {
            "polish_emotional_pacing": {"content": "short"},
            "polish_ai_trace_removal": {"content": "this is a much longer content version"},
        }
        result = compute(node, inputs)
        assert result.fail is False
        # max(len("short")=5, len("this is a much longer content version")=36) = 36
        assert result.output["content"] == "this is a much longer content version"

    def test_polish_merge_with_single_upstream(self):
        """单上游也能 merge (兜底, 不报错)"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("merge2", "polish_merge")
        inputs = {"polish_emotional_pacing": {"content": "only one"}}
        result = compute(node, inputs)
        assert result.fail is False
        assert result.output["content"] == "only one"

    def test_polish_merge_no_content_returns_error(self):
        """无 content 上游 → _error (不调 master)"""
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("merge3", "polish_merge")
        result = compute(node, {"upstream": {"other": "value"}})
        assert result.fail is True
        assert "polish_merge requires" in result.error


# === TestPolishMergeHandlerScored (Phase 7.5 NEW) ===

class TestPolishMergeHandlerScored:
    """Phase 7.5: _handler_polish_merge 调 master.polish_merge_synthesis (LLM S1-S8)"""

    def test_handler_returns_winner_with_score_fields(self):
        """2 上游走 LLM 评分路径, 返回 dict 含 winner / scores_total_* 字段"""
        # 构造 _StubMaster with LLM-模拟 chat response
        class _ScoringStub(_StubMaster):
            def __init__(self):
                super().__init__()
                # 加 polish_merge_synthesis 方法
                from infra.agent_system.agents.polisher.prompts import _S1_S8_NAMES  # noqa
                self._llm_response = {
                    "scores_A": {"S1": 9, "S2": 9, "S3": 9, "S4": 9, "S5": 9, "S6": 9, "S7": 9, "S8": 9},
                    "scores_B": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},
                    "reason": "A wins",
                }
            def polish_merge_synthesis_with_usage(self, content_a, content_b, *, labels=("A", "B")):
                # Phase 8.7: handler 改调 _with_usage variant, 模拟 LLM 评分
                # 返 (scored_dict, usage_dict) tuple (跟其他 5 *_with_usage methods 同模式)
                total_a = 9.0
                total_b = 5.0
                winner = labels[0] if total_a >= total_b else labels[1]
                content = content_a if winner == labels[0] else content_b
                return (
                    {
                        "content": content,
                        "winner": winner,
                        "scores_a": self._llm_response["scores_A"],
                        "scores_b": self._llm_response["scores_B"],
                        "scores_total_a": total_a,
                        "scores_total_b": total_b,
                        "scores_delta": total_a - total_b,
                    },
                    {"input_tokens": 100, "output_tokens": 50},
                )

        master = _ScoringStub()
        compute = AgentComputeFn(master)
        node = _node("merge_scored", "polish_merge")
        inputs = {
            "polish_emotional_pacing": {"content": "A version here" * 3},
            "polish_ai_trace_removal": {"content": "B version here" * 2},
        }
        result = compute(node, inputs)
        assert result.fail is False
        # handler 按 input key 字典序排序: polish_ai_trace_removal < polish_emotional_pacing
        # → label_a = "polish_ai_trace_removal" (得分 9)
        # → label_b = "polish_emotional_pacing" (得分 5)
        # → 9 > 5 → 选 label_a = "polish_ai_trace_removal"
        # → content = content_a = "B version here" * 2 (polish_ai_trace_removal 的值)
        assert result.output["winner"] == "polish_ai_trace_removal"
        assert result.output["scores_total_a"] == 9.0
        assert result.output["scores_total_b"] == 5.0
        assert "scores_a" in result.output
        assert "scores_b" in result.output
        assert result.output["content"] == "B version here" * 2


# === TestPolishVariantResilience (Phase 7.4 fixup M1 NEW) ===

class TestPolishVariantResilience:
    """Phase 7.4 fixup M1: polish_emotional_pacing + polish_ai_trace_removal 加
    per-step try/except 兜底, 沿用 Phase 7.2 polish_chapter 韧性契约 (LLM
    失败 → logger.warning + content 继续). 锁住 2 个 entry methods 在
    polisher LLM 抛错时仍返回 str (不冒泡到 AgentComputeFn → 节点 FAILED).
    """

    def _make_master_with_broken_polisher(
        self,
        dialogue_raises: bool = True,
        pacing_raises: bool = True,
    ):
        """构造 stub MasterController + polisher (可控 LLM 失败).

        通过 MasterController.__new__ 绕过 __init__ (避免 build_router 等重操作),
        只塞 self.polisher 即可 — polish_xxx methods 只读 self.polisher.
        """
        from infra.agent_system import master_controller as mc_mod

        controller = mc_mod.MasterController.__new__(mc_mod.MasterController)

        class _BrokenPolisher:
            """LLM 方法可控抛错, 规则方法正常"""

            def optimize_dialogue_llm(self, content, **kwargs):
                if dialogue_raises:
                    raise RuntimeError("dialogue_llm upstream error")
                return content + " [dialogue_ok]"

            def adjust_pacing_llm(self, content, **kwargs):
                if pacing_raises:
                    raise RuntimeError("pacing_llm upstream error")
                return content + " [pacing_ok]"

            def remove_ai_gloss(self, content):
                # 规则路径, 模拟 "首先/其次/..." 替换
                return content.replace("首先", "")

        controller.polisher = _BrokenPolisher()
        return controller

    def test_polish_emotional_pacing_survives_dialogue_llm_failure(self):
        """dialogue_llm 抛错 → emotional_pacing 仍返 str, content 走 fallback"""
        master = self._make_master_with_broken_polisher(
            dialogue_raises=True, pacing_raises=False,
        )
        result = master.polish_emotional_pacing("raw text")
        # 韧性契约: dialogue 失败 → content 不变, pacing 继续 → 加 [pacing_ok]
        assert isinstance(result, str)
        assert "[pacing_ok]" in result
        assert "raw text" in result

    def test_polish_emotional_pacing_survives_pacing_llm_failure(self):
        """pacing_llm 抛错 → emotional_pacing 仍返 str, dialogue 结果保留"""
        master = self._make_master_with_broken_polisher(
            dialogue_raises=False, pacing_raises=True,
        )
        result = master.polish_emotional_pacing("raw text")
        # 韧性契约: dialogue 成功 + pacing 失败 → 保留 dialogue 后的内容
        assert isinstance(result, str)
        assert "[dialogue_ok]" in result
        assert "[pacing_ok]" not in result

    def test_polish_emotional_pacing_survives_both_llm_failures(self):
        """双 LLM 全失败 → 返原 content (str), 不抛"""
        master = self._make_master_with_broken_polisher(
            dialogue_raises=True, pacing_raises=True,
        )
        result = master.polish_emotional_pacing("raw text")
        # 韧性契约: 双失败 → 走 fallback → 返原 content
        assert isinstance(result, str)
        assert result == "raw text"

    def test_polish_ai_trace_removal_survives_dialogue_llm_failure(self):
        """ai_trace_removal: remove_ai_gloss 规则先跑 (从不出错), dialogue 失败时仍返 str"""
        master = self._make_master_with_broken_polisher(
            dialogue_raises=True, pacing_raises=True,  # pacing 不被调
        )
        result = master.polish_ai_trace_removal("首先 raw text")
        # 韧性契约: remove_ai_gloss 成功 (规则) + dialogue 失败 → 返规则结果
        assert isinstance(result, str)
        assert "首先" not in result
        assert "raw text" in result
        # pacing 不被调 (orthogonal design)
        # 已隐式验证 (上面 _BrokenPolisher.adjust_pacing_llm 若被调会抛, 但 ai_trace_removal 不调)

    def test_polish_ai_trace_removal_happy_path(self):
        """ai_trace_removal 正常路径: remove_ai_gloss + dialogue_llm 都成功"""
        master = self._make_master_with_broken_polisher(
            dialogue_raises=False, pacing_raises=True,
        )
        result = master.polish_ai_trace_removal("首先 raw")
        # 规则去掉 "首先" → dialogue 加 [dialogue_ok]
        assert isinstance(result, str)
        assert "首先" not in result
        assert "[dialogue_ok]" in result


# === TestPolishHandlerTypoContract (Phase 7.4 fixup L3 NEW) ===

class TestPolishHandlerTypoContract:
    """Phase 7.4 fixup L3: 锁住 _make_polish_handler(method_name) 契约 —
    getattr(master, method_name) 拼错时抛 AttributeError, 由 AgentComputeFn
    try/except 捕获转 fail=True. 防止未来加 scenario 时拼错 method_name 静默漏掉.
    """

    def test_polish_handler_typo_propagates_as_attribute_error(self):
        """_make_polish_handler('nonexistent_method_xyz') → getattr 抛 AttributeError"""
        from infra.agent_system.got_bridge import _make_polish_handler

        handler = _make_polish_handler("nonexistent_method_xyz")

        class _BrokenMaster:
            """故意没定义 nonexistent_method_xyz"""

        # handler 是闭包, 在被调用时做 getattr(master, method_name)
        # 期望抛 AttributeError 含 method_name 字串 (AgentComputeFn 会捕获转 fail)
        with pytest.raises(AttributeError, match="nonexistent_method_xyz"):
            handler(_BrokenMaster(), {"content": "raw text"})


# === TestCostTrackerWiring (Phase 8.5 NEW) ===

class TestCostTrackerWiring:
    """Phase 8.5: AgentComputeFn 加 cost_tracker kwarg, handler 成功后估 token +
    写 cost_tracker.record(). 默认 None 兜底 (旧测试零修改)."""

    def test_compute_fn_records_cost_when_tracker_provided(self) -> None:
        """AgentComputeFn 注入 CostTracker → handler 调 → cost_tracker 至少 1 条"""
        master = _StubMaster()
        cost_tracker = CostTracker()
        compute = AgentComputeFn(master, cost_tracker=cost_tracker)

        node = _node("n1", "chapter_writing")
        result = compute(node, {"chapter_num": 1, "use_llm": False})

        assert result.fail is False
        # 1 笔记录, scenario=chapter_writing, tier=SONNET (per SCENARIO_TIER_MAP)
        records = cost_tracker.records()
        assert len(records) == 1
        assert records[0].scenario == "chapter_writing"
        assert records[0].tier == ModelTier.SONNET
        # cost_tokens 也填了 (替代硬编码 0)
        assert result.cost_tokens > 0
        # total_cost > 0
        assert cost_tracker.total_cost() > 0

    def test_compute_fn_no_tracker_is_noop(self) -> None:
        """AgentComputeFn 不传 cost_tracker → handler 调 → cost_tokens=0 (向后兼容旧 path)"""
        master = _StubMaster()
        compute = AgentComputeFn(master)  # 不传 cost_tracker (旧用法)

        node = _node("n1", "chapter_writing")
        result = compute(node, {"chapter_num": 1, "use_llm": False})

        # 旧 path 不破: result 正常, cost_tokens=0 (向后兼容)
        assert result.fail is False
        assert result.cost_tokens == 0

    def test_compute_result_cost_tokens_filled(self) -> None:
        """AgentComputeFn 注入 CostTracker → ComputeResult.cost_tokens = in_tok + out_tok > 0"""
        master = _StubMaster()
        cost_tracker = CostTracker()
        compute = AgentComputeFn(master, cost_tracker=cost_tracker)

        # 用 audit (返 dict 含 S1 score) — 验证 output 被估
        node = _node("n1", "chapter_review")
        inputs = {
            "chapter_num": 1,
            "content": "x" * 400,  # 400 chars input prompt
            "use_llm": False,
        }
        result = compute(node, inputs)

        assert result.fail is False
        # 行为级断言 (不耦合 //4 启发式): estimator 改成 tiktoken 也不破
        assert result.cost_tokens > 0
        # 至少 1 笔记录 + 字段正 (input/output tokens > 0, cost_usd > 0)
        assert len(cost_tracker.records()) == 1
        records = cost_tracker.records()
        assert records[0].input_tokens > 0
        assert records[0].output_tokens > 0
        assert records[0].cost_usd > 0

    def test_handler_returns_tuple_when_mc_variant_exists(self) -> None:
        """Phase 8.6.2: handler 调 MC *_with_usage variant → 返 (output, usage) tuple.

        AgentComputeFn 检测 tuple 拆 usage 喂 cost_tracker.record() 用真实数据
        (非 len()//4 估算). _StubMaster 5 *_with_usage methods 返 hardcoded 100/50.
        """
        master = _StubMaster()
        cost_tracker = CostTracker()
        compute = AgentComputeFn(master, cost_tracker=cost_tracker)

        node = _node("n1", "chapter_writing")
        result = compute(node, {"chapter_num": 1, "use_llm": False})

        assert result.fail is False
        # _StubMaster.write_chapter_with_usage 返 hardcoded 100/50
        records = cost_tracker.records()
        assert len(records) == 1
        assert records[0].input_tokens == 100  # 真实, 非 len()//4 估算
        assert records[0].output_tokens == 50
        # cost_tokens = 100 + 50 = 150 (真实)
        assert result.cost_tokens == 150

    def test_agent_compute_fn_uses_real_usage_from_tuple(self) -> None:
        """Phase 8.6.2: AgentComputeFn isinstance(output, tuple) 检测,
        tuple path 用真实 usage 喂 cost_tracker.record() (替换 Phase 8.5 len()//4 估算)."""
        master = _StubMaster()
        cost_tracker = CostTracker()
        compute = AgentComputeFn(master, cost_tracker=cost_tracker)

        # chapter_review scenario → audit_chapter_with_usage 返 (output, 80/40)
        node = _node("n1", "chapter_review")
        inputs = {
            "chapter_num": 1,
            "content": "x" * 400,  # 任意长度, 不影响真实 usage
            "use_llm": False,
        }
        result = compute(node, inputs)

        assert result.fail is False
        records = cost_tracker.records()
        assert len(records) == 1
        # 真实 usage (80/40 from _StubMaster), 不是 len()//4 估算 (100/100 chars)
        assert records[0].input_tokens == 80
        assert records[0].output_tokens == 40
        assert result.cost_tokens == 120  # 80 + 40 = 120

    def test_polish_merge_handler_returns_tuple(self) -> None:
        """Phase 8.7: _handler_polish_merge 调 MC variant, 返 (dict, usage) tuple."""
        from infra.agent_system import master_controller as mc_mod
        from infra.agent_system.got_bridge import _handler_polish_merge

        master = mc_mod.MasterController.__new__(mc_mod.MasterController)
        # Phase 8.7: handler 调 polish_merge_synthesis_with_usage, 返 tuple
        master.polish_merge_synthesis_with_usage = lambda **kw: (
            {
                "content": "winner content",
                "winner": "emotional_pacing",
                "scores_a": {f"S{i}": 8 for i in range(1, 9)},
                "scores_b": {f"S{i}": 5 for i in range(1, 9)},
                "scores_total_a": 7.0, "scores_total_b": 4.5, "scores_delta": 0.25,
            },
            {"input_tokens": 100, "output_tokens": 50},
        )

        result, usage = _handler_polish_merge(
            master=master,
            inputs={
                "polish_emotional_pacing": {"content": "variant A content here"},
                "polish_ai_trace_removal": {"content": "variant B content here"},
            },
        )
        # 1. tuple
        assert isinstance(result, dict)
        assert usage == {"input_tokens": 100, "output_tokens": 50}
        # 2. result 含 S1-S8 (Phase 7.6 dashboard radar 依赖)
        assert "scores_a" in result
        assert "scores_b" in result

    def test_agent_compute_fn_records_polish_merge_real_usage(self) -> None:
        """Phase 8.7: _handler_polish_merge 返 tuple → AgentComputeFn 喂 cost_tracker 真实 usage."""
        from infra.agent_system import master_controller as mc_mod

        cost_tracker = CostTracker()
        master = mc_mod.MasterController.__new__(mc_mod.MasterController)
        # Phase 8.7: handler 调 master.polish_merge_synthesis_with_usage, stub 该方法返 tuple
        # (走真实 tuple path 喂 cost_tracker, 替换 Phase 8.5 len()//4 估算)
        master.polish_merge_synthesis_with_usage = lambda content_a, content_b, *, labels=("A", "B"): (
            {
                "content": "winner content",
                "winner": "emotional_pacing",
                "scores_a": {}, "scores_b": {},
                "scores_total_a": 7.0, "scores_total_b": 4.5,
                "scores_delta": 0.25,
            },
            {"input_tokens": 200, "output_tokens": 100},
        )

        compute = AgentComputeFn(master, cost_tracker=cost_tracker)
        node = _node("n1", "polish_merge")
        inputs = {
            "polish_emotional_pacing": {"content": "A"},
            "polish_ai_trace_removal": {"content": "B"},
        }
        result = compute(node, inputs)

        # 1. success (无 _error, 不 fail)
        assert result.fail is False
        # 2. cost_tokens 是真实 200+100=300 (非 len()//4 估算)
        assert result.cost_tokens == 300
        # 3. cost_tracker 收到真实 200/100
        recs = cost_tracker.records()
        assert len(recs) == 1
        assert recs[0].scenario == "polish_merge"
        assert recs[0].input_tokens == 200
        assert recs[0].output_tokens == 100
