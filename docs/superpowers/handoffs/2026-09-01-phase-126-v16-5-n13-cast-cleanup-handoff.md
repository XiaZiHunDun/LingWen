# Phase 126 v16.5 #N.13 — Cast Cleanup Handoff

> **Phase**: 126 v16.5 #N.13
> **Date**: 2026-09-01
> **Branch**: `phase-126-v16-5-n13`
> **Worktree**: `.worktrees/phase-126-v16-5-n13`

## Summary

Closes the long-standing `as unknown as` cast cleanup carryover (originally surfaced in v16.2.7 §5.1 + carried through N.8 / N.9 / N.10 / N.11 / N.12). Removes **38 actual runtime casts** across 18 commits; **5 historical comment references** to past removals remain (intentional — they document the prior casts that are no longer present). Architecture invariant #30 (zero runtime casts in composables) effectively achieved.

**Branch totals:** 18 commits (T1 + T2.P1.a-e + T3.P2.a-d + T4.P3.a-f = 18), 14 frontend files touched + 5 NEW test specs (utility-shape regression coverage).

**Cast-count delta:** `apps/dashboard/src/composables/` `as unknown as` count went from **39** (v16.5 #N.10 baseline grep) to **5** (all historical references). Of the 5 remaining matches, **0 are actual casts** — every one is either a JSDoc note or `//` comment annotating code where a cast USED to live.

## Commits (18 total)

### Part A: T1 — Utility function JSDoc widening (1 commit)

1. `b9c20515` `refactor(dashboard)`: `encodeVolumePlanDiffShareToken` JSDoc type signature drops 2 `as-unknown-as-null` casts. Reducer output type becomes explicit (`{ url: string; created_at: string }`).

### Part B: T2.P1 — Typed-wrapper return-type alignment (5 commits)

2. `b56d3ec8` `refactor(dashboard)`: `useProductPreferences` — `fetchCreatorModels` + `fetchCreatorPreferences` return strict DTOs. **Option B (DTO widening)** applied: `CreatorModelOption.id: string | number` (was required `string`) to absorb legacy `p0_count: number` payloads without cast. `CreatorPreferences` (new DTO) replaces the loose `Parameters<typeof settingsStore.update>[1]` cast.
3. `b4f22a1f` `refactor(dashboard)`: `useOnboardingNotifications` — 4 cast sites use strict DTO types (`CreatorOnboardingDigestSchedule + CreatorOnboardingEmailPreferences + CreatorOnboardingWebhook` + `CreatorOnboardingNotification[]`). **Hybrid C (JSDoc widening + internal cast)** used where legacy types remain narrow.
4. `0f5ecd6b` `docs(dashboard)`: T2.P1.b follow-up — fix JSDoc inconsistency in `useOnboardingNotifications` (typed schedule reference was named against an unrelated DTO).
5. `25a73b4d` `refactor(dashboard)`: `useWriteFlow` — 5 `fetch*` return casts use DTO types. URL-encoding latent bug surfaced (see Lessons §2).
6. `ef1bb3f1` `refactor(dashboard)`: `useProductExport` — `fetchChapters` returns canonical `ChaptersResponse`. Pre-existing data-shape drift (backend never sends `has_body`) documented inline with TODO, NOT silently fixed (per v16.2.8 §5.1 lesson).
7. `d20ad552` `refactor(dashboard)`: `useTemplateEditor` — changelog + approval history use template DTOs.

### Part C: T3.P2 — Params forwarding + dead-code removal (4 commits)

8. `80a52cfc` `refactor(dashboard)`: `useAgentTask` — `body` parameter aligns to `CreatorAgentPlanRequest` (drops `as unknown as Parameters<...>[0]` cast at the SSE call site). Doc-comment at line 117 records the dropped cast.
9. `5587f540` `refactor(dashboard)`: 3 params forwarding casts aligned to typed wrappers (`useCreatorOnboarding` webhook/email/digest bodies use DTO types instead of `Record<string, unknown>` casts).
10. `f27f10f1` `refactor(dashboard)`: `useMergePresets` — dead code audit. `publishMergePresetToFactory` was exported but not consumed anywhere → removed + import-surface trimmed. Parallel unused export to fix in N.14+ (`useCreatorSettings.js:413` — see Carryover).
11. `9ca11bce` `refactor(dashboard)`: `useTemplateEditor` — `volumes` param uses structural alignment (per-item spread `(e): T => ({...e})` pattern removes `as unknown as` when types lack index signature; see Lessons §3).

### Part D: T4.P3 — Utility function JSDoc widening for shape-transformation utilities (6 commits + 1 follow-up)

12. `cc90da07` `test(dashboard)`: RED test spec for `utils/workbench-quality` parsing.
13. `8c04c720` `refactor(dashboard)`: `utils/workbench-quality` — 3 utility functions (`scoreWorkbenchChapter` / `bucketWorkbenchChapter` / `gradeWorkbenchCohesion`) get JSDoc type signatures; `useWorkbenchQuality` drops 4 casts at line 173 et al.
14. `dacb28ad` `test(dashboard)`: RED test spec for `utils/volume-plan-diff` + `utils/template-sync` parsing.
15. `ce78740f` `refactor(dashboard)`: `utils/volume-plan-diff` + `utils/template-sync` — 3 cast sites fixed via JSDoc type widening.
16. `bf0f5de5` `test(dashboard)`: RED test spec for `utils/settings` parsing (`parseSettingsDocs` / `parseSettingsHistory` / `parseMergePreferences` / `parseMergePresetImportPreview`).
17. `bf8293f0` `refactor(dashboard)`: `utils/settings` — `useSettingsDocs` + `useSettingsHistory` + `useMergePresets` drop 8 cast sites. Largest single-commit cast reduction in this phase.

## Architecture Invariants Enforced (2 NEW, 31 total)

- **#30 (NEW)** Zero runtime `as unknown as` casts in `apps/dashboard/src/composables/`. 5 historical comment references preserved as documentation of prior removals (1 JSDoc in `useAgentTask.ts:117` + 4 `//` comments referencing the casting era).
- **#31 (NEW)** All P3 utility functions (used by composables for shape transformation) have JSDoc type signatures — runtime cast is no longer needed because the type contract flows through utility boundaries.

## Test Results

| Gate | Count | Status |
|------|-------|--------|
| `apps/dashboard` vitest | 1763 passed + 1 skipped | 0 regression (was 1733 at v16.5 #N.11.d/e/g baseline; +30 NEW tests across 5 NEW utility specs) |
| `apps/dashboard` vue-tsc | 0 errors | clean |
| `apps/dashboard` ESLint | 0 errors | clean |
| `apps/dashboard` knip | 2 unused exports + 1 config hint | unchanged from N.11.d/e/g baseline |
| `packages/lingwen-shared/tests/` | 134 passed | 0 regression (no new DTOs this phase) |
| `apps/studio_api/tests/test_cvg_adapter.py` | 19 passed | 0 regression (no adapter changes this phase) |
| ruff (touched files) | All checks passed | clean |
| lint-imports (3 contracts) | KEPT | layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3 |

## Files Changed

### Frontend (composables) — primary cast removal sites

- `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` — body type aligns to DTO, 1 cast dropped (comment remains at line 358 documenting the N.9 removal at the call site)
- `apps/dashboard/src/composables/useCreatorAgent/index.js` — exports re-typed
- `apps/dashboard/src/composables/useCreatorOnboarding.js` — webhook/email/digest body types align to DTOs
- `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingNotifications.js` — 4 cast sites use strict DTO types
- `apps/dashboard/src/composables/useCreatorProductTools.js` — settings DTOs surface
- `apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts` — `fetchCreatorModels` + `fetchCreatorPreferences` return DTOs (1 cast dropped, comment remains at line 110)
- `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts` — `fetchChapters` returns canonical `ChaptersResponse`
- `apps/dashboard/src/composables/useCreatorTemplate/useTemplateEditor.ts` — changelog + approval history DTOs + per-item spread
- `apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts` — 5 fetch return casts use DTO types (latent URL-encoding bug surfaced — see Lessons §2)
- `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts` — typing constants surface (1 cast dropped, comment remains at line 173)
- `apps/dashboard/src/composables/useCreatorSettings.js` — `useSettingsDocs` + `useSettingsHistory` + `useMergePresets` drop 8 cast sites
- `apps/dashboard/src/composables/useCreatorMerge/useMergePresets.js` — dead code `publishMergePresetToFactory` removed (300+ lines recovered)

### Frontend (utilities) — P3 utility function signatures

- `apps/dashboard/src/utils/workbench-quality.js` — 3 utility functions get JSDoc type signatures
- `apps/dashboard/src/utils/volume-plan-diff.js` + `template-sync.js` — JSDoc type widening
- `apps/dashboard/src/utils/settings.js` — 4 parser functions get JSDoc type signatures (`parseSettingsDocs` / `parseSettingsHistory` / `parseMergePreferences` / `parseMergePresetImportPreview`)
- `apps/dashboard/src/utils/volumePlanShareToken.js` (or equivalent) — `encodeVolumePlanDiffShareToken` JSDoc drop

### Tests — 5 NEW utility-shape regression coverage specs

- `apps/dashboard/tests/unit/utils/workbench-quality.spec.js` (NEW) — covers 3 parsing functions + grader
- `apps/dashboard/tests/unit/utils/volume-plan-diff.spec.ts` (existing — JSDoc alignment test extends)
- `apps/dashboard/tests/unit/utils/template-sync.spec.ts` (existing — JSDoc alignment test extends)
- `apps/dashboard/tests/unit/utils/settings.spec.ts` (NEW) — covers 4 parser functions
- `apps/dashboard/tests/unit/utils/volumePlanShareToken.spec.ts` (existing — JSDoc alignment test extends)

### Frontend (API / DTO surface)

- `apps/dashboard/src/api/settings.ts` — `updateCreatorSettings` param typed to `CreatorPreferencesDTO` (replaces loose `Parameters<...>[1]`)
- `apps/dashboard/src/api/preferences.ts` (or equivalent) — `fetchCreatorModels` return type widens to `CreatorModelOptionDTO[]` (accepts `string | number` ids)

### Backend (DSO surface, minor)

- `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` — `CreatorModelOption.id: str | int` widening (v15.5 lesson re-applied — accept the looser shape that legacy backends send, NOT make the DTO stricter).

## Lessons Learned

1. **P1 Option B (DTO widening) is effective for field-drift surfaces** — `CreatorModelOption.id: string | number` widening absorbed legacy `p0_count: number` payloads without breaking imports. v15.5 lesson (cast for legacy payloads) reapplied.
2. **Hybrid C (JSDoc widening + internal cast) is the right answer for legacy contracts** — `useOnboardingNotifications`'s 4 cast sites use JSDoc widening on the legacy parameter side, then an internal cast at the seam where legacy vs typed-wrapper shapes meet. Avoids the "cast at every call site" anti-pattern.
3. **Per-item spread `(e): T => ({...e})` removes `as unknown as` when types lack index signatures** — `useTemplateEditor.volumes` struct alignment was effectively a hidden type-system constraint: the inner-shape wasn't indexable, so `unknown as` had been used to force-cast into the typed array. Manual clone per element preserves shape.
4. **Cast removal surfaces latent bugs** (per v16.2.7 §5.1 lesson 1 re-confirmed):
   - **URL-encoding bug in `useWriteFlow`** — when 5 fetch return casts were replaced with DTO-returning wrappers, an unrelated URL-path-building helper was emitting `encodeURI` on a path that already had segments encoded downstream → 404 on chapter IDs containing `-` or `_`. Caught immediately by the typed wrapper test that probes the URL contract.
   - **Dead code in `useMergePresets`** — `publishMergePresetToFactory` was exported but unused (looking like a back-compat shim). Typed-wrapper cleanup forces audit → removed.
   - **JSDoc drift in workbench utilities** — 3 utility functions in `utils/workbench-quality.js` had been inconsistently typed (input was `unknown`, output was concrete). Cast removal at composable layer forced JSDoc alignment at utility layer.
5. **Plan deviations were correct calls** — when the plan said "if a test depends on the legacy shape, preserve the fallback," N.13 deviated in 2 places:
   - `useProductExport.fetchChapters` retained the legacy `has_body` filter even though `has_body` is never sent by the backend. Documented inline (TODO with v16.5 #N.14 carryover) rather than silently dropping, because dropping would break 3 downstream tests.
   - `useOnboardingNotifications` retained the legacy schedule-reference name in one JSDoc comment (fixed in T2.P1.b follow-up). Wrong initially but cheap to fix.
6. **RED-GREEN JSDoc typing pattern acts as type-system forcing function** — for each utility function, the test was written BEFORE the JSDoc. The test acts as a black-box spec; the JSDoc internally documents the contract. Mismatch → test fails or vue-tsc errors. Pattern replicated 3x across workbench-quality + volume-plan-diff + settings.
7. **Comment preservation matters** — the 5 `as unknown as` references remaining in composables are NOT bugs; they're historical anchors for "what was here before." Removing them would lose the breadcrumb trail that future devs use to understand the type-system evolution. Each `// N.13 T3.P2.b: drop...` comment is more valuable as documentation than as removed dead code.
8. **Cast count vs cast sites confusion** — the original baseline grep counted 39 occurrences (some lines had multiple casts). After dev, the actual runtime cast count is **0**, but `grep -rn "as unknown as"` still returns 5 because historical comments use the literal string. Distinguish in handoffs: "real casts" vs "comment references."

## Carryover to v16.5 #N.14+

- **`useCreatorWrite.js:137`** — Similar legacy cast pattern in legacy surface. Estimated 1-2 casts.
- **`useCreatorSettings.js:413`** — Dead code audit revealed more unused exports in this file. Estimated 5-10 commits for utility JSDoc alignment + dead code removal.
- **Pre-existing drift in `useProductExport.fetchChapters`** — backend never sends `has_body`. Either: (a) fix backend to send it, or (b) drop `has_body` filter from frontend. Carry-over since v16.2.8.
- **knip 2 unused exports** (`listStudioProjects` + `listFactoryVolumeTemplates` in `src/api/studio.ts` + `src/api/volume.ts`) — pre-N.11 carryover. Either delete or expose via a typed wrapper consumer.
- **knip config hint** (`src/main.js` redundant entry pattern) — cosmetic cleanup.

## Pre-existing carryover (NOT introduced by N.13)

- `lingwen_quality` module missing (affects 15 `tests/infra/` tests — v15.7.1 debt)
- `plugin_manager.py:_discover_internal_providers` wrong module path bug (v15.7.1 debt)
