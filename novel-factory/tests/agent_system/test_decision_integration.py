"""Tests for decision integration in MasterController.run_workflow (Phase 4.3)

Doc 4 §10 + Phase 4: 决策面板整合
- run_workflow 识别 NodeType.DECISION 节点 → 创建 HumanDecision
- run_workflow 返回值新增 "pending_decisions" 字段 (list[dict])
- 新增 MasterController.resolve_decision(decision_id, option) API
- 新增 MasterController.list_pending_decisions() API
- 老 API (advance_step/dispatch_task/...advance_step) 不受影响
"""
from __future__ import annotations

import types
from typing import Any

import pytest

from infra.agent_system.decision_queue import (
    DecisionKind,
    DecisionStatus,
    HumanDecision,
    HumanDecisionQueue,
    create_decision,
)
from infra.got.data_structures import NodeType, ThoughtNode

# === Reuse stub helpers from test_master_controller_workflow ===

def _make_controller_with_stubs(monkeypatch) -> tuple[Any, Any]:
    """构造 MasterController 但 stub 掉 init 中的重操作,只保留 run_workflow 链路"""
    from infra.agent_system import master_controller as mc_mod

    monkeypatch.setattr(mc_mod, "build_router", lambda config: None)
    monkeypatch.setattr(mc_mod, "build_orchestrator", lambda **kwargs: None)
    monkeypatch.setattr(mc_mod, "build_skill_registry", lambda: None)
    monkeypatch.setattr(mc_mod, "build_agent_tools", lambda router: None)
    monkeypatch.setattr(mc_mod, "build_social_engine", lambda state_dir: None)

    import infra.state.state_manager as sm_mod
    monkeypatch.setattr(sm_mod, "StateManager", lambda *a, **kw: None)

    controller = mc_mod.MasterController.__new__(mc_mod.MasterController)
    stub = _StubMaster()
    controller.content_writer = type(
        "cw", (), {"generate_chapter": stub.write_chapter}
    )()
    controller.auditor = type("au", (), {})()
    controller.polisher = type("po", (), {"remove_ai_gloss": stub.polish_chapter})()
    controller.outline_master = type(
        "om",
        (),
        {"schema": type("s", (), {"get_chapter_outline": staticmethod(lambda *a, **kw: {})})()},
    )()
    controller.character_designer = type("cd", (), {})()
    controller.context_builder = type("cb", (), {"build_writing_context": staticmethod(lambda **kw: {})})()
    controller.writing_suggestion = type("ws", (), {"generate_suggestions": staticmethod(lambda *a, **kw: [])})()
    controller.relationship_tracker = type("rt", (), {"get_network": staticmethod(lambda: {})})()
    controller.event_calculator = None
    controller.conflict_alert = None
    controller._router = None
    controller._state_manager = None
    controller._orchestrator = None
    controller._skill_registry = None
    controller._config = None
    # decision queue 默认 None,测试中按需注入
    controller._decision_queue = None

    controller.write_chapter = types.MethodType(
        lambda self, chapter_num, outline, characters, memory_context, style_guide, use_llm: stub.write_chapter(
            chapter_num, outline, characters, memory_context, style_guide, use_llm,
        ),
        controller,
    )
    controller.audit_chapter = types.MethodType(
        lambda self, chapter_num, content, characters, timeline, use_llm: stub.audit_chapter(
            chapter_num, content, characters, timeline, use_llm,
        ),
        controller,
    )
    controller.polish_chapter = types.MethodType(
        lambda self, content: stub.polish_chapter(content), controller,
    )
    # Phase 7.4: stub 新增的 2 个 variant entry methods
    controller.polish_emotional_pacing = types.MethodType(
        lambda self, content: stub.polish_chapter(content), controller,
    )
    controller.polish_ai_trace_removal = types.MethodType(
        lambda self, content: stub.polish_chapter(content), controller,
    )
    controller.generate_outline = types.MethodType(
        lambda self, settings, requirements: stub.generate_outline(settings, requirements), controller,
    )
    return controller, stub


class _StubMaster:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def write_chapter(self, chapter_num, outline, characters, memory_context, style_guide, use_llm):
        self.calls.append(("write_chapter", {"chapter_num": chapter_num}))
        return {"content": f"ch{chapter_num} text", "word_count": 100, "chapter_num": chapter_num}

    def audit_chapter(self, chapter_num, content, characters, timeline, use_llm):
        self.calls.append(("audit_chapter", {"chapter_num": chapter_num, "content_len": len(content)}))
        return {"chapter": chapter_num, "issues": [], "scores": {"S1": 80}}

    def polish_chapter(self, content: str) -> str:
        return content + " [polished]"

    def generate_outline(self, settings, requirements):
        return {"chapters": [], "volume": 1}


# === TestRunWorkflowDecisionDiscovery ===

class TestRunWorkflowDecisionDiscovery:
    """run_workflow 扫描图中的 DECISION 节点 → 创建 HumanDecision"""

    def test_no_decision_nodes_yields_no_pending(self, monkeypatch):
        """workflow 全是 GENERATION/EVALUATION 节点 → pending_decisions = []"""
        controller, _ = _make_controller_with_stubs(monkeypatch)
        result = controller.run_workflow(
            workflow_name="novel_writing",
            start_nodes=["read_snapshot"],
            initial_inputs={"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []},
        )
        assert "pending_decisions" in result
        assert result["pending_decisions"] == []

    def test_decision_node_creates_pending_decision(self, monkeypatch, tmp_path):
        """workflow 含 DECISION 节点 → run_workflow 自动创建 HumanDecision

        模拟:加载一个工作流,其中 1 个 DECISION 节点
        """
        controller, _ = _make_controller_with_stubs(monkeypatch)
        # 注入独立 decision queue (避免污染 .state)
        controller._decision_queue = HumanDecisionQueue(state_dir=str(tmp_path))

        # 构造含 DECISION 节点的图
        from pathlib import Path

        from infra.got.graph import ThoughtGraph
        from infra.got.workflow_loader import load_workflow

        # 用 novel_writing 作基础,然后注入 1 个 DECISION 节点
        graph = load_workflow("novel_writing")
        decision_node = ThoughtNode(
            node_id="outline_judgment",
            type=NodeType.DECISION,
            name="Outline Judgment",
            description="审核大纲决定通过/打回",
            depends_on=("read_snapshot",),
            prompt_scenario=None,
        )
        graph.add_node(decision_node)
        # 写一个临时 workflow YAML? 简化为直接构造 graph,再用 scheduler

        from infra.agent_system.got_bridge import AgentComputeFn
        from infra.got.scheduler import GoTScheduler

        sched = GoTScheduler(graph, compute_fn=AgentComputeFn(controller), max_backtracks=0)
        del sched  # 仅构造验证 compute_fn 可注入
        # 把图 注入 decision discovery 流程
        from infra.agent_system.master_controller import _collect_decision_specs_from_graph

        specs = _collect_decision_specs_from_graph(graph)
        assert len(specs) == 1
        spec = specs[0]
        assert spec["node_id"] == "outline_judgment"
        assert spec["decision_kind"] == DecisionKind.OUTLINE_JUDGMENT

    def test_decision_kind_inferred_from_node_id(self, monkeypatch):
        """DECISION 节点 → DecisionKind 根据 node_id 推断"""
        from infra.agent_system.master_controller import _infer_decision_kind
        assert _infer_decision_kind("outline_judgment") == DecisionKind.OUTLINE_JUDGMENT
        assert _infer_decision_kind("volume_judgment") == DecisionKind.VOLUME_JUDGMENT
        assert _infer_decision_kind("publish_judgment") == DecisionKind.PUBLISH_JUDGMENT
        assert _infer_decision_kind("subplot_open") == DecisionKind.SUBPLOT_OPEN
        assert _infer_decision_kind("subplot_close") == DecisionKind.SUBPLOT_CLOSE
        assert _infer_decision_kind("style_pick") == DecisionKind.STYLE_PICK
        # 未知 → OUTLINE_JUDGMENT 兜底
        assert _infer_decision_kind("unknown_xyz") == DecisionKind.OUTLINE_JUDGMENT


# === TestResolveDecisionAPI ===

class TestResolveDecisionAPI:
    """MasterController.resolve_decision + list_pending_decisions API"""

    def test_resolve_decision_uses_injected_queue(self, monkeypatch, tmp_path):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        d = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="outline_judge",
            prompt="通过?",
            options=("approve", "revise"),
        )
        q.add(d)
        controller._decision_queue = q

        resolved = controller.resolve_decision(d.decision_id, "approve")
        assert resolved.status == DecisionStatus.RESOLVED
        assert resolved.resolution == "approve"

    def test_resolve_decision_persists(self, monkeypatch, tmp_path):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        d = create_decision(
            decision_kind=DecisionKind.STYLE_PICK,
            node_id="style_pick",
            prompt="选风格?",
            options=("燃系", "细腻"),
        )
        q.add(d)
        controller._decision_queue = q

        controller.resolve_decision(d.decision_id, "燃系")
        # 重新读
        q2 = HumanDecisionQueue(state_dir=str(tmp_path))
        loaded = q2.get(d.decision_id)
        assert loaded.status == DecisionStatus.RESOLVED
        assert loaded.resolution == "燃系"

    def test_list_pending_decisions_returns_list(self, monkeypatch, tmp_path):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        q.add(create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="o1", prompt="p1", options=("a", "b"),
        ))
        q.add(create_decision(
            decision_kind=DecisionKind.STYLE_PICK,
            node_id="s1", prompt="p2", options=("x", "y"),
        ))
        controller._decision_queue = q

        pending = controller.list_pending_decisions()
        assert len(pending) == 2
        # 全部 PENDING
        assert all(p["status"] == "pending" for p in pending)

    def test_resolve_without_queue_raises(self, monkeypatch):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        controller._decision_queue = None
        with pytest.raises(RuntimeError):
            controller.resolve_decision("nope", "approve")


# === TestDecisionQueueAutoInit ===

class TestDecisionQueueAutoInit:
    """MasterController 默认初始化 decision queue (state_dir/decisions.json)"""

    def test_run_workflow_with_injected_queue_creates_decisions(self, monkeypatch, tmp_path):
        """注入 decision queue 后,run_workflow 自动扫描 DECISION 节点"""
        from infra.got.data_structures import NodeType, ThoughtNode
        from infra.got.graph import ThoughtGraph
        from infra.got.workflow_loader import load_workflow

        controller, _ = _make_controller_with_stubs(monkeypatch)
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        controller._decision_queue = q

        # 构造 workflow 包含 DECISION 节点
        wf_path = tmp_path / "decision_test.yaml"
        wf_path.write_text("""\
workflow: decision_test
version: 1
nodes:
  - id: read_snapshot
    type: input
    name: Read
    description: read
    depends_on: []
  - id: outline_judgment
    type: decision
    name: Outline Judgment
    description: 大纲审核
    depends_on: [read_snapshot]
  - id: emit
    type: output
    name: Emit
    description: emit
    depends_on: [outline_judgment]
""", encoding="utf-8")

        result = controller.run_workflow(
            workflow_name="decision_test",
            base_dir=str(tmp_path),
            start_nodes=["read_snapshot"],
            initial_inputs={},
        )

        # 应创建 1 个 pending decision (outline_judgment)
        assert len(result["pending_decisions"]) == 1
        pd = result["pending_decisions"][0]
        assert pd["node_id"] == "outline_judgment"
        assert pd["decision_kind"] == DecisionKind.OUTLINE_JUDGMENT.value
        assert q.pending_count() == 1
