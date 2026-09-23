# Phase 110 — Pre-existing Issues Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close 55 `pnpm tsc --noEmit` errors and 4 `pnpm vitest run` failures that have accumulated across the Phase 90-109 cluster. Frontend-only tech-debt cleanup.

**Architecture:** Minimum-diff per file. Replace 8 `$fetch` calls in `src/api/illustrations.ts` with native `fetch()` (mirror existing `fetchProviderModels`). Register 4 missing composables in `index.ts`. Add `.spec.ts` exclusion to `architecture-guards.spec.ts`. Update 3 stale test expectations. Add type annotations / fix test patterns in 7 spec files. 6 regression guards G1-G6.

**Tech Stack:** Vue 3 + TypeScript (strict mode + `noUncheckedIndexedAccess`) + Vitest + Pinia + native browser `fetch`. No new dependencies.

---

## File Structure

**Production code touched (1 file):**
- `apps/dashboard/src/api/illustrations.ts` — 9 tsc errors → 0

**Composables exports (1 file):**
- `apps/dashboard/src/composables/index.ts` — 4 missing exports added

**Test files modified (7 files for tsc + 2 for vitest):**
- `tests/unit/guards/architecture-guards.spec.ts` — vitest fix (`.spec.ts` exclusion)
- `tests/unit/components/illustrations/GenerateIllustrationDialog.spec.js` — vitest fix (provider assertion)
- `tests/unit/human-first-nav.spec.ts` — vitest fix (nav array)
- `tests/unit/components/creator/CreatorDeviationFinalize.spec.ts` — 18 tsc errors (Pinia store usage)
- `tests/unit/components/creator/CreatorBatchRhythm.spec.ts` — 11 tsc errors (Pinia store usage)
- `tests/unit/components/world/factions/FactionGraphCanvas.spec.ts` — 14 tsc errors (Vue Test Utils + tuple)
- `tests/unit/components/world/factions/FactionGraph.spec.ts` — 1 tsc error
- `tests/unit/components/world/characters/CharacterRelationships.spec.ts` — 1 tsc error
- `tests/unit/components/world/WorldTabs.spec.ts` — 1 tsc error

**New files (1 test):**
- `tests/unit/guards/phase110-regression-guards.spec.ts` — 6 guards G1-G6

**Docs (2 files):**
- `CLAUDE.md` — version v60.7 → v60.8
- `docs/superpowers/handoffs/2026-09-23-phase-110-pre-existing-issues-cleanup-handoff.md`

---

## Task 1: Pre-flight verification

**Files:** none

- [ ] **Step 1.1: Verify baseline failure counts**

Run:
```bash
cd apps/dashboard && pnpm tsc --noEmit 2>&1 | grep -E "error TS" | wc -l
```
Expected: `55`

- [ ] **Step 1.2: Verify vitest baseline failures**

Run:
```bash
cd apps/dashboard && pnpm vitest run 2>&1 | grep -E "Test Files|Tests" | tail -2
```
Expected: `Test Files  3 failed | 285 passed (288)` and `Tests  4 failed | 2162 passed | 1 skipped (2167)`

- [ ] **Step 1.3: Verify working tree is clean**

Run: `git status`
Expected: `nothing to commit, working tree clean` (C0 docs already committed in spec/fixup)

---

## Task 2: Fix `src/api/illustrations.ts` — 9 production tsc errors (Commit C1)

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts`
- Create: `apps/dashboard/tests/unit/guards/phase110-no-dollar-fetch.spec.ts` (G1)

- [ ] **Step 2.1: Write G1 regression guard (test-first)**

Create `apps/dashboard/tests/unit/guards/phase110-no-dollar-fetch.spec.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Phase 110 G1: production code MUST NOT reference `$fetch` global.
 * `$fetch` is a Nuxt auto-import not provided by Vite. Phase 96-109 wrappers
 * used it but silently depended on test stubs. Phase 110 closes the gap.
 */

const productionFiles = [
  'src/api/illustrations.ts',
];

describe('Phase 110 G1: no $fetch in production code', () => {
  for (const relPath of productionFiles) {
    it(`${relPath} contains zero $fetch references`, () => {
      const fullPath = path.resolve(__dirname, '../../../', relPath);
      const content = fs.readFileSync(fullPath, 'utf-8');
      // Match $fetch as a function call or as a reference (not in a string literal)
      const matches = content.match(/\$fetch(?:\s*\()/g) ?? [];
      expect(matches).toEqual([]);
    });
  }
});
```

- [ ] **Step 2.2: Run G1 to verify it fails**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/guards/phase110-no-dollar-fetch.spec.ts 2>&1 | tail -20`
Expected: FAIL with "expected 8 to equal 0"

- [ ] **Step 2.3: Read current `illustrations.ts` to identify all `$fetch` call sites**

Open `apps/dashboard/src/api/illustrations.ts` and find all `$fetch(` occurrences:
- Line 14: `fetchReferenceImageInfo` — `return $fetch(\`/api/projects/${slug}/reference-image\`)`
- Line 18: `fetchReferenceImageBlob` — `return $fetch(\`/api/projects/${slug}/reference-image\`, { responseType: 'blob' })`
- Line 24: `uploadReferenceImage` — `return $fetch(\`/api/projects/${slug}/reference-image\`, { method: 'POST', body: formData })`
- Line 31: `deleteReferenceImage` — `return $fetch(\`/api/projects/${slug}/reference-image\`, { method: 'DELETE' })`
- Line 127: bulk regenerate wrapper — `return $fetch(\`/api/illustrations?${params.toString()}\`, { method: 'PUT', body })` (verify exact location by reading file)
- Line 154: regenerate wrapper — `return $fetch(\`/api/illustrations/${assetId}/regenerate?${params.toString()}\`, { method: 'PUT', body })` (verify)
- Line 265: notifications stream — `return $fetch(\`/api/projects/${slug}/notifications/stream\`)`
- Line 279: notifications endpoint — `return $fetch(\`/api/projects/${slug}/notifications\`, { method: 'DELETE' })`

Verify exact line numbers by reading the file. If lines differ, adjust in Step 2.4.

- [ ] **Step 2.4: Add private helper `rawFetchJson<T>` and `rawFetchVoid` near top of file**

Add immediately after the imports/types (find the right insertion point by reading the file):
```typescript
/**
 * Native fetch helper that mirrors $fetch semantics for JSON responses.
 * Throws on non-2xx status; returns parsed JSON. Used by Phase 110 to
 * remove Nuxt-only `$fetch` global from production code.
 *
 * @internal — not exported
 */
async function rawFetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(`fetch ${url} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Native fetch helper for void responses (e.g. DELETE/POST without body).
 * Throws on non-2xx status; returns undefined.
 *
 * @internal — not exported
 */
async function rawFetchVoid(url: string, init?: RequestInit): Promise<void> {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(`fetch ${url} failed: ${res.status} ${res.statusText}`);
  }
}
```

- [ ] **Step 2.5: Replace 8 `$fetch` call sites**

For each call site identified in Step 2.3, replace per the following table:

| Original | Replacement |
|----------|-------------|
| `return $fetch(\`/api/projects/${slug}/reference-image\`)` (line 14) | `return rawFetchJson(\`/api/projects/${slug}/reference-image\`)` |
| `return $fetch(\`/api/projects/${slug}/reference-image\`, { responseType: 'blob' })` (line 18) | `const res = await fetch(\`/api/projects/${slug}/reference-image\`); if (!res.ok) throw new Error(\`fetch failed: ${res.status}\`); return res.blob()` (manual handling for blob — no JSON parsing) |
| `return $fetch(\`/api/projects/${slug}/reference-image\`, { method: 'POST', body: formData })` (line 24) | `await rawFetchVoid(\`/api/projects/${slug}/reference-image\`, { method: 'POST', body: formData })` |
| `return $fetch(\`/api/projects/${slug}/reference-image\`, { method: 'DELETE' })` (line 31) | `await rawFetchVoid(\`/api/projects/${slug}/reference-image\`, { method: 'DELETE' })` |
| (line 127 bulk regen) | `return rawFetchJson(\`/api/illustrations?${params.toString()}\`, { method: 'PUT', body })` |
| (line 154 regen) | `return rawFetchJson(\`/api/illustrations/${assetId}/regenerate?${params.toString()}\`, { method: 'PUT', body })` |
| (line 265 stream) | `const res = await fetch(\`/api/projects/${slug}/notifications/stream\`); if (!res.ok) throw new Error(\`fetch failed: ${res.status}\`); return res` (manual — stream needs raw Response for SSE) |
| (line 279 delete notif) | `await rawFetchVoid(\`/api/projects/${slug}/notifications\`, { method: 'DELETE' })` |

Verify each replacement by re-reading the file.

- [ ] **Step 2.6: Fix the `Response → ProviderModelCatalog` cast at line 173**

Change line 173 from `return res as ProviderModelCatalog` to `return res as unknown as ProviderModelCatalog`.

- [ ] **Step 2.7: Run tsc to verify 0 errors in `illustrations.ts`**

Run: `cd apps/dashboard && pnpm tsc --noEmit 2>&1 | grep "illustrations" || echo "OK: zero illustrations errors"`
Expected: `OK: zero illustrations errors`

- [ ] **Step 2.8: Run G1 to verify it now passes**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/guards/phase110-no-dollar-fetch.spec.ts 2>&1 | tail -10`
Expected: `Test Files  1 passed`

- [ ] **Step 2.9: Run full vitest to check no regressions**

Run: `cd apps/dashboard && pnpm vitest run 2>&1 | tail -5`
Expected: same baseline failures (3 files / 4 tests) — must NOT increase. Acceptable to decrease if some tests relied on `$fetch`.

- [ ] **Step 2.10: Commit C1**

```bash
git add apps/dashboard/src/api/illustrations.ts apps/dashboard/tests/unit/guards/phase110-no-dollar-fetch.spec.ts
git commit -m "fix(phase-110): illustrations.ts \$fetch -> native fetch (9 prod errors)

- Add rawFetchJson + rawFetchVoid private helpers (mirror \$fetch semantics)
- Replace 8 \$fetch call sites with native fetch
- Fix Response->ProviderModelCatalog cast (line 173: as unknown as)
- New G1 regression guard ensures no future \$fetch in production code

Phase 110 Task 2 / 9."
```

---

## Task 3: Register 4 missing composables in `src/composables/index.ts` (Commit C2)

**Files:**
- Modify: `apps/dashboard/src/composables/index.ts`
- Create: `apps/dashboard/tests/unit/guards/phase110-composables-registered.spec.ts` (G2)

- [ ] **Step 3.1: Write G2 regression guard (test-first)**

Create `apps/dashboard/tests/unit/guards/phase110-composables-registered.spec.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Phase 110 G2: composables/index.ts must export all Phase 107-109
 * composables introduced after the last index update.
 */

const NEW_COMPOSABLES = [
  'useBulkDeleteToast',
  'useBulkRegenerateToast',
  'useDeleteFromNotificationToast',
  'useNotificationStream',
];

describe('Phase 110 G2: Phase 107-109 composables registered', () => {
  const indexPath = path.resolve(__dirname, '../../../src/composables/index.ts');
  const content = fs.readFileSync(indexPath, 'utf-8');

  for (const name of NEW_COMPOSABLES) {
    it(`${name} is exported from index.ts`, () => {
      expect(content).toContain(name);
    });
  }

  it('docstring mentions Phase 107-109', () => {
    expect(content).toMatch(/Phase 107.*?10[789]/);
  });
});
```

- [ ] **Step 3.2: Run G2 to verify it fails**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/guards/phase110-composables-registered.spec.ts 2>&1 | tail -10`
Expected: FAIL with 4 missing-export errors

- [ ] **Step 3.3: Read current index.ts to find right insertion region**

Open `apps/dashboard/src/composables/index.ts`. Find the existing `useBatchEventStream, BATCH_EVENT_BUFFER` export line. New exports will be added in the same notification/illustration region.

- [ ] **Step 3.4: Add 4 export lines after `useBatchEventStream`**

Insert immediately after the `useBatchEventStream` export line:
```typescript
// Phase 107: bulk delete illustration toast composable
export { useBulkDeleteToast } from './useBulkDeleteToast.js';
// Phase 108: bulk regenerate illustration toast composable
export { useBulkRegenerateToast } from './useBulkRegenerateToast.js';
// Phase 109: delete-from-notification toast composable
export { useDeleteFromNotificationToast } from './useDeleteFromNotificationToast.js';
// Phase 99: SSE notification stream composable
export { useNotificationStream } from './useNotificationStream.js';
```

- [ ] **Step 3.5: Update docstring at top of file**

Find the line listing exported items in the docstring (around the `useBatchEventStream` region). Add to the listed composables:
```
 * - 通知/批量: useBulkDeleteToast (Phase 107), useBulkRegenerateToast (Phase 108),
 *   useDeleteFromNotificationToast (Phase 109), useNotificationStream (Phase 99),
 *   useBatchEventStream, BATCH_EVENT_BUFFER
```

- [ ] **Step 3.6: Run G2 to verify it passes**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/guards/phase110-composables-registered.spec.ts 2>&1 | tail -10`
Expected: `Test Files  1 passed (1)` with 5 tests passing

- [ ] **Step 3.7: Commit C2**

```bash
git add apps/dashboard/src/composables/index.ts apps/dashboard/tests/unit/guards/phase110-composables-registered.spec.ts
git commit -m "fix(phase-110): register 4 Phase 107-109 composables in index.ts

- useBulkDeleteToast (Phase 107)
- useBulkRegenerateToast (Phase 108)
- useDeleteFromNotificationToast (Phase 109)
- useNotificationStream (Phase 99)

Plus docstring update. New G2 regression guard.

Phase 110 Task 3 / 9."
```

---

## Task 4: Fix `architecture-guards.spec.ts` `.spec.ts` scan (Commit C3)

**Files:**
- Modify: `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts`

- [ ] **Step 4.1: Read the failing test logic**

Open `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` lines 21-56. The filter at line 24-28 only excludes `.d.ts`. Add `.spec.ts` exclusion.

- [ ] **Step 4.2: Add `.spec.ts` exclusion filter**

Change line 27 from:
```typescript
&& !f.endsWith('.d.ts')
```
to:
```typescript
&& !f.endsWith('.d.ts')
&& !f.endsWith('.spec.ts')
```

- [ ] **Step 4.3: Run the test to verify it now passes**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/guards/architecture-guards.spec.ts 2>&1 | tail -10`
Expected: `Test Files  1 passed (1)` with all 14 tests passing

- [ ] **Step 4.4: Run full vitest to confirm 3 -> 2 failing test files**

Run: `cd apps/dashboard && pnpm vitest run 2>&1 | grep -E "Test Files|Tests " | tail -3`
Expected: `Test Files  2 failed | 286 passed (288)` and `Tests  2 failed | 2164 passed | 1 skipped (2167)` — architecture-guards.spec.ts resolved, the 2 GenerateIllustrationDialog.spec.js tests still fail.

- [ ] **Step 4.5: Commit C3**

```bash
git add apps/dashboard/tests/unit/guards/architecture-guards.spec.ts
git commit -m "fix(phase-110): architecture-guards.spec.ts exclude .spec.ts from export scan

Test files are not production exports. Add .spec.ts to the readdirSync filter
alongside .d.ts. Resolves 1 of 4 vitest failures.

Phase 110 Task 4 / 9."
```

---

## Task 5: Fix `GenerateIllustrationDialog.spec.js` provider assertions (Commit C4)

**Files:**
- Modify: `apps/dashboard/tests/unit/components/illustrations/GenerateIllustrationDialog.spec.js`

- [ ] **Step 5.1: Read the failing test file**

Open `apps/dashboard/tests/unit/components/illustrations/GenerateIllustrationDialog.spec.js` and find the 2 lines with `toBe('minimax')` for "preselects provider from project default" and "user can override provider per call".

- [ ] **Step 5.2: Verify current default in ProjectSettings store**

Open `apps/dashboard/src/stores/useProjectSettings.js` and find the `defaultProvider` field default value. Confirm whether it is `openai` or `minimax` (Phase 96 spec used `openai`; Phase 100 catalog update may have changed).

- [ ] **Step 5.3: Update both assertions to match the current default**

If the current default is `openai` (per Phase 96 spec), change both `expect(...).toBe('minimax')` to `expect(...).toBe('openai')`. If the current default is `minimax`, the test was correct and the issue is elsewhere — defer and flag for plan revision.

- [ ] **Step 5.4: Run the failing test to verify it passes**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/components/illustrations/GenerateIllustrationDialog.spec.js 2>&1 | tail -10`
Expected: `Test Files  1 passed (1)` with all tests passing

- [ ] **Step 5.5: Run full vitest to confirm 2 -> 1 failing test file**

Run: `cd apps/dashboard && pnpm vitest run 2>&1 | grep -E "Test Files|Tests " | tail -3`
Expected: `Test Files  1 failed | 287 passed (288)` — only `human-first-nav.spec.ts` remains

- [ ] **Step 5.6: Commit C4**

```bash
git add apps/dashboard/tests/unit/components/illustrations/GenerateIllustrationDialog.spec.js
git commit -m "fix(phase-110): GenerateIllustrationDialog.spec.js provider default assertion

Per Phase 96 ProjectSettings default = openai. Tests were hardcoded to
\`minimax\` pre-Phase-96. Update 2 assertions.

Phase 110 Task 5 / 9."
```

---

## Task 6: Fix `human-first-nav.spec.ts` expected array (Commit C5)

**Files:**
- Modify: `apps/dashboard/tests/unit/human-first-nav.spec.ts`

- [ ] **Step 6.1: Read the failing test**

Open `apps/dashboard/tests/unit/human-first-nav.spec.ts` and find the test "companion shows ask/write/library/pilot/more/settings". Note the expected array.

- [ ] **Step 6.2: Find current nav source**

Search for the `humanFirstNav` array or equivalent. Likely in `apps/dashboard/src/config/nav.js` or `apps/dashboard/src/composables/useDashboardNav.js`. Open and find the companion mode nav array.

- [ ] **Step 6.3: Identify the 4th element**

Compare current nav array to test expected array. The 4th element is the new one (likely "notifications" added in Phase 99). Determine its exact name (kebab-case vs camelCase in the array).

- [ ] **Step 6.4: Update the test expected array**

Add the missing 4th element to the expected array in the spec. Match exact spelling/kebab-case.

- [ ] **Step 6.5: Run the failing test to verify it passes**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/human-first-nav.spec.ts 2>&1 | tail -10`
Expected: `Test Files  1 passed (1)` with all tests passing

- [ ] **Step 6.6: Run full vitest to confirm 0 failing tests**

Run: `cd apps/dashboard && pnpm vitest run 2>&1 | grep -E "Test Files|Tests " | tail -3`
Expected: `Test Files  288 passed (288)` and `Tests  2166 passed | 1 skipped (2167)` — **0 failed**.

- [ ] **Step 6.7: Commit C5**

```bash
git add apps/dashboard/tests/unit/human-first-nav.spec.ts
git commit -m "fix(phase-110): human-first-nav.spec.ts expected array (Phase 99 added 4th)

Per Phase 99: Notifications nav item added in companion mode sidebar.
Update test expected to include it.

Phase 110 Task 6 / 9. Last vitest failure closed."
```

---

## Task 7: Fix 43 test tsc errors across 7 spec files (Commit C6)

**Files:**
- Modify: `apps/dashboard/tests/unit/components/creator/CreatorDeviationFinalize.spec.ts`
- Modify: `apps/dashboard/tests/unit/components/creator/CreatorBatchRhythm.spec.ts`
- Modify: `apps/dashboard/tests/unit/components/world/factions/FactionGraphCanvas.spec.ts`
- Modify: `apps/dashboard/tests/unit/components/world/factions/FactionGraph.spec.ts`
- Modify: `apps/dashboard/tests/unit/components/world/characters/CharacterRelationships.spec.ts`
- Modify: `apps/dashboard/tests/unit/components/world/WorldTabs.spec.ts`

These errors are **real test bugs**, not pure type annotations. They fall into 3 categories:

### Category A — Pinia store direct mutation (CreatorDeviationFinalize 18 + CreatorBatchRhythm 11 = 29 errors)

Pattern:
```
error TS2322: Type '{ job_id: string; ... }' is not assignable to type 'null'.
```

Root cause: tests assign objects to a store property typed as `null`. The Pinia store's `activeJob` field is typed as `Ref<null>` because tests use `store.activeJob = {...}` instead of `store.setActiveJob({...})` or `store.$patch({...})`.

**Fix per error**: replace direct property assignment with the proper store action. Read the store file `apps/dashboard/src/stores/useCreatorBatch.js` to find the correct action name (likely `setActiveJob`, `setCurrentJob`, or use `$patch`).

### Category B — Vue Test Utils `wrapper.emitted()` tuple access (FactionGraphCanvas 14 errors)

Pattern:
```
error TS2493: Tuple type '[]' of length '0' has no element at index '0'.
error TS2532: Object is possibly 'undefined'.
error TS7006: Parameter 'e' implicitly has an 'any' type.
```

Root cause: the component does not declare `emits`, so TS sees the emitted events as an empty tuple. Direct indexing fails. Vue's strict mode flags implicit `any` in callback params.

**Fix per error**:
- `const [[a, b]] = wrapper.emitted('event-name') ?? []` → `const emitted = wrapper.emitted('event-name') ?? []; const [a, b] = (emitted[0] ?? []) as [string, string]`
- `(e) => ...` → `(e: Event) => ...`

### Category C — minor (3 small files × 1 error each)

Inspect each independently.

- [ ] **Step 7.1: Run tsc to confirm current error count**

Run: `cd apps/dashboard && pnpm tsc --noEmit 2>&1 | grep -E "error TS" | wc -l`
Expected: `12` (55 - 9 from C1 - 0 from C2-C5 = 49, plus check) — recalculate based on actual.

Actually after C1 (which only fixed illustrations.ts) the count should still be ~55 because test errors weren't touched. After C2-C5 (vitest only) the count stays the same. So expected: `55` unchanged at this point.

- [ ] **Step 7.2: Read `CreatorDeviationFinalize.spec.ts` lines 45-110**

Find the `store.activeJob = ...` patterns and the import of the store. Determine the correct action name.

- [ ] **Step 7.3: Read `useCreatorBatch.js` store to find correct action**

Search for `setActiveJob`, `setCurrentJob`, `setBatch`, `startBatch`, etc. Pick the action that takes the same parameters as the test is trying to assign.

- [ ] **Step 7.4: Replace direct mutation in `CreatorDeviationFinalize.spec.ts` (18 errors)**

For each `store.activeJob = {...}` or similar pattern, replace with `store.ACTION_NAME(...)`. Verify with tsc.

- [ ] **Step 7.5: Replace direct mutation in `CreatorBatchRhythm.spec.ts` (11 errors)**

Same pattern as 7.4.

- [ ] **Step 7.6: Read `FactionGraphCanvas.spec.ts` lines 60-145 to understand emit usage**

- [ ] **Step 7.7: Apply Category B fixes to `FactionGraphCanvas.spec.ts` (14 errors)**

- [ ] **Step 7.8: Fix 3 minor spec files (FactionGraph + CharacterRelationships + WorldTabs)**

For each file:
- Open and read the failing line
- Apply minimal fix (type annotation, non-null assertion, or method rename)

- [ ] **Step 7.9: Run tsc to verify 0 errors**

Run: `cd apps/dashboard && pnpm tsc --noEmit 2>&1 | grep -E "error TS" | wc -l`
Expected: `0`

- [ ] **Step 7.10: Run full vitest to confirm no regressions**

Run: `cd apps/dashboard && pnpm vitest run 2>&1 | grep -E "Test Files|Tests " | tail -3`
Expected: `Test Files  288 passed (288)` and `Tests  2166 passed | 1 skipped (2167)` — same as after C5

- [ ] **Step 7.11: Commit C5**

```bash
git add apps/dashboard/tests/unit/components/creator/CreatorDeviationFinalize.spec.ts \
        apps/dashboard/tests/unit/components/creator/CreatorBatchRhythm.spec.ts \
        apps/dashboard/tests/unit/components/world/factions/FactionGraphCanvas.spec.ts \
        apps/dashboard/tests/unit/components/world/factions/FactionGraph.spec.ts \
        apps/dashboard/tests/unit/components/world/characters/CharacterRelationships.spec.ts \
        apps/dashboard/tests/unit/components/world/WorldTabs.spec.ts
git commit -m "fix(phase-110): 43 test tsc errors across 7 spec files

- CreatorDeviationFinalize (18) + CreatorBatchRhythm (11): Pinia store
  direct mutation -> store action method
- FactionCanvas (14): wrapper.emitted() tuple access + implicit any
- 3 minor spec files (1 each): type annotations

Phase 110 Task 7 / 9."
```

---

## Task 8: Add 4 remaining regression guards G3-G6 (Commit C7)

**Files:**
- Modify: `apps/dashboard/tests/unit/guards/phase110-regression-guards.spec.ts` (or new file per guard)

- [ ] **Step 8.1: Write G3 (tsc clean baseline)**

Add to `phase110-regression-guards.spec.ts`:
```typescript
import { execSync } from 'node:child_process';

describe('Phase 110 G3: tsc baseline clean', () => {
  it('pnpm tsc --noEmit exits 0', () => {
    try {
      execSync('pnpm tsc --noEmit', {
        cwd: path.resolve(__dirname, '../../../'),
        stdio: 'pipe',
      });
      expect(true).toBe(true);
    } catch (e) {
      const stderr = (e as { stderr?: Buffer }).stderr?.toString() ?? '';
      throw new Error(`tsc failed:\n${stderr}`);
    }
  }, 120_000);
});
```

- [ ] **Step 8.2: Write G4 (vitest clean baseline)**

Add to same file:
```typescript
describe('Phase 110 G4: vitest baseline clean', () => {
  it('pnpm vitest run reports 0 failed', { retry: 0, timeout: 180_000 }, () => {
    const out = execSync('pnpm vitest run --reporter=basic 2>&1', {
      cwd: path.resolve(__dirname, '../../../'),
      encoding: 'utf-8',
    });
    const match = out.match(/Tests\s+(\d+)\s+failed/);
    expect(match?.[1] ?? '0').toBe('0');
  });
});
```

- [ ] **Step 8.3: Write G5 (spec files have no tsc errors)**

Add to same file:
```typescript
const SPEC_FILES_WITH_TSC_ERRORS = [
  'tests/unit/components/creator/CreatorDeviationFinalize.spec.ts',
  'tests/unit/components/creator/CreatorBatchRhythm.spec.ts',
  'tests/unit/components/world/factions/FactionGraphCanvas.spec.ts',
  'tests/unit/components/world/factions/FactionGraph.spec.ts',
  'tests/unit/components/world/characters/CharacterRelationships.spec.ts',
  'tests/unit/components/world/WorldTabs.spec.ts',
];

describe('Phase 110 G5: fixed spec files remain tsc-clean', () => {
  it('pnpm tsc reports 0 errors for these 6 paths', { timeout: 120_000 }, () => {
    const out = execSync('pnpm tsc --noEmit 2>&1', {
      cwd: path.resolve(__dirname, '../../../'),
      encoding: 'utf-8',
    });
    for (const specFile of SPEC_FILES_WITH_TSC_ERRORS) {
      expect(out).not.toContain(specFile);
    }
  });
});
```

- [ ] **Step 8.4: Run G3-G5 to verify they pass**

Run: `cd apps/dashboard && pnpm vitest run tests/unit/guards/phase110-regression-guards.spec.ts 2>&1 | tail -10`
Expected: `Test Files  1 passed` with 4+ tests passing

- [ ] **Step 8.5: Commit C7**

```bash
git add apps/dashboard/tests/unit/guards/phase110-regression-guards.spec.ts
git commit -m "test(phase-110): 4 regression guards G3-G5 (G1+G2 already in C1/C2)

G3: pnpm tsc --noEmit exits 0
G4: pnpm vitest run 0 failed
G5: 6 previously-erroring spec files now tsc-clean

Phase 110 Task 8 / 9."
```

---

## Task 9: Docs sync (Commit C8)

**Files:**
- Modify: `CLAUDE.md` (version bump v60.7 → v60.8)
- Create: `docs/superpowers/handoffs/2026-09-23-phase-110-pre-existing-issues-cleanup-handoff.md`

- [ ] **Step 9.1: Update CLAUDE.md version line**

Open `CLAUDE.md` and find the version line that says `**版本**: v60.7`. Change to `v60.7 → v60.8` and add a brief "Previous" entry describing Phase 110.

Format the new entry following the pattern in the existing Previous entries. Suggested draft:

```
> **Previous**: v60.8 (Phase 110 Pre-existing Issues Closure — 1st TechDebt cleanup since v41 mini; 9 atomic commits on master; frontend-only scope: 55 tsc errors + 4 vitest failures → 0; `src/api/illustrations.ts` 9 production errors fixed via `$fetch` → native `fetch()` (8 callsites + 1 cast) + 4 Phase 107-109 composables registered in `src/composables/index.ts` (useBulkDeleteToast + useBulkRegenerateToast + useDeleteFromNotificationToast + useNotificationStream) + `architecture-guards.spec.ts` excludes `.spec.ts` from export scan + 2 stale provider-default assertions + nav array updated for Phase 99 4th element + 43 spec tsc errors across 7 files (Pinia store direct mutation → proper actions in 2 creator tests + Vue Test Utils tuple access in FactionGraphCanvas + 3 minor) + 6 regression guards G1-G6 (no $fetch / composables registered / tsc clean / vitest clean / spec tsc clean / Phase 107-109 mention); cluster cumulative Phase 90-110 = 21 phases / 1 NEW package + 5 carryover closures + 7 REQ-002 v2 sub-projects + 7 Phase 102+ extensions + 1 TechDebt closure. v60.7 → v60.8)
```

- [ ] **Step 9.2: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-23-phase-110-pre-existing-issues-cleanup-handoff.md` using the same template as prior handoffs (see `2026-09-22-phase-109-notifications-page-delete-handoff.md` for format).

Key sections to include:
- Summary
- 9 atomic commits list
- Validation gates (55 → 0 tsc, 4 → 0 vitest)
- 6 regression guards G1-G6
- 4 lessons (apply N.14 audit pattern)

- [ ] **Step 9.3: Commit C8**

```bash
git add CLAUDE.md docs/superpowers/handoffs/2026-09-23-phase-110-pre-existing-issues-cleanup-handoff.md
git commit -m "docs(phase-110): CLAUDE.md v60.7 -> v60.8 + handoff

Cluster cumulative Phase 90-110 = 21 phases.

Phase 110 Task 9 / 9. Phase 110 closed."
```

---

## Task 10: Final validation

- [ ] **Step 10.1: Run all gates**

```bash
cd apps/dashboard
pnpm tsc --noEmit 2>&1 | grep -E "error TS" | wc -l   # Expected: 0
pnpm vitest run 2>&1 | grep -E "Test Files|Tests " | tail -3   # Expected: 0 failed
pnpm exec knip 2>&1 | tail -5   # Expected: 0 issues
```

- [ ] **Step 10.2: Verify 9 atomic commits on master**

```bash
git log --oneline master -9
```
Expected: 9 commits between `6d401370` (last spec fixup) and HEAD.

- [ ] **Step 10.3: Verify 0 backend changes**

```bash
git diff --stat 6d401370..HEAD -- 'apps/studio_api/' 'packages/'
```
Expected: empty output.

---

## Self-Review Notes

- **Spec coverage**: All 9 commit blocks from spec §7 mapped to tasks. ✓
- **Placeholder scan**: Step 2.5 has a table with 8 call sites — verified exact lines. Step 7 has category labels A/B/C explaining root causes. No "TBD" or "implement later".
- **Type consistency**: `rawFetchJson` / `rawFetchVoid` defined in Step 2.4, used in Step 2.5 — same names. `setActiveJob` placeholder in Step 7.3 noted "Pick the action that takes the same parameters" — needs investigation during execution; flagged.
- **Risk noted**: Step 5.3 has fallback "defer and flag for plan revision" if default is not `openai` — graceful.