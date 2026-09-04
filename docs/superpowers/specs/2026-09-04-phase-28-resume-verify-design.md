# Phase 28 P2-RESUME-VERIFY — `start_nodes=None` Resume E2E Verification Design Spec

> **Author**: Phase 28 brainstorm session · **Date**: 2026-09-04
> **Status**: Draft (carryover from Phase 27 N3)
> **Predecessor**: Phase 27 P2-WFRUNNER (`docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md`)
> **Carryover source**: Phase 27 handoff P2-RESUME-VERIFY entry (BACKLOG.md)

## 1. Context (Why)

Phase 27 P2-WFRUNNER 闭环把 `run_workflow` / `resume_workflow` 从 `WorkflowMixin` 拆到 `WorkflowRunner` service (307 行)，新增 21 个 unit tests。spec N3 显式 carryover：

> **N3** | `start_nodes=None` 时 resume_workflow 重跑行为 E2E 验证 | 独立 P2-RESUME-VERIFY phase (建议 Phase 28)

Phase 27 边界表（同 spec §6.2）：

> | `start_nodes=None` 时 resume 重跑行为 | carryover **P2-RESUME-VERIFY** 标记 | ⚠️ 不在本 phase（独立 Phase 28）；Phase 27 仅保证行为不变 |

BACKLOG.md 复述：

> P2-RESUME-VERIFY | start_nodes=None 时 resume_workflow 重跑 E2E 验证 | **代码 review 列为 important**。**scheduler 对已完成节点是否幂等无测试覆盖**

代码 review (Phase 27) 关键缺口：

1. `run_workflow(start_nodes=None)` 通过 graph 推导得到 root 节点列表，缓存到 `controller._state.start_nodes`（via `WorkflowState.with_updates`）。
2. `resume_workflow(decision_id, option)` 从 `controller._state.start_nodes` 读回此列表，传给 `scheduler.run(start_nodes=...)`。
3. **`scheduler.run` 对已 COMPLETED 节点是否幂等** —— 没有 E2E 测试验证。

代码 review 担忧场景：

| 场景 | 现状（推演） | 风险 |
|------|------------|------|
| DECISION pause → resume → scheduler.run([n1, n2]) | `graph.ready_nodes()` 已 exclude status≠PENDING 的节点（`infra/got/graph.py:152-155`） | **预期幂等** —— 但无测试实证 |
| `start_nodes` 包含 graph 推导 root 节点 + 已 COMPLETED DECISION | DECISION 节点已被 `scheduler.resume` 改 COMPLETED（含 option output） | 预期 ready_nodes 不再返回它 |
| `start_nodes` 包含 cache hit 节点 | `scheduler._run_node` cache 检查命中 → 复用（`infra/got/scheduler.py:317-330`） | **预期 cache 命中** —— 但无测试实证 |
| run 中途 raise → finally budget reset → 下次 run 接续 | Phase 8.8/8.12 不变量由现有 test_run_resets_current_budget_usd_in_finally_even_on_raise 覆盖 | ✓ 已有测试 |

## 2. Goals & Non-Goals

### Goals (in scope)

| ID | 目标 |
|----|------|
| G1 | 添加 2 个 E2E 测试，用**真实 `GoTScheduler` + `ThoughtGraph`**（非 MagicMock），覆盖 `scheduler.run` 对已 COMPLETED 节点的幂等行为 |
| G2 | 添加 1 个 E2E 测试覆盖 `WorkflowRunner.run → resume` 完整 cycle：用真实 scheduler + 真实 DECISION pause + 真实 resume |
| G3 | 0 源码改动 —— Phase 27 实现不动，仅补测试 |
| G4 | 0 新失败 —— 新测试必须 PASS（RED→GREEN）；现有 84 pre-existing cascade failures 不变 |
| G5 | 0 改范围 —— 不动 gateway facade / WorkflowRunner / scheduler / graph / phase 27 dataclass / phase 26 refactor guards / phase 25.9 还原 |
| G6 | TDD 严格 RED→GREEN —— 先写 failing test，再验证 GREEN |

### Non-Goals (out of scope, 显式不做)

| ID | 不做 | 去向 |
|----|------|------|
| N1 | 改 `WorkflowRunner.run` / `resume` 实现 | ✓ Phase 27 闭环已 OK |
| N2 | 改 `GoTScheduler` / `ThoughtGraph` / `resume` API | 同上 |
| N3 | 改 `mc_workflow.py` / `WorkflowMixin` | 同上 |
| N4 | 修 84 pre-existing cascade failures | 留 P2-MC-WRITING |
| N5 | 迁 `infra.got.*` 到 `packages/lingwen-got/` | 留 P2-ARCHDEBT |
| N6 | 5 薄 orchestrator 代理拆分 | 留 P2-ARCHDEBT |
| N7 | 删 stale PHASE-COMPAT shim (`master_controller.py`) | 留 P2-ARCHDEBT |
| N8 | 重构现有 MagicMock-based unit tests 为真实 scheduler | YAGNI —— 现有 unit tests 已足够测单步行为；E2E 仅补缺口 |

## 4. Test Surface Design

### 4.1 测试策略：MagicMock unit tests → 真实 scheduler E2E

现有 `tests/agent_system/test_workflow_runner.py` 用 `MagicMock` 模拟 scheduler（line 67-72 等）：

```python
stub_node = MagicMock(depends_on=[])
stub_graph = MagicMock(
    node_ids=lambda: [],
    get_node=MagicMock(return_value=stub_node),
    has_execution=lambda _: False,
    get_execution=lambda _: None,
)
stub_scheduler = MagicMock(run=MagicMock(return_value=MagicMock()))
got_bridge.build_got_scheduler = MagicMock(return_value=(stub_scheduler, stub_graph))
```

**MagicMock 缺陷**：测 `WorkflowRunner` 行为时不验证 scheduler 真实语义 —— 仅验证"WorkflowRunner 调 scheduler.run 时传的参数"。

**Phase 28 补缺**：用真实 `GoTScheduler` + `ThoughtGraph` 测**scheduler 本身对已 COMPLETED 节点的幂等** + `WorkflowRunner.run → resume` cycle。

### 4.2 测试文件结构

新测试加在 `tests/agent_system/test_workflow_runner.py` 末尾（与现有 21 tests 同文件，避免拆分）：

```python
class TestResumeE2EWithRealScheduler:
    """E2E 测试 — 真实 GoTScheduler + ThoughtGraph (非 MagicMock).

    Phase 28 P2-RESUME-VERIFY: 验证 start_nodes=None resume cycle
    + scheduler 对已完成节点幂等 (代码 review 列 important).
    """

    def _build_graph_with_decision(self) -> tuple[GoTScheduler, ThoughtGraph]:
        """构建 4-节点图: n1 (GENERATION) → n2 (DECISION) → n3 (GENERATION) → n4 (OUTPUT).

        compute_fn lambda 简单递增计数器验证执行次数.
        """
        ...

    def test_scheduler_run_is_idempotent_on_completed_nodes(self) -> None:
        """scheduler.run(start_nodes=[n1]) 二次调用时 n1 不重跑 (ready_nodes 排除已执行节点)."""

    def test_resume_after_decision_pause_continues_from_cached_start_nodes(self) -> None:
        """DECISION pause → scheduler.resume → scheduler.run(start_nodes): 下游节点执行,已执行节点跳过."""

    def test_workflow_runner_resume_e2e_full_cycle(self) -> None:
        """WorkflowRunner.run(start_nodes=None) → DECISION pause → WorkflowRunner.resume()
        → 完整 cycle, 验证 start_nodes=None 推导 + 缓存 + resume 复用 + 已执行节点不重跑."""


class TestRunWithNoneStartNodesDerivation:
    """E2E 验证 start_nodes=None 推导 + 持久化 + resume 复用."""

    def test_run_with_none_start_nodes_persists_derived_list_to_state(self) -> None:
        """run(workflow_name, start_nodes=None) 后 state.start_nodes == derived list."""

    def test_resume_reuses_start_nodes_persisted_during_run_with_none(self) -> None:
        """run(start_nodes=None) 后续 resume 复用 derived start_nodes (非 graph 重推导)."""
```

### 4.3 测试 Fixture：`_build_graph_with_decision`

4 节点链式图 + 简单 lambda compute_fn：

```python
def _build_graph_with_decision(self) -> tuple[GoTScheduler, ThoughtGraph]:
    graph = ThoughtGraph()
    graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, name="gen1", description="gen1", depends_on=()))
    graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, name="decision", description="decision", depends_on=("n1",)))
    graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, name="gen2", description="gen2", depends_on=("n2",)))
    graph.add_node(ThoughtNode(node_id="n4", type=NodeType.OUTPUT, name="out", description="out", depends_on=("n3",)))

    call_log: list[str] = []

    def compute_fn(node, inputs):
        call_log.append(node.node_id)
        return ComputeResult(output={"node": node.node_id, "input_keys": list(inputs.keys())}, cost_tokens=1)

    scheduler = GoTScheduler(graph, compute_fn=compute_fn, max_backtracks=0)
    # 暴露 call_log 给测试用 (monkeypatch-friendly)
    scheduler._test_call_log = call_log  # type: ignore[attr-defined]
    return scheduler, graph
```

### 4.4 测试用例细节

#### Test 1: `test_scheduler_run_is_idempotent_on_completed_nodes`

```python
def test_scheduler_run_is_idempotent_on_completed_nodes(self) -> None:
    """scheduler.run(start_nodes) 二次调用不重跑已 COMPLETED 节点."""
    scheduler, _ = self._build_graph_with_decision()

    # 第一次 run: n1 执行 → n2 DECISION pause → n3/n4 未执行
    summary1 = scheduler.run(start_nodes=["n1"])
    assert summary1.completed == 1  # 仅 n1
    assert summary1.paused is True
    assert summary1.paused_nodes == ("n2",)
    # n2 此时 status=WAITING (已 record execution)

    # 第二次 run: 应跳过 n1 (COMPLETED), 跳过 n2 (WAITING≠PENDING)
    summary2 = scheduler.run(start_nodes=["n1"])
    assert summary2.completed == 0  # 无新执行
    assert summary2.paused is True  # n2 仍是 WAITING
    assert summary2.paused_nodes == ("n2",)
    # call_log 不变 (n1 未重跑)
    assert scheduler._test_call_log == ["n1"]
```

**关键验证**：`graph.ready_nodes()` (line 152-155) 排除 `status != PENDING` 节点 → 已 COMPLETED n1 不进 ready_nodes → 不重跑。

#### Test 2: `test_resume_after_decision_pause_continues_from_cached_start_nodes`

```python
def test_resume_after_decision_pause_continues_from_cached_start_nodes(self) -> None:
    """DECISION pause → resume → run(start_nodes): 下游执行, 已执行节点跳过."""
    scheduler, _ = self._build_graph_with_decision()

    # 1) 第一次 run: n1 → n2 (pause)
    summary1 = scheduler.run(start_nodes=["n1"])
    assert summary1.completed == 1
    assert summary1.paused_nodes == ("n2",)

    # 2) Resume DECISION (Phase 5 API)
    decision_exec = scheduler.resume(decision_node_id="n2", option="approve")
    assert decision_exec.status == NodeStatus.COMPLETED

    # 3) 第二次 run (resume 后继续) — 用 cached start_nodes ["n1"]
    summary2 = scheduler.run(start_nodes=["n1"])
    # n1 COMPLETED → skip; n2 COMPLETED → skip; n3 now ready → execute; n4 ready → execute
    assert summary2.completed == 2  # n3 + n4
    assert summary2.paused is False
    # call_log: n1 (第一次), n3, n4 (第二次 — n2 DECISION 不调 compute_fn)
    assert scheduler._test_call_log == ["n1", "n3", "n4"]
```

**关键验证**：scheduler.resume 把 n2 改 COMPLETED → 下次 run 时 n2 不进 ready_nodes → n3 ready → execute → n4 ready → execute。

#### Test 3: `test_workflow_runner_resume_e2e_full_cycle`

```python
def test_workflow_runner_resume_e2e_full_cycle(self) -> None:
    """完整 WorkflowRunner.run(start_nodes=None) → DECISION pause → resume → 验证 cached start_nodes 复用.

    用真实 GoTScheduler + ThoughtGraph (monkeypatch got_bridge.build_got_scheduler).
    """
    master = MasterController.__new__(MasterController)
    from lingwen_core.agents.workflow_state import WorkflowState
    master._state = WorkflowState.empty()
    master.budget_service = None
    master._decision_queue = MagicMock()  # stub queue
    master._memory_rag_mode = None
    master._incremental_backfill_enabled = None

    # Build real graph + scheduler
    graph = ThoughtGraph()
    graph.add_node(ThoughtNode(node_id="n1", type=NodeType.GENERATION, ...))
    graph.add_node(ThoughtNode(node_id="n2", type=NodeType.DECISION, ...))
    graph.add_node(ThoughtNode(node_id="n3", type=NodeType.GENERATION, ...))

    call_log: list[str] = []
    def compute_fn(node, inputs):
        call_log.append(node.node_id)
        return ComputeResult(output={"node": node.node_id}, cost_tokens=1)

    scheduler = GoTScheduler(graph, compute_fn=compute_fn, max_backtracks=0)

    # Monkeypatch build_got_scheduler to return real scheduler/graph
    from lingwen_core.agents import got_bridge
    original_build = got_bridge.build_got_scheduler
    got_bridge.build_got_scheduler = MagicMock(return_value=(scheduler, graph))
    try:
        # Need decision_queue.add to be stubbed for harvest
        master._decision_queue = MagicMock(
            pending=MagicMock(return_value=[]),
            add=MagicMock(),
        )

        runner = WorkflowRunner(master)
        runner._maybe_memory_context = MagicMock(return_value=None)
        runner._maybe_incremental_backfill = MagicMock(return_value=None)

        # 1) run(start_nodes=None) — 应推导 ["n1"] (n1 是 root, n2 depends_on n1)
        result1 = runner.run(workflow_name="test", start_nodes=None)
        assert result1["summary"].paused_nodes == ("n2",)
        # state.start_nodes 应缓存 ["n1"]
        assert master._state.start_nodes == ["n1"]

        # 2) stub decision_queue.get + queue.resolve + scheduler.resume (Phase 5)
        master._decision_queue.get = MagicMock(return_value=MagicMock(node_id="n2"))
        master._decision_queue.resolve = MagicMock(return_value="resolved_decision")
        # _resolve_decision_locked will queue.with_lock → queue.resolve
        master._decision_queue.with_lock = MagicMock(
            return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock()), __exit__=MagicMock(return_value=False))
        )
        # _harvest_decision_specs will iterate graph again — stub to return []
        runner._harvest_decision_specs = MagicMock(return_value=[])

        # 3) resume_workflow — 复用 cached start_nodes ["n1"]
        result2 = runner.resume(decision_id="d1", option="approve")
        assert result2["summary"].completed == 1  # 仅 n3 (n1 已 COMPLETED skip)
        # 验证: call_log 包含 n1 (首次) + n3 (resume), 不含 n2 (DECISION 不调 compute)
        assert call_log == ["n1", "n3"]
    finally:
        got_bridge.build_got_scheduler = original_build
```

**关键验证**：`start_nodes=None` 推导 + `state.start_nodes` 缓存 + resume 复用 + scheduler 幂等 —— 一次测 4 个不变量。

### 4.5 现有 unit test gap 分析

| 现有测试 | 测什么 | 缺口 |
|---------|--------|------|
| `test_run_uses_default_start_nodes_when_none` | derivation 调用 `graph.node_ids()` + `get_node().depends_on` | ✓ 但**未**验证最终 start_nodes list 内容（仅验证 access 序列） |
| `test_run_writes_state_workflow_name_and_start_nodes_before_scheduler` | `state.start_nodes` 在 scheduler.run 前写入 | ✓ 但 start_nodes 是显式传入的 list，**未**测 None 路径 |
| `test_resume_reuses_cached_start_nodes_from_state` | resume 用 `state.start_nodes` 而非 graph 重推导 | ✓ 但仅 MagicMock，**未**测真实 scheduler 行为 |
| (Phase 28 新增) | 真实 GoTScheduler + ThoughtGraph 全 cycle | ✓ 补全 |

## 5. Out of Scope (Phase 28 vs Phase 29+)

| ID | 内容 | 去向 |
|----|------|------|
| P2-MC-WRITING | 84+ pre-existing cascade failures 根因 | 独立 phase (大) |
| P2-ARCHDEBT | infra.got 迁移 + chapter_golden_path 反向 import + 5 薄代理 → OrchestratorProxyMixin + 删 PHASE-COMPAT shim | 战术分散 |
| 真实 workflow YAML 跑 E2E | 需要真实 infra/got/workflows/*.yaml + DB | YAGNI —— unit-level E2E 已够验证幂等 + continuation |

## 6. References

- Phase 27 spec: `docs/superpowers/specs/2026-09-04-phase-27-wfrunner-design.md`
- Phase 27 handoff: `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md`
- Phase 27 carryover: BACKLOG.md P2-RESUME-VERIFY
- WorkflowRunner (Phase 27 deliverable): `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- WorkflowMixin: `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py`
- GoTScheduler: `infra/got/scheduler.py:123-298` (`run()` line 150 + `resume()` line 256)
- ThoughtGraph.ready_nodes: `infra/got/graph.py:147-171` (excludes `status != PENDING`)
- NodeStatus: `infra/got/data_structures.py:40-50`
- Existing test file: `tests/agent_system/test_workflow_runner.py` (21 tests + Phase 27 2 refactor guards)