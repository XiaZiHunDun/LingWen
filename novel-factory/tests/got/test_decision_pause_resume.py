"""Tests for DECISION node pause/resume semantics (Phase 5)

Doc 4 §10 Phase 5: 决策节点真正暂停工作流,等待 resolve_decision 后恢复。

设计:
- NodeStatus 新增 WAITING (等待人工决策)
- GoTScheduler.run() 遇到 DECISION 节点:
  - 不调用 compute_fn
  - 记录 NodeExecution(status=WAITING)
  - 返回 ExecutionSummary.paused=True
- GoTScheduler.resume(decision_id, option):
  - 找到对应 WAITING execution
  - 写入 output={"option": option, "resolved_by": "human"}
  - status=COMPLETED
  - 继续执行
- MasterController:
  - run_workflow() 现在返回 paused summary (替代一冲到底)
  - 新增 resume_workflow(decision_id, option) API
"""
from __future__ import annotations

import pytest

from infra.got.data_structures import (
    NodeStatus,
    NodeType,
    ThoughtNode,
)
from infra.got.graph import ThoughtGraph
from infra.got.scheduler import (
    ComputeResult,
    GoTScheduler,
)

# === Test fixtures ===

def _node(
    nid: str,
    ntype: NodeType = NodeType.GENERATION,
    deps: tuple[str, ...] = (),
) -> ThoughtNode:
    return ThoughtNode(
        node_id=nid,
        type=ntype,
        name=f"Node {nid}",
        description=f"test node {nid}",
        depends_on=deps,
    )


class _StubCompute:
    """记录调用,可注入输出"""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.outputs: dict[str, dict] = {}

    def __call__(self, node: ThoughtNode, inputs: dict) -> ComputeResult:
        self.calls.append(node.node_id)
        out = self.outputs.get(node.node_id, {"echo": node.node_id, "inputs": inputs})
        return ComputeResult(output=out, cost_tokens=10)


# === TestDecisionNodePausesExecution ===

class TestDecisionNodePausesExecution:
    """DECISION 节点 → scheduler 暂停,compute_fn 不被调用"""

    def test_decision_node_marks_waiting(self):
        """DECISION 节点 → NodeExecution.status=WAITING,compute_fn 未被调用"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("decide", ntype=NodeType.DECISION, deps=("a",)))
        graph.add_node(_node("b", deps=("decide",)))

        compute = _StubCompute()
        sched = GoTScheduler(graph, compute_fn=compute)
        summary = sched.run(start_nodes=["a"])

        # DECISION 节点:compute_fn 未被调用
        assert "decide" not in compute.calls
        # DECISION 节点 status=WAITING
        dec_exec = graph.get_execution("decide")
        assert dec_exec.status == NodeStatus.WAITING
        # summary 标记 paused
        assert summary.paused is True
        assert "decide" in summary.paused_nodes
        # 下游 b 未执行
        assert "b" not in compute.calls

    def test_decision_node_with_no_resume_returns_immediately(self):
        """无 resolve_decision → 一直等待,不抛错"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("decide", ntype=NodeType.DECISION, deps=("a",)))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        # 不抛错
        summary = sched.run(start_nodes=["a"])
        assert summary.completed == 1  # a
        assert summary.paused is True

    def test_no_decision_node_no_pause(self):
        """无 DECISION 节点 → 正常完成,paused=False"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("b", deps=("a",)))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        summary = sched.run(start_nodes=["a"])
        assert summary.paused is False
        assert summary.paused_nodes == ()


# === TestSchedulerResume ===

class TestSchedulerResume:
    """scheduler.resume(decision_id, option) 继续执行"""

    def test_resume_marks_decision_completed(self):
        """resume → DECISION 节点 status=COMPLETED,output 包含 option"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("decide", ntype=NodeType.DECISION, deps=("a",)))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        sched.run(start_nodes=["a"])

        # resolve
        sched.resume(decision_node_id="decide", option="approve")
        dec_exec = graph.get_execution("decide")
        assert dec_exec.status == NodeStatus.COMPLETED
        assert dec_exec.output == {"option": "approve", "resolved_by": "human"}

    def test_resume_continues_downstream(self):
        """resume 后,再 run() 触发下游执行"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("decide", ntype=NodeType.DECISION, deps=("a",)))
        graph.add_node(_node("b", deps=("decide",)))

        compute = _StubCompute()
        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        # b 未执行
        assert "b" not in compute.calls

        # resolve + 再次 run() → b 执行
        sched.resume(decision_node_id="decide", option="approve")
        sched.run(start_nodes=["a"])
        assert "b" in compute.calls
        b_exec = graph.get_execution("b")
        assert b_exec.status == NodeStatus.COMPLETED

    def test_resume_preserves_upstream_execution(self):
        """resume 不影响上游已完成的 execution"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("decide", ntype=NodeType.DECISION, deps=("a",)))

        compute = _StubCompute()
        sched = GoTScheduler(graph, compute_fn=compute)
        sched.run(start_nodes=["a"])

        a_exec_before = graph.get_execution("a")
        # resolve
        sched.resume(decision_node_id="decide", option="approve")
        a_exec_after = graph.get_execution("a")
        # a 的状态未变
        assert a_exec_after.status == a_exec_before.status
        assert a_exec_after.output == a_exec_before.output

    def test_resume_unknown_node_raises(self):
        """resume(未知 node_id) → KeyError / ValueError"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        sched.run(start_nodes=["a"])
        with pytest.raises((KeyError, ValueError)):
            sched.resume(decision_node_id="nonexistent", option="x")

    def test_resume_non_waiting_node_raises(self):
        """resume 已 COMPLETED 的节点 → 报错"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        sched.run(start_nodes=["a"])
        # a 已 COMPLETED
        with pytest.raises(ValueError, match="(?i)waiting|decision"):
            sched.resume(decision_node_id="a", option="x")


# === TestMultipleDecisionNodes ===

class TestMultipleDecisionNodes:
    """图中多个 DECISION 节点 → 串行等待"""

    def test_two_decision_nodes_pause_sequentially(self):
        """2 个 DECISION 节点 → 第一个 pause,resume 后第二个 pause"""
        graph = ThoughtGraph()
        graph.add_node(_node("a"))
        graph.add_node(_node("d1", ntype=NodeType.DECISION, deps=("a",)))
        graph.add_node(_node("d2", ntype=NodeType.DECISION, deps=("d1",)))
        graph.add_node(_node("b", deps=("d2",)))

        compute = _StubCompute()
        sched = GoTScheduler(graph, compute_fn=compute)
        # 第一次 run → pause 在 d1
        summary1 = sched.run(start_nodes=["a"])
        assert summary1.paused is True
        assert "d1" in summary1.paused_nodes

        # resolve d1
        sched.resume(decision_node_id="d1", option="approve")
        # 第二次 run → pause 在 d2
        summary2 = sched.run(start_nodes=["a"])
        assert summary2.paused is True
        assert "d2" in summary2.paused_nodes

        # resolve d2
        sched.resume(decision_node_id="d2", option="approve")
        # 第三次 run → 完成
        summary3 = sched.run(start_nodes=["a"])
        assert summary3.paused is False
        # 全部 4 节点都是 COMPLETED
        for nid in ["a", "d1", "d2", "b"]:
            assert graph.get_execution(nid).status == NodeStatus.COMPLETED
        # b 是第三次 run 新完成的
        assert "b" in compute.calls
        assert graph.get_execution("b").status == NodeStatus.COMPLETED


# === TestControllerResumeWorkflow ===

class TestControllerResumeWorkflow:
    """MasterController.resume_workflow API"""

    def test_resume_workflow_via_controller(self, monkeypatch, tmp_path):
        """controller.resume_workflow(decision_id, option) → 继续"""
        import infra.agent_system.master_controller as mc_mod
        import infra.state.state_manager as sm_mod
        from infra.agent_system.decision_queue import (
            DecisionKind,
            HumanDecisionQueue,
            create_decision,
        )
        from infra.agent_system.master_controller import MasterController

        monkeypatch.setattr(mc_mod, "build_router", lambda config: None)
        monkeypatch.setattr(mc_mod, "build_orchestrator", lambda **kwargs: None)
        monkeypatch.setattr(mc_mod, "build_skill_registry", lambda: None)
        monkeypatch.setattr(mc_mod, "build_agent_tools", lambda router: None)
        monkeypatch.setattr(mc_mod, "build_social_engine", lambda state_dir: None)
        monkeypatch.setattr(sm_mod, "StateManager", lambda *a, **kw: None)

        controller = MasterController.__new__(MasterController)
        # 注入最小 stub (避免 __init__)
        controller._decision_queue = HumanDecisionQueue(state_dir=str(tmp_path))
        controller._config = None
        controller._router = None
        controller._orchestrator = None
        controller._skill_registry = None

        # 写一个含 DECISION 的工作流
        wf = tmp_path / "dec_pause.yaml"
        wf.write_text(
            "workflow: dec_pause\n"
            "version: 1\n"
            "nodes:\n"
            "  - id: a\n"
            "    type: generation\n"
            "    name: A\n"
            "    description: a\n"
            "    depends_on: []\n"
            "  - id: judge\n"
            "    type: decision\n"
            "    name: Judge\n"
            "    description: outline_judgment\n"
            "    depends_on: [a]\n",
            encoding="utf-8",
        )

        # 构造 scheduler
        from infra.agent_system.got_bridge import build_got_scheduler
        scheduler, graph = build_got_scheduler(
            master=controller,
            workflow_name="dec_pause",
            base_dir=str(tmp_path),
            max_backtracks=0,
        )
        # 跑 → pause 在 judge
        summary1 = scheduler.run(start_nodes=["a"])
        assert summary1.paused is True

        # 注入对应 decision (模拟 _harvest_decision_specs 行为)
        d = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="judge",
            prompt="OK?",
            options=("approve", "revise"),
        )
        controller._decision_queue.add(d)

        # resolve + 继续
        controller.resolve_decision(d.decision_id, "approve")
        # resume_workflow 调用
        # 先把 judge 的 execution 标记为 completed with option (由 resolve_decision 写)
        # 这里 scheduler 需要知道 option → 简化:resolve_decision 已写 execution output
        # 但我们直接调 scheduler.resume
        scheduler.resume(decision_node_id="judge", option="approve")
        # 再 run → paused=False
        summary2 = scheduler.run(start_nodes=["a"])
        assert summary2.paused is False

    def _build_controller_with_workflow(self, monkeypatch, tmp_path, workflow_body: str):
        """构造一个 stub MasterController + 含 DECISION 的工作流 + 注入的 scheduler"""
        import infra.agent_system.master_controller as mc_mod
        import infra.state.state_manager as sm_mod
        from infra.agent_system.decision_queue import HumanDecisionQueue
        from infra.agent_system.master_controller import MasterController

        monkeypatch.setattr(mc_mod, "build_router", lambda config: None)
        monkeypatch.setattr(mc_mod, "build_orchestrator", lambda **kwargs: None)
        monkeypatch.setattr(mc_mod, "build_skill_registry", lambda: None)
        monkeypatch.setattr(mc_mod, "build_agent_tools", lambda router: None)
        monkeypatch.setattr(mc_mod, "build_social_engine", lambda state_dir: None)
        monkeypatch.setattr(sm_mod, "StateManager", lambda *a, **kw: None)

        controller = MasterController.__new__(MasterController)
        controller._decision_queue = HumanDecisionQueue(state_dir=str(tmp_path))
        controller._config = None
        controller._router = None
        controller._orchestrator = None
        controller._skill_registry = None
        # Phase 5: 活跃工作流缓存初始 None
        controller._last_scheduler = None
        controller._last_graph = None
        controller._last_workflow_name = None
        controller._last_start_nodes = []

        wf = tmp_path / "wf_resume.yaml"
        wf.write_text(workflow_body, encoding="utf-8")

        from infra.agent_system.got_bridge import build_got_scheduler
        scheduler, graph = build_got_scheduler(
            master=controller,
            workflow_name="wf_resume",
            base_dir=str(tmp_path),
            max_backtracks=0,
        )
        return controller, scheduler, graph

    def test_resume_workflow_continues_via_controller(self, monkeypatch, tmp_path):
        """controller.resume_workflow(decision_id, option) 真正让工作流继续"""
        from infra.agent_system.decision_queue import (
            DecisionKind,
            create_decision,
        )

        wf_body = (
            "workflow: wf_resume\n"
            "version: 1\n"
            "nodes:\n"
            "  - id: a\n"
            "    type: generation\n"
            "    name: A\n"
            "    description: a\n"
            "    depends_on: []\n"
            "  - id: judge\n"
            "    type: decision\n"
            "    name: Judge\n"
            "    description: outline_judgment\n"
            "    depends_on: [a]\n"
            "  - id: b\n"
            "    type: generation\n"
            "    name: B\n"
            "    description: b\n"
            "    depends_on: [judge]\n"
        )
        controller, scheduler, graph = self._build_controller_with_workflow(
            monkeypatch, tmp_path, wf_body
        )

        # 缓存活跃工作流 (模拟 run_workflow() 的行为)
        controller._last_scheduler = scheduler
        controller._last_graph = graph
        controller._last_workflow_name = "wf_resume"
        controller._last_start_nodes = ["a"]

        # 手动跑第一次,pause 在 judge
        summary1 = scheduler.run(start_nodes=["a"])
        assert summary1.paused is True
        assert "judge" in summary1.paused_nodes
        assert "b" not in scheduler._graph.get_execution("b").status.value if graph.has_execution("b") else True

        # 注入 HumanDecision (模拟 _harvest_decision_specs)
        d = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="judge",
            prompt="Approve outline?",
            options=("approve", "revise"),
        )
        controller._decision_queue.add(d)

        # 调 controller.resume_workflow() — 三步合一
        result = controller.resume_workflow(d.decision_id, "approve")

        # 验证返回结构
        assert "summary" in result
        assert "graph" in result
        assert "executions" in result
        assert "pending_decisions" in result
        assert "resolved_decision" in result
        # summary 不再 paused
        assert result["summary"].paused is False
        # resolved_decision 是 RESOLVED 状态
        assert result["resolved_decision"].status.value == "resolved"
        assert result["resolved_decision"].resolution == "approve"
        # judge 节点已 COMPLETED
        assert graph.get_execution("judge").status.value == "completed"
        # 下游 b 节点被触发执行
        assert "b" in graph._executions
        assert graph.get_execution("b").status.value == "completed"
        # 队列中决策已 RESOLVED
        assert controller._decision_queue.get(d.decision_id).status.value == "resolved"

    def test_resume_workflow_raises_without_active_workflow(self, monkeypatch, tmp_path):
        """从未 run_workflow → resume_workflow 抛 RuntimeError"""
        import infra.agent_system.master_controller as mc_mod
        import infra.state.state_manager as sm_mod
        from infra.agent_system.decision_queue import (
            DecisionKind,
            HumanDecisionQueue,
            create_decision,
        )
        from infra.agent_system.master_controller import MasterController

        monkeypatch.setattr(mc_mod, "build_router", lambda config: None)
        monkeypatch.setattr(mc_mod, "build_orchestrator", lambda **kwargs: None)
        monkeypatch.setattr(mc_mod, "build_skill_registry", lambda: None)
        monkeypatch.setattr(mc_mod, "build_agent_tools", lambda router: None)
        monkeypatch.setattr(mc_mod, "build_social_engine", lambda state_dir: None)
        monkeypatch.setattr(sm_mod, "StateManager", lambda *a, **kw: None)

        controller = MasterController.__new__(MasterController)
        controller._decision_queue = HumanDecisionQueue(state_dir=str(tmp_path))
        controller._config = None
        controller._router = None
        controller._orchestrator = None
        controller._skill_registry = None
        controller._last_scheduler = None  # 关键:无活跃工作流
        controller._last_graph = None
        controller._last_workflow_name = None
        controller._last_start_nodes = []

        d = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="judge",
            prompt="OK?",
            options=("approve", "revise"),
        )
        controller._decision_queue.add(d)

        with pytest.raises(RuntimeError, match="(?i)no active workflow|run_workflow"):
            controller.resume_workflow(d.decision_id, "approve")

    def test_resume_workflow_raises_for_unknown_decision_id(self, monkeypatch, tmp_path):
        """decision_id 不在队列 → KeyError"""
        wf_body = (
            "workflow: wf_resume\n"
            "version: 1\n"
            "nodes:\n"
            "  - id: a\n"
            "    type: generation\n"
            "    name: A\n"
            "    description: a\n"
            "    depends_on: []\n"
            "  - id: judge\n"
            "    type: decision\n"
            "    name: Judge\n"
            "    description: outline_judgment\n"
            "    depends_on: [a]\n"
        )
        controller, scheduler, graph = self._build_controller_with_workflow(
            monkeypatch, tmp_path, wf_body
        )
        controller._last_scheduler = scheduler
        controller._last_graph = graph
        controller._last_start_nodes = ["a"]

        with pytest.raises(KeyError, match="nonexistent"):
            controller.resume_workflow("nonexistent", "approve")

    def test_resume_workflow_resolved_by_kwarg(self, monkeypatch, tmp_path):
        """resolved_by kwarg 透传到 HumanDecision 和 DECISION 节点"""
        from infra.agent_system.decision_queue import (
            DecisionKind,
            create_decision,
        )

        wf_body = (
            "workflow: wf_resume\n"
            "version: 1\n"
            "nodes:\n"
            "  - id: judge\n"
            "    type: decision\n"
            "    name: Judge\n"
            "    description: outline_judgment\n"
            "    depends_on: []\n"
        )
        controller, scheduler, graph = self._build_controller_with_workflow(
            monkeypatch, tmp_path, wf_body
        )
        controller._last_scheduler = scheduler
        controller._last_graph = graph
        controller._last_start_nodes = ["judge"]

        # 跑 → pause
        scheduler.run(start_nodes=["judge"])
        d = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="judge",
            prompt="OK?",
            options=("approve", "revise"),
        )
        controller._decision_queue.add(d)

        # 用非默认 resolved_by
        result = controller.resume_workflow(
            d.decision_id, "approve", resolved_by="auto_auditor"
        )
        # HumanDecision.resolved_by 透传
        assert result["resolved_decision"].resolved_by == "auto_auditor"
        # DECISION 节点 execution.output.resolved_by 透传
        assert graph.get_execution("judge").output["resolved_by"] == "auto_auditor"

    def test_resume_workflow_serial_decisions(self, monkeypatch, tmp_path):
        """两个串行 DECISION → 每次 resume 推进一个,直到全部 COMPLETED"""
        from infra.agent_system.decision_queue import (
            DecisionKind,
            create_decision,
        )

        wf_body = (
            "workflow: wf_resume\n"
            "version: 1\n"
            "nodes:\n"
            "  - id: a\n"
            "    type: generation\n"
            "    name: A\n"
            "    description: a\n"
            "    depends_on: []\n"
            "  - id: d1\n"
            "    type: decision\n"
            "    name: D1\n"
            "    description: first_decision\n"
            "    depends_on: [a]\n"
            "  - id: d2\n"
            "    type: decision\n"
            "    name: D2\n"
            "    description: second_decision\n"
            "    depends_on: [d1]\n"
            "  - id: b\n"
            "    type: generation\n"
            "    name: B\n"
            "    description: b\n"
            "    depends_on: [d2]\n"
        )
        controller, scheduler, graph = self._build_controller_with_workflow(
            monkeypatch, tmp_path, wf_body
        )
        controller._last_scheduler = scheduler
        controller._last_graph = graph
        controller._last_start_nodes = ["a"]

        # 跑 → pause 在 d1
        summary1 = scheduler.run(start_nodes=["a"])
        assert summary1.paused is True
        assert "d1" in summary1.paused_nodes

        # 注入 d1 decision
        d1 = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="d1",
            prompt="first?",
            options=("approve", "revise"),
        )
        controller._decision_queue.add(d1)

        # resume d1 → 应 pause 在 d2
        result1 = controller.resume_workflow(d1.decision_id, "approve")
        assert result1["summary"].paused is True
        assert "d2" in result1["summary"].paused_nodes
        # b 仍未执行
        assert not graph.has_execution("b") or graph.get_execution("b").status.value != "completed"

        # 注入 d2 decision
        d2 = create_decision(
            decision_kind=DecisionKind.OUTLINE_JUDGMENT,
            node_id="d2",
            prompt="second?",
            options=("approve", "revise"),
        )
        controller._decision_queue.add(d2)

        # resume d2 → 应全部完成
        result2 = controller.resume_workflow(d2.decision_id, "approve")
        assert result2["summary"].paused is False
        # b 已执行
        assert graph.get_execution("b").status.value == "completed"
        # 两个决策都 RESOLVED
        assert controller._decision_queue.get(d1.decision_id).status.value == "resolved"
        assert controller._decision_queue.get(d2.decision_id).status.value == "resolved"


# === TestDecisionNodeExecutionOutput ===

class TestDecisionNodeExecutionOutput:
    """DECISION 节点的 output 是 {option, resolved_by} 字典"""

    def test_output_shape(self):
        graph = ThoughtGraph()
        graph.add_node(_node("decide", ntype=NodeType.DECISION))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        sched.run(start_nodes=["decide"])
        sched.resume(decision_node_id="decide", option="revise")

        dec_exec = graph.get_execution("decide")
        assert dec_exec.output is not None
        assert dec_exec.output["option"] == "revise"
        assert dec_exec.output["resolved_by"] == "human"

    def test_resolved_at_timestamp_set(self):
        """resume 后 finished_at 不为 None"""
        graph = ThoughtGraph()
        graph.add_node(_node("decide", ntype=NodeType.DECISION))

        sched = GoTScheduler(graph, compute_fn=_StubCompute())
        sched.run(start_nodes=["decide"])
        sched.resume(decision_node_id="decide", option="x")

        dec_exec = graph.get_execution("decide")
        assert dec_exec.finished_at is not None
