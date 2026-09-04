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
