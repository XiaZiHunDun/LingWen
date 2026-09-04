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
        """
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

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
            # Task 2 raises NotImplementedError after budget setup
            pass

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
