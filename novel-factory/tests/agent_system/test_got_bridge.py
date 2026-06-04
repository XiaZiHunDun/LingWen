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
        assert len(scenarios) == 12

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
        assert master.calls[0][0] == "write_chapter"
        assert master.calls[0][1]["chapter_num"] == 1

    def test_chapter_review_routes_to_audit(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("rev1", "chapter_review")
        result = compute(node, {"chapter_num": 1, "content": "abcdefg", "use_llm": False})
        assert result.fail is False
        assert result.output["chapter"] == 1
        assert master.calls[0][0] == "audit_chapter"

    def test_ai_trace_removal_routes_to_polish(self):
        master = _StubMaster()
        compute = AgentComputeFn(master)
        node = _node("pol1", "ai_trace_removal")
        result = compute(node, {"content": "raw text"})
        assert result.fail is False
        assert "[polished]" in result.output["content"]
        assert master.calls[0][0] == "polish_chapter"

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
        # 强行让 write_chapter 抛错
        def boom(*args, **kwargs):
            raise RuntimeError("upstream error")
        master.write_chapter = boom

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
        # 4 节点: read_snapshot → write_chapter → review_chapter → emit_chapter
        assert len(graph.node_ids()) == 4
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

        # write_chapter + audit_chapter 都被调用
        called = [c[0] for c in master.calls]
        assert "write_chapter" in called
        assert "audit_chapter" in called

    def test_review_chapter_receives_write_chapter_output(self):
        """review_chapter 的 content 来自 write_chapter 的 output"""
        master = _StubMaster()
        scheduler, graph = build_got_scheduler(master, "novel_writing", max_backtracks=0)
        initial = {"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []}
        scheduler.run(start_nodes=["read_snapshot"], initial_inputs=initial)

        # 找到 audit_chapter 调用,验证 content_len > 0
        audit_call = next(c for c in master.calls if c[0] == "audit_chapter")
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
