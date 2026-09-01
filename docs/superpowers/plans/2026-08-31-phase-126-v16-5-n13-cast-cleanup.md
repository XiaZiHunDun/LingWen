# Phase 126 v16.5 #N.13 — `as unknown as` Cast Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate 38 `as unknown as` cast instances (across 37 lines + 1 multi-cast line) in `apps/dashboard/src/composables/` by tightening types layer-by-layer using a pattern-stratified approach (P1/P2/P3/P4).

**Architecture:** Fix casts in dependency order — P4 (isolated null-cast fix) → P1 (DTO widening in lingwen-shared, benefits P2/P3) → P2 (caller param alignment using P1 widened DTOs) → P3 (utility function JSDoc typing using T2/T3 aligned types) → T5 (handoff + CLAUDE.md). Each cast fix is atomic 1-file commit per DP-06 strict. Primary verification gate is `pnpm tsc --noEmit` + `pnpm vitest run --reporter=basic`.

**Tech Stack:** Vue 3 + TypeScript strict / Pydantic v2 (lingwen-shared) / vitest / vue-tsc / ruff / hand-rolled JSON Schema → TS codegen

**Reference spec:** [`../specs/2026-08-31-phase-126-v16-5-n13-cast-cleanup-design.md`](../specs/2026-08-31-phase-126-v16-5-n13-cast-cleanup-design.md)

---

## Worktree Setup

- [ ] **Step 1: Create worktree + branch**

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-126-v16-5-n13 -b phase-126-v16-5-n13 master
cd .worktrees/phase-126-v16-5-n13
```

- [ ] **Step 2: Sync uv workspace + install test deps (per MEMORY.md N.11.d/e/g gotcha)**

```bash
uv sync --all-packages
uv pip install pytest psutil
```

- [ ] **Step 3: Verify baseline tests pass**

```bash
cd apps/dashboard && pnpm install && pnpm vitest run --reporter=basic && pnpm tsc --noEmit
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared
```

Expected: 1733 vitest passed, 0 vue-tsc errors, 129 shared tests passed.

---

## Task T1: P4 Null Cast Fix (`encodeVolumePlanDiffShareToken`)

**Files:**
- Modify: `apps/dashboard/src/utils/volumePlanDiffShareToken.js` (or locate exact `.js` file)
- Modify: `apps/dashboard/src/composables/useCreatorVolumePlanDiff/useVolumePlanDiffShare.ts:109-116` (remove `as unknown as null` casts)

### T1.1: Add JSDoc to `encodeVolumePlanDiffShareToken`

- [ ] **Step 1: Locate the function**

```bash
grep -rn "function encodeVolumePlanDiffShareToken\|encodeVolumePlanDiffShareToken = " apps/dashboard/src/
```

Identify the file (likely `apps/dashboard/src/utils/volumePlanDiffShareToken.js`).

- [ ] **Step 2: Read the function definition**

```bash
cat <file-path>
```

Confirm 3 params: `payload`, `draft`, `collabNotes`.

- [ ] **Step 3: Add JSDoc above function definition**

```javascript
/**
 * Encode a volume-plan-diff share token for URL hash.
 * @param {object} payload - The volume-plan-diff payload (shape from buildVolumePlanDiffExportPayload)
 * @param {string | null} draft - Optional draft JSON string; null when share-link apply is disabled
 * @param {string | null} collabNotes - Optional collab-notes JSON string; null when none
 * @returns {string} URL-safe base64-encoded token
 */
export function encodeVolumePlanDiffShareToken(payload, draft, collabNotes) {
  // ... existing implementation
}
```

- [ ] **Step 4: Verify vue-tsc inference**

```bash
cd apps/dashboard && pnpm tsc --noEmit 2>&1 | head -20
```

Expected: still reports errors at `useVolumePlanDiffShare.ts:114` and `:115` because casts remain.

### T1.2: Remove casts in `useVolumePlanDiffShare.ts`

- [ ] **Step 1: Read the cast lines**

```bash
sed -n '105,120p' apps/dashboard/src/composables/useCreatorVolumePlanDiff/useVolumePlanDiffShare.ts
```

Confirm 2 casts at lines 114, 115.

- [ ] **Step 2: Remove the casts**

Edit `useVolumePlanDiffShare.ts` line 114:
```typescript
// Before:
draft as unknown as null,
// After:
draft,
```

Edit line 115:
```typescript
// Before:
collabNotes as unknown as null,
// After:
collabNotes,
```

Also remove the comment block above explaining why (lines 109-112), since it's no longer needed.

- [ ] **Step 3: Verify vue-tsc passes**

```bash
cd apps/dashboard && pnpm tsc --noEmit 2>&1 | head -20
```

Expected: 0 errors.

- [ ] **Step 4: Run vitest to verify no regression**

```bash
cd apps/dashboard && pnpm vitest run tests/unit/composables/use-volume-plan-diff-share.spec.ts --reporter=basic
```

Expected: 0 regression. If no spec exists for this composable, run full vitest suite:
```bash
pnpm vitest run --reporter=basic
```

- [ ] **Step 5: Verify #29 invariant**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
grep -rn "as unknown as" apps/dashboard/src/composables/ | wc -l
```

Expected: 37 (was 39 before T1).

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
git add apps/dashboard/src/utils/volumePlanDiffShareToken.js \
        apps/dashboard/src/composables/useCreatorVolumePlanDiff/useVolumePlanDiffShare.ts
git commit -m "refactor(dashboard): N.13 T1 encodeVolumePlanDiffShareToken JSDoc drops 2 as-unknown-as-null casts"
```

---

## Task T2: P1 Typed-Wrapper Return Narrowing

**Pattern template for T2.x (apply to each sub-task):**

For each cast, the steps are:
1. Read the typed-wrapper return type (in `apps/dashboard/src/api/*.ts`)
2. Read the cast site (in `composables/`)
3. Decide fix strategy: A (remove cast, use DTO directly) / B (widen lingwen-shared DTO) / C (local DTO-subset interface)
4. Apply fix
5. Run vue-tsc + vitest
6. Commit

### T2.1: `useProductPreferences` (2 casts at lines 61, 74)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts:61,74`

- [ ] **Step 1: Read typed wrapper**

```bash
cat apps/dashboard/src/api/creator.ts | grep -A 20 "fetchCreatorModels\|fetchCreatorPreferences"
```

Identify the return DTOs (`CreatorModelsResponseDTO` + `CreatorPreferencesResponseDTO`).

- [ ] **Step 2: Read cast sites**

```bash
sed -n '55,80p' apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts
```

- [ ] **Step 3: Apply Option A fix (assume DTOs match)**

Edit line 61:
```typescript
// Before:
const data = await fetchCreatorModels() as unknown as { models?: Array<{ id: string; label: string }> };
// After:
const data: CreatorModelsResponseDTO = await fetchCreatorModels();
if (data.models?.length) {
  creatorModelOptions.value = data.models;
}
```

Edit line 74:
```typescript
// Before:
const data = await fetchCreatorPreferences() as unknown as Record<string, unknown>;
// After:
const data: CreatorPreferencesResponseDTO = await fetchCreatorPreferences();
preferences.value = preferencesFromApi(data as unknown as Parameters<typeof preferencesFromApi>[0]);
```

(If `preferencesFromApi` accepts the DTO directly, omit the secondary cast.)

- [ ] **Step 4: Verify**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic
```

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts
git commit -m "refactor(dashboard): N.13 T2.P1.a useProductPreferences fetchCreatorModels + fetchCreatorPreferences return strict DTOs"
```

### T2.2: `useOnboardingNotifications` (4 casts at lines 140, 148, 174, 176)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingNotifications.ts:140,148,174,176`

Apply the same template as T2.1:
1. Read typed wrappers `fetchOnboardingNotifications` / `buildOnboardingNotificationDigest` / `fetchDigestRetryQueue` / `fetchDigestDeadLetter` in `apps/dashboard/src/api/onboarding.ts`.
2. Apply Option A/B/C per cast.
3. Likely outcome: replace 4 casts with typed local assignments.
4. Run vue-tsc + vitest.
5. Commit:
```bash
git commit -m "refactor(dashboard): N.13 T2.P1.b useOnboardingNotifications 4 cast sites use DTO subset types"
```

### T2.3: `useWriteFlow` (5 P1 casts at lines 145, 181, 206, 227, 253; line 206 also has P2 cast)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts:145,181,206,227,253`

Apply the same template as T2.1:
1. Read typed wrappers in `apps/dashboard/src/api/content.ts`.
2. Apply Option A/B/C per cast.
3. For line 206, handle BOTH the P1 cast (`as { p0_count?: number }`) AND the P2 cast (`{ chapter } as Parameters<typeof runCreatorLogicCheck>[0]`).
4. Run vue-tsc + vitest.
5. Commit:
```bash
git commit -m "refactor(dashboard): N.13 T2.P1.c useWriteFlow 5 fetch return casts use DTO subset types"
```

### T2.4: `useProductExport` (2 casts at lines 148, 161)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts:148,161`

Apply the same template as T2.1:
1. Read `fetchChapters` typed wrapper in `apps/dashboard/src/api/content.ts`.
2. NOTE: This may also fix the v16.5 #7 `has_body` carryover (per v16.2.7 §5 lesson 2). If `ChaptersResponseDTO` now has `has_body` field, remove the v16.2.7 `as unknown as` workaround.
3. Apply Option A/B/C per cast.
4. Run vue-tsc + vitest.
5. Commit:
```bash
git commit -m "refactor(dashboard): N.13 T2.P1.d useProductExport fetchChapters uses ChaptersResponse subset (may fix has_body carryover)"
```

### T2.5: `useTemplateEditor` (2 P1 casts at lines 233, 386; line 153 is P2)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateEditor.ts:233,386`

Apply the same template as T2.1:
1. Read `fetchVolumeTemplateChangelog` + `fetchVolumeTemplateApprovalHistory` in `apps/dashboard/src/api/volume.ts`.
2. Apply Option A/B/C per cast.
3. Run vue-tsc + vitest.
4. Commit:
```bash
git commit -m "refactor(dashboard): N.13 T2.P1.e useTemplateEditor changelog + approval history DTO alignment"
```

### T2.6: `lingwen-shared` DTO widen (conditional, only if Option B path triggered)

**Files (if needed):**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (or relevant DTO file)
- Regenerate: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/*.ts` via `python tooling/contracts/generate.py`

- [ ] **Step 1: Identify which DTO needs widening**

After T2.1-T2.5 execution, document which DTO was missing fields.

- [ ] **Step 2: Add field to Pydantic model**

```python
class CreatorXxxResponse(BaseModel):
    """..."""
    # ... existing fields ...
    model_config = ConfigDict(extra="ignore")  # CONFIRM present
    new_field: Optional[SomeType] = None  # NEW field
```

- [ ] **Step 3: Regenerate TS**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
python tooling/contracts/generate.py
```

- [ ] **Step 4: Verify backend + frontend**

```bash
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(lingwen-shared): N.13 T2.P1.f widen CreatorXxxResponse DTO for cast removal"
```

---

## Task T3: P2 Typed-Wrapper Params Forwarding

**Pattern template for T3.x (apply to each sub-task):**

For each cast, the steps are:
1. Read the typed-wrapper's parameter type (in `apps/dashboard/src/api/*.ts`)
2. Read the call site to see how the arg is constructed
3. Align caller's local type to match the typed-wrapper param type
4. Remove cast
5. Run vue-tsc + vitest
6. Commit

### T3.1: `useAgentTask` (1 cast at line 365)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:365`

- [ ] **Step 1: Read typed wrapper**

```bash
grep -A 15 "function runCreatorAgentPlan" apps/dashboard/src/api/content.ts
```

Identify param type (likely `CreatorAgentPlanRequest` from lingwen-shared).

- [ ] **Step 2: Read cast site**

```bash
sed -n '355,375p' apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts
```

- [ ] **Step 3: Apply alignment fix**

Build the body with proper typed local declaration:
```typescript
// Before:
body as unknown as Parameters<typeof runCreatorAgentPlan>[0],

// After (body is constructed as CreatorAgentPlanRequest):
const body: CreatorAgentPlanRequest = {
  project_id: project.value,
  // ... other fields
};
// Then call:
await runCreatorAgentPlan(body);
```

- [ ] **Step 4: Verify**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic
```

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts
git commit -m "refactor(dashboard): N.13 T3.P2.a useAgentTask body type aligns to CreatorAgentPlanRequest"
```

### T3.2: `useWriteFlow` + `useProductPreferences` + `useWorkbenchLayout` (3 casts)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts:206` (already counted in T2.3; verify P2 cast removed)
- Modify: `apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts:101`
- Modify: `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts:173`

Apply the same template as T3.1 for each. Commit:
```bash
git commit -m "refactor(dashboard): N.13 T3.P2.b useWriteFlow + useProductPreferences + useWorkbenchLayout params align to typed wrappers"
```

### T3.3: `useMergePresets` (1 cast at line 185 — likely dead code)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts:185`

- [ ] **Step 1: Investigate dead code**

```bash
sed -n '180,195p' apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
```

Confirm the call site uses `{}` as empty payload — likely a no-op call. Check git blame to see if there's a TODO or stub.

- [ ] **Step 2: Decide fix strategy**

Option A: Delete the dead call (preferred if truly unused).
Option B: Build proper typed payload.
Option C: Keep as `await publishMergePresetToFactoryApi()` (no args, if param is optional).

- [ ] **Step 3: Apply fix + verify + commit**

```bash
git commit -m "refactor(dashboard): N.13 T3.P2.c useMergePresets publishMergePresetToFactoryApi call site audit (potential dead code)"
```

### T3.4: `useTemplateEditor` (1 P2 cast at line 153)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateEditor.ts:153`

Apply the same template as T3.1. Commit:
```bash
git commit -m "refactor(dashboard): N.13 T3.P2.d useTemplateEditor volumes param structural alignment"
```

---

## Task T4: P3 Utility Function Typing (RED-GREEN-REFACTOR pattern)

**Pattern template for T4.x (apply to each sub-task):**

For each utility function:
1. Read the `.js` utility file
2. Read the call site to understand input/output types
3. Write a failing vitest spec (RED)
4. Run spec, verify FAIL
5. Add JSDoc to the utility function (GREEN)
6. Run spec, verify PASS
7. Update call site to remove cast
8. Run vue-tsc + vitest full suite
9. Commit

### T4.1: `useWorkbenchQuality` (4 casts at lines 204, 209, 234, 284)

**Files:**
- Create: `apps/dashboard/tests/unit/utils/workbench-quality.spec.ts`
- Modify: `apps/dashboard/src/utils/workbenchQuality.js` (or locate exact `.js` file)
- Modify: `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts:204,209,234,284`

- [ ] **Step 1: Identify utility functions**

```bash
grep -rn "summarizeLightValidation\|runLightValidation\|buildInlineConflictMarkers" apps/dashboard/src/utils/
```

- [ ] **Step 2: Write RED vitest spec**

Create `apps/dashboard/tests/unit/utils/workbench-quality.spec.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import {
  summarizeLightValidation,
  runLightValidation,
  buildInlineConflictMarkers,
  summarizeInlineConflicts,
} from '@/utils/workbenchQuality';
import type { LightValidationIssue } from '@/utils/workbenchQualityTypes';

describe('summarizeLightValidation', () => {
  it('returns ok status for empty issues array', () => {
    const result = summarizeLightValidation([]);
    expect(result.status).toBe('ok');
  });

  it('returns warn status for warning-level issues', () => {
    const issues: LightValidationIssue[] = [
      { id: '1', level: 'warn', label: 'test warning', location: null },
    ];
    const result = summarizeLightValidation(issues);
    expect(result.status).toBe('warn');
    expect(result.count).toBe(1);
  });
});

describe('runLightValidation', () => {
  it('returns empty array for clean body', () => {
    const issues = runLightValidation({ body: 'clean body', chapter: 1 });
    expect(issues).toEqual([]);
  });
});

describe('buildInlineConflictMarkers', () => {
  it('returns empty array when no conflicts', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 1,
      deviations: [],
      logicIssues: [],
      lightIssues: [],
    });
    expect(markers).toEqual([]);
  });
});

describe('summarizeInlineConflicts', () => {
  it('returns ok for no markers', () => {
    const summary = summarizeInlineConflicts([]);
    expect(summary.status).toBe('ok');
  });
});
```

- [ ] **Step 3: Run spec, verify FAIL (compile error: no types inferred)**

```bash
cd apps/dashboard && pnpm vitest run tests/unit/utils/workbench-quality.spec.ts --reporter=basic
```

Expected: FAIL with "summarizeLightValidation not defined" OR "lightValidationIssues.value type mismatch" (depending on whether utility is exported).

- [ ] **Step 4: Add JSDoc to utility functions**

Edit `workbenchQuality.js` (or wherever the utility is):
```javascript
/**
 * @typedef {object} LightValidationIssue
 * @property {string} id
 * @property {'warn'|'info'|'error'} level
 * @property {string} label
 * @property {number | null} location
 */

/**
 * Summarize light validation issues into a status object.
 * @param {LightValidationIssue[]} issues
 * @returns {{ status: 'ok'|'warn'|'info'; count: number; firstLabel?: string }}
 */
export function summarizeLightValidation(issues) { /* ... */ }

/**
 * Run light validation on chapter body.
 * @param {{ body: string; chapter: number }} params
 * @returns {LightValidationIssue[]}
 */
export function runLightValidation({ body, chapter }) { /* ... */ }

// ... similar for buildInlineConflictMarkers, summarizeInlineConflicts
```

- [ ] **Step 5: Run spec, verify PASS**

```bash
pnpm vitest run tests/unit/utils/workbench-quality.spec.ts --reporter=basic
```

Expected: all tests pass.

- [ ] **Step 6: Remove casts in `useWorkbenchQuality.ts`**

Edit each cast site:
```typescript
// Line 204 (before):
summarizeLightValidation(lightValidationIssues.value as unknown as Array<{ level?: string }>),
// Line 204 (after):
summarizeLightValidation(lightValidationIssues.value),

// Line 209 (before):
summarizeLightValidation(issues as unknown as Array<{ level?: string }>),
// Line 209 (after):
summarizeLightValidation(issues),

// Line 234 (before):
const issues = runLightValidation({ body, chapter }) as unknown as LightValidationIssue[];
// Line 234 (after):
const issues: LightValidationIssue[] = runLightValidation({ body, chapter });

// Line 284 (before):
}) as unknown as InlineConflictMarker[],
// Line 284 (after):
}) as InlineConflictMarker[],
```

(Note: `as InlineConflictMarker[]` is narrower than `as unknown as InlineConflictMarker[]` — verify TS infers correctly.)

- [ ] **Step 7: Run vue-tsc + vitest full suite**

```bash
cd apps/dashboard && pnpm tsc --noEmit && pnpm vitest run --reporter=basic
```

Expected: 0 errors.

- [ ] **Step 8: Verify #29 invariant progress**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
grep -rn "as unknown as" apps/dashboard/src/composables/ | wc -l
```

Expected: 33 (was 37 before T4.1, removed 4 casts).

- [ ] **Step 9: Commit spec**

```bash
git add apps/dashboard/tests/unit/utils/workbench-quality.spec.ts apps/dashboard/src/utils/workbenchQuality.js
git commit -m "test(dashboard): N.13 T4.P3.a workbench-quality utility spec covers 4 functions"
```

- [ ] **Step 10: Commit refactor**

```bash
git add apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts
git commit -m "refactor(dashboard): N.13 T4.P3.b workbench-quality 4 cast sites removed via JSDoc"
```

### T4.2: `useVolumePlanDiff` + `useTemplateSync` (3 casts at lines 144, 145, 202)

**Files:**
- Create: `apps/dashboard/tests/unit/utils/volume-plan-diff.spec.ts`
- Modify: `apps/dashboard/src/utils/volumePlanDiff.js` (or locate `.js`)
- Modify: `apps/dashboard/src/utils/templateSync.js` (or locate `.js`)
- Modify: `apps/dashboard/src/composables/useCreatorVolumePlanDiff/useVolumePlanDiff.ts:144,145`
- Modify: `apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateSync.ts:202`

Apply the same RED-GREEN-REFACTOR template as T4.1. Commits:
```bash
git commit -m "test(dashboard): N.13 T4.P3.c volume-plan-diff + template-sync utility spec"
git commit -m "refactor(dashboard): N.13 T4.P3.d volume-plan-diff + template-sync 3 cast sites removed via JSDoc"
```

### T4.3: `useSettingsDocs` + `useSettingsHistory` + `useMergePresets` (8 casts at 79, 82, 83, 85, 86, 65, 131, 262)

**Files:**
- Create: `apps/dashboard/tests/unit/utils/settings.spec.ts`
- Modify: `apps/dashboard/src/utils/settingsDocs.js` (or locate `.js`)
- Modify: `apps/dashboard/src/utils/settingsHistory.js` (or locate `.js`)
- Modify: `apps/dashboard/src/utils/mergePresets.js` (or locate `.js`)
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts:79,82,83,85,86`
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts:65` (special: drop `history` legacy fallback)
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts:131,262`

Apply the same RED-GREEN-REFACTOR template as T4.1.

Special note for `useSettingsHistory.ts:65`:
```typescript
// Before:
const data: CreatorSettingsHistoryResponse = await fetchSettingsHistory();
const rawData = data as unknown as { snapshots?: SettingsSnapshot[]; history?: SettingsSnapshot[] };
settingsHistory.value = rawData.snapshots || rawData.history || [];

// After (drop legacy `history` fallback):
const data: CreatorSettingsHistoryResponse = await fetchSettingsHistory();
settingsHistory.value = data.snapshots ?? [];
```

Verify no vitest test depends on the `history` fallback path before removing.

Commits:
```bash
git commit -m "test(dashboard): N.13 T4.P3.e settings utility spec covers parseSettingsDocs/loadSettingsHistory/mergePresets"
git commit -m "refactor(dashboard): N.13 T4.P3.f useSettingsDocs + useSettingsHistory + useMergePresets 8 cast sites removed via JSDoc"
```

---

## Task T5: Final Gate + Handoff

### T5.1: Final verification gate

- [ ] **Step 1: Frontend full gate**

```bash
cd apps/dashboard
pnpm vitest run --reporter=basic     # expected: 1733 + 16-26 NEW = ~1750+
pnpm tsc --noEmit                    # expected: 0 errors
pnpm eslint .                        # expected: 0 errors
pnpm exec knip                       # expected: 0 (5 advisory hints unchanged)
```

- [ ] **Step 2: Backend full gate**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ packages/lingwen-creator/tests/ apps/studio_api/tests/
ruff check packages/lingwen-shared/src/lingwen_shared/ apps/studio_api/
```

- [ ] **Step 3: Architecture invariant #29 verification**

```bash
grep -rn "as unknown as" apps/dashboard/src/composables/
```

Expected: 0 lines.

- [ ] **Step 4: Architecture invariant #30 verification**

```bash
grep -rn "summarizeLightValidation\|runLightValidation\|buildInlineConflictMarkers\|parseSettingsDocs\|loadSettingsHistory\|mergePresets\|applyVolumeTemplate\|buildVolumePlanDiffPreview" apps/dashboard/src/utils/ | grep -E "\.js$"
```

Expected: each function has JSDoc directly above (verify via `grep -B 2` on each match).

- [ ] **Step 5: Push branch to origin**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
git push -u origin phase-126-v16-5-n13
```

### T5.2: Write handoff doc

- [ ] **Step 1: Create handoff doc**

Create `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n13-cast-cleanup-handoff.md` with the structure from prior handoffs (N.11.d/e/g pattern):
- Summary
- Commits (list all 17-20)
- Architecture invariants enforced (#29, #30)
- Test results table
- Files changed (frontend + backend if any)
- Lessons learned
- Carryover to v16.5 #N.14+

- [ ] **Step 2: Update CLAUDE.md**

Update root `CLAUDE.md`:
1. Add v16.5 #N.13 closure section at top of version history.
2. Increment version line.
3. Note #29 and #30 invariants enforced.
4. Note N.14+ carryover.

- [ ] **Step 3: Commit handoff + CLAUDE.md**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n13
git add docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n13-cast-cleanup-handoff.md CLAUDE.md
git commit -m "docs(phase-126): N.13 cast cleanup handoff + CLAUDE.md"
```

### T5.3: Merge to master

- [ ] **Step 1: Merge to master (direct merge per N.11.d/e/g precedent)**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --no-ff phase-126-v16-5-n13 -m "Merge phase-126-v16-5-n13: 38 as-unknown-as cast cleanup (#29 invariant)"
```

- [ ] **Step 2: Push master to origin**

```bash
git push origin master
```

- [ ] **Step 3: Clean up worktree + branch**

```bash
git worktree remove .worktrees/phase-126-v16-5-n13
git branch -d phase-126-v16-5-n13
```

---

## Self-Review (per writing-plans skill checklist)

### 1. Spec coverage

| Spec section | Plan task |
|---|---|
| Summary (38 cast instances, 4 patterns) | T1-T4 cover all 4 patterns |
| Architecture invariants #29 + #30 | T5.1 steps 3-4 verify; T5.2 step 2 documents |
| Pattern P1 (15 casts) | T2.1-T2.5 + T2.6 (conditional DTO widen) |
| Pattern P2 (6 casts) | T3.1-T3.4 |
| Pattern P3 (15 casts) | T4.1 (4), T4.2 (3), T4.3 (8) |
| Pattern P4 (2 casts) | T1.1-T1.2 |
| Test strategy (vue-tsc primary + P3 specs) | Per-commit vue-tsc + T4.x vitest specs |
| Risk register (R1-R6) | Per-commit verification gates; T5.1 final gate |
| Commit plan (17-20 commits) | T1 (1 commit) + T2 (5-6) + T3 (3-4) + T4 (6-7 commits) + T5 (3 ops) = 18-21 |
| Carryover to N.14+ | T5.2 step 1 documents |

### 2. Placeholder scan

No "TBD" / "TODO" / "implement later" / "fill in details" in concrete steps. Conditional sections (T2.6, T3.3) explicitly marked.

### 3. Type consistency

- `CreatorModelsResponseDTO` / `CreatorPreferencesResponseDTO` referenced consistently in T2.1
- `CreatorAgentPlanRequest` referenced consistently in T3.1
- `LightValidationIssue` referenced consistently in T4.1
- `SettingsSnapshot[]` / `MergePreferences` referenced consistently in T4.3
- DTO names match lingwen-shared canonical source per N.7 codegen

### 4. Ambiguity check

- "Run vitest full suite" — clearly defined as `pnpm vitest run --reporter=basic`
- "Locate utility function" — uses `grep -rn` to find exact path
- "Apply Option A/B/C" — each option defined in T2 task template
- "Special note for useSettingsHistory.ts:65" — exact before/after code provided
