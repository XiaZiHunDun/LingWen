# Phase 31 — ARCHDEBT-MINI Handoff

> **Branch:** `worktree-phase-31-archdebt` (6 commits ahead of `master` — 5 phase commits + 1 handoff commit)
> **Date:** 2026-09-07
> **Spec:** `docs/superpowers/specs/2026-09-07-phase-31-archdebt-mini-design.md`
> **Plan:** `docs/superpowers/plans/2026-09-07-phase-31-archdebt-mini.md`
> **Goal:** Clean up 2 minimum, isolated, high-ROI ARCHDEBT sub-tasks from the v25.9/v27/v29 P2-ARCHDEBT backlog: (A) fix `chapter_golden_path.py` reverse-import of `apps.studio_api.*`; (B) consolidate the 4 (not 5 — see correction below) thin orchestrator proxies in `WorkflowMixin` into a new `OrchestratorProxyMixin`. Zero behavior change.

---

## Summary

Phase 31 ARCHDEBT-MINI completes 2 of 4 P2-ARCHDEBT sub-tasks (A: `chapter_golden_path` reverse-import fix, B: `OrchestratorProxyMixin` extraction) plus a stale-docstring sweep across 12 doc files. Zero behavior change. 5 atomic commits (`ff3ad52b` intermediate + `353a9891` c1 + `2f8a4863` c2 + `8f8c3e1a` c3 + `ec130269` c4). All G1–G11 verification gates green (G1 `tests/agent_system` 480 → 485, +5 from new `TestOrchestratorProxyMixin`; G2 `tests/got` 156 unchanged; G3a `lingwen-core/tests` 68 unchanged; G3b ruff clean).

---

## Final verification gates

| Gate | Command | Phase 30 baseline | Phase 31 final | Delta |
|------|---------|-------------------|----------------|-------|
| G1 (`tests/agent_system` full) | `.venv/bin/python -m pytest tests/agent_system -q --tb=no` | **0 failed, 480 passed, 20 skipped** | **0 failed, 485 passed, 20 skipped** | **0 / +5 / 0** |
| G2 (`tests/got`) | `.venv/bin/python -m pytest tests/got -q --tb=no` | 156 passed | 156 passed | 0 |
| G3a (`packages/lingwen-core/tests/`) | `.venv/bin/python -m pytest packages/lingwen-core/tests/ -q` | 68 passed | 68 passed | 0 |
| G3b (ruff) | `ruff check packages/lingwen-core/src/lingwen_core/agents/` | clean | clean | 0 |

**Net result: +5 new tests (OrchestratorProxyMixin refactor-guards). 0 new failures, 0 behavior change.** All other gates unchanged.

---

## Scope

**IN (executed this phase):**
- **Sub-task A** — `chapter_golden_path.py` reverse-import fix: `create_golden_dashboard_client` + `run_human_review_smoke` + `HumanReviewSmokeResult` moved from `packages/lingwen-core/.../chapter_golden_path.py` to new `apps/studio_api/tests/golden_path_smoke.py`. Fixes I001 *spirit* violation (lingwen-core no longer imports `apps.studio_api.*`).
- **Sub-task B** — `OrchestratorProxyMixin` extraction: 4 thin proxies (`advance_step` / `dispatch_task` / `verify_task` / `get_workflow_status`) moved from `WorkflowMixin` to dedicated `mc_orchestrator_proxy.py`. `MasterController` MRO updated to include `OrchestratorProxyMixin` first. Pure passthrough — zero added logic.
- **Doc sync** — Stale "5 薄代理" / "5 thin proxies" corrected to "4" across 12 doc files (mechanical `sed` replacement, no semantic changes).

**DEFERRED to Phase 32+:**
- `infra.got.*` → `packages/lingwen-got/` migration (1 phase, 20–30 commits, ~199 tests, multi-day)
- `infra/subplot/data_structures.py` + `infra/world_model/data_structures.py` deletion (Phase 33 candidate A; 0 consumers, high confidence) — **CLOSED by Phase 32** (both deleted)
- `MasterController` shim deletion (Phase 33 candidate B; 11 lines + 6 test consumers, needs migration commit + deletion)
- `infra/world_model/__init__.py` split into root API + behavior services (Phase 34+; multi-phase)

---

## Sub-task A — chapter_golden_path reverse-import fix

**Files touched (3):**

| File | Lines | Type |
|------|-------|------|
| `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py` | −87 | prod (delete dashboard-side symbols) |
| `apps/studio_api/tests/golden_path_smoke.py` | new (106 lines) | new file (moved code, no new logic) |
| `tests/dashboard/test_human_review_smoke.py` | +4 / −3 | test (import path update: `chapter_golden_path` → `apps.studio_api.tests.golden_path_smoke`) |
| `tests/ci/test_human_review_smoke_f61_ci.py` | +5 / −5 | test (CI contract test asserts symbols in new location) |

**Architecture rationale:** The split follows **invariant I001 *spirit*** (not just letter): `infra/` (and now `packages/lingwen-core/`) must not depend on `apps/`. Previously `chapter_golden_path.py` did `from fastapi.testclient import TestClient` and assembled a `TestClient(app=...)` instance — a FastAPI-side concern living in core. Now:

- `lingwen_core.agents.chapter_golden_path` keeps only MC-side helpers (`build_stub_master_controller`, `setup_golden_workflow_dir`, `run_golden_path`).
- `apps/studio_api.tests.golden_path_smoke` owns the FastAPI/TestClient assembly (`create_golden_dashboard_client`, `run_human_review_smoke`, `HumanReviewSmokeResult`).

This is the **first** I001 violation found in `packages/lingwen-core/` (v19.2 had fixed the equivalent in `infra/world_model/`). Phase 31 closes it.

---

## Sub-task B — OrchestratorProxyMixin extraction

**Files touched (3):**

| File | Lines | Type |
|------|-------|------|
| `packages/lingwen-core/src/lingwen_core/agents/mc_orchestrator_proxy.py` | new (58 lines) | new file (4 thin proxies + class-level docstring) |
| `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` | +6 / −34 (net −28) | prod (delete 4 proxies + add "已搬到 mc_orchestrator_proxy" cross-ref docstring) |
| `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py` | +3 / −2 | prod (MRO: add `OrchestratorProxyMixin` to imports + class bases) |
| `tests/agent_system/test_workflow_state.py` | new `TestOrchestratorProxyMixin` class (5 tests, +73 lines) | test (refactor-guards: 4 forwarders + MRO membership) |

**The 4 thin proxies** (moved verbatim, signature preserved):
1. `advance_step(target_step, context=None) -> Tuple[bool, str]` → `self._orchestrator.advance_step(...)`
2. `dispatch_task(task_type, agent_id, payload, priority=...)` → `self._orchestrator.dispatch_task(...)`
3. `verify_task(task_id, criteria)` → `self._orchestrator.verify_task(...)`
4. `get_workflow_status() -> Dict[str, Any]` → `self._orchestrator.get_workflow_status(...)`

**`WorkflowMixin` after extraction** now contains only:
- 3 decision-queue delegates (`resolve_decision`, `list_pending_decisions`, `get_decision_queue`)
- `_get_runner()` lazy accessor
- `run_workflow` / `resume_workflow` 1-line delegates → `WorkflowRunner`

**5 new refactor-guard tests** (in `tests/agent_system/test_workflow_state.py:179-260`):
- `test_advance_step_forwards_to_orchestrator`
- `test_dispatch_task_forwards_to_orchestrator`
- `test_verify_task_forwards_to_orchestrator`
- `test_get_workflow_status_forwards_to_orchestrator`
- `test_mixin_is_in_master_controller_mro` (regression guard: `OrchestratorProxyMixin in MasterController.__mro__`)

### Correction: count was 4, not 5 (stale docstring since Phase 27)

The original ARCHDEBT backlog item said "**5** thin proxies → `OrchestratorProxyMixin`". Investigation in Phase 31 found the actual count was **4**:

- **Phase 15.0 P3-SPLIT** bundled 5 orchestrator proxies in `WorkflowMixin`.
- **Phase 27 P2-WFRUNNER** reduced the count to 4 when `WorkflowRunner.run_workflow` / `resume_workflow` split off as **runner delegates** (not orchestrator proxies — they delegate to `_get_runner()`, not `_orchestrator`).
- Docstrings and 12 carryover mentions in handoffs/specs/plans/CLAUDE.md never updated.

Phase 31 fixed the docstrings + carryover text + counts to "4 薄代理" / "4 thin proxies". The extracted `OrchestratorProxyMixin` itself documents this history in its module docstring.

---

## Doc sync (Task 8 c4) — 12 files updated

Mechanical `sed` replacement: `"5 薄代理" → "4 薄代理"` and `"5 thin proxies" → "4 thin proxies"`. No semantic changes. Files:

```
CLAUDE.md                                                         2 +/-
collaboration/BACKLOG.md                                          4 +/-
collaboration/CURRENT_STATUS.md                                   6 +/-
docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md       2 +/-
docs/superpowers/handoffs/2026-09-04-phase-28-resume-verify-handoff.md  2 +/-
docs/superpowers/handoffs/2026-09-04-phase-29-mc-writing-handoff.md     2 +/-
docs/superpowers/handoffs/2026-09-07-phase-30-tackle-14-handoff.md      2 +/-
docs/superpowers/plans/2026-09-04-phase-27-wfrunner.md             12 +/-
docs/superpowers/plans/2026-09-04-phase-28-resume-verify.md         2 +/-
docs/superpowers/specs/2026-09-04-phase-27-wfrunner-design.md      12 +/-
docs/superpowers/specs/2026-09-04-phase-28-resume-verify-design.md  4 +/-
docs/superpowers/specs/2026-09-07-phase-30-tackle-14-failures-design.md 2 +/-
```

---

## Phase 31 commit log (T1–T10)

| Task | Commit | Subject | Type | Effect |
|------|--------|---------|------|--------|
| T0 (setup) | (worktree only) | create worktree + uv sync | n/a | n/a |
| T1 | `ff3ad52b` | refactor(architecture): add apps-side golden path smoke helper (intermediate) | prod (new file, duplicated) | prepare split |
| T2 | `353a9891` | refactor(architecture): split chapter_golden_path dashboard smoke out of lingwen-core | prod + tests | Sub-task A done |
| T3 (RED) | `2f8a4863` | test(workflow_state): add OrchestratorProxyMixin refactor-guard tests (RED) | test | 5 tests RED |
| T4 (GREEN) | `8f8c3e1a` | refactor(agents): extract OrchestratorProxyMixin from WorkflowMixin | prod + MRO | Sub-task B done; 5 tests GREEN |
| T8 (docs) | `ec130269` | docs(sync): correct stale '5 thin proxies' → '4 thin proxies' across 12 files | docs | doc-sync |
| T10 (handoff) | (this commit) | docs(handoff): phase-31 ARCHDEBT-MINI handoff | docs | handoff |

**Total: 5 phase commits + this handoff commit.**

---

## Files touched (20 total)

| Category | Files | Net Δ |
|----------|-------|------|
| New prod files | `mc_orchestrator_proxy.py`, `apps/studio_api/tests/golden_path_smoke.py` | +164 |
| Modified prod files | `mc_workflow.py`, `chapter_golden_path.py`, `master_controller.py` | −87 + (rest net 0) |
| Modified test files | `test_workflow_state.py`, `test_human_review_smoke.py`, `test_human_review_smoke_f61_ci.py` | +5 tests, +76 lines test |
| Modified doc files | 12 files (CLAUDE.md + 11 docs/superpowers/*) | mechanical sed |
| New docs | `phase-31-archdebt-mini-handoff.md` (this file) | new |
| **Total diff** | (per `git diff --stat master..HEAD`) | **+282 / −150** |

---

## Carryover to Phase 32+

1. **`infra.got.*` → `packages/lingwen-got/` migration** (Phase 32 candidate):
   - ~199 tests across `infra/got/*` and consumers
   - Multi-day phase (20–30 commits)
   - Need import-linter rule update + ARCH invariant I001 reinforcement
2. **`infra/subplot/data_structures.py` + `infra/world_model/data_structures.py` deletion** (Phase 33 candidate A):
   - 0 consumers per grep audit (high confidence)
   - Mechanical deletion + ruff + import-linter sweep
   - **CLOSED by Phase 32** (both deleted; +1 fixup migrated 4 missed relative imports in infra/subplot/__init__.py, infra/world_model/__init__.py, infra/world_model/key_point_graph.py, infra/world_model/snapshot_store.py)
3. **`MasterController` shim deletion** (Phase 33 candidate B):
   - 11-line `master_controller.py` shim in `packages/lingwen-pipeline/`
   - 6 test consumers need migration
   - Requires migration commit + deletion commit
   - **CLOSED by Phase 32** (deleted; +1 fixup migrated 1 missed relative import in packages/lingwen-core/src/lingwen_core/agents/got_bridge.py:32)
4. **`infra/world_model/__init__.py` split** (Phase 33+):
   - Split root API surface from behavior services
   - Multi-phase, needs careful API stability review
5. **Phase 114 prod preview regression** (still accepted debt — do NOT attempt fix).

---

## Lessons learned

1. **Spec verification with ruff:** The plan's `apps/studio_api/tests/golden_path_smoke.py` import order had `from dataclasses import asdict, dataclass` AFTER `from pathlib import Path` — ruff I001 caught this on the first `git commit`. Lesson: **verify import order with `ruff check --fix` before committing any new file**, especially after copying from another module.

2. **Stale counts propagate:** Spec said "5 薄代理" but the actual count was 4 since Phase 27 P2-WFRUNNER. The Phase 27 handoff itself contained the stale count. Lesson: **when doc-syncing a count, cross-check the actual code** (`grep -c "^    def <method>" <file>`) and trace back through the git history when the count seems suspiciously stable.

3. **Worktree venv dependency gaps:** Fresh `uv sync --all-packages` does NOT include `pytest-timeout` or `pytest-cov`. Full test runs that touch timeout-decorated tests need `uv pip install pytest-timeout pytest-cov`. (Added in Task 9 verification setup.)

4. **Refactor-guard tests are cheap insurance:** The 5 new tests in `TestOrchestratorProxyMixin` are <100 lines but prevent the next person from accidentally moving a proxy back into `WorkflowMixin` or breaking the MRO. TDD discipline paid off — RED → GREEN with zero behavior change.

---

## Branch state — ready for ff-merge

```
Branch:  worktree-phase-31-archdebt
Ahead:   5 commits ahead of master (clean working tree for tracked files)
Commits: ec130269 docs(sync): correct stale '5 thin proxies' → '4 thin proxies' across 12 files
         8f8c3e1a refactor(agents): extract OrchestratorProxyMixin from WorkflowMixin
         2f8a4863 test(workflow_state): add OrchestratorProxyMixin refactor-guard tests (RED)
         353a9891 refactor(architecture): split chapter_golden_path dashboard smoke out of lingwen-core
         ff3ad52b refactor(architecture): add apps-side golden path smoke helper (intermediate)
         58717f1b chore(phase-30): state sync (CURRENT_STATUS + BACKLOG + CLAUDE.md)   ← master HEAD
         (this handoff commit)
```

**Per project workflow rule (2026-09-01):** "No more PRs; for future phases: work in worktree, commit atomically per task, push branch directly, merge locally, push master." Human approval is required to run `git checkout master && git merge --ff-only worktree-phase-31-archdebt && git push origin master`. This handoff document does not run that command. Task 11 (state sync + ff-merge) is the next step.

---

## Baseline vs final state

| Metric | Phase 30 final | Phase 31 final | Delta |
|--------|----------------|----------------|-------|
| `tests/agent_system` failed | 0 | 0 | 0 |
| `tests/agent_system` passed | 480 | **485** | **+5** |
| `tests/agent_system` skipped | 20 | 20 | 0 |
| `tests/got` passed | 156 | 156 | 0 |
| `packages/lingwen-core/tests/` passed | 68 | 68 | 0 |
| ruff check (`packages/lingwen-core/src/lingwen_core/agents/`) | clean | clean | 0 |
| Production files touched | n/a | **3 + 2 new** | +5 |
| Test files touched | n/a | 3 | +3 |
| Doc files touched (sed) | n/a | 12 | +12 |
| Doc files added | n/a | 1 (handoff) | +1 |
| Total commits since master | n/a | 6 (5 phase + 1 handoff) | +6 |

Phase 31 delivered the targeted 2-sub-task ARCHDEBT cleanup (A: I001-spirit violation fix; B: 4-proxy mixin extraction) plus a 12-file doc-sync correction, with **+5 new refactor-guard tests**, **0 new failures**, and **0 behavior change**.