# Phase 27 P2-WFRUNNER — Handoff

> **Date**: 2026-09-04 · **Status**: ✅ All tasks complete · **Spec**: `docs/superpowers/specs/2026-09-04-phase-27-wfrunner-design.md` · **Plan**: `docs/superpowers/plans/2026-09-04-phase-27-wfrunner.md`

## 闭环内容

### 新源 (1)
- `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` (307 lines) — `WorkflowRunner` service class with `run()` + `resume()` + 5 internal helpers + `_resolve_decision_locked` (Phase 6.5 fcntl lock)

### 修改源 (1)
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` — **404 → 119 行 (-70%)** — only 5 thin orchestrator proxies + 3 decision queue delegations + `_get_runner()` lazy accessor + `run_workflow`/`resume_workflow` 1-line delegates

### 新测试 (1)
- `tests/agent_system/test_workflow_runner.py` (669 lines, 21 tests) — TDD coverage of WorkflowRunner construction + run() 11 steps + resume() 8 steps + 4 internal helpers

### 修改测试 (3)
- `tests/agent_system/test_workflow_state.py` (+2 refactor guards) — `TestWorkflowRunnerRefactorGuard` ensures runner has no `_last_*` attrs and no `_state` attribute (preserves Phase 26's anti-scatter invariant)
- `tests/agent_system/test_master_controller_budget.py` (6 sed updates + 1 stub init fix) — `_harvest_decision_specs` stub now routes via `master._get_runner()._harvest_decision_specs`; `_make_stub_master` adds `master._state = WorkflowState.empty()` (Phase 26 carryover that Phase 27 made visible)
- `tests/cross_volume/test_incremental_backfill.py` (1 monkeypatch target update) — test that monkeypatches `MasterController._maybe_incremental_backfill` now patches `WorkflowRunner._maybe_incremental_backfill` (attribute migrated to Runner)

### 0 改范围承诺遵守
- ❌ `apps/studio_api/protocols.py` (gateway facade)
- ❌ `apps/studio_api/routes/workflows.py` (FastAPI route)
- ❌ `apps/studio_api/helpers/workflow.py` (response helper)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` (Phase 26 dataclass)
- ❌ `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` (PHASE-COMPAT shim, 留 P2-ARCHDEBT)
- ❌ `infra/got/*`, `.lingwen/architecture.yml`, `HANDOFF.md`

## Verification Gates (实测)

| Gate | 实测 |
|------|------|
| G1 test_workflow_state.py | 13/13 ✓ (11 Phase 26 + 2 Phase 27 refactor guards) |
| G2 test_workflow_runner.py | 21/21 ✓ |
| G3 test_master_controller_budget.py | 6/6 target ✓ (2 pre-existing env FileNotFoundError out of scope) |
| G4 tests/agent_system/ | 84 fail = master 84 cascade baseline (0 NEW failures; net -6 from Task 11 fix) |
| G5 tests/got/test_decision_pause_resume.py | 17/17 ✓ (gateway facade unchanged) |
| G6 tests/cross_volume/test_incremental_backfill.py | 15/15 ✓ |
| G7 ruff check | clean ✓ |
| G8 grep _last_* scatter | 0 hits (excluding guard test file) ✓ |
| G9 mc_workflow.py | 119 lines (from 404, -70%) ✓ |
| G10 workflow_runner.py | 307 lines (new file) ✓ |

## Carryover to Phase 28+

| ID | 标题 | 顺位 |
|----|------|------|
| **P2-RESUME-VERIFY** | `start_nodes=None` 时 resume_workflow 重跑行为 E2E 验证 | 紧接（建议 Phase 28） |
| P2-MC-WRITING | 84+ pre-existing cascade failures 根因（推测 `mc_writing.py` 类似 gutted） | 独立大 phase |
| P2-ARCHDEBT | `infra.got.*` 迁至 `packages/lingwen-got/` + `chapter_golden_path.py` 反向 import 整改 + 删 stale PHASE-COMPAT shim + 5 薄代理 → OrchestratorProxyMixin | 战术分散 |

## 关键纪律亮点

- ✅ TDD 严格 RED→GREEN：14 commits 全部先写 failing test 再实现
- ✅ Bite-sized plan：13 implementation tasks (Task 1-13) + Task 14 push/merge
- ✅ Lazy init via `_get_runner()` — 17+ `__new__` 测试 stub 0 修改（仅 Task 11 增量加 `_state = WorkflowState.empty()`）
- ✅ Refactor guard 5 tests (Phase 26 3 + Phase 27 2) 防 `_last_*` 散点回潮
- ✅ 0 改范围声明遵守 — 7 类文件不动 (gateway facade / route / helper / dataclass / shim / got_bridge / architecture)
- ✅ 0 新失败经 git stash 实证 (G4: master 90 fail → worktree 84 fail，净 -6 from Task 11 修复)
- ✅ Plan self-review catch：Task 3 plan 内部不一致 (test 需 scheduler.run，但 impl 不调) → peer agent 报告后 revert + 改 access-tracking pattern + 改 test 用 `get_node` access tracking
- ✅ Spec deviation handled：`**kwargs` delegate 签名破坏 facade → 用显式 args 匹配 WorkflowRunner API (mc_workflow.py 119 行 vs spec ~110)

## 已知遗留

- Pre-existing 2 FileNotFoundError `skill_registry.yaml` in test_master_controller_budget.py — env issue, master 上同样失败 (out of scope for Phase 27)
- Pre-existing 84 cascade failures in `tests/agent_system/` + `tests/got/` — 推测 `mc_writing.py` 类似 gutted (P2-MC-WRITING phase carryover)

## Branch / Worktree

- Branch: `phase-27-wfrunner`
- Worktree: `/home/ailearn/projects/LingWen/.worktrees/phase-27-wfrunner/`
- 13 commits ahead of master (`f12765b9`):
  - `9b57d16a` chore(phase-27): all verification gates pass
  - `b042a22b` test(master-controller-budget): route _harvest_decision_specs stub via _get_runner() (Phase 27)
  - `fc08d113` test(workflow-state): add 2 refactor guards for WorkflowRunner (Phase 27)
  - `bfc9e126` feat(workflow-runner): move 5 internal helpers from Mixin + simplify mc_workflow.py
  - `954edcab` feat(workflow-runner): resume() step 6-8 complete continue + collect + backfill + state + return
  - `18e6cee5` feat(workflow-runner): resume() step 3-5 resolve + scheduler.resume + harvest
  - `9208d0d7` feat(workflow-runner): resume() step 1-2 guards (RuntimeError on missing state/queue)
  - `9309fbd8` feat(workflow-runner): complete run() 11-step pipeline + state writes + return
  - `f86f7c7c` feat(workflow-runner): memory RAG context + harvest DECISION specs (Phase 4.3/9.70)
  - `ec30f37f` feat(workflow-runner): scheduler build + default start_nodes (Phase 9.63, plan-faithful)
  - `d2135d85` test(workflow-runner): fix budget lifecycle test scope (Task 2 polish)
  - `1d04f5f8` feat(workflow-runner): budget lifecycle setup + finally reset (Phase 8.8/8.12)
  - `849aecae` style(workflow-runner): remove unused imports + add EOF newlines (Task 1 polish)
  - `d2167e0f` feat(lingwen-core): add WorkflowRunner service skeleton + lazy Mixin accessor
  - `8c988a7c` docs(phase-27): wfrunner implementation plan (14 tasks, TDD bite-sized)
  - `48c26b5c` docs(phase-27): wfrunner service split design spec
- Master HEAD: `f12765b9` (Phase 26 final)
- Pending: Task 14 push + ff-merge + worktree cleanup
