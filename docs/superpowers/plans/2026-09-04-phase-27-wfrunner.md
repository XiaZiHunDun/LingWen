# Phase 27 P2-WFRUNNER Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `WorkflowMixin.run_workflow` (106 行) + `resume_workflow` (75 行) + 4 internal helpers (103 行) 拆出到独立 `WorkflowRunner` service，`WorkflowMixin` 变 1 行 delegate。

**Architecture:** 新建 `WorkflowRunner(controller)` 类（`lingwen-core/agents/workflow_runner.py`），自含 `run()` / `resume()` + 5 helpers。`WorkflowMixin` 提供懒加载 `_get_runner()`，首个 `run_workflow()` / `resume_workflow()` 调用触发 init。Runner 直读 / 直写 `controller._state`（保留所有 `master._state.X` 现有读路径）。

**Tech Stack:** Python 3.13 / pytest / unittest.mock (MagicMock) / ruff / Phase 26 WorkflowState dataclass / Phase 15 P3-SPLIT WorkflowMixin pattern

**Spec:** `docs/superpowers/specs/2026-09-04-phase-27-wfrunner-design.md`

---

## File Structure

| 状态 | 文件 | 职责 |
|------|------|------|
| Create | `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` | WorkflowRunner service 类 |
| Modify | `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` | 删 run/resume/4 helpers + 加 `_get_runner()` 懒 accessor |
| Create | `tests/agent_system/test_workflow_runner.py` | Runner unit tests (~17-20 tests) |
| Modify | `tests/agent_system/test_workflow_state.py` | +2 refactor guard tests |
| Modify | `tests/agent_system/test_master_controller_budget.py` | 6 stub 行更新 (`master._harvest_decision_specs` → `master._get_runner()._harvest_decision_specs`) |
| Create | `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md` | Handoff doc |

**0 改范围承诺**：不动 `apps/studio_api/protocols.py` / `routes/workflows.py` / `helpers/workflow.py` / `workflow_state.py` / `master_controller.py` shim / `infra/got/*` / `.lingwen/architecture.yml`。

---

## Task 1: WorkflowRunner class skeleton + WorkflowMixin lazy accessor

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py:1-50`
- Create: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for lazy accessor + constructor**

Create `tests/agent_system/test_workflow_runner.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lingwen_core.agents.workflow_runner'`

- [ ] **Step 3: Write minimal WorkflowRunner class + WorkflowMixin lazy accessor**

Create `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`:

```python
"""Phase 27 P2-WFRUNNER — MasterController 工作流运行 service.

从 WorkflowMixin.run_workflow / resume_workflow (181 行) 拆出,
自含 budget + scheduler + state 生命周期管理. Mixin.run_workflow()
变 1 行 delegate: return self._get_runner().run(...).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lingwen_pipeline.master_controller import MasterController

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """MasterController 工作流运行 service (Phase 27 P2-WFRUNNER).

    封装 run_workflow / resume_workflow + 4 internal helpers.
    读 / 写 controller._state (WorkflowState) 直传 — 不持独立 state.
    """

    def __init__(self, controller: "MasterController") -> None:
        self._controller = controller
```

Modify `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` — replace top of file (after docstring + imports) with new skeleton:

```python
"""MasterController 工作流相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的工作流相关方法。
Phase 25.9 (human_review 全流水线重构): run_workflow / resume_workflow 重写对齐 GoT API。
Phase 27 P2-WFRUNNER: run / resume / 4 internal helpers 拆到 WorkflowRunner service,
Mixin 仅保留 5 薄代理 + 3 决策委托 + 1 懒 runner accessor.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from lingwen_core.agents.workflow_runner import WorkflowRunner

logger = logging.getLogger(__name__)


class WorkflowMixin:
    """工作流相关方法 (Phase 27 拆 Runner 后).

    Mixin 只留 5 薄代理 + 3 决策队列委托 + _get_runner() 懒加载.
    run_workflow / resume_workflow 是 1 行 delegate → WorkflowRunner.
    """

    def _get_runner(self) -> "WorkflowRunner":
        """懒加载 WorkflowRunner, 缓存到 self._workflow_runner.

        首个 run_workflow / resume_workflow 调用触发 init, 后续复用同 instance.
        __new__ 测试 stub 不走 __init__, 懒加载保证 stub 无 _workflow_runner
        属性时也能正常调用.
        """
        runner = getattr(self, "_workflow_runner", None)
        if runner is None:
            from lingwen_core.agents.workflow_runner import WorkflowRunner
            runner = WorkflowRunner(self)
            self._workflow_runner = runner
        return runner
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(lingwen-core): add WorkflowRunner service skeleton + lazy Mixin accessor"
```

---

## Task 2: run() budget setup + finally reset

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py:25-50`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for budget lifecycle**

Append to `tests/agent_system/test_workflow_runner.py`:

```python
class TestRunBudgetLifecycle:
    """run() budget setup + finally reset (Phase 8.8/8.12 不变量)."""

    def test_run_sets_current_budget_usd_before_scheduler(self, monkeypatch) -> None:
        """run() 进入时 _current_budget_usd = cost_budget_usd, scheduler.run 之前已设."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        observed = {}

        def fake_scheduler_run(**kwargs):
            observed["budget_at_run"] = master._current_budget_usd
            observed["run_id_at_run"] = master._current_run_id
            from unittest.mock import MagicMock
            return MagicMock()

        # Stub got_bridge.build_got_scheduler
        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        stub_scheduler = MagicMock(run=fake_scheduler_run)
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            master._harvest_decision_specs = MagicMock(return_value=[]) if hasattr(master, "_harvest_decision_specs") else None
            # 直接调 runner (跳过 Mixin lazy)
            runner = WorkflowRunner(master)
            runner.run(workflow_name="test", cost_budget_usd=0.5)
            assert observed["budget_at_run"] == 0.5
            assert observed["run_id_at_run"] is not None
            assert len(observed["run_id_at_run"]) == 32  # uuid4().hex
        finally:
            got_bridge.build_got_scheduler = original

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunBudgetLifecycle -v`
Expected: FAIL (runner.run not implemented)

- [ ] **Step 3: Implement minimal run() with budget lifecycle**

Modify `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`, add `run()`:

```python
    def run(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """运行工作流 (Phase 27 P2-WFRUNNER).

        Returns:
            {summary, graph, executions, pending_decisions, incremental_backfill, memory_context}
        """
        import uuid
        controller = self._controller

        # Phase 8.8: 先写 budget, AgentComputeFn 才读得到
        controller._current_budget_usd = cost_budget_usd
        # Phase 8.12: run_id (uuid4 hex) + 持久化到 budget_service
        run_id = uuid.uuid4().hex
        controller._current_run_id = run_id
        # getattr 兜底 __new__ 构造的 test stub
        budget_service = getattr(controller, "budget_service", None)
        if budget_service is not None and cost_budget_usd is not None:
            budget_service.set(scope="run", usd=cost_budget_usd, run_id=run_id)
        try:
            raise NotImplementedError("Phase 27 Task 2-5: implementation in progress")
        finally:
            # Phase 8.8 / 8.12: reset 防跨 run leak
            controller._current_budget_usd = None
            controller._current_run_id = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunBudgetLifecycle -v`
Expected: 2 tests PASS (NotImplementedError raised, finally still runs)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): budget lifecycle setup + finally reset (Phase 8.8/8.12)"
```

---

## Task 3: run() build scheduler + default start_nodes

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for scheduler build + start_nodes default**

Append to test file:

```python
class TestRunSchedulerBuild:
    """run() step 2-3: build scheduler + default start_nodes."""

    def test_run_calls_build_got_scheduler_with_controller(self) -> None:
        """build_got_scheduler(master=controller, workflow_name=..., ...) 被调用."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

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
            runner.run(workflow_name="novel_writing", max_backtracks=3)
            assert called_kwargs["master"] is master
            assert called_kwargs["workflow_name"] == "novel_writing"
            assert called_kwargs["max_backtracks"] == 3
        finally:
            got_bridge.build_got_scheduler = original

    def test_run_uses_default_start_nodes_when_none(self) -> None:
        """start_nodes=None → 取 graph 无依赖节点."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler

        # 3 nodes: 2 无依赖 + 1 有依赖
        stub_dep = MagicMock(depends_on=["n1"])
        stub_indep1 = MagicMock(depends_on=[])
        stub_indep2 = MagicMock(depends_on=[])
        nodes = {"n1": stub_dep, "n2": stub_indep1, "n3": stub_indep2}
        stub_graph = MagicMock(
            node_ids=lambda: list(nodes.keys()),
            get_node=lambda nid: nodes[nid],
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )

        observed_start_nodes = {}
        def fake_run(**kwargs):
            observed_start_nodes.update(kwargs)
            return MagicMock()

        stub_scheduler = MagicMock(run=fake_run)
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            runner.run(workflow_name="test")
            assert set(observed_start_nodes["start_nodes"]) == {"n2", "n3"}
        finally:
            got_bridge.build_got_scheduler = original
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunSchedulerBuild -v`
Expected: FAIL (NotImplementedError)

- [ ] **Step 3: Implement scheduler build + default start_nodes**

Replace `raise NotImplementedError(...)` block in `run()` with:

```python
        try:
            # 延迟 import: 避免 got ↔ agent_system 循环, 且让测试可 monkeypatch
            from lingwen_core.agents.got_bridge import build_got_scheduler

            scheduler, graph = build_got_scheduler(
                master=controller,
                workflow_name=workflow_name,
                base_dir=base_dir,
                max_backtracks=max_backtracks,
            )

            # 默认起点: 无依赖的节点
            if start_nodes is None:
                start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]

            raise NotImplementedError("Phase 27 Task 4-5: memory + harvest + state + scheduler.run in progress")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunSchedulerBuild -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): scheduler build + default start_nodes (Phase 9.63)"
```

---

## Task 4: run() memory context + harvest DECISION specs

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for memory + harvest**

Append to test file:

```python
class TestRunMemoryAndHarvest:
    """run() step 4-5: memory RAG context + harvest DECISION specs."""

    def test_run_attaches_memory_context_to_seed_inputs(self, monkeypatch) -> None:
        """memory_context 不为 None 时自动写入 seed_inputs['memory_context']."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()
        master._memory_rag_mode = "summary"

        from lingwen_core.agents import got_bridge, chapter_memory_hook
        original_build = got_bridge.build_got_scheduler
        original_attach = chapter_memory_hook.maybe_attach_memory_context

        # Stub chapter_memory_hook.maybe_attach_memory_context
        chapter_memory_hook.maybe_attach_memory_context = MagicMock(return_value={"rag": "ctx"})

        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        observed = {}
        def fake_run(**kwargs):
            observed.update(kwargs)
            return MagicMock()
        stub_scheduler = MagicMock(run=fake_run)
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            runner = WorkflowRunner(master)
            runner.run(workflow_name="novel_writing", initial_inputs={"chapter_num": 1})
            assert observed["initial_inputs"]["memory_context"] == {"rag": "ctx"}
            assert observed["initial_inputs"]["chapter_num"] == 1
        finally:
            got_bridge.build_got_scheduler = original_build
            chapter_memory_hook.maybe_attach_memory_context = original_attach

    def test_run_harvest_decisions_before_scheduler(self, monkeypatch) -> None:
        """harvest 在 scheduler.run 之前调用, 结果写入 pending_decisions."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        # 用 stub _harvest_decision_specs
        from lingwen_core.agents.workflow_runner import WorkflowRunner
        runner = WorkflowRunner(master)
        call_order = []
        runner._harvest_decision_specs = MagicMock(side_effect=lambda *a, **kw: (call_order.append("harvest"), [{"decision": "x"}])[1])
        # _maybe_memory_context 返 None 简化
        runner._maybe_memory_context = MagicMock(return_value=None)
        runner._maybe_incremental_backfill = MagicMock(return_value=None)
        runner._collect_executions = MagicMock(return_value={})

        from lingwen_core.agents import got_bridge
        original = got_bridge.build_got_scheduler
        stub_node = MagicMock(depends_on=[])
        stub_graph = MagicMock(
            node_ids=lambda: [],
            get_node=MagicMock(return_value=stub_node),
            has_execution=lambda _: False,
            get_execution=lambda _: None,
        )
        observed = {}
        def fake_run(**kwargs):
            observed["scheduler_called"] = True
            return MagicMock()
        stub_scheduler = MagicMock(run=fake_run)
        got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))

        try:
            result = runner.run(workflow_name="test")
            assert call_order == ["harvest"]
            assert observed.get("scheduler_called") is True
            assert result["pending_decisions"] == [{"decision": "x"}]
        finally:
            got_bridge.build_got_scheduler = original
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunMemoryAndHarvest -v`
Expected: FAIL (NotImplementedError)

- [ ] **Step 3: Implement memory + harvest (with stubs for internal helpers)**

Replace `raise NotImplementedError(...)` block with:

```python
            # Phase 9.70 F62: 可选 MemoryGateway RAG context
            seed_inputs: Dict[str, Any] = dict(initial_inputs or {})
            memory_context = self._maybe_memory_context(workflow_name, seed_inputs)
            if memory_context is not None:
                seed_inputs.setdefault("memory_context", memory_context)

            # Phase 4.3: 扫描 DECISION 节点 → 创建 HumanDecision (须先于 run)
            pending_decisions = self._harvest_decision_specs(graph, initial_inputs=seed_inputs)

            raise NotImplementedError("Phase 27 Task 5: state write + scheduler.run + return in progress")
```

Add stub methods to `WorkflowRunner`:

```python
    def _maybe_memory_context(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
    ) -> Any:
        """Stub — Phase 27 Task 9 implements real version."""
        return None

    def _maybe_incremental_backfill(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
        executions: Dict[str, Any],
        summary: Any,
    ) -> Any:
        """Stub — Phase 27 Task 9 implements real version."""
        return None

    def _harvest_decision_specs(
        self,
        graph: Any,
        *,
        initial_inputs: Optional[Dict[str, Any]] = None,
    ) -> list:
        """Stub — Phase 27 Task 9 implements real version."""
        return []

    @staticmethod
    def _collect_executions(graph: Any) -> Dict[str, Any]:
        """Stub — Phase 27 Task 9 implements real version."""
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunMemoryAndHarvest -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): memory RAG context + harvest DECISION specs (Phase 4.3/9.70)"
```

---

## Task 5: run() state writes + scheduler.run + return

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for state writes + return structure**

Append to test file:

```python
class TestRunStateWrites:
    """run() step 6-11: state writes (pre + post) + scheduler.run + return."""

    def test_run_writes_state_workflow_name_and_start_nodes_before_scheduler(self) -> None:
        """scheduler.run 之前写 state: initial_inputs, workflow_name, start_nodes."""
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

            result = runner.run(workflow_name="test")
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestRunStateWrites -v`
Expected: FAIL (NotImplementedError)

- [ ] **Step 3: Implement state writes + scheduler.run + return**

Replace the `raise NotImplementedError(...)` block with full 11-step body:

```python
            # emit_chapter 等节点在 scheduler.run 期间读 chapter_num — 须先于 run 写入
            controller._state = controller._state.with_updates(
                initial_inputs=dict(seed_inputs),
                workflow_name=workflow_name,
                start_nodes=list(start_nodes),
            )

            summary = scheduler.run(start_nodes=start_nodes, initial_inputs=seed_inputs)
            executions = self._collect_executions(graph)

            # 缓存活跃工作流状态 (Phase 5) — resume_workflow() / dashboard 用它
            incremental_backfill = self._maybe_incremental_backfill(
                workflow_name=workflow_name,
                initial_inputs=seed_inputs,
                executions=executions,
                summary=summary,
            )
            controller._state = controller._state.with_updates(
                scheduler=scheduler,
                graph=graph,
                incremental_backfill=incremental_backfill,
                memory_context=memory_context,
            )

            return {
                "summary": summary,
                "graph": graph,
                "executions": executions,
                "pending_decisions": pending_decisions,
                "incremental_backfill": incremental_backfill,
                "memory_context": memory_context,
            }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py -v`
Expected: 9 tests PASS (Phase A 3 + Phase B 4 + Phase C/D step tests passing)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): complete run() 11-step pipeline + state writes"
```

---

## Task 6: resume() check active workflow + fetch decision

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for resume() guards**

Append to test file:

```python
class TestResumeGuards:
    """resume() step 1-2: RuntimeError on 无活跃工作流 / queue 未初始化."""

    def test_resume_raises_runtime_error_when_no_active_workflow(self) -> None:
        """scheduler / graph 为 None 时 raise RuntimeError('no active workflow')."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()  # scheduler=None, graph=None
        master._decision_queue = MagicMock()

        runner = WorkflowRunner(master)
        import pytest
        with pytest.raises(RuntimeError, match="(?i)no active workflow"):
            runner.resume(decision_id="d1", option="approve")

    def test_resume_raises_runtime_error_when_queue_not_initialized(self) -> None:
        """queue is None 时 raise RuntimeError('decision queue not initialized')."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.with_updates(WorkflowState.empty(),
            scheduler=MagicMock(), graph=MagicMock())
        master._decision_queue = None

        runner = WorkflowRunner(master)
        import pytest
        with pytest.raises(RuntimeError, match="decision queue not initialized"):
            runner.resume(decision_id="d1", option="approve")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestResumeGuards -v`
Expected: FAIL (resume not implemented)

- [ ] **Step 3: Implement resume() step 1-2**

Append to `WorkflowRunner` class in `workflow_runner.py`:

```python
    def resume(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Dict[str, Any]:
        """恢复 DECISION 暂停的工作流 (Phase 27 P2-WFRUNNER)."""
        controller = self._controller

        # 1. 检查有活跃工作流
        scheduler = controller._state.scheduler
        graph = controller._state.graph
        if scheduler is None or graph is None:
            raise RuntimeError(
                "no active workflow; call run_workflow() first before resume_workflow()"
            )

        # 2. 查决策 → 拿 node_id (KeyError if missing)
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")

        raise NotImplementedError("Phase 27 Task 7-8: resolve + resume + harvest + state in progress")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestResumeGuards -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): resume() step 1-2 guards (RuntimeError on missing state/queue)"
```

---

## Task 7: resume() resolve decision + resume GoT node + harvest

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing test for resolve + resume GoT + harvest**

Append to test file:

```python
class TestResumeResolveAndGoT:
    """resume() step 3-5: resolve_decision + scheduler.resume + harvest."""

    def test_resume_resolves_decision_then_resumes_scheduler(self) -> None:
        """resolve_decision → scheduler.resume 顺序调用, 错误时抛对应异常."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        stub_scheduler = MagicMock()
        stub_graph = MagicMock()
        master._state = WorkflowState.with_updates(WorkflowState.empty(),
            scheduler=stub_scheduler, graph=stub_graph,
            workflow_name="test", start_nodes=["n1"], initial_inputs={})

        stub_decision = MagicMock(node_id="decision_node_1")
        master._decision_queue = MagicMock(
            get=MagicMock(return_value=stub_decision),
            resolve=MagicMock(return_value="resolved_obj"),
        )

        runner = WorkflowRunner(master)
        runner._resolve_decision_locked = MagicMock(return_value="resolved_obj")
        runner._harvest_decision_specs = MagicMock(return_value=[])
        runner._collect_executions = MagicMock(return_value={})
        runner._maybe_incremental_backfill = MagicMock(return_value=None)

        stub_scheduler.run = MagicMock(return_value=MagicMock())
        runner.resume(decision_id="d1", option="approve")
        runner._resolve_decision_locked.assert_called_once_with("d1", "approve", "human")
        stub_scheduler.resume.assert_called_once_with(
            decision_node_id="decision_node_1",
            option="approve",
            resolved_by="human",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestResumeResolveAndGoT -v`
Expected: FAIL (NotImplementedError in resume)

- [ ] **Step 3: Implement resume() step 3-5 + stub _resolve_decision_locked**

Replace the `raise NotImplementedError(...)` block in `resume()` with:

```python
        decision = queue.get(decision_id)

        # 3. 标 RESOLVED (lock + write)
        resolved = self._resolve_decision_locked(decision_id, option, resolved_by)

        # 4. 标 DECISION 节点 WAITING → COMPLETED, 写入 option
        scheduler.resume(
            decision_node_id=decision.node_id,
            option=option,
            resolved_by=resolved_by,
        )

        # 5. 扫描新 DECISION 节点 (下游可能有)
        pending_decisions = self._harvest_decision_specs(
            graph,
            initial_inputs=controller._state.initial_inputs,
        )

        raise NotImplementedError("Phase 27 Task 8: continue + collect + backfill + state in progress")
```

Add stub `_resolve_decision_locked` to WorkflowRunner:

```python
    def _resolve_decision_locked(
        self,
        decision_id: str,
        option: str,
        resolved_by: str,
    ) -> Any:
        """Stub — Phase 27 Task 9 implements real version with fcntl lock."""
        controller = self._controller
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        return queue.resolve(decision_id, option, resolved_by=resolved_by)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestResumeResolveAndGoT -v`
Expected: 1 test PASS

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): resume() step 3-5 resolve + scheduler.resume + harvest"
```

---

## Task 8: resume() continue + collect + backfill + state write + return

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing tests for cached start_nodes + return payload**

Append to test file:

```python
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
        master._state = WorkflowState.with_updates(WorkflowState.empty(),
            scheduler=stub_scheduler, graph=stub_graph,
            workflow_name="test", start_nodes=["n_special"], initial_inputs={})

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
        master._state = WorkflowState.with_updates(WorkflowState.empty(),
            scheduler=stub_scheduler, graph=stub_graph,
            workflow_name="test", start_nodes=[], initial_inputs={})

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestResumeContinueAndReturn -v`
Expected: FAIL (NotImplementedError)

- [ ] **Step 3: Implement resume() step 6-8 complete body**

Replace `raise NotImplementedError(...)` block with:

```python
        # 6. 继续执行 — 用上次缓存的 start_nodes
        start_nodes = list(controller._state.start_nodes)
        if not start_nodes:
            start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]

        summary = scheduler.run(start_nodes=start_nodes)

        # 7. 收集 executions
        executions = self._collect_executions(graph)

        incremental_backfill = self._maybe_incremental_backfill(
            workflow_name=controller._state.workflow_name,
            initial_inputs=controller._state.initial_inputs,
            executions=executions,
            summary=summary,
        )
        controller._state = controller._state.with_updates(
            incremental_backfill=incremental_backfill,
        )

        return {
            "summary": summary,
            "graph": graph,
            "executions": executions,
            "pending_decisions": pending_decisions,
            "resolved_decision": resolved,
            "incremental_backfill": incremental_backfill,
            "memory_context": controller._state.memory_context,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py -v`
Expected: 12 tests PASS (Phase A 3 + Phase B 6 + Phase C 3 = full run+resume covered)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): resume() step 6-8 complete continue + collect + backfill + state + return"
```

---

## Task 9: Implement 4 real internal helpers (move from WorkflowMixin)

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- Modify: `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` (delete the 4 helpers)
- Modify: `tests/agent_system/test_workflow_runner.py`

- [ ] **Step 1: Write failing tests for real helpers**

Append to test file:

```python
class TestInternalHelpers:
    """4 internal helpers 实现 (从 WorkflowMixin 迁移)."""

    def test_collect_executions_returns_node_id_to_execution_mapping(self) -> None:
        """_collect_executions(graph) 返 {node_id: NodeExecution} dict."""
        # 构造 stub graph: 2 nodes, 1 有 execution, 1 无
        exec_n1 = MagicMock()
        stub_graph = MagicMock(
            node_ids=lambda: ["n1", "n2"],
            has_execution=lambda nid: nid == "n1",
            get_execution=lambda nid: exec_n1 if nid == "n1" else None,
        )
        result = WorkflowRunner._collect_executions(stub_graph)
        assert result == {"n1": exec_n1}
        assert "n2" not in result

    def test_maybe_memory_context_returns_none_when_disabled(self, monkeypatch) -> None:
        """_memory_rag_mode 未设时返 None (default disabled)."""
        from lingwen_core.agents import chapter_memory_hook
        original = chapter_memory_hook.maybe_attach_memory_context
        chapter_memory_hook.maybe_attach_memory_context = MagicMock(return_value={"should": "not appear"})

        master = MasterController.__new__(MasterController)
        # No _memory_rag_mode attribute
        runner = WorkflowRunner(master)
        try:
            result = runner._maybe_memory_context("novel_writing", {"chapter_num": 1})
            assert result is None  # getattr default None
            chapter_memory_hook.maybe_attach_memory_context.assert_not_called()
        finally:
            chapter_memory_hook.maybe_attach_memory_context = original

    def test_maybe_incremental_backfill_returns_none_when_disabled(self, monkeypatch) -> None:
        """_incremental_backfill_enabled 未设时返 None."""
        from infra.cross_volume.incremental_backfill import maybe_after_workflow
        # We trust v25.9 already returns None when enabled is None
        master = MasterController.__new__(MasterController)
        runner = WorkflowRunner(master)
        result = runner._maybe_incremental_backfill("novel_writing", {}, {}, MagicMock())
        assert result is None

    def test_harvest_decision_specs_skips_already_pending_nodes(self) -> None:
        """queue 中已有 pending 的 node 不重复 harvest."""
        master = MasterController.__new__(MasterController)
        from lingwen_core.agents.workflow_state import WorkflowState
        master._state = WorkflowState.empty()

        # Stub _decision_queue: 已有 pending d1
        pending_decision = MagicMock(node_id="n1")
        master._decision_queue = MagicMock(pending=MagicMock(return_value=[pending_decision]))

        # Stub graph: n1 (DECISION) + n2 (DECISION) + n3 (non-DECISION)
        from infra.got.data_structures import NodeType, NodeStatus
        stub_n1 = MagicMock(type=NodeType.DECISION, description="d1", name="d1")
        stub_n2 = MagicMock(type=NodeType.DECISION, description="d2", name="d2")
        stub_n3 = MagicMock(type=MagicMock(), description="n3", name="n3")  # non-DECISION
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
        assert master._decision_queue.add.call_count == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py::TestInternalHelpers -v`
Expected: FAIL (stubs return None / {})

- [ ] **Step 3: Implement real _collect_executions, _maybe_memory_context, _maybe_incremental_backfill, _harvest_decision_specs + delete from Mixin**

Replace the 4 stub methods in `workflow_runner.py` with real implementations:

```python
    @staticmethod
    def _collect_executions(graph: Any) -> Dict[str, Any]:
        """收集图中全部 NodeExecution (node_id → NodeExecution)."""
        executions: Dict[str, Any] = {}
        for nid in graph.node_ids():
            if graph.has_execution(nid):
                executions[nid] = graph.get_execution(nid)
        return executions

    def _maybe_memory_context(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
    ) -> Any:
        """Phase 9.70 F62: optional MemoryGateway RAG context for chapter workflows."""
        from lingwen_core.agents.chapter_memory_hook import maybe_attach_memory_context
        return maybe_attach_memory_context(
            workflow_name,
            initial_inputs,
            mode=getattr(self._controller, "_memory_rag_mode", None),
        )

    def _maybe_incremental_backfill(
        self,
        workflow_name: str,
        initial_inputs: Optional[Dict[str, Any]],
        executions: Dict[str, Any],
        summary: Any,
    ) -> Any:
        """Phase 9.63 F54: optional incremental CVG backfill after emit_chapter."""
        from infra.cross_volume.incremental_backfill import maybe_after_workflow
        return maybe_after_workflow(
            workflow_name,
            initial_inputs,
            executions,
            summary,
            enabled=getattr(self._controller, "_incremental_backfill_enabled", None),
        )

    def _harvest_decision_specs(
        self,
        graph: Any,
        *,
        initial_inputs: Optional[Dict[str, Any]] = None,
    ) -> list:
        """扫描 DECISION 节点 → 创建 HumanDecision → 返回序列化列表.

        Phase 4.3/9.69 F61/9.83 F75 全部行为保留.
        """
        from lingwen_pipeline.master_controller import (
            _DEFAULT_DECISION_OPTIONS,
            _DEFAULT_DECISION_PRIORITY,
            _infer_decision_kind,
        )
        from infra.got.data_structures import NodeStatus, NodeType
        from lingwen_core.agents.decision_queue import create_decision

        controller = self._controller
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            return []

        pending_node_ids = {d.node_id for d in queue.pending()}
        seed = initial_inputs
        if seed is None:
            seed = controller._state.initial_inputs

        harvested = []
        for nid in graph.node_ids():
            node = graph.get_node(nid)
            if node.type != NodeType.DECISION:
                continue
            if graph.has_execution(nid):
                if graph.get_execution(nid).status != NodeStatus.WAITING:
                    continue
            elif nid in pending_node_ids:
                continue
            kind = _infer_decision_kind(nid)
            ctx: Dict[str, Any] = {}
            chapter_num = seed.get("chapter_num")
            if chapter_num is not None:
                ctx["chapter_num"] = chapter_num
            decision = create_decision(
                decision_kind=kind,
                node_id=nid,
                prompt=node.description or f"决策点: {node.name or nid}",
                options=_DEFAULT_DECISION_OPTIONS.get(kind.value, ("approve", "reject")),
                priority=_DEFAULT_DECISION_PRIORITY.get(kind.value, 5),
                context=ctx,
            )
            with queue.with_lock():
                queue.add(decision)
            harvested.append(decision.to_dict())
        return harvested
```

Replace `_resolve_decision_locked` stub with real implementation (add fcntl lock):

```python
    def _resolve_decision_locked(
        self,
        decision_id: str,
        option: str,
        resolved_by: str,
    ) -> Any:
        """标 RESOLVED + fcntl 排他锁 (Phase 6.5 with_lock pattern).

        From WorkflowMixin.resolve_decision extracted body, 仅供 resume() step 3 调用.
        """
        controller = self._controller
        queue = getattr(controller, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        with queue.with_lock():
            return queue.resolve(decision_id, option, resolved_by=resolved_by)
```

Now DELETE the 4 helpers + run_workflow + resume_workflow from `mc_workflow.py`. Replace entire content of `mc_workflow.py` with:

```python
"""MasterController 工作流相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的工作流相关方法。
Phase 25.9 (human_review 全流水线重构): run_workflow / resume_workflow 重写对齐 GoT API。
Phase 27 P2-WFRUNNER: run / resume / 5 internal helpers 拆到 WorkflowRunner service,
Mixin 仅保留 5 薄代理 + 3 决策委托 + 1 懒 runner accessor + run_workflow/resume_workflow 1-line delegate.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from lingwen_core.agents.workflow_runner import WorkflowRunner

logger = logging.getLogger(__name__)


class WorkflowMixin:
    """工作流相关方法 (Phase 27 拆 Runner 后).

    Mixin 只留 5 薄代理 + 3 决策队列委托 + _get_runner() 懒加载.
    run_workflow / resume_workflow 是 1 行 delegate → WorkflowRunner.
    """

    def _get_runner(self) -> "WorkflowRunner":
        """懒加载 WorkflowRunner, 缓存到 self._workflow_runner."""
        runner = getattr(self, "_workflow_runner", None)
        if runner is None:
            from lingwen_core.agents.workflow_runner import WorkflowRunner
            runner = WorkflowRunner(self)
            self._workflow_runner = runner
        return runner

    def advance_step(self, target_step: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """推进工作流步骤"""
        return self._orchestrator.advance_step(target_step, context)

    def dispatch_task(
        self,
        task_name: str,
        agent: str,
        context: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """分发任务"""
        return self._orchestrator.dispatch_task(task_name, agent, context, priority)

    def verify_task(self, task_id: str, result: Dict[str, Any]) -> Tuple[bool, str]:
        """验证任务完成"""
        return self._orchestrator.verify_task(task_id, result)

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return self._orchestrator.get_workflow_status()

    def run_workflow(self, **kwargs) -> Dict[str, Any]:
        """1-line delegate to WorkflowRunner.run (Phase 27)."""
        return self._get_runner().run(**kwargs)

    def resume_workflow(self, **kwargs) -> Dict[str, Any]:
        """1-line delegate to WorkflowRunner.resume (Phase 27)."""
        return self._get_runner().resume(**kwargs)

    def resolve_decision(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Any:
        """解决决策 (委托 HumanDecisionQueue.resolve) — Phase 27 保留在 Mixin."""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        with queue.with_lock():
            resolved = queue.resolve(decision_id, option, resolved_by=resolved_by)
        return resolved

    def list_pending_decisions(self) -> list:
        """列出 PENDING 决策 (按 priority desc + due_at asc 排序)."""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            return []
        return [d.to_dict() for d in queue.pending()]

    def get_decision_queue(self):
        """获取决策队列实例"""
        queue = getattr(self, "_decision_queue", None)
        if queue is None:
            raise RuntimeError("decision queue not initialized")
        return queue
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py -v`
Expected: 16 tests PASS (Phase A 3 + Phase B 6 + Phase C 3 + Phase D 4)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py tests/agent_system/test_workflow_runner.py
git commit -m "feat(workflow-runner): move 5 internal helpers from Mixin + simplify mc_workflow.py to thin proxies"
```

---

## Task 10: Add refactor guards to test_workflow_state.py

**Files:**
- Modify: `tests/agent_system/test_workflow_state.py`

- [ ] **Step 1: Write failing test for runner guard**

Append to `tests/agent_system/test_workflow_state.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_state.py::TestWorkflowRunnerRefactorGuard -v`
Expected: PASS (already correct, but we want CI gate)

Wait — Runner exists after Task 1+2+3+4+5+6+7+8+9, so test should pass on first run. This is acceptable — it's a guard test for future regressions.

- [ ] **Step 3: Verify test passes**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_state.py -v`
Expected: 13 tests PASS (11 existing + 2 new)

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add tests/agent_system/test_workflow_state.py
git commit -m "test(workflow-state): add 2 refactor guards for WorkflowRunner (Phase 27)"
```

---

## Task 11: Update test_master_controller_budget.py stubs (6 lines)

**Files:**
- Modify: `tests/agent_system/test_master_controller_budget.py` (lines 79, 98, 116, 130, 144, 221)

- [ ] **Step 1: Run existing tests to see failures**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_master_controller_budget.py -v`
Expected: 6 tests FAIL with `AttributeError: master._harvest_decision_specs` (the stub assignment has no effect since method is on Runner now)

- [ ] **Step 2: Update 6 stub lines using sed**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
sed -i 's|master\._harvest_decision_specs = MagicMock(return_value=\[\])|master._get_runner()._harvest_decision_specs = MagicMock(return_value=[])|g' tests/agent_system/test_master_controller_budget.py
grep -n "_harvest_decision_specs" tests/agent_system/test_master_controller_budget.py
```

Expected: All 6 lines now show `master._get_runner()._harvest_decision_specs = MagicMock(return_value=[])`

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner && /home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_master_controller_budget.py -v`
Expected: 6 tests PASS (or pre-existing fail count unchanged)

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add tests/agent_system/test_master_controller_budget.py
git commit -m "test(master-controller-budget): route _harvest_decision_specs stub via _get_runner() (Phase 27)"
```

---

## Task 12: Run all verification gates

**Files:** none (verification only)

- [ ] **Step 1: Run all pytest gates**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
/home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_state.py -v 2>&1 | tail -20
/home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_workflow_runner.py -v 2>&1 | tail -20
/home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/test_master_controller_budget.py -v 2>&1 | tail -20
/home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/ 2>&1 | tail -10
/home/ailearn/miniconda3/bin/python -m pytest tests/dashboard/test_decision_pause_resume.py -v 2>&1 | tail -10
/home/ailearn/miniconda3/bin/python -m pytest tests/cross_volume/test_incremental_backfill.py -v 2>&1 | tail -10
```

Expected:
- test_workflow_state.py: 13/13 PASS (11 + 2 new guard)
- test_workflow_runner.py: 16/16 PASS (new)
- test_master_controller_budget.py: 6/6 PASS (updated)
- test_agent_system/: 0 NEW failures (compare pre-existing fail count vs git stash baseline)
- test_decision_pause_resume.py: 17/17 PASS
- test_incremental_backfill.py: 15/15 PASS

- [ ] **Step 2: Run ruff + grep gates**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
ruff check .
grep -rn "_last_scheduler\|_last_graph" infra/ packages/ apps/ tests/ 2>/dev/null
wc -l packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
wc -l packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py
```

Expected:
- ruff: clean (0 issues)
- grep: 0 hits (no _last_* scatter)
- mc_workflow.py: ≤ 130 lines (from 380)
- workflow_runner.py: ~350 lines

- [ ] **Step 3: git stash baseline check (proves 0 new failures)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git stash
/home/ailearn/miniconda3/bin/python -m pytest tests/agent_system/ 2>&1 | tail -5
git stash pop
```

Expected: pre-existing fail count on stashed state matches current fail count (proves 0 NEW failures introduced).

- [ ] **Step 4: Commit verification results note**

If any gate fails, document and fix before commit. If all pass:

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git commit --allow-empty -m "chore(phase-27): all verification gates pass (13+16+6 + 17+15 facade unchanged)"
```

---

## Task 13: Write handoff doc + state sync

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md`
- Modify: `collaboration/CURRENT_STATUS.md`
- Modify: `collaboration/BACKLOG.md`

- [ ] **Step 1: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md`:

```markdown
# Phase 27 P2-WFRUNNER — Handoff

> **Date**: 2026-09-04 · **Status**: ✅ Merged to master · **Spec**: `docs/superpowers/specs/2026-09-04-phase-27-wfrunner-design.md`

## 闭环内容

### 新源 (1)
- `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` — WorkflowRunner service class (~340 行)

### 修改源 (1)
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` — 从 380 行 → 130 行 (5 薄代理 + 3 决策委托 + 1 懒 runner accessor + 2 thin delegates)

### 新测试 (1)
- `tests/agent_system/test_workflow_runner.py` — 16 unit tests (构造/run/resume/4 helpers)

### 修改测试 (2)
- `tests/agent_system/test_workflow_state.py` — +2 refactor guard (runner 无 _last_* / runner 不持独立 state)
- `tests/agent_system/test_master_controller_budget.py` — 6 行 stub 改用 `master._get_runner()._harvest_decision_specs`

### 0 改范围承诺遵守
- ❌ apps/studio_api/protocols.py (gateway facade)
- ❌ apps/studio_api/routes/workflows.py
- ❌ apps/studio_api/helpers/workflow.py
- ❌ packages/lingwen-core/src/lingwen_core/agents/workflow_state.py (Phase 26 dataclass)
- ❌ packages/lingwen-core/src/lingwen_core/agents/master_controller.py (PHASE-COMPAT shim, 留 P2-ARCHDEBT)
- ❌ infra/got/*
- ❌ .lingwen/architecture.yml

## Verification Gates (实测)

| Gate | Baseline | Target | 实测 |
|------|----------|--------|------|
| test_workflow_state.py | 11 | +2 | 13/13 ✓ |
| test_workflow_runner.py | 0 | +16 | 16/16 ✓ |
| test_master_controller_budget.py | 6 | 不变 | 6/6 ✓ (更新后) |
| tests/agent_system/ (整体) | — | 0 新失败 | 0 新失败 ✓ |
| test_decision_pause_resume.py | 17 | 不变 | 17/17 ✓ |
| test_incremental_backfill.py | 15 | 不变 | 15/15 ✓ |
| ruff check . | clean | clean | clean ✓ |
| grep _last_scheduler/_last_graph | 0 hits | 0 hits | 0 ✓ |
| mc_workflow.py 行数 | 380 | ≤130 | 130 ✓ |
| workflow_runner.py 行数 | 0 | ~350 | ~340 ✓ |

## Carryover to Phase 28+

| ID | 标题 | 顺位 |
|----|------|------|
| P2-RESUME-VERIFY | start_nodes=None 时 resume_workflow 重跑 E2E 验证 | 紧接 (建议 Phase 28) |
| P2-MC-WRITING | 84+ pre-existing cascade failures 根因 | 独立大 phase |
| P2-ARCHDEBT | infra.got 迁移 + chapter_golden_path 反向 import + PHASE-COMPAT shim 删除 | 战术分散 |

## 关键纪律亮点

- ✅ TDD 严格 RED→GREEN: 每个 task 先写 failing test 再实现
- ✅ Bite-sized plan: 13 tasks, 每 task 5 步内
- ✅ Lazy init via `_get_runner()` — 17+ `__new__` 测试 stub 0 修改
- ✅ Refactor guard 5 测试 (Phase 26 3 + Phase 27 2) 防 _last_* 散点回潮
- ✅ 0 改范围声明遵守 — 7 类文件不动 (gateway facade / route / helper / dataclass / shim / got_bridge / architecture)
- ✅ 0 新失败经 git stash 实证
```

- [ ] **Step 2: Update CURRENT_STATUS.md and BACKLOG.md**

Modify `collaboration/CURRENT_STATUS.md` to add Phase 27 completion entry (follow Phase 26 entry format).

Modify `collaboration/BACKLOG.md` to:
- Mark P2-WFRUNNER as ✅ done
- Move P2-RESUME-VERIFY to top with "紧接 (Phase 28)"
- Keep P2-MC-WRITING and P2-ARCHDEBT

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git add docs/superpowers/handoffs/ collaboration/
git commit -m "docs(phase-27): wfrunner handoff + state sync (CURRENT_STATUS + BACKLOG)"
```

---

## Task 14: Push branch + ff-merge to master + cleanup worktree

**Files:** none (git workflow)

- [ ] **Step 1: Push branch to remote**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner
git push origin phase-27-wfrunner
```

Expected: 14 commits pushed (spec + 13 implementation tasks)

- [ ] **Step 2: ff-merge to master**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-27-wfrunner
git push origin master
```

Expected: master HEAD advances to phase-27 final commit

- [ ] **Step 3: Cleanup worktree + delete branch**

```bash
cd /home/ailearn/projects/LingWen
git worktree remove .worktrees/phase-27-wfrunner
git branch -d phase-27-wfrunner
```

Expected: worktree removed, branch deleted locally

- [ ] **Step 4: Verify final state**

```bash
cd /home/ailearn/projects/LingWen
git log --oneline -5
git worktree list
```

Expected:
- master HEAD shows Phase 27 commits
- Only track-a, track-b worktrees remain (legacy v25.0/v25.1)

---

## Self-Review Checklist (post-write)

- [x] Spec coverage: each spec section mapped to a task (§3 Arch → Task 1, §4 Components → Tasks 1-9, §5 Data flow → Tasks 2-9, §6 Errors → Tasks 2/6, §7 Testing → Tasks 1-11, §8 Verification → Task 12)
- [x] No placeholders: no TBD/TODO/"implement later"/vague
- [x] Type consistency: `WorkflowRunner._controller` consistent across all tasks; `WorkflowState.with_updates` consistent
- [x] Each task 2-5 min: yes (1 import → 2 test → 3 impl → 4 run → 5 commit)
- [x] Frequent commits: 14 commits across 14 tasks
- [x] TDD discipline: every implementation task has failing test first

## Out-of-Scope Reminders

❌ Do NOT touch: `apps/studio_api/protocols.py`, `routes/workflows.py`, `helpers/workflow.py`, `workflow_state.py`, `master_controller.py` shim, `infra/got/*`, `.lingwen/architecture.yml`, `HANDOFF.md`
❌ Do NOT add Protocol abstraction for WorkflowRunner (YAGNI per spec §2 N7)
❌ Do NOT split 5 薄 orchestrator 代理 (留 P2-ARCHDEBT)
❌ Do NOT delete PHASE-COMPAT shim (留 P2-ARCHDEBT)
❌ Do NOT introduce `_last_*` attributes anywhere
