"""Tests for WorkflowRunner service (Phase 27 P2-WFRUNNER).

从 WorkflowMixin 拆出 run_workflow / resume_workflow / 4 helpers
到独立 service, WorkflowMixin 提供懒加载 _get_runner().
"""
from __future__ import annotations

from unittest.mock import MagicMock

from lingwen_core.agents.workflow_runner import WorkflowRunner
from lingwen_pipeline.master_controller import MasterController


class TestWorkflowRunnerConstruction:
    """WorkflowRunner.__init__ + WorkflowMixin._get_runner() 懒加载."""

    def test_runner_init_stores_controller_reference(self) -> None:
        """__init__(controller) 把 controller 存到 self._controller."""
        controller = MasterController.__new__(MasterController)
        runner = WorkflowRunner(controller)
        assert runner._controller is controller

    def test_get_runner_lazy_creates_workflow_runner_on_first_call(self) -> None:
        """首次 _get_runner() 创建 WorkflowRunner 实例并存到 _workflow_runner."""
        master = MasterController.__new__(MasterController)
        assert not hasattr(master, "_workflow_runner")
        # _get_runner 是 Mixin 方法, 这里直接测 lazy 行为
        from lingwen_core.agents.mc_workflow import WorkflowMixin
        runner = WorkflowMixin._get_runner(master)
        assert isinstance(runner, WorkflowRunner)
        assert runner._controller is master
        assert master._workflow_runner is runner  # 缓存到属性

    def test_get_runner_returns_same_instance_on_subsequent_calls(self) -> None:
        """第二次 _get_runner() 返同 instance (不重建)."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.mc_workflow import WorkflowMixin
        r1 = WorkflowMixin._get_runner(master)
        r2 = WorkflowMixin._get_runner(master)
        assert r1 is r2


class TestRunBudgetLifecycle:
    """run() budget setup + finally reset (Phase 8.8/8.12 不变量)."""

    def test_run_sets_current_budget_usd_before_scheduler(self) -> None:
        """run() 进入时 _current_budget_usd = cost_budget_usd, budget_service.set 调用时已设.

        Task 2 scope: 验证 budget 在 try block 内 budget_service.set 调用时已 set.
        'before scheduler.run' 验证由 Task 3 (scheduler build) + Task 5 (full pipeline)
        共同覆盖 — 完整 11 步流水线后 budget 一定先于 scheduler.run 设置.

        Note: stub got_bridge.build_got_scheduler 避免真实 YAML load (workflow_name="test"
        不存在), 否则 WorkflowNotFoundError 会替换 NotImplementedError 传出.
        """
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        from lingwen_core.agents import got_bridge
        original_build = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_scheduler = MagicMock(run=MagicMock(return_value=MagicMock()))
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        captured = {}

        def capture_set(**kwargs):
            captured["usd"] = kwargs.get("usd")
            captured["run_id"] = kwargs.get("run_id")
            captured["budget_at_call"] = master._current_budget_usd
            captured["run_id_at_call"] = master._current_run_id

        master.budget_service = MagicMock(set=MagicMock(side_effect=capture_set))

        runner = WorkflowRunner(master)
        try:
            runner.run(workflow_name="test", cost_budget_usd=0.5)
        except NotImplementedError:
            # Task 3 raises NotImplementedError after scheduler build + start_nodes
            pass
        finally:
            got_bridge.build_got_scheduler = original_build

        master.budget_service.set.assert_called_once()
        assert captured["usd"] == 0.5
        assert captured["budget_at_call"] == 0.5
        assert captured["run_id_at_call"] is not None
        assert len(captured["run_id_at_call"]) == 32  # uuid4().hex

    def test_run_resets_current_budget_usd_in_finally_even_on_raise(self) -> None:
        """raise 时 finally 仍 reset _current_budget_usd + _current_run_id."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )

        def raise_error(**kwargs):
            raise RuntimeError("simulated scheduler failure")

        stub_scheduler = MagicMock(run=raise_error)
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            try:
                runner.run(workflow_name="test", cost_budget_usd=0.5)
            except RuntimeError:
                pass
            # finally 仍 reset
            assert master._current_budget_usd is None
            assert master._current_run_id is None
        finally:
            got_bridge.build_got_scheduler = original


class TestRunSchedulerBuild:
    """run() step 2-3: build scheduler + default start_nodes."""

    def test_run_calls_build_got_scheduler_with_controller(self) -> None:
        """build_got_scheduler(master=controller, workflow_name=..., max_backtracks=...) 被调用."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        called_kwargs = {}
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_scheduler = MagicMock(run=MagicMock(return_value=MagicMock()))

        def fake_build(**kwargs):
            called_kwargs.update(kwargs)
            return stub_scheduler, stub_graph

        got_bridge.build_got_scheduler = fake_build

        try:
            runner = WorkflowRunner(master)
            try:
                runner.run(workflow_name="novel_writing", max_backtracks=3)
            except NotImplementedError:
                pass
            assert called_kwargs["master"] is master
            assert called_kwargs["workflow_name"] == "novel_writing"
            assert called_kwargs["max_backtracks"] == 3
        finally:
            got_bridge.build_got_scheduler = original

    def test_run_uses_default_start_nodes_when_none(self) -> None:
        """start_nodes=None → derivation 走 graph.node_ids() + graph.get_node().depends_on.

        Task 3 scope 仅验证 derivation 调用序列；最终 start_nodes list 由 Task 5 通过
        state.write + scheduler.run 时刻 state.start_nodes 验证.
        """
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler

        # 3 nodes: n1 has deps, n2/n3 no deps
        nodes_map = {
            "n1": MagicMock(depends_on=["n2"]),
            "n2": MagicMock(depends_on=[]),
            "n3": MagicMock(depends_on=[]),
        }
        # track get_node access for derivation verification
        accessed = []

        def track_get_node(nid):
            accessed.append((nid, nodes_map[nid].depends_on))
            return nodes_map[nid]

        stub_graph = MagicMock(
            node_ids=lambda: list(nodes_map.keys()),
            get_node=track_get_node,
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_scheduler = MagicMock(run=MagicMock(return_value=MagicMock()))
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            try:
                runner.run(workflow_name="test")
            except NotImplementedError:
                pass
            # derivation logic: graph.node_ids() iterated, get_node().depends_on checked for all 3
            assert set(nid for nid, _ in accessed) == {"n1", "n2", "n3"}
            # Task 3 verifies call sequence; final start_nodes == {n2, n3} validated in Task 5
        finally:
            got_bridge.build_got_scheduler = original


class TestRunMemoryAndHarvest:
    """run() step 4-5: memory RAG context + harvest DECISION specs."""

    def test_run_attaches_memory_context_to_seed_inputs(self) -> None:
        """memory_context 不为 None 时写入 seed_inputs['memory_context'].

        Observation: 通过 _harvest_decision_specs side_effect 捕获 seed_inputs
        (Task 4 calls harvest AFTER memory attachment). 不依赖 scheduler.run.
        """
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master._memory_rag_mode = "summary"
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original_build = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_scheduler = MagicMock(run=MagicMock(return_value=MagicMock()))
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        captured_seed_inputs = {}

        def capture_harvest(graph, *, initial_inputs=None):
            captured_seed_inputs.update(dict(initial_inputs or {}))
            return []

        # Bypass real chapter_memory_hook — stub _maybe_memory_context directly on runner
        # (Phase 4.3 + 9.70 logic tested via _maybe_memory_context unit in Task 9)
        runner = WorkflowRunner(master)
        runner._maybe_memory_context = MagicMock(return_value={"rag": "ctx"})
        runner._harvest_decision_specs = MagicMock(side_effect=capture_harvest)

        try:
            try:
                runner.run(workflow_name="novel_writing", initial_inputs={"chapter_num": 1})
            except NotImplementedError:
                pass
            assert captured_seed_inputs.get("memory_context") == {"rag": "ctx"}
            assert captured_seed_inputs.get("chapter_num") == 1
            runner._maybe_memory_context.assert_called_once()
        finally:
            got_bridge.build_got_scheduler = original_build

    def test_run_harvest_decisions_before_placeholder(self) -> None:
        """harvest 在 raise NotImplementedError 之前被调用.

        Observation: 通过 runner._harvest_decision_specs call_count + 'before scheduler.run'
        验证由 Task 5 full pipeline 覆盖 (Task 4 不调 scheduler.run).
        """
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original_build = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_scheduler = MagicMock(run=MagicMock(return_value=MagicMock()))
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        runner = WorkflowRunner(master)
        runner._maybe_memory_context = MagicMock(return_value=None)
        runner._harvest_decision_specs = MagicMock(return_value=[{"p": 1}])

        try:
            try:
                runner.run(workflow_name="test")
            except NotImplementedError:
                pass
            runner._harvest_decision_specs.assert_called_once()
            # 验证 graph + seed_inputs (这里 None) 传入
            call_args = runner._harvest_decision_specs.call_args
            assert call_args.args[0] is stub_graph  # graph passed positionally
        finally:
            got_bridge.build_got_scheduler = original_build


class TestRunStateWrites:
    """run() step 6-11: state writes (pre + post) + scheduler.run + return."""

    def test_run_writes_state_workflow_name_and_start_nodes_before_scheduler(self) -> None:
        """scheduler.run 之前写 state: initial_inputs, workflow_name, start_nodes.

        Observation: scheduler.run fake_run 捕获 state_at_run dict — Task 5 调 scheduler.run
        后, state 已写入.
        """
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        state_at_run = {}

        def fake_run(**kwargs):
            state_at_run.update({
                "workflow_name": master._state.workflow_name,
                "start_nodes": list(master._state.start_nodes),
                "initial_inputs": dict(master._state.initial_inputs),
            })
            return MagicMock()

        stub_scheduler = MagicMock(run=fake_run)
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            runner._harvest_decision_specs = MagicMock(return_value=[])
            runner._maybe_memory_context = MagicMock(return_value=None)
            runner._maybe_incremental_backfill = MagicMock(return_value=None)
            runner._collect_executions = MagicMock(return_value={"n1": MagicMock()})

            runner.run(workflow_name="novel_writing", initial_inputs={"chapter_num": 5})
            assert state_at_run["workflow_name"] == "novel_writing"
            assert state_at_run["initial_inputs"]["chapter_num"] == 5
        finally:
            got_bridge.build_got_scheduler = original

    def test_run_writes_state_scheduler_graph_backfill_after_scheduler(self) -> None:
        """scheduler.run 之后写 state: scheduler, graph, incremental_backfill, memory_context."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_summary = MagicMock()
        stub_scheduler = MagicMock(run=MagicMock(return_value=stub_summary))
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            runner._harvest_decision_specs = MagicMock(return_value=[])
            runner._maybe_memory_context = MagicMock(return_value={"mem": "ctx"})
            runner._maybe_incremental_backfill = MagicMock(return_value={"backfill": "stats"})
            runner._collect_executions = MagicMock(return_value={})

            runner.run(workflow_name="test")
            assert master._state.scheduler is stub_scheduler
            assert master._state.graph is stub_graph
            assert master._state.incremental_backfill == {"backfill": "stats"}
            assert master._state.memory_context == {"mem": "ctx"}
        finally:
            got_bridge.build_got_scheduler = original

    def test_run_returns_summary_executions_pending_decisions(self) -> None:
        """return dict 含 summary, graph, executions, pending_decisions, backfill, memory_context."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_summary = MagicMock()
        stub_scheduler = MagicMock(run=MagicMock(return_value=stub_summary))
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            runner._harvest_decision_specs = MagicMock(return_value=[{"p": 1}])
            runner._maybe_memory_context = MagicMock(return_value=None)
            runner._maybe_incremental_backfill = MagicMock(return_value=None)
            runner._collect_executions = MagicMock(return_value={"n1": "exec"})

            result = runner.run(workflow_name="test")
            assert result["summary"] is stub_summary
            assert result["graph"] is stub_graph
            assert result["executions"] == {"n1": "exec"}
            assert result["pending_decisions"] == [{"p": 1}]
            assert "incremental_backfill" in result
            assert "memory_context" in result
        finally:
            got_bridge.build_got_scheduler = original


class TestResumeGuards:
    """resume() step 1-2: RuntimeError on 无活跃工作流 / queue 未初始化."""

    def test_resume_raises_runtime_error_when_no_active_workflow(self) -> None:
        """scheduler / graph 为 None 时 raise RuntimeError('no active workflow')."""
        import pytest

        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()  # scheduler=None, graph=None
        master._decision_queue = MagicMock()  # queue 存在但 state 无 active workflow

        runner = WorkflowRunner(master)
        with pytest.raises(RuntimeError, match="(?i)no active workflow"):
            runner.resume(decision_id="d1", option="approve")

    def test_resume_raises_runtime_error_when_queue_not_initialized(self) -> None:
        """queue is None 时 raise RuntimeError('decision queue not initialized')."""
        import pytest

        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        # state has active workflow (scheduler + graph not None)
        master._state = WorkflowState.empty().with_updates(
            scheduler=MagicMock(),
            graph=MagicMock(),
        )
        master._decision_queue = None  # queue is None

        runner = WorkflowRunner(master)
        with pytest.raises(RuntimeError, match="decision queue not initialized"):
            runner.resume(decision_id="d1", option="approve")


class TestResumeResolveAndGoT:
    """resume() step 3-5: resolve_decision + scheduler.resume + harvest."""

    def test_resume_resolves_decision_then_resumes_scheduler(self) -> None:
        """resolve_decision_locked → scheduler.resume 顺序调用, 错误时抛对应异常."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        stub_scheduler = MagicMock()
        stub_graph = MagicMock()
        master._state = WorkflowState.empty().with_updates(
            scheduler=stub_scheduler,
            graph=stub_graph,
            workflow_name="test",
            start_nodes=["n1"],
            initial_inputs={},
        )

        stub_decision = MagicMock(node_id="decision_node_1")
        master._decision_queue = MagicMock(get=MagicMock(return_value=stub_decision))

        runner = WorkflowRunner(master)
        runner._resolve_decision_locked = MagicMock(return_value="resolved_obj")
        runner._harvest_decision_specs = MagicMock(return_value=[])

        try:
            runner.resume(decision_id="d1", option="approve")
        except NotImplementedError:
            # Task 7 raises NotImplementedError after step 3-5
            pass

        runner._resolve_decision_locked.assert_called_once_with("d1", "approve", "human")
        stub_scheduler.resume.assert_called_once_with(
            decision_node_id="decision_node_1",
            option="approve",
            resolved_by="human",
        )


class TestResumeContinueAndReturn:
    """resume() step 6-8: continue scheduler + collect + backfill + state write + return."""

    def test_resume_reuses_cached_start_nodes_from_state(self) -> None:
        """resume 用 cached start_nodes, 不用 graph 默认无依赖节点."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        stub_scheduler = MagicMock()
        stub_graph = MagicMock(
            node_ids=lambda: ["n1", "n2", "n3"],
            get_node=MagicMock(return_value=MagicMock(depends_on=[])),
        )
        # cached start_nodes = ["n_special"] (与 graph node_ids 不重叠)
        master._state = WorkflowState.empty().with_updates(
            scheduler=stub_scheduler,
            graph=stub_graph,
            workflow_name="test",
            start_nodes=["n_special"],
            initial_inputs={},
        )

        stub_decision = MagicMock(node_id="d_node")
        master._decision_queue = MagicMock(get=MagicMock(return_value=stub_decision))
        observed = {}
        stub_scheduler.run = MagicMock(
            side_effect=lambda **kw: (observed.update(kw), MagicMock())[1])
        stub_scheduler.resume = MagicMock()

        runner = WorkflowRunner(master)
        runner._resolve_decision_locked = MagicMock(return_value="resolved")
        runner._harvest_decision_specs = MagicMock(return_value=[])
        runner._collect_executions = MagicMock(return_value={})
        runner._maybe_incremental_backfill = MagicMock(return_value=None)

        runner.resume(decision_id="d1", option="approve")
        assert observed["start_nodes"] == ["n_special"]

    def test_resume_returns_resolved_decision_in_payload(self) -> None:
        """return dict 含 resolved_decision 字段 (HumanDecision 对象)."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        stub_scheduler = MagicMock()
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=MagicMock(depends_on=[])),
        )
        master._state = WorkflowState.empty().with_updates(
            scheduler=stub_scheduler,
            graph=stub_graph,
            workflow_name="test",
            start_nodes=[],
            initial_inputs={},
        )

        stub_decision = MagicMock(node_id="d_node")
        master._decision_queue = MagicMock(get=MagicMock(return_value=stub_decision))
        stub_scheduler.run = MagicMock(return_value=MagicMock())
        stub_scheduler.resume = MagicMock()

        runner = WorkflowRunner(master)
        runner._resolve_decision_locked = MagicMock(return_value="RESOLVED_OBJ")
        runner._harvest_decision_specs = MagicMock(return_value=[{"p": 1}])
        runner._collect_executions = MagicMock(return_value={})
        runner._maybe_incremental_backfill = MagicMock(return_value=None)

        result = runner.resume(decision_id="d1", option="approve")
        assert result["resolved_decision"] == "RESOLVED_OBJ"
        assert result["pending_decisions"] == [{"p": 1}]
        assert "summary" in result
        assert "graph" in result
        assert "executions" in result
        assert "incremental_backfill" in result
        assert "memory_context" in result


class TestInternalHelpers:
    """5 internal helpers 实现 (从 WorkflowMixin 迁移).

    Task 4 + Task 7 加了 5 stub methods. Task 9 替换为真实实现 + fcntl lock.
    """

    def test_collect_executions_returns_node_id_to_execution_mapping(self) -> None:
        """_collect_executions(graph) 返 {node_id: NodeExecution} dict."""
        exec_n1 = MagicMock()
        stub_graph = MagicMock(
            node_ids=lambda: ["n1", "n2"],
            has_execution=lambda nid: nid == "n1",
            get_execution=lambda nid: exec_n1 if nid == "n1" else None,
        )
        result = WorkflowRunner._collect_executions(stub_graph)
        assert result == {"n1": exec_n1}
        assert "n2" not in result

    def test_maybe_memory_context_returns_none_when_mode_unset(self, monkeypatch) -> None:
        """_memory_rag_mode 未设时返 None, 不调 chapter_memory_hook."""
        import lingwen_core.agents.chapter_memory_hook as cmh
        called = []
        def fake_attach(workflow_name, initial_inputs, mode=None):
            called.append((workflow_name, initial_inputs, mode))
            return {"should": "not appear"}
        monkeypatch.setattr(cmh, "maybe_attach_memory_context", fake_attach)

        master = MasterController.__new__(MasterController)
        # No _memory_rag_mode attribute → getattr default None
        runner = WorkflowRunner(master)
        result = runner._maybe_memory_context("novel_writing", {"chapter_num": 1})
        assert result is None  # getattr default None → early return
        assert called == []  # real impl never called

    def test_maybe_incremental_backfill_returns_none_when_enabled_unset(self, monkeypatch) -> None:
        """_incremental_backfill_enabled 未设时返 None, 传 enabled=None 到 maybe_after_workflow."""
        import infra.cross_volume.incremental_backfill as cv_backfill
        captured = []
        def fake_after(workflow_name, initial_inputs, executions, summary, *, enabled=None):
            captured.append({
                "workflow_name": workflow_name,
                "initial_inputs": initial_inputs,
                "executions": executions,
                "summary": summary,
                "enabled": enabled,
            })
            return None
        monkeypatch.setattr(cv_backfill, "maybe_after_workflow", fake_after)

        master = MasterController.__new__(MasterController)
        runner = WorkflowRunner(master)
        summary = MagicMock()
        result = runner._maybe_incremental_backfill("novel_writing", {"k": 1}, {"n1": "exec"}, summary)
        assert result is None
        assert len(captured) == 1
        assert captured[0]["workflow_name"] == "novel_writing"
        assert captured[0]["enabled"] is None
        assert captured[0]["summary"] is summary

    def test_harvest_decision_specs_skips_already_pending_nodes(self) -> None:
        """queue 中已有 pending 的 node 不重复 harvest."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        # Stub _decision_queue: 已有 pending d1
        pending_decision = MagicMock(node_id="n1")
        master._decision_queue = MagicMock(
            pending=MagicMock(return_value=[pending_decision]),
            add=MagicMock(),
        )

        # Stub graph: n1 (DECISION) + n2 (DECISION) + n3 (non-DECISION)
        from infra.got.data_structures import NodeType
        stub_n1 = MagicMock(type=NodeType.DECISION, description="d1", name="d1")
        stub_n2 = MagicMock(type=NodeType.DECISION, description="d2", name="d2")
        # non-DECISION node uses any non-DECISION type
        stub_n3 = MagicMock(type=MagicMock(), description="n3", name="n3")
        stub_graph = MagicMock(
            node_ids=lambda: ["n1", "n2", "n3"],
            get_node=lambda nid: {"n1": stub_n1, "n2": stub_n2, "n3": stub_n3}[nid],
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )

        runner = WorkflowRunner(master)
        result = runner._harvest_decision_specs(stub_graph, initial_inputs={})
        # n1 已有 pending → skip; n2 新建 → 1 entry; n3 不是 DECISION → skip
        assert len(result) == 1
        master._decision_queue.add.assert_called_once()


# === Phase 28 P2-RESUME-VERIFY: E2E tests with real GoTScheduler ===

class TestResumeE2EWithRealScheduler:
    """E2E 测试 — 真实 GoTScheduler + ThoughtGraph (非 MagicMock).

    Phase 28 P2-RESUME-VERIFY: 验证 scheduler 对已 COMPLETED 节点幂等
    + start_nodes=None resume cycle (代码 review 列 important).
    """

    def _build_graph_with_decision(self) -> tuple:
        """构建 4 节点图: n1 (GENERATION) → n2 (DECISION) → n3 (GENERATION) → n4 (OUTPUT).

        compute_fn 简单递增计数器记录执行次数.
        """
        from infra.got.data_structures import NodeType, ThoughtNode
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import ComputeResult, GoTScheduler

        graph = ThoughtGraph()
        graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, name="gen1", description="gen1", depends_on=()))
        graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, name="decision", description="decision", depends_on=("n1",)))
        graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, name="gen2", description="gen2", depends_on=("n2",)))
        graph.add_node(ThoughtNode(node_id="n4", type=NodeType.OUTPUT, name="out", description="out", depends_on=("n3",)))

        call_log: list = []

        def compute_fn(node, inputs):
            call_log.append(node.node_id)
            return ComputeResult(
                output={"node": node.node_id, "input_keys": list(inputs.keys())},
                cost_tokens=1,
            )

        scheduler = GoTScheduler(graph, compute_fn=compute_fn, max_backtracks=0)
        scheduler._test_call_log = call_log  # type: ignore[attr-defined]
        return scheduler, graph

    def test_scheduler_run_is_idempotent_on_completed_nodes(self) -> None:
        """scheduler.run(start_nodes) 二次调用不重跑已 COMPLETED 节点.

        验证: graph.ready_nodes() (infra/got/graph.py:152-155) 排除 status≠PENDING
        → 已 COMPLETED n1 不进 ready_nodes → 不重跑.

        注: 第二次 run 时 n2 仍是 WAITING, n3/n4 被它阻塞 → ready_nodes 为空
        → scheduler 直接退出 (paused=False, paused_nodes=()). 这是正确行为 —
        scheduler.run 只报告 NEW pauses, 不报告之前已 paused 的节点.
        """
        from infra.got.data_structures import NodeStatus

        scheduler, _ = self._build_graph_with_decision()

        # 第一次 run: n1 执行 → n2 DECISION pause → n3/n4 未执行
        summary1 = scheduler.run(start_nodes=["n1"])
        assert summary1.completed == 1  # 仅 n1
        assert summary1.paused is True
        assert summary1.paused_nodes == ("n2",)

        # 验证 n2 已 WAITING (record_execution by scheduler)
        assert scheduler._graph.has_execution("n2")
        assert scheduler._graph.get_execution("n2").status == NodeStatus.WAITING

        # 第二次 run: ready_nodes 为空 (n1 COMPLETED, n2 WAITING, n3/n4 阻塞) → 立即退出
        summary2 = scheduler.run(start_nodes=["n1"])
        assert summary2.completed == 0  # 无新执行
        assert summary2.steps == 0  # compute_fn 未被调
        # call_log 不变 (n1 未重跑)
        assert scheduler._test_call_log == ["n1"]
        # n2 仍是 WAITING (状态跨 run 保留 — graph._executions 不被 reset)
        assert scheduler._graph.get_execution("n2").status == NodeStatus.WAITING

    def test_resume_after_decision_pause_continues_from_cached_start_nodes(self) -> None:
        """DECISION pause → scheduler.resume → scheduler.run(start_nodes): 下游执行, 已执行节点跳过.

        验证: scheduler.resume 把 n2 改 COMPLETED → 下次 run 时 n2 不进 ready_nodes
        → n3 ready → execute → n4 ready → execute.
        """
        from infra.got.data_structures import NodeStatus

        scheduler, _ = self._build_graph_with_decision()

        # 1) 第一次 run: n1 → n2 (pause)
        summary1 = scheduler.run(start_nodes=["n1"])
        assert summary1.completed == 1
        assert summary1.paused_nodes == ("n2",)

        # 2) Resume DECISION (Phase 5 API — infra/got/scheduler.py:256-298)
        decision_exec = scheduler.resume(decision_node_id="n2", option="approve")
        assert decision_exec.status == NodeStatus.COMPLETED
        assert decision_exec.output == {"option": "approve", "resolved_by": "human"}

        # 3) 第二次 run (resume 后继续) — 用 cached start_nodes ["n1"]
        summary2 = scheduler.run(start_nodes=["n1"])
        # n1 COMPLETED → skip; n2 COMPLETED → skip; n3 now ready → execute; n4 ready → execute
        assert summary2.completed == 2  # n3 + n4
        assert summary2.paused is False
        # call_log: n1 (第一次), n3, n4 (第二次 — n2 DECISION 不调 compute_fn)
        assert scheduler._test_call_log == ["n1", "n3", "n4"]


class TestRunWithNoneStartNodesDerivation:
    """E2E 验证 start_nodes=None 推导 + 持久化 + resume 复用 (Phase 28)."""

    def test_run_with_none_start_nodes_persists_derived_list_to_state(self) -> None:
        """run(workflow_name, start_nodes=None) 后 state.start_nodes == derived list.

        用真实 GoTScheduler + ThoughtGraph (3 节点: n1 root, n2 DECISION, n3 dependent).
        """
        from infra.got.data_structures import NodeType, ThoughtNode
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import ComputeResult, GoTScheduler

        # Setup real graph
        graph = ThoughtGraph()
        graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, name="gen1", description="gen1", depends_on=()))
        graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, name="dec", description="dec", depends_on=("n1",)))
        graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, name="gen3", description="gen3", depends_on=("n2",)))

        scheduler = GoTScheduler(graph, compute_fn=lambda n, i: ComputeResult(output={"x": 1}, cost_tokens=1), max_backtracks=0)

        # Setup WorkflowRunner via master stub
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None
        master._decision_queue = MagicMock(pending=MagicMock(return_value=[]), add=MagicMock())

        # Monkeypatch build_got_scheduler to return real scheduler/graph
        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        got_bridge.build_got_scheduler = MagicMock(return_value=(scheduler, graph))
        try:
            runner = WorkflowRunner(master)
            runner._maybe_memory_context = MagicMock(return_value=None)
            runner._maybe_incremental_backfill = MagicMock(return_value=None)
            runner._harvest_decision_specs = MagicMock(return_value=[])

            # run(start_nodes=None) — 应推导 ["n1"] (n1 是 root, n2 依赖 n1)
            runner.run(workflow_name="test", start_nodes=None)

            # 验证 state.start_nodes 缓存 derived list
            assert list(master._state.start_nodes) == ["n1"]
        finally:
            got_bridge.build_got_scheduler = original

    def test_resume_reuses_start_nodes_persisted_during_run_with_none(self) -> None:
        """run(start_nodes=None) → resume 复用 derived start_nodes.

        关键验证: state.start_nodes 在 resume 期间不被 graph mutation 污染.
        即使 graph 加新 root node (n4), state.start_nodes 仍是 run 时的 derived ["n1"].
        """
        from infra.got.data_structures import NodeType, ThoughtNode
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import ComputeResult, GoTScheduler

        # Setup real graph: n1 root + n2 DECISION + n3 dep
        graph = ThoughtGraph()
        graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, name="gen1", description="gen1", depends_on=()))
        graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, name="dec", description="dec", depends_on=("n1",)))
        graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, name="gen3", description="gen3", depends_on=("n2",)))

        call_log: list = []

        def compute_fn(node, inputs):
            call_log.append(node.node_id)
            return ComputeResult(output={"node": node.node_id}, cost_tokens=1)

        scheduler = GoTScheduler(graph, compute_fn=compute_fn, max_backtracks=0)

        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master.budget_service = None
        master._decision_queue = MagicMock(pending=MagicMock(return_value=[]), add=MagicMock())

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        got_bridge.build_got_scheduler = MagicMock(return_value=(scheduler, graph))
        try:
            runner = WorkflowRunner(master)
            runner._maybe_memory_context = MagicMock(return_value=None)
            runner._maybe_incremental_backfill = MagicMock(return_value=None)

            # 1) run(start_nodes=None) — 推导 ["n1"]
            runner.run(workflow_name="test", start_nodes=None)
            assert list(master._state.start_nodes) == ["n1"]
            # n1 executed + n2 paused (DECISION)
            assert call_log == ["n1"]

            # 2) Add n4 to graph (simulate post-pause graph mutation)
            #    If resume re-derives start_nodes, would now include both ["n1", "n4"]
            graph.add_node(ThoughtNode(node_id="n4", type=NodeType.GENERATION, name="gen4", description="gen4", depends_on=()))
            # But n4 has no DECISION dependency — would still be in re-derived list
            # The point: state.start_nodes should NOT be re-derived

            # 3) Stub decision_queue for resume
            master._decision_queue = MagicMock(
                pending=MagicMock(return_value=[]),
                add=MagicMock(),
                get=MagicMock(return_value=MagicMock(node_id="n2")),
                resolve=MagicMock(return_value="resolved"),
                with_lock=MagicMock(
                    return_value=MagicMock(
                        __enter__=MagicMock(return_value=MagicMock()),
                        __exit__=MagicMock(return_value=False),
                    )
                ),
            )
            runner._harvest_decision_specs = MagicMock(return_value=[])

            # 4) resume — state.start_nodes 应保持 ["n1"] (不被 n4 污染)
            runner.resume(decision_id="d1", option="approve")

            # state.start_nodes 仍是 ["n1"] — resume 不重推导 (即使 graph 有新 root)
            assert list(master._state.start_nodes) == ["n1"]
            # 验证 resume 调用 scheduler.run 时传入的是 ["n1"] (而非重推导的 ["n1", "n4"])
            # call_log 反映 n1 (run) + n3 (resume 下游) + n4 (新增 root ready) — 都执行
            # 但 n1 未被重跑 (cache/ready_nodes 跳过 COMPLETED)
            assert "n1" in call_log
            assert call_log.count("n1") == 1  # n1 仅在 run 时执行 1 次, resume 不重跑
        finally:
            got_bridge.build_got_scheduler = original
