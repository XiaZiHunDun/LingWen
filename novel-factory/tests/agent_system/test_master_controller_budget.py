"""Tests for MasterController budget_service injection + run_id (Phase 8.12)"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from infra.agent_system.master_controller import MasterController


@pytest.fixture
def tmp_state_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_stub_master(state_dir: Path) -> MasterController:
    """构造 MasterController 用 stub router/state 避免真实依赖"""
    from infra.agent_system.agent_config import MasterControllerConfig
    config = MasterControllerConfig(
        state_dir=str(state_dir),
        primary_provider="minimax",
        enable_failover=False,
        providers={},
    )
    master = MasterController.__new__(MasterController)
    master._config = config
    master._router = MagicMock()
    master.cost_tracker = MagicMock()
    master._current_budget_usd = None
    return master


def _patch_got_bridge():
    """Patch infra.agent_system.got_bridge.build_got_scheduler 返 stub (scheduler, graph).

    Stub graph 提供 run_workflow 内部需要的: node_ids(), get_node(nid).depends_on,
    has_execution(nid), get_execution(nid). Stub scheduler 提供 run() 返 fake summary.
    """
    from infra.agent_system import got_bridge
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
    got_bridge.build_got_scheduler = MagicMock(
        return_value=(stub_scheduler, stub_graph)
    )
    return original


class TestMasterControllerBudget:
    """MasterController budget_service 注入 + run_id uuid4 行为"""

    def test_run_workflow_generates_run_id_uuid4_hex(
        self, tmp_state_dir: Path
    ) -> None:
        """run_workflow 后, internal run_id 是 32 char hex (uuid4().hex)"""
        master = _make_stub_master(tmp_state_dir)
        # Stub budget_service
        master.budget_service = MagicMock()
        # Stub run_workflow 内部依赖 (避免真实 GoT 调度)
        master._harvest_decision_specs = MagicMock(return_value=[])
        original = _patch_got_bridge()
        try:
            master.run_workflow(
                workflow_name="test", cost_budget_usd=0.1
            )
            # Verify call to budget_service.set included run_id (32 char hex)
            call_kwargs = master.budget_service.set.call_args.kwargs
            assert "run_id" in call_kwargs
            assert re.match(r"^[0-9a-f]{32}$", call_kwargs["run_id"]), (
                f"run_id should be 32 char hex (uuid4().hex), got {call_kwargs['run_id']!r}"
            )
        finally:
            from infra.agent_system import got_bridge
            got_bridge.build_got_scheduler = original

    def test_run_workflow_calls_budget_service_set_run(
        self, tmp_state_dir: Path
    ) -> None:
        """run_workflow 调 budget_service.set(scope='run', usd=X, run_id=...)"""
        master = _make_stub_master(tmp_state_dir)
        master.budget_service = MagicMock()
        master._harvest_decision_specs = MagicMock(return_value=[])
        original = _patch_got_bridge()
        try:
            master.run_workflow(workflow_name="test", cost_budget_usd=0.1)
            master.budget_service.set.assert_called_once()
            call_kwargs = master.budget_service.set.call_args.kwargs
            assert call_kwargs["scope"] == "run"
            assert call_kwargs["usd"] == 0.1
            assert "run_id" in call_kwargs
        finally:
            from infra.agent_system import got_bridge
            got_bridge.build_got_scheduler = original

    def test_run_workflow_no_budget_service_does_not_call_set(
        self, tmp_state_dir: Path
    ) -> None:
        """budget_service=None → 不 set (backward compat)"""
        master = _make_stub_master(tmp_state_dir)
        master.budget_service = None
        master._harvest_decision_specs = MagicMock(return_value=[])
        original = _patch_got_bridge()
        try:
            # 不 raise 即 pass
            master.run_workflow(workflow_name="test", cost_budget_usd=0.1)
        finally:
            from infra.agent_system import got_bridge
            got_bridge.build_got_scheduler = original

    def test_run_workflow_finally_resets_budget_state(
        self, tmp_state_dir: Path
    ) -> None:
        """run 结束后 _current_budget_usd = None (防 leak 跨 run)"""
        master = _make_stub_master(tmp_state_dir)
        master.budget_service = MagicMock()
        master._harvest_decision_specs = MagicMock(return_value=[])
        original = _patch_got_bridge()
        try:
            master.run_workflow(workflow_name="test", cost_budget_usd=0.1)
            assert master._current_budget_usd is None  # finally reset
        finally:
            from infra.agent_system import got_bridge
            got_bridge.build_got_scheduler = original

    def test_old_run_workflow_signature_still_works(
        self, tmp_state_dir: Path
    ) -> None:
        """旧 signature (cost_budget_usd=None) 0 budget_service 不破"""
        master = _make_stub_master(tmp_state_dir)
        master.budget_service = None
        master._harvest_decision_specs = MagicMock(return_value=[])
        original = _patch_got_bridge()
        try:
            master.run_workflow(workflow_name="test", cost_budget_usd=None)
            assert master._current_budget_usd is None
        finally:
            from infra.agent_system import got_bridge
            got_bridge.build_got_scheduler = original
