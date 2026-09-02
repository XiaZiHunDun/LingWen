# Phase 23 — Pilot Page · Handoff

> **Date**: 2026-09-02
> **Branch**: `phase-23-pilot-page`
> **Commits**: 19 source commits `c0910284..948173ff`
> **First new feature phase since Phase 115 Write Workspace (v15.0)** — closes the longest LingWen dry spell (~10 months).

## What shipped

### Backend (6 source commits + 1 fixup)
- **`infra/studio_batch_runner.py` `cancel_batch_job()`** (T1): SIGTERM + 5s grace + SIGKILL fallback. Includes `/proc/<pid>/status` State field check for zombie detection — `os.kill(pid, 0)` returns success for zombies, so the State field check (`State: Z`) is required for reliable detection. (`c0910284`)
- **Test for SIGKILL fallback path** (T2): SIGTERM-ignoring process scenario. (`46d43f07`)
- **Test fixup** (T2.fix): `proc.wait()` to eliminate ResourceWarning + use monotonic clock for elapsed-time assertions. (`ad990edc`)
- **`POST /api/studio/batch/<job_id>/cancel`** route (T3): 404/409/200 semantics (404 if not found, 409 if already finished, 200 if cancelled). (`97711d58`)
- **`compute_pilot_eta()`** pure helper (T4): ETA from completed chapters + elapsed time. No I/O. (`4a89d8f1`)
- **`GET /api/studio/batch/history`** route (T6): list past batch jobs for a slug. (`e4317088`)

### Frontend (11 source commits + 1 fixup)
- **`cancelStudioBatchJob`** API wrapper (T5): uses `request()` helper, no `/api/` prefix. Fixup commit `f5e6c7ef` corrected plan's raw `fetch()` + `/api/` prefix regression. (`95a09a61` + `f5e6c7ef`)
- **`listStudioBatchJobs`** API wrapper + history route wire-up (T6): uses `request()` helper. (`e4317088`)
- **`usePilotBatch()` composable** (T7): state + actions + 3s auto-polling + ETA scaffolding + history list. (`ce5f3a8d`)
- **`PilotStartForm` + `PilotPreflightTable`** (T8): form for starting a new batch + preflight summary display. (`7c054948`)
- **`PilotLivePanel`** (T9): live status + ETA + log tail + cancel button. (`0c0408eb`)
- **`PilotCancelDialog`** (T10): confirm-with-grace (shows 5s grace period explanation). (`cfe03dac`)
- **`PilotHistoryList`** (T11): status table + select-job emit. (`c9534f14`)
- **`PilotPage.vue`** (T12): top-level page assembling 4 components + composable wiring + `useStudioProject` context. (`2a66985a`)
- **Nav entry** (T13): added `pilot` to `humanFirstNav.js` + `dashboardNavByMode.js` + `navConstants.ts` + `router/index.js`. (`bbcbc291`)

### Cleanup (2 source commits)
- **`StudioPage.vue` cleanup** (T14): removed embedded Pilot section (-369 lines). Pilot is now exclusively in PilotPage. (`75be85d1`)
- **`composables/index.ts` export fixup** (T15): export `usePilotBatch` from the composables barrel (was missing). (`c0ca75d0`)

### Hygiene (1 commit)
- **`knip unused export + ESLint testid sync + no-store-value + ruff format`** (T16): dead code removal + testid class sync + `noStore()` style cleanup + ruff format re-check. (`948173ff`)

## Architecture invariants

### 1 NEW invariant

- **#48** ✅ `PilotPage` owns batch lifecycle surface; `StudioPage` MUST NOT host embedded Pilot start/preflight/job panel. Scope: `apps/dashboard/src/pages/StudioPage.vue`.

All 47 previous invariants preserved.

## Verification gates (all green)

| Gate | Result |
|------|--------|
| vitest | **1800 passed + 1 skipped** (1762 baseline + 38 new from Phase 23) |
| vue-tsc | 0 errors |
| ESLint | 0 errors |
| knip | `{"issues":[]}` |
| ruff check | clean |
| ruff format --check | 1201 files already formatted |
| lint-imports | 3 contracts KEPT (316 files / 1388 deps) |

## Test counts added (54 NEW tests)

| Surface | Tests |
|---|---|
| Backend batch runner cancel (Task 1+2) | 4 |
| Backend batch runner ETA (Task 4) | 3 |
| Backend cancel route (Task 3) | 3 |
| Backend history route (Task 6) | 4 |
| Frontend cancelStudioBatchJob (Task 5) | 3 |
| Frontend listStudioBatchJobs (Task 6) | 4 |
| Frontend usePilotBatch (Task 7) | 5 |
| Frontend PilotStartForm + PilotPreflightTable (Task 8) | 7 |
| Frontend PilotLivePanel (Task 9) | 7 |
| Frontend PilotCancelDialog (Task 10) | 4 |
| Frontend PilotHistoryList (Task 11) | 4 |
| Frontend PilotPage (Task 12) | 3 |
| Frontend dashboardNav (Task 13) | 3 |
| **TOTAL** | **54 NEW tests** |

## Lessons

1. **Verify-before-design** (N.14 lesson 1, re-confirmed across all phases): The plan's Task 5 spec used raw `fetch()` + hardcoded `/api/` prefix; both were v16.2.1 regressions. The spec reviewer caught the deviation via `request()` convention deviation. The fixup commit `f5e6c7ef` was added to replace the raw fetch with `request()`.

2. **Plan references to non-existent APIs must be substituted, not failed** — Task 7 referenced `fetchStudioStartBatchJob` (which does not exist). The implementer substituted the canonical wrapper `studioProductionRun` and documented the deviation. Don't blindly fail when a plan references a missing API — substitute the closest canonical one and document.

3. **`mount(..., { attachTo: true })` is invalid in vue-test-utils v2.4.11** — only accepts `string | Element | undefined`. Boolean `true` raises both a runtime error (`to.appendChild is not a function`) and a TS error. Use `attachTo: document.body` or omit. (PilotLivePanel tests caught this.)

4. **`<button type="submit">` inside form + `trigger('click')`** doesn't simulate form submission in jsdom. Use `type="button"` with explicit `@click` handler; `@submit.prevent` still captures Enter-key accessibility. (PilotStartForm tests caught this.)

5. **DTO re-export chain requires BOTH `studio.ts` AND `index.ts`** — wrapper imports from `'@lingwen/dashboard-contracts/shared'` which resolves to `shared/index.ts`. Adding only to `studio.ts` leaves the import unresolved. tsc catches this — but without tsc, the wrapper would compile but fail at runtime.

6. **`DASHBOARD_NAV_ENTRIES` array doesn't exist** in `dashboardNav.js`. The real nav system is distributed across `humanFirstNav.js` + `dashboardNavByMode.js` + `navConstants.ts` + `router/index.js`. Adding to all 4 files is the correct minimum change.

7. **`/proc/<pid>/status` State field check is Linux-specific** but currently the production env is Linux-only. `os.kill(pid, 0)` returns success for zombies, so we needed the State field check (`State: Z`) for reliable zombie detection. Add inline comment if portability is needed.

8. **`request()` from `core.js` is the canonical wrapper pattern**, NOT raw `fetch()`. It provides timeout, retry, typed error mapping, `markApiOnline` side effect, and `API_ERROR_EVENT` emission. All Phase 23 wrappers use this.

9. **Atomic 1-task-per-commit scales to 19** — 19 commits on a single feature phase is a lot, but each commit has one logical unit (one component, one test file, one route). Easy to review, easy to revert, easy to bisect.

10. **Backend + frontend feature phase must coordinate DTO additions** — when `StudioBatchJobListResponseDTO` was added to `lingwen_shared`, the re-export chain (`packages/dashboard-contracts/src/shared/{studio,index}.ts`) had to be updated in lockstep. The test infra (zod reverse validation) catches drift at CI time.

11. **PilotPage owns the surface, not StudioPage** — invariant #48 was created specifically to prevent future regressions where Pilot is re-embedded into StudioPage. The cleanup of StudioPage.vue (-369 lines) demonstrates the actual saved complexity from extracting.

12. **3s polling is acceptable for MVP; SSE is the next step** — the polling design is documented as a carryover for Phase 24+. SSE/WebSocket will replace it once event-stream infra is wired (Phase 126 v16.5 #N.7 only typed the agent-plan SSE; pilot is a different surface).

## Carryover to Phase 24+

- **SSE/WebSocket real-time progress** — replace 3s polling with push (reduces server load + improves UX latency).
- **Per-chapter preview drawer** in PilotLivePanel — show chapter text on click for verification.
- **Batch templates** — save common mode/budget/chapters combos for reuse across projects.
- **Multi-LLM provider concurrent batches** — different chapters use different providers in parallel.
- **Pilot + Insight dashboard integration** — surface Pilot status in the main dashboard.
- **Batch priority queue** — high-priority batches jump the line.
- **Auto-restart on failure** — retry failed batches automatically.
- **Compose DTO migration** — `usePilotBatch` composable currently imports DTOs from `@lingwen/dashboard-contracts/shared` directly; consider migrating to `@/api/studio` re-export pattern (consistency with v16.2.4+ convention).
- **Phase 114 prod preview regression** (accepted, pre-existing).

## Files added/changed (summary)

### New frontend (8 files + 5 test files)

```
apps/dashboard/src/pages/PilotPage.vue
apps/dashboard/src/components/pilot/PilotStartForm.vue
apps/dashboard/src/components/pilot/PilotPreflightTable.vue
apps/dashboard/src/components/pilot/PilotLivePanel.vue
apps/dashboard/src/components/pilot/PilotCancelDialog.vue
apps/dashboard/src/components/pilot/PilotHistoryList.vue
apps/dashboard/src/composables/usePilotBatch.ts
apps/dashboard/src/api/studio.ts (added 2 wrappers, +2 DTOs)
```

### New tests (8 frontend test files)

```
apps/dashboard/tests/unit/components/pilot/PilotStartForm.spec.ts
apps/dashboard/tests/unit/components/pilot/PilotPreflightTable.spec.ts
apps/dashboard/tests/unit/components/pilot/PilotLivePanel.spec.ts
apps/dashboard/tests/unit/components/pilot/PilotCancelDialog.spec.ts
apps/dashboard/tests/unit/components/pilot/PilotHistoryList.spec.ts
apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts
apps/dashboard/tests/unit/pages/pilot-page.spec.ts
apps/dashboard/tests/unit/config/pilot-nav.spec.ts
apps/dashboard/tests/unit/api/cancel-studio-batch-jobs.spec.ts
apps/dashboard/tests/unit/api/list-studio-batch-jobs.spec.ts
```

### Modified frontend

```
apps/dashboard/src/api/studio.ts (added 2 wrappers + DTO interfaces, dropped dead fetchStudioBatchJob)
apps/dashboard/src/api/index.js (drop barrel re-export)
apps/dashboard/src/composables/index.ts (export usePilotBatch)
apps/dashboard/src/config/humanFirstNav.js (add pilot entry)
apps/dashboard/src/config/dashboardNavByMode.js (add pilot entry)
apps/dashboard/src/stores/navConstants.ts (add 'pilot' to VALID_NAV)
apps/dashboard/src/router/index.js (add /pilot route)
apps/dashboard/src/pages/StudioPage.vue (cleanup: -369 lines, removed embedded Pilot)
apps/dashboard/tests/unit/pages/studio-page.spec.ts (update assertions)
apps/dashboard/tests/unit/human-first-nav.spec.ts (add 'pilot' to expected order)
```

### Modified backend

```
infra/studio_batch_runner.py (added cancel_batch_job + zombie fix + compute_pilot_eta)
apps/studio_api/routes/studio.py (added cancel route + history route)
packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py (added 2 Pydantic DTOs)
packages/lingwen-shared/src/lingwen_shared/contracts/ts/studio.ts (auto-codegen)
packages/dashboard-contracts/src/shared/studio.ts (re-export chain)
packages/dashboard-contracts/src/shared/index.ts (re-export chain)
apps/studio_api/models/__init__.py (re-exports)
apps/studio_api/models/studio.py (re-exports)
tests/infra/test_studio_batch_runner_cancel.py (NEW, 4 tests + fixup)
tests/infra/test_studio_batch_runner_eta.py (NEW, 3 tests)
apps/studio_api/tests/test_studio_cancel_route.py (NEW, 3 tests)
apps/studio_api/tests/test_studio_batch_history_route.py (NEW, 4 tests)
```

### Docs

```
CLAUDE.md (v23.0 entry added at top of version list)
.lingwen/architecture.yml (version 23.0 + invariant #48 + phase_23 block)
docs/superpowers/handoffs/2026-09-02-phase-23-pilot-page-handoff.md (this file)
```

## Plan deviations (correct calls)

The plan had several minor bugs that were corrected during execution. These deviations are documented to inform future phase planning:

1. **Plan Task 5**: Spec used raw `fetch()` + hardcoded `/api/` prefix. **Fix**: Replaced with `request()` from `core.js` (canonical v16.2.1+ convention) in fixup commit `f5e6c7ef`.
2. **Plan Task 7**: Referenced `fetchStudioStartBatchJob` (non-existent wrapper). **Fix**: Substituted `studioProductionRun` (canonical) and documented the substitution.
3. **Plan Task 8**: Used `<button type="submit">` inside form. **Fix**: Changed to `type="button"` with explicit `@click` handler for jsdom test compat.
4. **Plan Task 10**: Used `attachTo: true` in mount options. **Fix**: Removed (vue-test-utils v2.4.11 rejects boolean; use `Element | string | undefined`).
5. **Plan Task 13**: Referenced `DASHBOARD_NAV_ENTRIES` (doesn't exist). **Fix**: Added entry to all 4 actual nav files (`humanFirstNav.js`, `dashboardNavByMode.js`, `navConstants.ts`, `router/index.js`).
6. **Plan Task 5/7**: Missing re-export chain entries in `dashboard-contracts/src/shared/index.ts`. **Fix**: Added during DTO propagation; tsc caught the gap.

All deviations were caught during execution or during the test/code-quality review pass. None were missed.

## Related phases

- **Phase 22 (v22.0)**: Test-env + format cleanup — immediate predecessor. Closed Phase 19+ chain carryovers and unlocked Phase 23.
- **Phase 21 (v21.0)**: Shim cleanup continuation — closed v19.3/v19.4 shim carryovers.
- **Phase 115 (v15.0)**: Write Workspace — last new feature phase before Phase 23 (8 month gap).
- **Phase 24+ (planned)**: SSE real-time + per-chapter preview + batch templates + multi-LLM concurrent (carryover from this phase).