# Phase 25.9 — human_review 流水线修复 · Handoff

> **Status**: 已实现并待合并 · **日期**: 2026-09-03
> **Branch**: `phase-25-9-human-review-pipeline-refactor` · **Design spec**: [../specs/2026-09-03-phase-25-9-human-review-pipeline-refactor-design.md](../specs/2026-09-03-phase-25-9-human-review-pipeline-refactor-design.md)
> **Master HEAD at start**: `f5934262` (v25.8) · **Commits**: 4 (`3268faa3`..`fd51986d`)
> **Scope**: MasterController `WorkflowMixin.run_workflow` / `resume_workflow` / `list_pending_decisions` / `resolve_decision` 对齐新 `GoTScheduler` API；4 个诚实 skip 的 dashboard smoke 用例去 skip；补全 4 个 helper（`_collect_executions` / `_maybe_memory_context` / `_maybe_incremental_backfill` / `_harvest_decision_specs`）

## TL;DR

Phase 25.9 还原 `mc_workflow.py` 自仓库迁移后遗失的真实实现（一直是 hallucinated stub），对齐新 `GoTScheduler` API，解 4 个 skip 的 dashboard smoke 用例，顺带修 15 个 cascade 测试 + 15 个 incremental backfill 测试。

**4 commits atomic**：

```
3268faa3  docs(phase-25-9): human_review 流水线修复 design spec
34bcef70  docs(phase-25-9): human_review 流水线修复 implementation plan
fd51986d  fix(lingwen-core): align WorkflowMixin with new GoTScheduler API; unskip human_review smoke
<待提交>   docs(phase-25-9): human_review 流水线修复 handoff  ← 本文件
```

**0 改范围（声明）**：`got_bridge.py` / `chapter_golden_path.py` / `apps/studio_api/*` / `infra/got/*` / `.lingwen/architecture.yml` / `HANDOFF*.md` / `CLAUDE.md`（本 phase 不发版）

---

## 背景与动机

v25.8（commit `f5934262`）将 `human_review` 模块做迁移友好修复（`GotScheduler`→`GoTScheduler`、dashboard.* → apps.studio_api.* 导入），但 `WorkflowMixin.run_workflow` / `resume_workflow` / `list_pending_decisions` / `resolve_decision` **未跟进适配新 API**。

### 实际真因（git history 验证）

`mc_workflow.py` 自仓库迁移后一直是 **hallucinated stub**：
- 调 `GoTScheduler(workflow_name=..., start_nodes=..., cost_budget_usd=..., ...)` 用旧 kwargs 签名
- 真实 `infra/got/scheduler.py:135 GoTScheduler.__init__(graph, compute_fn, cache, max_backtracks)` 拒绝上述 kwargs → `TypeError` → 500
- 4 个 helper (`_collect_executions` / `_maybe_memory_context` / `_maybe_incremental_backfill` / `_harvest_decision_specs`) 在迁移后丢失
- `HumanDecisionQueue.list_pending()` 不存在（实际是 `pending()`）
- `resume_workflow(self)` 无参数；`apps/studio_api/routes/workflows.py:90` 路由 / `apps/studio_api/protocols.py:218` adapter 传 `(decision_id, option, resolved_by)`（路由必然先于 mixin 失败）

正确路径已存在：`got_bridge.build_got_scheduler(master, workflow_name, base_dir, max_backtracks)` 工厂（`got_bridge.py:423`）能正确构造 `GoTScheduler` 并连线 `AgentComputeFn` / `cost_tracker` / `budget_service`。`WorkflowMixin.run_workflow` 应该调它，但没调。

---

## What shipped

### `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py`（MODIFIED, 105→376 行, +308/-44）

#### `WorkflowMixin.run_workflow`（line 49-153 改写）

- 走 `got_bridge.build_got_scheduler(master, workflow_name, base_dir, max_backtracks)` 工厂（不是直接构造 `GoTScheduler`）
- 函数内 import（保留 `tests/agent_system/test_master_controller_budget.py` 的 monkeypatch 路径）
- `getattr(self, "budget_service", None)` 兜底兼容 `__new__` stub controller
- 默认起点：`start_nodes=None` 时取无依赖节点
- 走 4 个 helper（`_maybe_memory_context` / `_harvest_decision_specs` / `_collect_executions` / `_maybe_incremental_backfill`）
- 返回 wrapper dict 含 `{summary, graph, executions, pending_decisions, incremental_backfill, memory_context}`
- `try/finally` 保护 `_current_budget_usd` / `_current_run_id` 不跨 run leak

#### `WorkflowMixin.resume_workflow`（line 155-216 改写）

- 签名：`(decision_id, option, resolved_by='human')` —— 与 `apps/studio_api/routes/workflows.py:90` resume 路由透传对齐
- 三步走：resolve queue → `scheduler.resume(decision_node_id=decision.node_id, ...)` → re-harvest → re-run scheduler 让下游节点完成
- 缺状态时 raise `RuntimeError`，符合 route 透传契约

#### `WorkflowMixin.list_pending_decisions`（line 218-230 改写）

- 改调 `queue.pending()`（之前错位调 `list_pending()` 不存在）
- 返回 `[d.to_dict() for d in queue.pending()]`
- `_decision_to_response` 接受 dict / object 两种

#### `WorkflowMixin.resolve_decision`（line 232-273 改写）

- 签名：`(decision_id, option, resolved_by='human')`
- 在 `queue.with_lock()` 下返回 `HumanDecision`
- 缺 `_decision_queue` 时 raise `RuntimeError`

#### 恢复 4 个 helper

- `_collect_executions(graph)` —— 收集所有节点执行结果成 `dict[node_id, NodeExecution]`
- `_maybe_memory_context(workflow_name, seed_inputs)` —— Phase 9.70 F62 可选 MemoryGateway RAG context
- `_maybe_incremental_backfill(workflow_name, initial_inputs, executions, summary)` —— 增量回填
- `_harvest_decision_specs(graph, initial_inputs)` —— 通过 deferred import 复用 `lingwen_pipeline.master_controller._infer_decision_kind` 与 option/priority map（避免循环依赖）

#### 恢复 Phase 8.12 budget_service.set

```python
budget_service = getattr(self, "budget_service", None)
if budget_service is not None and cost_budget_usd is not None:
    budget_service.set(scope="run", usd=cost_budget_usd, run_id=run_id)
```

`getattr` 兜底兼容 `__new__` stub controller（test 路径）。

### `tests/dashboard/test_human_review_smoke.py`（MODIFIED, -8 行）

- 移除 4 处 `@pytest.mark.skip(...)` 装饰器（行 22/32/44/52）
- 断言不变；RED → GREEN 由 mc_workflow.py 改写驱动

---

## 测试 gates

| 门 | baseline (master v25.8) | target (worktree v25.9) |
|---|---|---|
| tests/dashboard | 353 passed + 7 skipped | **357 passed + 3 skipped** (+4 -4skip) |
| tests/ci | 205 passed + 1 skipped | 205 passed + 1 skipped (不变) |
| tests/got + tests/agent_system | 99 failed / 495 passed / 20 skipped | **84 failed / 510 passed / 20 skipped** (+15 -0 new) |
| tests/cross_volume/test_incremental_backfill.py | (未跑 / 缺 helper 失败) | **15 passed** (新覆盖) |
| ruff check + ruff format --check | clean | clean |

> **+15 -0 new**：mc_workflow.py 4 个 helper 恢复连带修好 15 个关联 cascade 测试，**0 新增失败**。
> **剩余 84 failed**：pre-existing，根因推测 `mc_writing.py` 类似 gutted（详见 carryover）。

---

## Architecture invariants

**0 NEW architecture invariants**。本 phase 仅还原实现 + 解 skip，不引入新架构约束。

保留：`I001` (infra 不 import apps) / `I005` (创作流必须支持 checkpoint 恢复)。

---

## Files modified

**Modified**：
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` — 105→376 行 (+308/-44, +271 net)
- `tests/dashboard/test_human_review_smoke.py` — 移除 4 处 skip decorator (-8 行)

**New**：
- `docs/superpowers/specs/2026-09-03-phase-25-9-human-review-pipeline-refactor-design.md` — 234 行
- `docs/superpowers/plans/2026-09-03-phase-25-9-human-review-pipeline-refactor.md` — 446 行
- `docs/superpowers/handoffs/2026-09-03-phase-25-9-human-review-pipeline-refactor-handoff.md` — 本文件

**Unchanged（0 改范围）**：`got_bridge.py` / `chapter_golden_path.py` / `apps/studio_api/*` / `infra/got/*` / `.lingwen/architecture.yml` / `HANDOFF*.md` / `CLAUDE.md`

---

## Lessons

### 1. HANDOFF 措辞不可全信 — 必须实测勘察

CLAUDE.md / HANDOFF 描述"cost_tracker/latest_decision_queue 未初始化"是过度简化。**真因**：mc_workflow.py 整体是 hallucinated stub（指向已删除的 `infra/agent_system/` 路径 + 旧 `GotScheduler` API）。勘察时要做 git history + 实际运行验证，不能仅看 HANDOFF。

**lesson**：当 HANDOFF 描述过于笼统时，优先跑 RED 看具体 stack trace，比读设计文档更可靠。

### 2. spec 范围易低估 — 实施时需反推 spec 范围

最初 spec 估计"最小可用 = 修 2 处 API 签名"，但实施时 RED 暴露需要：

- `run_workflow` 改调 `build_got_scheduler` 工厂（不是直接 `GoTScheduler(...)`）
- `resume_workflow` 签名加 `(decision_id, option, resolved_by)` + 三步走实现
- `list_pending_decisions` 改调 `queue.pending()`（不是 `list_pending()`）
- `resolve_decision` 完整重写（queue.with_lock 路径）
- 4 个 helper 恢复（`_collect_executions` / `_maybe_memory_context` / `_maybe_incremental_backfill` / `_harvest_decision_specs`）
- `budget_service.set` 恢复（Phase 8.12）

**lesson**：spec 阶段宁多列范围（明确 "需要的辅助函数 + 已存在可复用"），免得实施时返工。

### 3. 测试污染要 guard（极其重要）

`tests/dashboard/test_creator_endpoints.py` 会写 `# snap-line` / `# disk-only` 到 `projects/anye-xinbiao/docs/novel-pillars.md`。**任何跑测试的步骤前/后都要 `git status` 核对**。

本 phase 已成功防御：所有 pytest run 之前/之后都 revert 一次 `projects/anye-xinbiao/docs/novel-pillars.md`。

**lesson**：跨 git worktree 操作时，污染文件不在 git diff 范围内（污染源在 test fixture 路径下），但 `git status --short` 会显示 M —— 必须用 `git checkout HEAD -- <file>` 显式 revert。

### 4. `git -C <worktree>` 比 `cd` 更稳

agent 线程 cwd 在每次 bash 调用之间会 reset。`cd /worktree && git status` 只在该次调用有效；后续调用会回到 `/home/ailearn/projects/LingWen`（master）。**必须用 `git -C /home/ailearn/projects/LingWen-phase-25-9 <cmd>`**，避免污染主 checkout 的 git state。

---

## Carryover to Phase 26+

| ID | 描述 | 优先级 |
|---|---|---|
| WorkflowRunner service 拆分 | run_workflow orchestration 90+ 行仍偏多，可拆 service | P1 |
| WorkflowState dataclass | `_last_*` 散点整合 dataclass (`_last_scheduler` / `_last_graph` / `_last_workflow_name` / `_last_start_nodes` / `_last_initial_inputs` / `_last_incremental_backfill` / `_last_memory_context`) | P1 |
| resume 重跑 start_nodes 验证 | `start_nodes=None` 时 resume 行为需 E2E 验证（spec 6.3 未覆盖） | P2 |
| **84 pre-existing failures** | 推测 `mc_writing.py` 类似 gutted；根因调查 | **P1** |
| infra.got → lingwen-got | 架构债；补 lingwen-core allowed_imports 或新包 | P2 |
| chapter_golden_path.py 反向 import | 架构债；test helper 迁 tests/ | P2 |
| HANDOFF latest_decision_queue 措辞 | 文档修订 | P3 |
| human_review 真 E2E | Playwright + live backend | P2 |

---

## Files added/changed (summary)

### Modified

- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` — `WorkflowMixin` 4 方法体改写 + 4 helper 补全 + Phase 8.12 budget_service.set 恢复
- `tests/dashboard/test_human_review_smoke.py` — 移除 4 处 `@pytest.mark.skip`

### Docs

- `docs/superpowers/specs/2026-09-03-phase-25-9-human-review-pipeline-refactor-design.md`（已有）
- `docs/superpowers/plans/2026-09-03-phase-25-9-human-review-pipeline-refactor.md`（已有）
- `docs/superpowers/handoffs/2026-09-03-phase-25-9-human-review-pipeline-refactor-handoff.md`（本文件）

---

## Related phases

- **Phase 25.8**（commit `f5934262`）：人审模块迁移友好修复（`GotScheduler`→`GoTScheduler`、dashboard.* → apps.studio_api.* 导入）；本 phase 是其后续还原 mc_workflow 真实实现
- **Phase 15.0 P3-SPLIT**：mc_workflow.py 从 master_controller.py 拆分出来

---

## Solo workflow closure

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-25-9-human-review-pipeline-refactor
git push origin master
git worktree remove /home/ailearn/projects/LingWen-phase-25-9
```

Master HEAD after merge: `fd51986d` (v25.9，待 +1 handoff commit)。

---

## 下一步（v25.9 closure 后）

- [ ] 主 checkout ff-merge `phase-25-9-human-review-pipeline-refactor` 到 master
- [ ] 更新 CLAUDE.md 版本块 v25.8 → v25.9
- [ ] 更新 collaboration/CURRENT_STATUS.md + BACKLOG.md
- [ ] Phase 26+ 立项考虑 carryover 优先级（建议 P1: 84 pre-existing failures + WorkflowRunner 拆分）
