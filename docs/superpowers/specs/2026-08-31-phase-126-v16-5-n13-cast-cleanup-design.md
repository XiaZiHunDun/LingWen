# Phase 126 v16.5 #N.13 — `as unknown as` Cast Cleanup Design

> **Date**: 2026-08-31
> **Phase**: 126 v16.5 #N.13
> **Author**: AI assistant (with user design approval)
> **Status**: Draft for user review

## Summary

Closes the **38 cast instances** (across 37 distinct lines, after excluding 2 JSDoc/comment references) accumulated in `apps/dashboard/src/composables/` since v16.2.x. `grep -rn "as unknown as" apps/dashboard/src/composables/` returns 39 lines total; 2 are comments at `useAgentTask.ts:117` (JSDoc note about past change) and `useAgentTask.ts:358` (// comment about past change). The remaining 37 lines contain 38 cast instances because `useWriteFlow.ts:206` has 2 casts on one line (P2 params forwarding + P1 return narrowing). Each cast represents a type contract gap between a typed-wrapper signature, a utility function signature, and a composable's local type assumption. This phase tightens types layer-by-layer using a pattern-stratified approach:

- **P4**: Special null casts → fix `.js` utility function JSDoc (2 casts, 1 file)
- **P1**: Typed-wrapper return narrowing → widen lingwen-shared DTOs OR use DTO subset types at call site (15 cast instances)
- **P2**: Typed-wrapper params forwarding → align caller's local types to DTO shape (6 cast instances)
- **P3**: Module-internal utility mismatch → add JSDoc types to `.js` utility functions + new vitest specs to lock behavior (15 cast instances)

**Out of scope**:
- `apps/dashboard/src/api/*.ts` (typed wrapper internals — already designed with casts)
- `apps/dashboard/tests/**/*` (test fixtures — cast is necessary for narrow assertions)
- Other directories (`components/`, `pages/`, `stores/`)

## Architecture Invariants Enforced (2 NEW, 30 total)

- **#29 (NEW)** Zero `as unknown as` casts in `apps/dashboard/src/composables/` — `grep -rn "as unknown as" apps/dashboard/src/composables/` returns 0 lines.
- **#30 (NEW)** All P3 utility functions (used by composables for shape-transformation) have JSDoc type signatures — no runtime cast needed.

## Pattern Catalog (39 casts, audited 2026-08-31)

| Pattern | Description | Cast count | Fix shape |
|---|---|---|---|
| **P1** | Typed-wrapper return narrowing | 15 | DTO widen (lingwen-shared) OR local DTO subset type |
| **P2** | Typed-wrapper params forwarding | 6 | Caller local type aligns to DTO |
| **P3** | Utility function mismatch (module-internal) | 15 | JSDoc on `.js` utility + caller alignment |
| **P4** | Special null cast | 2 | JSDoc on `.js` utility function |

### Pattern P1 — Typed-wrapper return narrowing (15 casts)

| File | Line | Function | Local target type |
|---|---|---|---|
| `useCreatorProductTools/useProductPreferences.ts` | 61 | `fetchCreatorModels()` | `{ models?: Array<{ id; label }> }` |
| `useCreatorProductTools/useProductPreferences.ts` | 74 | `fetchCreatorPreferences()` | `Record<string, unknown>` |
| `useCreatorOnboarding/useOnboardingNotifications.ts` | 140 | `fetchOnboardingNotifications()` | local type |
| `useCreatorOnboarding/useOnboardingNotifications.ts` | 148 | `buildOnboardingNotificationDigest()` | `NotificationDigest` |
| `useCreatorOnboarding/useOnboardingNotifications.ts` | 174 | `fetchDigestRetryQueue()` | `DigestQueue` |
| `useCreatorOnboarding/useOnboardingNotifications.ts` | 176 | `fetchDigestDeadLetter()` | `DigestQueue` |
| `useCreatorWrite/useWriteFlow.ts` | 145 | `fetchCreatorChapterPreview()` | `Record<string, unknown>` |
| `useCreatorWrite/useWriteFlow.ts` | 181 | (utility call) | `Record<string, unknown>` |
| `useCreatorWrite/useWriteFlow.ts` | 206 | `runCreatorLogicCheck()` | `{ p0_count?: number }` |
| `useCreatorWrite/useWriteFlow.ts` | 227 | (utility call) | `Record<string, unknown>` |
| `useCreatorWrite/useWriteFlow.ts` | 253 | (utility call) | `Record<string, unknown>` |
| `useCreatorProductTools/useProductExport.ts` | 148 | `fetchChapters()` | local type |
| `useCreatorProductTools/useProductExport.ts` | 161 | `fetchChapters()` | local type |
| `useCreatorSettings/useSettingsHistory.ts` | 65 | (typed-wrapper call) | `{ snapshots?; history? }` |
| `useCreatorVolumePlanTemplates/useTemplateEditor.ts` | 233 | `fetchVolumeTemplateChangelog()` | `{ entries?: Array<...> }` |
| `useCreatorVolumePlanTemplates/useTemplateEditor.ts` | 386 | `fetchVolumeTemplateApprovalHistory()` | `{ approvals?: Array<...> }` |

### Pattern P2 — Typed-wrapper params forwarding (6 casts)

| File | Line | Forwarding pattern |
|---|---|---|
| `useCreatorVolumePlanTemplates/useTemplateEditor.ts` | 153 | `editableVolumes.value as Parameters<typeof saveVolumeTemplate>[0]['volumes']` |
| `useCreatorAgent/useAgentTask.ts` | 365 | `body as Parameters<typeof runCreatorAgentPlan>[0]` |
| `useCreatorWrite/useWriteFlow.ts` | 206 | `{ chapter } as Parameters<typeof runCreatorLogicCheck>[0]` |
| `useCreatorProductTools/useProductPreferences.ts` | 101 | `preferencesToApi(...) as Parameters<typeof saveCreatorPreferences>[0]` |
| `useCreatorWriteWorkbench/useWorkbenchLayout.ts` | 173 | `assets as Parameters<typeof resolveChapterEntities>[0]['memoryAssets']` |
| `useCreatorSettings/useMergePresets.ts` | 185 | `{} as Parameters<typeof publishMergePresetToFactoryApi>[0]` (likely dead code — investigate during T3) |

### Pattern P3 — Utility function mismatch (15 casts)

| File | Line | Utility function | Expected arg type |
|---|---|---|---|
| `useCreatorWriteWorkbench/useWorkbenchQuality.ts` | 204 | `summarizeLightValidation` | `Array<{ level?: string }>` |
| `useCreatorWriteWorkbench/useWorkbenchQuality.ts` | 209 | `summarizeLightValidation` | same |
| `useCreatorWriteWorkbench/useWorkbenchQuality.ts` | 234 | `runLightValidation` | `LightValidationIssue[]` |
| `useCreatorWriteWorkbench/useWorkbenchQuality.ts` | 284 | `buildInlineConflictMarkers` | `InlineConflictMarker[]` |
| `useCreatorVolumePlanDiff/useVolumePlanDiff.ts` | 144 | (typed wrapper call) | `CreatorVolumePlanEntry[]` |
| `useCreatorVolumePlanDiff/useVolumePlanDiff.ts` | 145 | (typed wrapper call) | `DiffPreview` |
| `useCreatorVolumePlanTemplates/useTemplateSync.ts` | 202 | (typed wrapper call) | `AppliedResult` |
| `useCreatorSettings/useSettingsDocs.ts` | 79 | local assign | `SettingsDocs` |
| `useCreatorSettings/useSettingsDocs.ts` | 82 | local assign | `SettingsDocs` |
| `useCreatorSettings/useSettingsDocs.ts` | 83 | local assign | `Record<string, unknown>` |
| `useCreatorSettings/useSettingsDocs.ts` | 85 | local assign | `SettingsDocs` |
| `useCreatorSettings/useSettingsDocs.ts` | 86 | local assign | `Record<string, unknown>` |
| `useCreatorSettings/useMergePresets.ts` | 131 | local assign | `MergePreferences` |
| `useCreatorSettings/useMergePresets.ts` | 262 | local assign | `{ added; updated; removed }` |
| (1 more — confirm during T4 audit) | — | — | — |

### Pattern P4 — Special null cast (2 casts)

| File | Line | Cast |
|---|---|---|
| `useCreatorVolumePlanDiff/useVolumePlanDiffShare.ts` | 114 | `draft as unknown as null` |
| `useCreatorVolumePlanDiff/useVolumePlanDiffShare.ts` | 115 | `collabNotes as unknown as null` |

Fix: Add JSDoc to `encodeVolumePlanDiffShareToken` `.js` function so TS infers `draft`/`collabNotes` as `string | null` natively.

## Fix Strategy per Pattern

### P1 Fix Strategy

For each cast:
1. Read the typed-wrapper file (`apps/dashboard/src/api/*.ts`) to see the actual return DTO shape.
2. Compare to the caller's local target type.
3. **Option A**: DTO matches → remove cast, use DTO field directly.
4. **Option B**: DTO missing fields → widen lingwen-shared DTO (`packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py`) + regenerate TS via `python tooling/contracts/generate.py`.
5. **Option C**: DTO has more fields than needed → declare local DTO-subset interface in composable.

All Pydantic models in `lingwen-shared` MUST have `model_config = ConfigDict(extra="ignore")` to tolerate widened backend responses without validation failure.

### P2 Fix Strategy

For each cast:
1. Read typed-wrapper's parameter type.
2. Compare to caller's local type that builds the arg.
3. If structurally compatible → remove cast.
4. If local type is structurally compatible but uses `Record<string, unknown>` for simplicity → add typed local declaration matching DTO shape.
5. Special investigation: `useMergePresets.ts:185` `{} as Parameters<...>[0]` looks like dead code — verify call site usage, potentially delete.

### P3 Fix Strategy

For each utility function:
1. Identify the `.js` file with the untyped function.
2. Add JSDoc with `@param` for each input + `@returns` for output.
3. If utility references types from other modules, use `@typedef {import(...)}` to import types.
4. Add vitest spec covering happy path + edge cases.
5. Remove cast at call site (now type-safe via JSDoc).

### P4 Fix Strategy

For `encodeVolumePlanDiffShareToken`:
1. Add JSDoc `@param {string | null} draft` + `@param {string | null} collabNotes`.
2. Cast `draft as unknown as null` becomes redundant (TS infers `string | null`).
3. Add vitest spec covering null arg cases (if spec doesn't exist).

## Test Strategy

### Primary gate: `pnpm tsc --noEmit`

The "RED test" for each cast fix = vue-tsc error pointing to the cast site. "GREEN" = cast removed + vue-tsc 0 errors.

### Secondary gates

```bash
# Architecture invariant #29 verification
grep -rn "as unknown as" apps/dashboard/src/composables/
# Expected: 0 lines

# Full regression
cd apps/dashboard
pnpm vitest run --reporter=basic
pnpm tsc --noEmit
pnpm eslint .
pnpm exec knip
```

### Backend gate (T2 P1 may touch lingwen-shared)

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ packages/lingwen-creator/tests/
ruff check packages/lingwen-shared/src/lingwen_shared/contracts/python/
```

### NEW vitest specs (P3 + P4)

| Spec file (NEW) | Covers | Tests |
|---|---|---|
| `apps/dashboard/tests/unit/utils/workbench-quality.spec.ts` | `summarizeLightValidation`, `runLightValidation`, `buildInlineConflictMarkers`, `summarizeInlineConflicts` | 6-8 |
| `apps/dashboard/tests/unit/utils/volume-plan-diff.spec.ts` | `buildVolumePlanDiffPreview`, `applyVolumePlanDiff`, `buildDiffPreview`, plus `encodeVolumePlanDiffShareToken` (P4) | 5-8 |
| `apps/dashboard/tests/unit/utils/template-sync.spec.ts` | `applyVolumeTemplate`, `buildAppliedResult` | 2-4 |
| `apps/dashboard/tests/unit/utils/settings.spec.ts` | `parseSettingsDocs`, `loadSettingsHistory`, `mergePresets` | 4-6 |

**Total NEW vitest specs**: ~17-26 tests across 4 files.

### P1/P2/P4 — no NEW specs

These rely on vue-tsc + existing composable specs + utility specs (which already cover the wrapper behavior). Adding redundant tests would bloat the test suite without new coverage value.

P4 specifically: if `encodeVolumePlanDiffShareToken` has no existing spec, add a 1-spec minimal test covering null arg cases (covered by `volume-plan-diff.spec.ts` per table above).

## Risk + Rollback

### Risk register

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | P1 DTO widen triggers backend validation failure | MEDIUM | Each DTO widen commit verifies Pydantic `model_config = ConfigDict(extra="ignore")` is set; backend pytest runs after commit |
| R2 | P2 caller local type drift from DTO actual shape | MEDIUM | Per-commit `git grep` of typed-wrapper signature + commit msg records structural match assertion |
| R3 | P3 utility JSDoc exposes latent runtime bug | LOW-MEDIUM | New vitest specs cover happy path + edge cases (null/empty array) |
| R4 | Cross-composable type change breaks page-level test mock | MEDIUM | Per-commit full vitest run; per N.6 §5.1 lesson 2 — apply hoisted mock pattern if mock breaks |
| R5 | Typed-wrapper actual DTO ≠ caller assumed DTO (schema drift) | LOW | Per-cast `cat` of wrapper signature before fix |
| R6 | ESLint/knip new violation in 39-commit phase | LOW | Per-commit hook + T5 final gate |

### Detection cadence

- **Per commit**: `pnpm tsc --noEmit && pnpm vitest run --reporter=basic`
- **Per task boundary (T1-T4)**: full backend pytest + ruff
- **Phase end (T5)**: full final gate (vue-tsc + vitest + ESLint + knip + backend pytest + ruff + invariant grep)

### Rollback

- **Per cast**: atomic 1-file commit → revert individually
- **Per task**: revert task's commits in reverse order
- **Phase-level**: keep branch unmerged; carryover to N.14+ with new approach if direction proves wrong

## Commit Plan (17-20 commits estimated)

### Worktree setup

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-126-v16-5-n13 -b phase-126-v16-5-n13 master
cd .worktrees/phase-126-v16-5-n13
uv sync --all-packages
uv pip install pytest psutil   # MEMORY.md recurring gotcha
```

### Commit ordering (T1 → T2 → T3 → T4 → T5)

Strict ordering required: T3 uses T2's widened DTOs; T4 uses T2/T3's aligned types.

#### T1: P4 (2 commits)

```
T1.a refactor(dashboard): N.13 T1.P4.a encodeVolumePlanDiffShareToken JSDoc drops as-unknown-as-null
T1.b test(dashboard): N.13 T1.P4.b encodeVolumePlanDiffShareToken spec covers null args
```

#### T2: P1 (5-6 commits)

```
T2.a refactor(dashboard): N.13 T2.P1.a useProductPreferences fetchCreatorModels + fetchCreatorPreferences returns strict DTO
T2.b refactor(dashboard): N.13 T2.P1.b useOnboardingNotifications 4 cast sites use DTO subset type
T2.c refactor(dashboard): N.13 T2.P1.c useWriteFlow 5 fetch return casts use DTO subset types
T2.d refactor(dashboard): N.13 T2.P1.d useProductExport fetchChapters uses ChaptersResponse subset (may fix has_body carryover)
T2.e refactor(dashboard): N.13 T2.P1.e useTemplateEditor changelog + approval history DTO alignment
T2.f feat(lingwen-shared): N.13 T2.P1.f widen [某 DTO] if needed (conditional)
```

#### T3: P2 (3-4 commits)

```
T3.a refactor(dashboard): N.13 T3.P2.a useAgentTask body type aligns to CreatorAgentPlanRequest
T3.b refactor(dashboard): N.13 T3.P2.b useWriteFlow + useProductPreferences + useWorkbenchLayout params align to typed wrappers
T3.c refactor(dashboard): N.13 T3.P2.c useMergePresets publishMergePresetToFactoryApi call site audit (potential dead code)
T3.d refactor(dashboard): N.13 T3.P2.d useTemplateEditor volumes param structural alignment
```

#### T4: P3 (6-7 commits)

```
T4.a test(dashboard): N.13 T4.P3.a workbench-quality utility spec covers 4 functions
T4.b refactor(dashboard): N.13 T4.P3.b workbench-quality 4 utility functions JSDoc drops casts
T4.c test(dashboard): N.13 T4.P3.c volume-plan-diff + template-sync utility spec
T4.d refactor(dashboard): N.13 T4.P3.d volume-plan-diff + template-sync 3 cast sites fixed via JSDoc
T4.e test(dashboard): N.13 T4.P3.e settings utility spec covers parseSettingsDocs/loadSettingsHistory/mergePresets + useSettingsHistory legacy history fallback
T4.f refactor(dashboard): N.13 T4.P3.f useSettingsDocs + useSettingsHistory + useMergePresets 8 cast sites JSDoc + interface alignment
```

#### T5: Final (1 commit)

```
T5.a docs(phase-126): N.13 cast cleanup handoff + CLAUDE.md
```

### Commit message convention

Per N.10/N.11 precedent:
- Prefix: `refactor(dashboard):` / `feat(lingwen-shared):` / `test(dashboard):` / `docs(phase-126):`
- Body: `N.13 T{N}.P{M}.{letter}` (phase + task + pattern + within-task letter)
- Followed by: 1-phrase description naming the file + cast site
- Reference: file:line (in commit body, for review)

### Push strategy

- Local commits accumulate on `phase-126-v16-5-n13` branch
- Push to origin daily + at task boundaries (`git push -u origin phase-126-v16-5-n13`)
- Phase end: direct merge to master (per N.11.d/e/g precedent)

## Carryover (post-N.13)

After this phase, the cast cleanup is complete in `composables/`. Potential future work (NOT in N.13):

- `apps/dashboard/src/api/*.ts` internal casts (typed-wrapper internals)
- `apps/dashboard/src/components/**` casts (page-level components)
- `apps/dashboard/src/stores/**` casts (Pinia stores)
- Pre-existing v15.7.1 debt: `lingwen_quality` missing + `plugin_manager.py` module path bug

## Lessons Applied (from prior phases)

1. **N.6 §5.1 lesson 2** (shim mocks don't propagate): If P3 utility function refactor breaks composable spec mocks, apply hoisted mock pattern.
2. **N.7 §5 lesson 4** (DTO schema drift): P1 fixes may surface latent DTO drift — document inline, don't silently fix scope.
3. **N.10 §5 lesson 6** (T11 cleanup depends on T7-T10): P2/P3 fixes assume P1 DTOs are widened. Strict ordering required.
4. **N.11 §5 lesson 8** (atomic-commit counts vs plan estimates): commit counts are estimates; real count may vary.
5. **N.12 §5 lesson 7** (worktree env-sync recurring): `uv sync --all-packages` + `uv pip install pytest psutil` required after worktree creation.
