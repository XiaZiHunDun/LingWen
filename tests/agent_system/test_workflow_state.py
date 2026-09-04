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
