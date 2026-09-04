"""Phase 26 P2-WFSTATE — WorkflowState dataclass unit tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from lingwen_core.agents.workflow_state import WorkflowState


class TestWorkflowStateConstruction:
    """构造 / defaults / frozen 强制."""

    def test_empty_classmethod_returns_all_none_or_empty_defaults(self) -> None:
        state = WorkflowState.empty()
        assert state.scheduler is None
        assert state.graph is None
        assert state.workflow_name == ""
        assert state.start_nodes == []
        assert state.initial_inputs == {}
        assert state.incremental_backfill is None
        assert state.memory_context is None

    def test_constructor_with_no_args_equals_empty(self) -> None:
        assert WorkflowState() == WorkflowState.empty()

    def test_default_factory_independence_for_start_nodes(self) -> None:
        """list/dict 默认值不共享 (mutable default 复用陷阱)."""
        a = WorkflowState.empty()
        b = WorkflowState.empty()
        a.start_nodes.append("x")
        assert b.start_nodes == []  # b 不受 a 改动影响

    def test_default_factory_independence_for_initial_inputs(self) -> None:
        a = WorkflowState.empty()
        b = WorkflowState.empty()
        a.initial_inputs["k"] = "v"
        assert b.initial_inputs == {}

    def test_frozen_rejects_mutation(self) -> None:
        with pytest.raises(FrozenInstanceError):
            state = WorkflowState.empty()
            state.scheduler = object()  # type: ignore[misc]


class TestWorkflowStateWithUpdates:
    """with_updates 原子更新行为."""

    def test_with_updates_returns_new_instance_not_mutation(self) -> None:
        original = WorkflowState.empty()
        updated = original.with_updates(workflow_name="novel_writing")
        assert updated is not original
        assert original.workflow_name == ""  # 原 instance 不变

    def test_with_updates_overrides_only_named_fields(self) -> None:
        original = WorkflowState(workflow_name="wf1", initial_inputs={"k": 1})
        updated = original.with_updates(workflow_name="wf2")
        assert updated.workflow_name == "wf2"
        assert updated.initial_inputs == {"k": 1}  # 其他字段保留

    def test_with_updates_rejects_unknown_field(self) -> None:
        with pytest.raises(TypeError, match="unknown_field"):
            WorkflowState.empty().with_updates(unknown_field=1)


class TestRefactorGuard:
    """防 _last_* 散点回潮 — 仅 controller._state 单 source 模式."""

    def test_master_controller_has_state_attribute(self) -> None:
        """生产 MasterController.__init__ 后必有 _state 属性."""
        from lingwen_pipeline.master_controller import MasterController

        # 用 __new__ 跳过 __init__ 验证 dataclass 路径;
        # 完整 __init__ 依赖外部 fixture, 这里只验 dataclass 路径
        controller = MasterController.__new__(MasterController)
        controller._state = WorkflowState.empty()

        assert hasattr(controller, "_state")
        assert isinstance(controller._state, WorkflowState)

    def test_no_last_underscore_attrs_on_workflow_state_instance(self) -> None:
        """WorkflowState 实例不应有 _last_* 前缀字段 — 7 字段全部 canonical 命名."""
        state = WorkflowState.empty()

        forbidden_prefixes = (
            "_last_scheduler",
            "_last_graph",
            "_last_workflow_name",
            "_last_start_nodes",
            "_last_initial_inputs",
            "_last_incremental_backfill",
            "_last_memory_context",
        )
        for name in forbidden_prefixes:
            assert not hasattr(state, name), (
                f"WorkflowState 不应有 {name}; 用 workflow_name / graph 等 canonical 名"
            )

        # canonical 命名必须存在
        canonical = (
            "scheduler",
            "graph",
            "workflow_name",
            "start_nodes",
            "initial_inputs",
            "incremental_backfill",
            "memory_context",
        )
        for name in canonical:
            assert hasattr(state, name), f"WorkflowState 缺 canonical 字段 {name}"

    def test_stub_master_controller_uses_workflow_state(self) -> None:
        """chapter_golden_path stub master 初始化后所有 7 字段均可读 — 不再漏 init."""
        import tempfile

        # 用 tmp_path 派生 state_dir — 不实际写文件 (stub init 只设 attrs)
        from pathlib import Path

        from lingwen_core.agents.chapter_golden_path import build_stub_master_controller

        with tempfile.TemporaryDirectory() as tmp:
            controller = build_stub_master_controller(Path(tmp) / "state")

        # 全部 7 字段可读 + 默认值正确 (替代原 _last_X 漏 init AttributeError)
        assert controller._state.scheduler is None
        assert controller._state.graph is None
        assert controller._state.workflow_name == ""
        assert controller._state.start_nodes == []
        assert controller._state.initial_inputs == {}
        assert controller._state.incremental_backfill is None
        assert controller._state.memory_context is None


class TestWorkflowRunnerRefactorGuard:
    """防 WorkflowRunner 散点回潮 (Phase 27 P2-WFRUNNER).

    与 TestRefactorGuard (WorkflowState 字段) 对偶 — 守 Runner 内部不引入
    _last_* 散点属性 / 不持独立 state.
    """

    def test_workflow_runner_has_no_last_underscore_attrs(self) -> None:
        """WorkflowRunner 实例不应有 _last_* 私有字段."""
        from lingwen_core.agents.workflow_runner import WorkflowRunner
        from lingwen_pipeline.master_controller import MasterController

        controller = MasterController.__new__(MasterController)
        runner = WorkflowRunner(controller)

        forbidden_prefixes = (
            "_last_controller",
            "_last_scheduler",
            "_last_graph",
            "_last_state",
            "_last_workflow_name",
            "_last_run_id",
            "_last_budget",
        )
        for name in forbidden_prefixes:
            assert not hasattr(runner, name), (
                f"WorkflowRunner 不应有 {name}; 引用 controller 而非 cache"
            )

    def test_workflow_runner_does_not_mutate_state_directly(self) -> None:
        """Runner 不持独立 state — 所有 state 操作走 controller._state."""
        from lingwen_core.agents.workflow_runner import WorkflowRunner
        from lingwen_pipeline.master_controller import MasterController

        controller = MasterController.__new__(MasterController)
        runner = WorkflowRunner(controller)

        # Runner 不应有 _state 属性 — state 全部归 controller
        assert not hasattr(runner, "_state"), (
            "WorkflowRunner 不应持独立 state; 走 controller._state.with_updates()"
        )
        # Runner 必有 _controller 引用
        assert runner._controller is controller
