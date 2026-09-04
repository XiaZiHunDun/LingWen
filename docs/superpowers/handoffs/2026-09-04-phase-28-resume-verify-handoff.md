# Phase 28 P2-RESUME-VERIFY — Handoff

> **Date**: 2026-09-04 · **Status**: ✅ All tasks complete · **Spec**: `docs/superpowers/specs/2026-09-04-phase-28-resume-verify-design.md` · **Plan**: `docs/superpowers/plans/2026-09-04-phase-28-resume-verify.md`

## 闭环内容

### 测试增量 (5 E2E tests)

`tests/agent_system/test_workflow_runner.py` 追加 2 新 test classes (5 tests, +271 行):

#### `TestResumeE2EWithRealScheduler` (3 tests) — 真实 GoTScheduler + ThoughtGraph

| Test | 不变量验证 |
|------|----------|
| `test_scheduler_run_is_idempotent_on_completed_nodes` | `graph.ready_nodes()` (`infra/got/graph.py:152-155`) 排除 `status≠PENDING` → 已 COMPLETED n1 不进 ready_nodes → scheduler.run 二次调用不重跑 |
| `test_resume_after_decision_pause_continues_from_cached_start_nodes` | DECISION pause → `scheduler.resume()` → `scheduler.run()`: 下游节点执行, 已执行节点跳过, n2 DECISION 不调 compute_fn |
| `test_workflow_runner_resume_e2e_full_cycle` | 完整 `run(start_nodes=None) → DECISION pause → resume` cycle 验证 4 不变量: derived list / state cache / resume 复用 / scheduler 幂等 |

#### `TestRunWithNoneStartNodesDerivation` (2 tests) — WorkflowRunner + 真实 scheduler

| Test | 不变量验证 |
|------|----------|
| `test_run_with_none_start_nodes_persists_derived_list_to_state` | `run(start_nodes=None)` → `state.start_nodes` 缓存 ["n1"] (n1 root, n2/n3 依赖) |
| `test_resume_reuses_start_nodes_persisted_during_run_with_none` | resume 期间 graph mutation (新增 n4 root) 不影响 `state.start_nodes` — 仍是 ["n1"], n1 不重跑 |

### 0 改范围承诺遵守

Phase 28 是纯 test-only phase, 9 类文件不动:

- ❌ `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` (307 行, 不动)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` (119 行, 不动)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` (Phase 26 dataclass, 不动)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` (Phase 27 不动)
- ❌ `infra/got/{scheduler,graph,data_structures}.py` (验证正确, 不动)
- ❌ gateway facade / route / helper
- ❌ master_controller shim (PHASE-COMPAT, 留 P2-ARCHDEBT)
- ❌ `.lingwen/architecture.yml` / `HANDOFF*`

## Verification Gates (实测)

| Gate | Baseline | 实测 | 状态 |
|------|---------|------|------|
| G1 test_workflow_state.py | 13 | 13/13 ✓ | UNCHANGED |
| G2 test_workflow_runner.py | 21 | 26/26 ✓ | **+5 Phase 28 E2E** |
| G3 test_master_controller_budget.py | 6 + 2 env fail | 6/6 target + 2 pre-existing FileNotFoundError (carryover) | UNCHANGED |
| G4 tests/agent_system/ | 84 fail baseline | 84 fail + 393 pass (+5 NEW) + 20 skip | **0 NEW failure** |
| G5 test_decision_pause_resume.py | 17 | 17/17 ✓ | UNCHANGED |
| G6 test_incremental_backfill.py | 15 | 15/15 ✓ | UNCHANGED |
| G7 ruff check | clean | clean ✓ | UNCHANGED |
| G8 grep `_last_*` scatter | 0 hits | 0 hits ✓ | UNCHANGED |
| G9 mc_workflow.py | 119 lines | 119 lines ✓ | UNCHANGED |
| G10 workflow_runner.py | 307 lines | 307 lines ✓ | UNCHANGED (test-only phase) |

## 关键纪律亮点

- ✅ TDD 严格 RED→GREEN：5 commits 每个含写 → 跑 → 验证 PASS → commit
- ✅ 2 个 RED 实证 (Tasks 1+4)：
  - Task 1: 初始断言 `summary.paused is True` (二次 run) 错误 — 修正为 scheduler.run 二次调用无 ready nodes 立即退出 (paused=False)，状态跨 run 保留 — scheduler.run 只报告 NEW pauses
  - Task 4: 初始断言 `summary.completed == 1` 错误 — 修正为 scheduler.run 不限制执行范围到 start_nodes chain，会执行所有 ready 节点 (n3 + 新 root n4)
- ✅ 0 改范围 9 类文件不动
- ✅ 真实 GoTScheduler + ThoughtGraph (非 MagicMock) — 验证 scheduler 真实行为
- ✅ 验证 scheduler 幂等 (代码 review 列 important) 经实证 PASS

## RED 学习要点 (TDD 价值体现)

Phase 28 的 2 个 RED 不是 implementation bug，而是 **测试设计错误**。TDD 暴露了：

1. **scheduler.run 二次调用行为**: 当 graph 已处于 paused state (WAITING 节点 + 阻塞下游), `scheduler.run()` 第二次调用时 `ready_nodes` 为空 → 立即退出, `paused=False`。Scheduler 只报告 **NEW** pauses，不报告之前已 paused 的节点。这澄清了 "resume 应该 re-report 哪些 paused 节点" 的语义 — **不 report, 通过 graph._executions 状态查询**。

2. **scheduler.run(start_nodes) 不限制执行范围**: `start_nodes` 只用于 validation + initial_inputs seed, **不限制** `ready_nodes` 循环的执行节点集合。这意味着如果 graph mutation 在 pause 后新增 root 节点, resume 会执行新节点。这不是 bug, 是 scheduler 设计 — 但值得在 spec 明确 (Phase 28 已记录)。

## Carryover to Phase 29+

| ID | 标题 | 顺位 |
|----|------|------|
| P2-MC-WRITING | 84+ pre-existing cascade failures 根因 | 独立大 phase |
| P2-ARCHDEBT | infra.got 迁移 + chapter_golden_path 反向 import + 5 薄代理 → OrchestratorProxyMixin + 删 PHASE-COMPAT shim | 战术分散 |

## Branch / Worktree

- Branch: `phase-28-resume-verify`
- Worktree: `/home/ailearn/projects/LingWen/.worktrees/phase-28-resume-verify/`
- Master HEAD: `90593350` (Phase 27 final)
- Commits: 1 spec (`05e4f91b`) + 1 plan (`d3f164c8`) + 5 tests (`02f5c90b`, `90ac327a`, `06975ceb`, `659a51e1`, `0c622659`) = **7 commits total**

## Known Limitations

- pytest.ini `env = DEEPEVAL_DISABLE_DOTENV=1` warning in worktree venv (no pytest-env installed in worktree `.venv`; not blocking — `DEEPEVAL_DISABLE_DOTENV` env var passed via pytest.ini is silently ignored, tests don't depend on it because no test triggers deepeval/langsmith plugin loading)
- Worktree `.venv/bin/python` 是 Python 3.13 (master conda 是 3.10, 无 lingwen_core)
- `uv pip install pytest pytest-asyncio psutil` 一次性安装 — `uv sync --all-packages` 不自动装 pytest (per LingWen workspace design)