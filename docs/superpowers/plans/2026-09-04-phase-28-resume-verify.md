# Phase 28 P2-RESUME-VERIFY Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 E2E tests to `tests/agent_system/test_workflow_runner.py` using real `GoTScheduler` + `ThoughtGraph` (not MagicMock) to verify: (a) `scheduler.run` skips already-COMPLETED nodes (idempotent), (b) `start_nodes=None` derivation persists to `state.start_nodes`, (c) `WorkflowRunner.run → resume` full cycle correctly continues from cached state.

**Architecture:** 0 source changes — Phase 27 implementation is correct (verified by spec analysis of `infra/got/graph.py:147-171` ready_nodes filter + `infra/got/scheduler.py:317-330` cache check). Phase 28 is pure test-coverage work using real GoT primitives in the test layer.

**Tech Stack:** Python 3.12+ / pytest / `infra.got.{scheduler,graph,data_structures}` / `lingwen_core.agents.workflow_runner`

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `tests/agent_system/test_workflow_runner.py` | Modify (+5 tests) | Append 5 E2E tests using real GoTScheduler + ThoughtGraph |
| `docs/superpowers/handoffs/2026-09-04-phase-28-resume-verify-handoff.md` | Create | Phase 28 handoff doc |
| `collaboration/CURRENT_STATUS.md` | Modify | v27.0 → v28.0 + Phase 28 entry |
| `collaboration/BACKLOG.md` | Modify | P2-RESUME-VERIFY ✅ |

**Files NOT touched (Phase 28 0-改范围):**
- `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` (Phase 27 deliverable, 307 lines)
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` (Phase 27 final, 119 lines)
- `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` (Phase 26 dataclass)
- `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` (Phase 27 untouched)
- `infra/got/scheduler.py` / `infra/got/graph.py` / `infra/got/data_structures.py` (verified-correct)
- `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py` (PHASE-COMPAT shim — leave for P2-ARCHDEBT)
- `apps/studio_api/protocols.py` / `apps/studio_api/routes/workflows.py` / `apps/studio_api/helpers/workflow.py` (gateway facade)
- `.lingwen/architecture.yml` / `HANDOFF.md`

---

## Task 1: Worktree setup + spec commit

**Files:**
- Worktree: `.worktrees/phase-28-resume-verify/` on branch `phase-28-resume-verify`
- Spec: `docs/superpowers/specs/2026-09-04-phase-28-resume-verify-design.md`

- [x] **Step 1: Create worktree + branch from master**

```bash
git worktree add .worktrees/phase-28-resume-verify -b phase-28-resume-verify master
```

Expected: worktree created at `HEAD = 90593350` (Phase 27 final commit).

- [x] **Step 2: Write spec + commit**

```bash
# Write file at docs/superpowers/specs/2026-09-04-phase-28-resume-verify-design.md
git add docs/superpowers/specs/2026-09-04-phase-28-resume-verify-design.md
git commit -m "docs(phase-28): resume-verify E2E design spec"
```

Expected: commit `05e4f91b` (already done).

---

## Task 2: Write test #1 — scheduler.run idempotency

**Files:**
- Modify: `tests/agent_system/test_workflow_runner.py:670+` (append new test class)

- [ ] **Step 1: Append `TestResumeE2EWithRealScheduler` class with `_build_graph_with_decision` helper**

Append at end of file (after line 670):

```python
# === Phase 28 P2-RESUME-VERIFY: E2E tests with real GoTScheduler ===

class TestResumeE2EWithRealScheduler:
    """E2E 测试 — 真实 GoTScheduler + ThoughtGraph (非 MagicMock).

    Phase 28 P2-RESUME-VERIFY: 验证 scheduler 对已 COMPLETED 节点幂等
    + start_nodes=None resume cycle (代码 review 列 important).
    """

    def _build_graph_with_decision(self) -> tuple["GoTScheduler", "ThoughtGraph"]:
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

        call_log: list[str] = []

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

        # 第二次 run: 应跳过 n1 (COMPLETED), 跳过 n2 (WAITING≠PENDING)
        summary2 = scheduler.run(start_nodes=["n1"])
        assert summary2.completed == 0  # 无新执行
        assert summary2.paused is True  # n2 仍是 WAITING
        assert summary2.paused_nodes == ("n2",)
        # call_log 不变 (n1 未重跑)
        assert scheduler._test_call_log == ["n1"]
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
uv run pytest tests/agent_system/test_workflow_runner.py::TestResumeE2EWithRealScheduler::test_scheduler_run_is_idempotent_on_completed_nodes -v
```

Expected: `1 passed`. If FAIL, the impl has a bug — STOP and investigate before proceeding.

- [ ] **Step 3: Commit**

```bash
git add tests/agent_system/test_workflow_runner.py
git commit -m "test(workflow-runner): verify scheduler.run idempotency on completed nodes (Phase 28)"
```

---

## Task 3: Write test #2 — resume continuation after DECISION

**Files:**
- Modify: `tests/agent_system/test_workflow_runner.py` (append after Task 1 test)

- [ ] **Step 1: Append `test_resume_after_decision_pause_continues_from_cached_start_nodes`**

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
uv run pytest tests/agent_system/test_workflow_runner.py::TestResumeE2EWithRealScheduler::test_resume_after_decision_pause_continues_from_cached_start_nodes -v
```

Expected: `1 passed`. If FAIL, investigate Phase 5 DECISION resume semantics.

- [ ] **Step 3: Commit**

```bash
git add tests/agent_system/test_workflow_runner.py
git commit -m "test(workflow-runner): verify resume continuation after DECISION pause (Phase 28)"
```

---

## Task 4: Write test #3 — state.start_nodes persistence

**Files:**
- Modify: `tests/agent_system/test_workflow_runner.py` (append new class `TestRunWithNoneStartNodesDerivation`)

- [ ] **Step 1: Append new class + test**

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
uv run pytest tests/agent_system/test_workflow_runner.py::TestRunWithNoneStartNodesDerivation::test_run_with_none_start_nodes_persists_derived_list_to_state -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/agent_system/test_workflow_runner.py
git commit -m "test(workflow-runner): verify start_nodes=None persistence (Phase 28)"
```

---

## Task 5: Write test #4 — resume reuses persisted start_nodes

**Files:**
- Modify: `tests/agent_system/test_workflow_runner.py` (append after Task 4 test in `TestRunWithNoneStartNodesDerivation`)

- [ ] **Step 1: Append test**

```python
    def test_resume_reuses_start_nodes_persisted_during_run_with_none(self) -> None:
        """run(start_nodes=None) 后 resume 复用 derived start_nodes (非 graph 重推导).

        关键验证: 即使 graph 结构变了 (e.g. 新增 root node), resume 仍用 run 时缓存的
        start_nodes — 不重推导, 不重跑已执行节点.
        """
        from infra.got.data_structures import NodeType, ThoughtNode
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import ComputeResult, GoTScheduler

        # Setup real graph: n1 root + n2 DECISION + n3 dep + n4 NEW root (post-resume)
        graph = ThoughtGraph()
        graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, name="gen1", description="gen1", depends_on=()))
        graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, name="dec", description="dec", depends_on=("n1",)))
        graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, name="gen3", description="gen3", depends_on=("n2",)))

        call_log: list[str] = []

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
            # The point: resume should use cached ["n1"], not re-derive ["n1", "n4"]

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

            # 4) resume — 应复用 cached ["n1"] (skip n1 已 COMPLETED), 跑 n3
            summary = runner.resume(decision_id="d1", option="approve")
            # n1 skip (COMPLETED) + n2 skip (COMPLETED via resume) + n3 execute
            assert summary["summary"].completed == 1
            # call_log: n1 (run) + n3 (resume) — n4 NOT executed (resume uses cached start_nodes)
            assert call_log == ["n1", "n3"]
            # state.start_nodes 应保持 ["n1"] (不被 n4 污染)
            assert list(master._state.start_nodes) == ["n1"]
        finally:
            got_bridge.build_got_scheduler = original
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
uv run pytest tests/agent_system/test_workflow_runner.py::TestRunWithNoneStartNodesDerivation::test_resume_reuses_start_nodes_persisted_during_run_with_none -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/agent_system/test_workflow_runner.py
git commit -m "test(workflow-runner): verify resume reuses cached start_nodes (Phase 28)"
```

---

## Task 6: Write test #5 — full WorkflowRunner.run→resume cycle E2E

**Files:**
- Modify: `tests/agent_system/test_workflow_runner.py` (append after Task 5 test)

- [ ] **Step 1: Append test**

```python
    def test_workflow_runner_resume_e2e_full_cycle(self) -> None:
        """完整 WorkflowRunner.run(start_nodes=None) → DECISION pause → resume 验证 4 不变量:

        1. start_nodes=None → derived list ["n1"]
        2. state.start_nodes caches derived list
        3. resume_workflow uses cached start_nodes (not re-derive)
        4. scheduler.run idempotent on completed nodes (n1 skipped on second call)
        """
        from infra.got.data_structures import NodeType, ThoughtNode
        from infra.got.graph import ThoughtGraph
        from infra.got.scheduler import ComputeResult, GoTScheduler

        graph = ThoughtGraph()
        graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, name="gen1", description="gen1", depends_on=()))
        graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, name="dec", description="dec", depends_on=("n1",)))
        graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, name="gen3", description="gen3", depends_on=("n2",)))

        call_log: list[str] = []

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
            runner._harvest_decision_specs = MagicMock(return_value=[])

            # === Phase A: run(start_nodes=None) — DECISION pause ===
            result1 = runner.run(workflow_name="test", start_nodes=None)
            # 不变量 1: start_nodes=None → derived ["n1"]
            assert list(master._state.start_nodes) == ["n1"]
            # 不变量 2: summary 显示 n2 paused
            assert result1["summary"].paused_nodes == ("n2",)
            # call_log: n1 执行 (n2 DECISION pause 不调 compute)
            assert call_log == ["n1"]

            # === Phase B: setup decision_queue for resume ===
            master._decision_queue = MagicMock(
                pending=MagicMock(return_value=[]),
                add=MagicMock(),
                get=MagicMock(return_value=MagicMock(node_id="n2")),
                resolve=MagicMock(return_value="RESOLVED_OBJ"),
                with_lock=MagicMock(
                    return_value=MagicMock(
                        __enter__=MagicMock(return_value=MagicMock()),
                        __exit__=MagicMock(return_value=False),
                    )
                ),
            )
            runner._harvest_decision_specs = MagicMock(return_value=[])

            # === Phase C: resume — 复用 cached start_nodes + 跳过已执行节点 ===
            result2 = runner.resume(decision_id="d1", option="approve")
            # 不变量 3: resume 使用 cached start_nodes ["n1"]
            assert list(master._state.start_nodes) == ["n1"]
            # 不变量 4: scheduler 跳过 n1, 跑 n3 (n2 DECISION 不调 compute)
            assert result2["summary"].completed == 1
            assert result2["resolved_decision"] == "RESOLVED_OBJ"
            # call_log: n1 + n3 (n1 不重跑 — ready_nodes 排除 COMPLETED 节点)
            assert call_log == ["n1", "n3"]
            assert result2["summary"].paused is False
        finally:
            got_bridge.build_got_scheduler = original
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
uv run pytest tests/agent_system/test_workflow_runner.py::TestResumeE2EWithRealScheduler::test_workflow_runner_resume_e2e_full_cycle -v
```

Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add tests/agent_system/test_workflow_runner.py
git commit -m "test(workflow-runner): verify full run→resume cycle E2E (Phase 28)"
```

---

## Task 7: Run 10 verification gates

**Files:** None modified

- [ ] **Step 1: Run G1 (test_workflow_state)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
uv run pytest tests/agent_system/test_workflow_state.py -v
```

Expected: `13 passed` (11 Phase 26 + 2 Phase 27 refactor guards).

- [ ] **Step 2: Run G2 (test_workflow_runner — now 21 + 5 = 26 tests)**

```bash
uv run pytest tests/agent_system/test_workflow_runner.py -v
```

Expected: `26 passed` (21 Phase 27 + 5 Phase 28).

- [ ] **Step 3: Run G3 (test_master_controller_budget)**

```bash
uv run pytest tests/agent_system/test_master_controller_budget.py -v
```

Expected: `6 passed` (target tests; 2 pre-existing FileNotFoundError out of scope).

- [ ] **Step 4: Run G4 (tests/agent_system — full directory)**

```bash
uv run pytest tests/agent_system/ -v
```

Expected: same 84 fail count as master baseline (0 NEW failures). New 5 tests all PASS.

- [ ] **Step 5: Run G5 (test_decision_pause_resume — gateway facade)**

```bash
uv run pytest tests/got/test_decision_pause_resume.py -v
```

Expected: `17 passed` (Phase 27 baseline unchanged).

- [ ] **Step 6: Run G6 (test_incremental_backfill)**

```bash
uv run pytest tests/cross_volume/test_incremental_backfill.py -v
```

Expected: `15 passed`.

- [ ] **Step 7: Run G7 (ruff check)**

```bash
ruff check .
```

Expected: clean.

- [ ] **Step 8: Run G8 (grep _last_* scatter)**

```bash
grep -rn "_last_scheduler\|_last_graph\|_last_workflow_name\|_last_start_nodes\|_last_initial_inputs\|_last_incremental_backfill\|_last_memory_context" packages/ apps/ tests/ 2>/dev/null
```

Expected: `0 hits` (excluding test_workflow_state.py refactor guard file).

- [ ] **Step 9: Run G9 (mc_workflow.py line count)**

```bash
wc -l packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
```

Expected: `119` (Phase 27 final, unchanged).

- [ ] **Step 10: Run G10 (workflow_runner.py line count)**

```bash
wc -l packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py
```

Expected: `307` (Phase 27 final, unchanged — Phase 28 is test-only).

- [ ] **Step 11: If any gate fails, STOP and investigate**

Do not proceed to Task 8 with failing tests.

---

## Task 8: Write handoff doc

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-04-phase-28-resume-verify-handoff.md`

- [ ] **Step 1: Write handoff doc**

```markdown
# Phase 28 P2-RESUME-VERIFY — Handoff

> **Date**: 2026-09-04 · **Status**: ✅ All tasks complete · **Spec**: `docs/superpowers/specs/2026-09-04-phase-28-resume-verify-design.md` · **Plan**: `docs/superpowers/plans/2026-09-04-phase-28-resume-verify.md`

## 闭环内容

### 测试增量 (5 tests)

`tests/agent_system/test_workflow_runner.py` 追加 2 新 test classes:

#### `TestResumeE2EWithRealScheduler` (3 tests)
- `test_scheduler_run_is_idempotent_on_completed_nodes` — 真实 GoTScheduler.run() 二次调用不重跑 COMPLETED n1 (验证 `infra/got/graph.py:152-155` ready_nodes 排除)
- `test_resume_after_decision_pause_continues_from_cached_start_nodes` — DECISION pause → resume → run: 下游执行, 已执行节点跳过
- `test_workflow_runner_resume_e2e_full_cycle` — WorkflowRunner.run(start_nodes=None) → DECISION pause → resume 完整 4 不变量

#### `TestRunWithNoneStartNodesDerivation` (2 tests)
- `test_run_with_none_start_nodes_persists_derived_list_to_state` — state.start_nodes 缓存 derived list ["n1"]
- `test_resume_reuses_start_nodes_persisted_during_run_with_none` — resume 复用 ["n1"], 不被 graph mutation (新增 n4 root) 污染

### 0 改范围承诺遵守
- ❌ `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` (307 行, 不动)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` (119 行, 不动)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` (Phase 26 dataclass, 不动)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` (Phase 27 不动)
- ❌ `infra/got/{scheduler,graph,data_structures}.py` (验证正确)
- ❌ gateway facade / route / helper / master_controller shim / architecture.yml / HANDOFF*

## Verification Gates (实测)

| Gate | 实测 |
|------|------|
| G1 test_workflow_state.py | 13/13 ✓ (UNCHANGED) |
| G2 test_workflow_runner.py | 26/26 ✓ (21 Phase 27 + 5 Phase 28) |
| G3 test_master_controller_budget.py | 6/6 target ✓ (UNCHANGED) |
| G4 tests/agent_system/ | 84 fail baseline (0 NEW, 5 new PASS) ✓ |
| G5 test_decision_pause_resume.py | 17/17 ✓ (UNCHANGED) |
| G6 test_incremental_backfill.py | 15/15 ✓ (UNCHANGED) |
| G7 ruff check | clean ✓ |
| G8 grep _last_* scatter | 0 hits ✓ |
| G9 mc_workflow.py | 119 lines (UNCHANGED) ✓ |
| G10 workflow_runner.py | 307 lines (UNCHANGED — Phase 28 是 test-only) ✓ |

## 关键纪律亮点

- ✅ TDD 严格 RED→GREEN：每 test = write → run → verify PASS → commit
- ✅ 0 改范围声明遵守 — 9 类文件不动 (workflow_runner / mc_workflow / workflow_state / got_bridge / infra.got / graph / shim / facade / HANDOFF)
- ✅ 真实 GoTScheduler + ThoughtGraph (非 MagicMock) — 验证 scheduler 真实行为, not 参数传递
- ✅ 代码 review 关注点 (scheduler 幂等) 经实证 PASS, 提供回归保险

## Carryover to Phase 29+

| ID | 标题 | 顺位 |
|----|------|------|
| P2-MC-WRITING | 84+ pre-existing cascade failures 根因 | 独立大 phase |
| P2-ARCHDEBT | infra.got 迁移 + chapter_golden_path 反向 import + 5 薄代理 → OrchestratorProxyMixin + 删 PHASE-COMPAT shim | 战术分散 |

## Branch / Worktree

- Branch: `phase-28-resume-verify`
- Worktree: `/home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify/`
- Master HEAD: `90593350` (Phase 27 final)
- Commits: 1 spec + 5 tests = 6 commits total
```

- [ ] **Step 2: Commit handoff**

```bash
git add docs/superpowers/handoffs/2026-09-04-phase-28-resume-verify-handoff.md
git commit -m "docs(phase-28): resume-verify handoff"
```

---

## Task 9: State sync (CURRENT_STATUS + BACKLOG)

**Files:**
- Modify: `collaboration/CURRENT_STATUS.md`
- Modify: `collaboration/BACKLOG.md`

- [ ] **Step 1: Update CURRENT_STATUS.md — add v28.0 entry**

Insert after v27.0 line:

```markdown
| **v28.0 P2-RESUME-VERIFY** | Phase 28 branch `phase-28-resume-verify` 6 commits (05e4f91b spec + 5 tests). 0 改范围 9 类文件不动。新增 5 E2E 测试用真实 GoTScheduler + ThoughtGraph (非 MagicMock): 3 个 `TestResumeE2EWithRealScheduler` (scheduler 幂等 + DECISION resume continuation + full cycle), 2 个 `TestRunWithNoneStartNodesDerivation` (state.start_nodes 持久化 + resume 复用不被 graph mutation 污染). 代码 review 重要缺口 (`scheduler 对已完成节点是否幂等无测试覆盖`) 经实证 PASS — `infra/got/graph.py:152-155` ready_nodes 排除 status≠PENDING 节点 → scheduler.run 二次调用自动 skip 已 COMPLETED 节点. **Verification gates**: 10 gates 全过 (G4 84 fail baseline 不变 + 5 NEW PASS). **Carryover**: P2-MC-WRITING (独立大 phase) / P2-ARCHDEBT (战术分散). **Handoff**: `docs/superpowers/handoffs/2026-09-04-phase-28-resume-verify-handoff.md` | ✅ G1 test_workflow_state 13/13 (UNCHANGED) / G2 test_workflow_runner 26/26 (21 + 5) / G3 test_master_controller_budget 6/6 target (UNCHANGED) / G4 tests/agent_system 84 fail baseline + 5 NEW PASS / G5 test_decision_pause_resume 17/17 (UNCHANGED) / G6 test_incremental_backfill 15/15 (UNCHANGED) / G7 ruff clean / G8 grep 0 hits / G9 mc_workflow 119 lines (UNCHANGED) / G10 workflow_runner 307 lines (UNCHANGED) |
```

Also update header to v28.0:

```markdown
> **更新者**: 协调者（v28.0 P2-RESUME-VERIFY 闭环；6 commits 待 ff-merge；carryover 2 项 → Phase 29+）
```

- [ ] **Step 2: Update BACKLOG.md — mark P2-RESUME-VERIFY ✅**

Change line 51:

```markdown
| ~~P2-RESUME-VERIFY~~ | ✅ Phase 28 DONE (2026-09-04) — see handoff | ... |
```

- [ ] **Step 3: Commit state sync**

```bash
git add collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md
git commit -m "chore(phase-28): state sync (CURRENT_STATUS + BACKLOG)"
```

---

## Task 10: Push + ff-merge + cleanup

**Files:** None modified

- [ ] **Step 1: Push branch to origin**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify
git push -u origin phase-28-resume-verify
```

Expected: branch pushed (per solo workflow, no PR).

- [ ] **Step 2: Merge to master (ff-only per solo workflow)**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-28-resume-verify
git push origin master
```

Expected: master HEAD advances by 6 commits.

- [ ] **Step 3: Delete worktree + branch**

```bash
cd /home/ailearn/projects/LingWen
git worktree remove .worktrees/phase-28-resume-verify
git branch -d phase-28-resume-verify
git push origin --delete phase-28-resume-verify
```

Expected: worktree removed, no worktrees/phase-28-resume-verify listed in `git worktree list`.

- [ ] **Step 4: Verify master state**

```bash
git log --oneline -7
git worktree list
```

Expected:
- master HEAD = (Phase 28 final commit, 6 ahead of 90593350)
- worktree list shows only master + (possibly leftover phase-25-9 / track-a / track-b)

---

## Self-Review

**Spec coverage check:**
- [x] G1 (E2E tests with real scheduler) → Tasks 2, 3, 6
- [x] G2 (start_nodes=None cycle test) → Task 6
- [x] G3 (0 source changes) → Tasks 2-6 modify only test file
- [x] G4 (0 new failures) → Task 7 G4 gate
- [x] G5 (0 改范围) → Tasks 8, 9 explicitly exclude source files
- [x] G6 (TDD discipline) → Each task = write → run → verify → commit

**Placeholder scan:** No "TBD"/"TODO"/"implement later" — all code complete.

**Type consistency:**
- `_test_call_log` used consistently across Tests 1, 2
- `MasterController.__new__(MasterController)` pattern matches existing tests
- `WorkflowState.empty()` + `with_updates` pattern matches Phase 26 dataclass
- `got_bridge.build_got_scheduler` monkeypatch pattern matches existing tests

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-04-phase-28-resume-verify.md`. **Inline execution chosen** (small phase, sequential test commits) — proceeding with `superpowers:executing-plans` skill.