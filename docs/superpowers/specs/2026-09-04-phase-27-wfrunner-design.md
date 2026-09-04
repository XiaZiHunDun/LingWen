# Phase 27 P2-WFRUNNER — WorkflowRunner Service 拆分 Design Spec

> **Author**: Phase 27 brainstorm session · **Date**: 2026-09-04
> **Status**: Draft (brainstorm approved) · **Predecessor**: Phase 26 P2-WFSTATE
> **Carryover source**: Phase 26 handoff P2-WFRUNNER entry (BACKLOG.md)

## 1. Context (Why)

Phase 26 P2-WFSTATE 闭环后，`WorkflowMixin` 仍持有 ~181 行核心 (`run_workflow` 106 行 + `resume_workflow` 75 行) + ~103 行 helpers + 14 行薄代理 = **380 行总长**。`run_workflow` 单方法跨 11 个步骤 (budget setup → scheduler build → start_nodes 默认 → memory context → harvest DECISION → state write → scheduler.run → collect executions → backfill → final state write → return)，超过 50 行 + 单职责违反。

`run_workflow` 与 `resume_workflow` 共享 ~70% 结构 (collect_executions / maybe_incremental_backfill / harvest_decision_specs / state.with_updates)。单方法粒度太大，难独立测试 / 复用 / 演进。

Phase 26 carryover **P2-WFRUNNER**（BACKLOG.md）：把 `run_workflow` 90+ 行 → 拆 `WorkflowRunner` service。承接 Phase 26 dataclass 自然延展 — WorkflowState 已就位，Runner 直接读写 `controller._state`。

## 2. Goals & Non-Goals

### Goals (in scope)

| ID | 目标 |
|----|------|
| G1 | 新建 `WorkflowRunner` service 类，自含 `run()` + `resume()` + 4 internal helpers |
| G2 | `WorkflowMixin` 拆后只剩 5 薄代理 + 3 决策委托 + 1 懒 runner accessor |
| G3 | `master.run_workflow()` / `master.resume_workflow()` 调用签名 100% 保持不变 |
| G4 | 所有 `master._state.X` 读路径零修改（production_summary / protocols / chapter_golden_path） |
| G5 | TDD RED→GREEN，新增 17-20 unit tests + 2 refactor guards |
| G6 | 0 新失败（git stash 实证 pre-existing fail 数与 Phase 26 一致） |
| G7 | 0 改范围（不动 gateway facade / route / got_bridge / Phase 26 dataclass / PHASE-COMPAT shim / architecture.yml） |

### Non-Goals (out of scope, 显式不做)

| ID | 不做 | 去向 |
|----|------|------|
| N1 | 5 薄 orchestrator 代理（advance_step / dispatch_task / verify_task / get_workflow_status）拆分 | 留 P2-ARCHDEBT 或独立 phase |
| N2 | 删 stale PHASE-COMPAT shim (`master_controller.py` 530B, 标 "DELETE after v16.x" 但 v25.9 仍在) | 留 P2-ARCHDEBT |
| N3 | `start_nodes=None` 时 resume_workflow 重跑行为 E2E 验证 | 独立 P2-RESUME-VERIFY phase (建议 Phase 28) |
| N4 | `infra.got.*` 迁移 + `chapter_golden_path.py` 反向 import 整改 | 留 P2-ARCHDEBT |
| N5 | 84+ pre-existing cascade failures 根因调查 | 独立 P2-MC-WRITING phase |
| N6 | `mc_writing.py` 等其他 Mixin 拆分 | 不在 P2-WFRUNNER 范围 |
| N7 | WorkflowRunner 引入 Protocol 解耦 (与 MC 接口化) | YAGNI — 紧耦合可接受 |

## 3. Architecture (Section 1)

### 3.1 Placement & Naming

| 项 | 决策 |
|----|------|
| 文件 | `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`（NEW） |
| 类 | `WorkflowRunner`（无前缀 — 是 service 不是 mixin） |
| 与谁同目录 | `mc_workflow.py` (WorkflowMixin) / `workflow_state.py` (Phase 26 dataclass) / `got_bridge.py` (调度器工厂) |
| 命名约定一致性 | `mc_*.py` 仅用于 mixin；service / dataclass 用名词命名 |

### 3.2 Class Shape

```python
# packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py
"""Phase 27 P2-WFRUNNER — MasterController 工作流运行 service.

从 WorkflowMixin.run_workflow / resume_workflow (181 行) 拆出,
自含 budget + scheduler + state 生命周期管理. Mixin.run_workflow()
变 1 行 delegate: return self._get_runner().run(...).
"""
from __future__ import annotations
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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

    # === Public API ===
    def run(self, workflow_name, start_nodes=None, initial_inputs=None,
            cost_budget_usd=None, max_backtracks=2, base_dir=None): ...
    def resume(self, decision_id, option, resolved_by="human"): ...

    # === Internals (4 helpers from WorkflowMixin) ===
    @staticmethod
    def _collect_executions(graph): ...
    def _maybe_memory_context(self, workflow_name, initial_inputs): ...
    def _maybe_incremental_backfill(self, ...): ...
    def _harvest_decision_specs(self, graph, *, initial_inputs=None): ...
    def _resolve_decision_locked(self, decision_id, option, resolved_by): ...
```

### 3.3 Dependency Direction

| 边 | 方向 | 备注 |
|----|------|------|
| `workflow_runner.py` → `MasterController` (lingwen-pipeline) | TYPE_CHECKING only | 前向引用，零运行时循环 |
| `workflow_runner.py` → `got_bridge.build_got_scheduler` | call-time import | 保留 v25.9 lazy pattern，测试可 monkeypatch |
| `workflow_runner.py` → `chapter_memory_hook.maybe_attach_memory_context` | call-time import | 同上 |
| `workflow_runner.py` → `infra.cross_volume.incremental_backfill.maybe_after_workflow` | call-time import | 同上 |
| `workflow_runner.py` → `lingwen_pipeline.master_controller` (`_DEFAULT_DECISION_*`, `_infer_decision_kind`) | call-time import | 避开 core ↔ pipeline 模块循环（v25.9 既有约定） |
| `MasterController` (lingwen-pipeline) → `WorkflowRunner` (via WorkflowMixin) | ✓ 同方向 | 不引入新跨包依赖 |

### 3.4 Lazy Init Strategy（关键 — `__new__` 测试 stub 兼容）

**`MasterController.__init__` 不创建 `self._workflow_runner`** — 避免 17+ `__new__` stub 全部要改。

```python
class WorkflowMixin:
    def _get_runner(self) -> WorkflowRunner:
        runner = getattr(self, "_workflow_runner", None)
        if runner is None:
            runner = WorkflowRunner(self)
            self._workflow_runner = runner
        return runner

    def run_workflow(self, **kwargs):
        return self._get_runner().run(**kwargs)

    def resume_workflow(self, **kwargs):
        return self._get_runner().resume(**kwargs)
```

- 首个 `run_workflow()` / `resume_workflow()` 调用触发 lazy init
- 同一 controller 多次访问复用同一 Runner 实例
- 测试 stub 用 `master._get_runner()._harvest_decision_specs = MagicMock(...)` 即可 stub 内部方法

### 3.5 WorkflowMixin 删后状态

```python
class WorkflowMixin:
    """工作流相关 — Phase 27 后只剩 5 薄代理 + 3 决策委托 + 1 懒 runner accessor."""

    # === Runner 入口 (lazy) ===
    def _get_runner(self) -> WorkflowRunner: ...
    def run_workflow(self, **kwargs) -> Dict[str, Any]: ...
    def resume_workflow(self, **kwargs) -> Dict[str, Any]: ...

    # === 5 薄 orchestrator 代理 (out of scope) ===
    def advance_step(self, target_step, context=None): ...
    def dispatch_task(self, task_name, agent, context, priority=0): ...
    def verify_task(self, task_id, result): ...
    def get_workflow_status(self): ...

    # === 3 决策队列委托 (in scope) ===
    def resolve_decision(self, decision_id, option, resolved_by="human"): ...
    def list_pending_decisions(self): ...
    def get_decision_queue(self): ...
```

### 3.6 MasterController 影响

- `__init__` **零变化** — 不创建 `_workflow_runner`（lazy via `_get_runner()`）
- 所有现有 method (get_router / switch_agent_role / 等) 不变
- 不动 `_decision_queue` / `_state` / `_current_budget_usd` / `_current_run_id` 构造路径

## 4. Components & Public Surface (Section 2)

### 4.1 `WorkflowRunner.run` 签名

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
    """运行工作流 (从 WorkflowMixin.run_workflow 移出).

    Returns:
        {
            "summary": ExecutionSummary,
            "graph": ThoughtGraph,
            "executions": dict[node_id, NodeExecution],
            "pending_decisions": list[dict],
            "incremental_backfill": BackfillStats | None,
            "memory_context": dict | None,
        }

    Raises:
        WorkflowError: 加载失败
        HumanInterventionRequired: 回溯超限
        MaxStepsExceeded: 步数超限
    """
```

完整 11 步流水线见 §5.1。

### 4.2 `WorkflowRunner.resume` 签名

```python
def resume(
    self,
    decision_id: str,
    option: str,
    resolved_by: str = "human",
) -> Dict[str, Any]:
    """恢复 DECISION 暂停的工作流 (从 WorkflowMixin.resume_workflow 移出).

    Returns:
        同 run() 结构 + resolved_decision (HumanDecision 对象)

    Raises:
        RuntimeError: 无活跃工作流 / queue 未初始化
        KeyError: decision_id 不存在
        ValueError: 决策已 RESOLVED / option 不在 options / node 非 WAITING
    """
```

完整 8 步流水线见 §5.2。

### 4.3 Internal Helpers (5 总 — 4 迁移 + 1 NEW)

| Helper | 静态? | 移到 Runner 的形式 | 备注 |
|--------|-------|-------------------|------|
| `_collect_executions(graph)` | @staticmethod | `WorkflowRunner._collect_executions` | 不需要 controller 引用 |
| `_maybe_memory_context(workflow_name, initial_inputs)` | instance | `self._controller._memory_rag_mode` 访问 | Phase 9.70 F62 |
| `_maybe_incremental_backfill(workflow_name, initial_inputs, executions, summary)` | instance | `self._controller._incremental_backfill_enabled` 访问 | Phase 9.63 F54 |
| `_harvest_decision_specs(graph, *, initial_inputs=None)` | instance | `self._controller._decision_queue` + `self._controller._state.initial_inputs` 访问 | Phase 4.3/9.69 F61/9.83 F75 |
| `_resolve_decision_locked(decision_id, option, resolved_by)` | instance | `self._controller._decision_queue` 访问 | **NEW** (Phase 27): 从 `resolve_decision` 提取的内部版本，仅供 `resume()` step 3 调用 |

> **测试覆盖策略**：`_resolve_decision_locked` 不单独建测试 — 通过 `resume()` Phase C 5 个测试间接覆盖（`test_resume_resolves_decision_then_resumes_scheduler` 等）。如 E2E 暴露该 helper bug，再补 unit test。

### 4.4 不变 Caller 接口

| Caller | 调用 | 影响 |
|--------|------|------|
| `apps/studio_api/protocols.py:85` `run_workflow(...)` | `self._controller.run_workflow(...)` | ✓ Mixin 仍 delegate |
| `apps/studio_api/routes/workflows.py:45` `run_workflow(body)` | `ctrl.run_workflow(...)` | ✓ 同上 |
| `chapter_golden_path.py:114` | `controller.run_workflow(...)` | ✓ |
| `chapter_production_pilot.py:426` | `master.run_workflow(...)` | ✓ |
| `production_summary.py:61` `Read controller._state cache` | 直读 `controller._state.workflow_name` 等 | ✓ Runner 不持独立 state |

## 5. Data Flow (Section 3)

### 5.1 `run()` 调用链（11 步）

```
1.  budget setup:  ctrl._current_budget_usd = cost_budget_usd
                  run_id = uuid.uuid4().hex
                  ctrl._current_run_id = run_id
                  budget_service.set(scope='run', usd=X, run_id=run_id)
                  ↳ if hasattr(ctrl, "budget_service") and X is not None
2.  build scheduler: scheduler, graph = build_got_scheduler(...)
3.  default start_nodes: if None, 取 graph 无依赖节点
4.  memory RAG context: seed_inputs += memory_context (optional)
5.  harvest DECISION specs: pending = self._harvest_decision_specs(graph, initial_inputs=seed_inputs)
6.  ★ STATE WRITE 1 (pre-run): ctrl._state = ctrl._state.with_updates(
                  initial_inputs, workflow_name, start_nodes)
7.  scheduler.run(start_nodes, initial_inputs=seed_inputs)
8.  executions = self._collect_executions(graph)
9.  incremental backfill: backfill = self._maybe_incremental_backfill(...)
10. ★ STATE WRITE 2 (post-run): ctrl._state = ctrl._state.with_updates(
                  scheduler, graph, incremental_backfill, memory_context)
11. return {...}
finally: ctrl._current_budget_usd = None  # ALWAYS
         ctrl._current_run_id = None      # ALWAYS
```

### 5.2 `resume()` 调用链（8 步）

```
1.  CHECK active workflow: scheduler = ctrl._state.scheduler
                          graph = ctrl._state.graph
                          if None: raise RuntimeError("no active workflow; ...")
2.  FETCH decision: queue = getattr(ctrl, "_decision_queue", None)
                    if None: raise RuntimeError("decision queue not initialized")
                    decision = queue.get(decision_id)  # KeyError if missing
3.  RESOLVE locked: resolved = self._resolve_decision_locked(decision_id, option, resolved_by)
4.  RESUME GoT node: scheduler.resume(decision_node_id=decision.node_id, option=option, resolved_by=resolved_by)
5.  HARVEST new DECISIONs: pending = self._harvest_decision_specs(graph, initial_inputs=ctrl._state.initial_inputs)
6.  CONTINUE execution: start_nodes = list(ctrl._state.start_nodes) or default
                        summary = scheduler.run(start_nodes=start_nodes)
7.  COLLECT + BACKFILL: executions = self._collect_executions(graph)
                        backfill = self._maybe_incremental_backfill(...)
8.  ★ STATE WRITE 3 (post-resume): ctrl._state = ctrl._state.with_updates(
                        incremental_backfill=backfill)
   return {summary, graph, executions, pending_decisions,
           resolved_decision, backfill, memory_context}
```

### 5.3 State Write 时点表

| WRITE | 时点 | 写入字段 | 读它的人 |
|-------|------|---------|---------|
| **WRITE 1** | `run()` scheduler.run **之前** | `initial_inputs`, `workflow_name`, `start_nodes` | `emit_chapter` 等节点（scheduler.run 期间读 chapter_num） |
| **WRITE 2** | `run()` scheduler.run **之后** | `scheduler`, `graph`, `incremental_backfill`, `memory_context` | `resume_workflow()` step 1、`production_summary.py:61`、`apps/studio_api/protocols.py:241`、`apps/studio_api/helpers/workflow.py:53` |
| **WRITE 3** | `resume()` scheduler.run **之后** | 仅 `incremental_backfill` | 同 WRITE 2 |

**不变量**：
- WRITE 1 必在 WRITE 2 之前（emit_chapter 必须在 scheduler.run 期间能读到 chapter_num）
- WRITE 3 不重写 `scheduler/graph/start_nodes`（它们从 cached state 继承）
- 所有写入走 `ctrl._state = ctrl._state.with_updates(...)` — frozen dataclass 强制 immutable

### 5.4 Budget 生命周期（Phase 8.8/8.12 不变量）

```
run() 进入
  ├─ setup:    ctrl._current_budget_usd = X
  │            ctrl._current_run_id = uuid4().hex
  │            budget_service.set(scope='run', usd=X, run_id=run_id)
  ├─ try:
  │    scheduler.run(...)
  │    ... (其他 10 步)
  └─ finally:  ctrl._current_budget_usd = None  # ALWAYS
               ctrl._current_run_id = None      # ALWAYS
```

**不变量**：
- `try/finally` 保证 raise 也 reset
- `_current_budget_usd = None` 防御跨 run leak
- `getattr(ctrl, "budget_service", None)` 兜底 `__new__` 测试 stub
- `if budget_service is not None and cost_budget_usd is not None` 双重 guard

`resume()` **不** setup / reset budget — 原 `WorkflowMixin.resume_workflow` 也无 budget，resume 是同次 run 的延续。

## 6. Error Handling (Section 4.A)

### 6.1 异常边界表

| 异常 | 抛出位置 | 边界 | finally reset? |
|------|----------|------|----------------|
| `WorkflowError` | `got_bridge.build_got_scheduler()` 内部 | bubble up 出 `run()` | ✓ budget reset |
| `HumanInterventionRequired` | `scheduler.run()` 内部 | bubble up 出 `run()` | ✓ budget reset |
| `MaxStepsExceeded` | `scheduler.run()` 内部 | bubble up 出 `run()` | ✓ budget reset |
| `RuntimeError("no active workflow")` | `resume()` step 1 | bubble up 出 `resume()` | n/a |
| `RuntimeError("decision queue not initialized")` | `resume()` step 2 / `resolve_decision` | bubble up | n/a |
| `KeyError` | `queue.get(decision_id)` step 2 | bubble up | n/a |
| `ValueError`（已 RESOLVED / option 不在 / node 非 WAITING） | `queue.resolve()` step 3 / `scheduler.resume()` step 4 | bubble up | n/a |
| `ImportError` / `KeyError` in `_harvest_decision_specs` | helper 内部 | bubble up | ✓ (run) / n/a (resume) |

**核心原则**：WorkflowRunner **不 try/except** — 让异常自然 bubble。`try/finally` **仅**为 budget reset，不吞异常。

### 6.2 边界情形（defensive 保留）

| 场景 | 现状 | Phase 27 处理 |
|------|------|--------------|
| `__new__` 测试 stub 无 `_state` | Phase 26 refactor guard 3 测试覆盖（`WorkflowState.empty()` 默认值） | ✓ 行为不变 |
| `__new__` 测试 stub 无 `_decision_queue` | `_harvest_decision_specs` 已有 `getattr(..., None)` 兜底返 `[]` | ✓ Runner 内同样保留 |
| `start_nodes=None` 时 resume 重跑行为 | carryover **P2-RESUME-VERIFY** 标记 | ⚠️ 不在本 phase（独立 Phase 28）；Phase 27 仅保证行为不变 |
| 5 薄 orchestrator 代理 | out of scope per (b) | ✓ 保留 Mixin |

## 7. Testing Strategy (Section 4.B-D)

### 7.1 新建 `tests/agent_system/test_workflow_runner.py` (~17-20 tests)

TDD RED→GREEN→IMPROVE 顺序：

**Phase A — 构造 & lazy accessor (~3 tests)**
- `test_get_runner_lazy_creates_workflow_runner_on_first_call`
- `test_get_runner_returns_same_instance_on_subsequent_calls`
- `test_workflow_runner_init_stores_controller_reference`

**Phase B — `run()` 行为 (~8 tests, stub controller)**
- `test_run_sets_current_budget_usd_before_scheduler`
- `test_run_resets_current_budget_usd_in_finally_even_on_raise`
- `test_run_generates_uuid4_hex_run_id`
- `test_run_calls_budget_service_set_with_run_scope`
- `test_run_skips_budget_service_set_when_budget_service_is_none`
- `test_run_writes_state_workflow_name_and_start_nodes_before_scheduler`
- `test_run_writes_state_scheduler_graph_backfill_after_scheduler`
- `test_run_returns_summary_executions_pending_decisions`

**Phase C — `resume()` 行为 (~5 tests, stub controller)**
- `test_resume_raises_runtime_error_when_no_active_workflow`
- `test_resume_raises_runtime_error_when_queue_not_initialized`
- `test_resume_resolves_decision_then_resumes_scheduler`
- `test_resume_reuses_cached_start_nodes_from_state`
- `test_resume_returns_resolved_decision_in_payload`

**Phase D — 4 internal helpers (~4 tests)**
- `test_collect_executions_returns_node_id_to_execution_mapping`
- `test_maybe_memory_context_returns_none_when_disabled`
- `test_maybe_incremental_backfill_returns_none_when_disabled`
- `test_harvest_decision_specs_skips_already_pending_nodes`

### 7.2 扩展 `tests/agent_system/test_workflow_state.py` — Refactor Guard (+2 tests)

防 WorkflowRunner 散点回潮：

- `test_workflow_runner_has_no_last_underscore_attrs` — runner 实例不应有 `_last_*` 私有字段（与现有 `test_no_last_underscore_attrs_on_workflow_state_instance` 对偶）
- `test_workflow_runner_does_not_mutate_state_directly` — runner 不持独立 state（与现有 `test_master_controller_has_state_attribute` 对偶）

### 7.3 更新 `tests/agent_system/test_master_controller_budget.py` (6 处 stub)

```python
# 旧 (Phase 26):
master._harvest_decision_specs = MagicMock(return_value=[])

# 新 (Phase 27):
master._get_runner()._harvest_decision_specs = MagicMock(return_value=[])
```

需修改行号：79, 98, 116, 130, 144, 221。

### 7.4 不动的现有测试

- `test_workflow_state.py` 现有 11 tests（8 unit + 3 guard） — 应**继续 pass**
- `test_master_controller_workflow.py` — 不直接 stub private helper
- `test_got_bridge*.py`, `test_decision_*.py`, `test_chapter_*.py` — 通过 facade 间接测 WorkflowRunner

## 8. Verification Gates (Section 4.D)

merge 前必跑：

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `pytest tests/agent_system/test_workflow_state.py -v` | 13/13 pass（11 现有 + 2 新 guard） |
| G2 | `pytest tests/agent_system/test_workflow_runner.py -v` | 17-20/17-20 pass（新加） |
| G3 | `pytest tests/agent_system/test_master_controller_budget.py -v` | 6/6 pass（更新后） |
| G4 | `pytest tests/agent_system/ -v` | 0 新失败（git stash 实证 pre-existing 9 fail 数一致） |
| G5 | `pytest tests/dashboard/test_decision_pause_resume.py -v` | 17/17 pass（gateway facade 不动） |
| G6 | `pytest tests/cross_volume/test_incremental_backfill.py -v` | 15/15 pass |
| G7 | `ruff check .` | clean |
| G8 | `grep -rn "_last_scheduler\|_last_graph" infra/ packages/ apps/ tests/ 2>/dev/null` | 0 hits |
| G9 | `wc -l packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` | ≤ 130 行（从 380 行缩减） |
| G10 | `wc -l packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` | ~350 行（新文件） |

## 9. Out of Scope (Phase 27 vs Phase 28+)

| ID | 内容 | 去向 |
|----|------|------|
| P2-RESUME-VERIFY | `start_nodes=None` resume_workflow 重跑行为 E2E 验证 | 独立 Phase 28（小） |
| P2-MC-WRITING | 84+ pre-existing cascade failures 根因 | 独立 phase（大） |
| P2-ARCHDEBT | `infra.got.*` 迁移 + `chapter_golden_path.py` 反向 import 整改 + HANDOFF 措辞修订 + 删 stale PHASE-COMPAT shim | 战术分散 |
| Thin proxies 拆分 | 5 薄 orchestrator 代理 → OrchestratorProxyMixin | 留 P2-ARCHDEBT |
| Protocol 解耦 | Runner 与 MC 接口化 | YAGNI，紧耦合可接受 |

## 10. References

- Phase 26 handoff: `docs/superpowers/handoffs/2026-09-04-phase-26-wfstate-handoff.md`
- Phase 26 carryover P2-WFRUNNER: `collaboration/BACKLOG.md`
- Phase 26 spec: `docs/superpowers/specs/2026-09-03-phase-26-wfstate-design.md`
- WorkflowState (Phase 26 deliverable): `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py`
- WorkflowMixin (现状): `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py`
- MasterController (lingwen-pipeline): `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py`
- got_bridge scheduler factory: `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py`
- Phase 26 refactor guard: `tests/agent_system/test_workflow_state.py` (11 tests, 8 unit + 3 guard)
