# Phase 103 — Audit & Resolve Unused Exports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce knip's `Unused exports` from 27 source files (130+ individual exports) to zero by deleting truly-dead exports + adding `composables/index.ts` barrel re-exports to knip.json#ignore.

**Architecture:** Bulk surgical cleanup — 4 whole-file deletes + 19 source-file partial edits (export stripping) + 1 file delete (`types/index.ts`) + 1 type-list strip (`types/composables.ts`) + 1 knip.json edit. Single atomic commit because knip.json ignore entry depends on deletions being done first (intermediate state would have dangling barrel re-exports).

**Tech Stack:** JavaScript/TypeScript, Vue 3, knip 6.32.2, pnpm.

---

## File Structure

**Files deleted (5 whole files):**
- `apps/dashboard/src/composables/useApiConnectivity.js`
- `apps/dashboard/src/composables/useDashboardRole.js`
- `apps/dashboard/src/composables/useWidgetRegistry.js`
- `apps/dashboard/src/config/creatorPanelMatrix.js`
- `apps/dashboard/src/types/index.ts`

**Files with partial edits (19):**
- `apps/dashboard/src/api/core.js` — 11 dead exports removed
- `apps/dashboard/src/composables/useCreatorProductTools.js` — 1 export removed
- `apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts` — 1 export → local const
- `apps/dashboard/src/composables/useCreatorWrite/index.ts` — 1 re-export removed
- `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts` — 1 export → local const
- `apps/dashboard/src/composables/useDashboardWidgets.js` — 1 export removed
- `apps/dashboard/src/composables/useEventBus.js` — 2 exports removed
- `apps/dashboard/src/composables/useTierBudgetAlerts.js` — 3 exports removed
- `apps/dashboard/src/composables/index.ts` — barrel re-exports of dead sources stripped
- `apps/dashboard/src/config/brand.js` — 3 deprecated exports removed
- `apps/dashboard/src/config/dashboardNav.js` — 2 exports removed
- `apps/dashboard/src/config/dashboardNavByMode.js` — 2 exports removed
- `apps/dashboard/src/config/dashboardNavTitles.js` — 1 export removed
- `apps/dashboard/src/config/humanFirstNav.js` — 2 exports removed
- `apps/dashboard/src/utils/cascadeGraphUtils.js` — 3 exports → local consts
- `apps/dashboard/src/utils/creatorMicroTaskUtils.js` — 1 export → local const
- `apps/dashboard/src/utils/writeResumeStorage.js` — 1 export removed
- `apps/dashboard/tests/e2e-smoke/helpers/live-backend.js` — 1 export → local const
- `apps/dashboard/tests/e2e-smoke/helpers/quarantine.js` — 1 export → removed entirely
- `apps/dashboard/tests/visual-audit/helpers/capture-ui-audit.js` — 1 export → local const
- `apps/dashboard/src/types/composables.ts` — 9 dead type exports removed

**Files with knip config edit (1):**
- `apps/dashboard/knip.json` — add `src/composables/index.ts` to `ignore` array

**Total**: 25 file operations + 1 config edit.

---

## Task 1: Pre-flight — git state + verify all 24 source files exist + tests baseline

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `4f85a760 docs(spec): Phase 103 — audit & resolve unused exports design`. Working tree clean.

- [ ] **Step 1.2: Confirm all 5 to-be-deleted files exist**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/src/composables/useApiConnectivity.js \
  apps/dashboard/src/composables/useDashboardRole.js \
  apps/dashboard/src/composables/useWidgetRegistry.js \
  apps/dashboard/src/config/creatorPanelMatrix.js \
  apps/dashboard/src/types/index.ts; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "All 5 files exist"
```

Expected: `All 5 files exist`. If any MISSING, STOP.

- [ ] **Step 1.3: Confirm all 19 to-be-partially-edited files exist**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/src/api/core.js \
  apps/dashboard/src/composables/useCreatorProductTools.js \
  apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts \
  apps/dashboard/src/composables/useCreatorWrite/index.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts \
  apps/dashboard/src/composables/useDashboardWidgets.js \
  apps/dashboard/src/composables/useEventBus.js \
  apps/dashboard/src/composables/useTierBudgetAlerts.js \
  apps/dashboard/src/composables/index.ts \
  apps/dashboard/src/config/brand.js \
  apps/dashboard/src/config/dashboardNav.js \
  apps/dashboard/src/config/dashboardNavByMode.js \
  apps/dashboard/src/config/dashboardNavTitles.js \
  apps/dashboard/src/config/humanFirstNav.js \
  apps/dashboard/src/utils/cascadeGraphUtils.js \
  apps/dashboard/src/utils/creatorMicroTaskUtils.js \
  apps/dashboard/src/utils/writeResumeStorage.js \
  apps/dashboard/tests/e2e-smoke/helpers/live-backend.js \
  apps/dashboard/tests/e2e-smoke/helpers/quarantine.js \
  apps/dashboard/tests/visual-audit/helpers/capture-ui-audit.js \
  apps/dashboard/src/types/composables.ts; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "All 21 files exist"
```

(Note: 21 files in Group 2+4 — 20 partial edits + 1 type strip = 21 distinct file ops)

Expected: `All 21 files exist`.

- [ ] **Step 1.4: Confirm knip.json is at apps/dashboard/**

```bash
cd /home/ailearn/projects/LingWen && cat apps/dashboard/knip.json
```

Expected content:
```json
{
  "entry": [
    "src/main.js",
    "src/router/index.js",
    "src/router/routes.js"
  ],
  "project": [
    "src/**/*.{js,ts,vue}",
    "tests/**/*.{js,ts}"
  ],
  "ignore": [
    "tests/fixtures/lint-testid/clean.spec.ts",
    "tests/fixtures/lint-testid/dirty.spec.ts",
    "tests/visual-audit/capture.spec.js",
    "tests/visual-audit/regression.spec.js",
    "tests/visual-audit/ui-metrics.spec.js"
  ]
}
```

- [ ] **Step 1.5: Capture test baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If red, STOP.

- [ ] **Step 1.6: Capture knip baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused exports"
```

Expected: `Unused exports (27)` (was 27 source files at design time).

---

## Task 2: Delete 5 whole files (Groups 1 + 3)

**Files:**
- Delete: 5 files via `git rm`

- [ ] **Step 2.1: Delete via `git rm`**

```bash
cd /home/ailearn/projects/LingWen && git rm \
  apps/dashboard/src/composables/useApiConnectivity.js \
  apps/dashboard/src/composables/useDashboardRole.js \
  apps/dashboard/src/composables/useWidgetRegistry.js \
  apps/dashboard/src/config/creatorPanelMatrix.js \
  apps/dashboard/src/types/index.ts
```

Expected: 5 `rm '...'` lines.

- [ ] **Step 2.2: Verify all 5 deleted**

```bash
cd /home/ailearn/projects/LingWen && git status --short | grep "^[[:space:]]*D " | wc -l
```

Expected: `5` (or higher if other files changed; minimum 5 deleted).

---

## Task 3: Strip dead exports from 20 source files (Groups 2 + 4, excluding barrel)

**Files:**
- Edit: 20 files

The exact edits per file are documented in spec §4.1. For each, use the Edit tool with old_string/new_string. After all 20 edits, proceed to Task 4.

- [ ] **Step 3.1: Edit `src/api/core.js`** — Remove 8 error class exports + API_ERROR_EVENT const + duplicate re-export line

For each export to remove, the Edit pattern is:
- Find: `export const API_ERROR_EVENT` (or class definition with `export` prefix)
- Replace: drop the `export` keyword OR remove the entire line if it becomes unused

Specifically:
- Line 17: `export const API_ERROR_EVENT` → `const API_ERROR_EVENT` (keep const, drop export)
- Lines 37-126: 8 error classes — remove `export` from each `export class XxxError extends Error {`
- Line 255: `export { apiConnectivity, markApiOffline, markApiOnline };` → remove entire line (these are re-exports from `./connectivity.js` and consumers import from `./connectivity.js` directly)

```bash
cd /home/ailearn/projects/LingWen && grep -c "^export" apps/dashboard/src/api/core.js
```
Before: 11+ export lines. After: 0 `export` lines starting with `export` at column 0 (since each remaining export has indentation or the `export` was removed).

- [ ] **Step 3.2: Edit `src/composables/useCreatorProductTools.js`** — Remove 1 export

- Find: `export { CREATOR_PUBLISH_PLATFORMS }`
- Replace: (remove entire line)

- [ ] **Step 3.3: Edit `src/composables/useCreatorProductTools/useProductPublish.ts`** — Convert 1 export to local const

- Find: `export const CREATOR_PUBLISH_PLATFORMS`
- Replace: `const CREATOR_PUBLISH_PLATFORMS`

- [ ] **Step 3.4: Edit `src/composables/useCreatorWrite/index.ts`** — Remove 1 re-export

- Find: `export { useWriteValidation }` (or similar — verify exact text via `grep`)
- Replace: (remove entire line)

- [ ] **Step 3.5: Edit `src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts`** — Convert 1 export to local const

- Find: `export const VALID_CREATION_MODES`
- Replace: `const VALID_CREATION_MODES`

- [ ] **Step 3.6: Edit `src/composables/useDashboardWidgets.js`** — Remove 1 export

- Find: `export { getDefaultDashboardLayout }` (or whichever line exports it)
- Replace: (remove entire line)

- [ ] **Step 3.7: Edit `src/composables/useEventBus.js`** — Remove 2 exports

- Find: the line containing `onWsConnected, onWsDisconnected` (likely in an `export { ... }` block)
- Replace: remove those names from the export block (keep other exports)

- [ ] **Step 3.8: Edit `src/composables/useTierBudgetAlerts.js`** — Remove 3 exports

- Find: `export const TIER_ORDER`, `export const TIER_ALARM_WARNING_PCT`, `export const TIER_ALARM_EXCEEDED_PCT` (or similar)
- Replace: each → drop `export` (keep as local const)

- [ ] **Step 3.9: Edit `src/config/brand.js`** — Remove 3 deprecated exports + their comment block

Find the deprecated block:
```
/**
 * @deprecated  Use BRAND.* object instead.
 */
export const BRAND_PRODUCT_NAME
export const BRAND_PRODUCT_TAGLINE
export const BRAND_FEATURE_READING_POWER
```
Replace with empty (remove entire block including deprecated comment).

- [ ] **Step 3.10: Edit `src/config/dashboardNav.js`** — Remove 2 exports

- Find: `export const DASHBOARD_NAV_GROUPS`, `export const DASHBOARD_NAV_IDS`
- Replace: drop `export` (keep as local const) OR remove entirely if unused internally

- [ ] **Step 3.11: Edit `src/config/dashboardNavByMode.js`** — Remove 2 exports

Same pattern as 3.10.

- [ ] **Step 3.12: Edit `src/config/dashboardNavTitles.js`** — Remove 1 export

Same pattern.

- [ ] **Step 3.13: Edit `src/config/humanFirstNav.js`** — Remove 2 exports

Same pattern.

- [ ] **Step 3.14: Edit `src/utils/cascadeGraphUtils.js`** — Convert 3 exports to local consts

- Find: `export const DEPTH_LAYER_COLORS`, `export const ACTION_TYPE_COLORS`, `export const ACTION_TYPE_ORDER`
- Replace: drop `export` from each (keep as local const)

- [ ] **Step 3.15: Edit `src/utils/creatorMicroTaskUtils.js`** — Convert 1 export to local const

Same pattern.

- [ ] **Step 3.16: Edit `src/utils/writeResumeStorage.js`** — Remove 1 export

- Find: `export function hasAnyWriteResume`
- Replace: drop `export` (keep as local function) OR remove entirely if unused

Verify first that `hasAnyWriteResume` is not called anywhere within the same file before removing. Per explore agent, it's defined at line 51 but never called. Remove entirely if safe.

- [ ] **Step 3.17: Edit `tests/e2e-smoke/helpers/live-backend.js`** — Convert 1 export to local const

- Find: `export const LIVE_LLM_E2E_ENABLED`
- Replace: `const LIVE_LLM_E2E_ENABLED`

- [ ] **Step 3.18: Edit `tests/e2e-smoke/helpers/quarantine.js`** — Remove 1 export

- Find: `export const QUARANTINE_TAG`
- Replace: (remove entire line) — playwright.config.js uses string literal `/@quarantine/` directly

Verify `QUARANTINE_TAG` is not referenced elsewhere in the file before removing.

- [ ] **Step 3.19: Edit `tests/visual-audit/helpers/capture-ui-audit.js`** — Convert 1 export to local const

- Find: `export const VISUAL_AUDIT_OUTPUT_DIR`
- Replace: `const VISUAL_AUDIT_OUTPUT_DIR`

- [ ] **Step 3.20: Edit `src/types/composables.ts`** — Remove 9 dead type exports

The 9 types to remove: `WorkspaceTab`, `StudioProjectState`, `DashboardNavState`, `PulseEntry`, `ReviewDecision`, `CostWindowReturn`, `RippleStoreReturn`, `SplitTabsResult`, `CreatorUiProfile`.

For each:
- Find: `export interface WorkspaceTab { ... }` (or `export type WorkspaceTab = ...`)
- Replace: drop `export` keyword (keep as internal type) OR remove the entire declaration if it becomes orphaned

---

## Task 4: Strip barrel re-exports from `composables/index.ts`

**Files:**
- Edit: `apps/dashboard/src/composables/index.ts`

After Task 2 + 3 deletions, the barrel re-exports for dead source exports become dangling. Remove them.

- [ ] **Step 4.1: View current barrel re-export**

```bash
cd /home/ailearn/projects/LingWen && cat apps/dashboard/src/composables/index.ts
```

- [ ] **Step 4.2: Identify which re-exports to remove**

After Tasks 2+3, these re-exports in `composables/index.ts` must be removed:
- `useApiConnectivity` (source deleted)
- `useDashboardRole` (source deleted)
- `useDevice` (source — useDevice.js had only useDevice export which is dead; whole file may need deletion — verify)
- `useWidgetRegistry` + 15 widget functions (source deleted)
- `registerDashboardWidgets` (verify in barrel)
- `getDefaultDashboardLayout` (useDashboardWidgets.js stripped; still might be in barrel from earlier re-export)
- `useCreatorVolumePlanDiff` (verify)
- All other re-exports of dead source exports

Important: Do NOT remove re-exports for `useCreatorPage.js` parent facade consumers — those are public API.

- [ ] **Step 4.3: Apply targeted Edits to barrel**

For each dangling re-export, use Edit tool. Examples:
- Find: `export { useApiConnectivity } from './useApiConnectivity.js';`
- Replace: (remove entire line)

- Find: `export { useWidgetRegistry, defineWidget, registerWidget, ... } from './useWidgetRegistry.js';`
- Replace: (remove entire line)

- [ ] **Step 4.4: Verify barrel no longer references deleted source files**

```bash
cd /home/ailearn/projects/LingWen && grep -E "useApiConnectivity|useDashboardRole|useWidgetRegistry|useDevice\.js|getDefaultDashboardLayout" apps/dashboard/src/composables/index.ts
```

Expected: zero matches (or only the legitimate `useDevice` reference that may remain if `useDevice` is still exported from elsewhere).

---

## Task 5: Edit `apps/dashboard/knip.json` — add barrel to ignore

**Files:**
- Modify: `apps/dashboard/knip.json`

- [ ] **Step 5.1: Apply Edit**

Use Edit tool.

- **Find (old_string)**:
```json
    "tests/visual-audit/ui-metrics.spec.js"
  ]
}
```

- **Replace (new_string)**:
```json
    "tests/visual-audit/ui-metrics.spec.js",
    "src/composables/index.ts"
  ]
}
```

The new entry `src/composables/index.ts` is added to the existing ignore array. Trailing comma added to the previous last entry.

- [ ] **Step 5.2: Verify JSON parses**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import json;d=json.load(open('apps/dashboard/knip.json'));print('OK, ignore has', len(d.get('ignore', [])), 'entries:', d['ignore'])"
```

Expected: `OK, ignore has 6 entries: ['tests/fixtures/lint-testid/clean.spec.ts', 'tests/fixtures/lint-testid/dirty.spec.ts', 'tests/visual-audit/capture.spec.js', 'tests/visual-audit/regression.spec.js', 'tests/visual-audit/ui-metrics.spec.js', 'src/composables/index.ts']`

---

## Task 6: Verify post-edit state

**Files:**
- Read-only verification.

- [ ] **Step 6.1: knip `Unused exports` is now 0**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused exports"
```

Expected: `Unused exports (0)`. If still showing files, STOP — investigate which exports remain.

- [ ] **Step 6.2: Full knip report — other categories unchanged**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

Expected:
```
Unlisted binaries (1)
Unused dependencies (1)
Unused devDependencies (1)
Unused exported types (12)  (or 3 if Phase 103 also cleared 9 dead types in types/composables.ts)
Unused files (1)  (just types/index.ts if kept — wait, it was DELETED in Task 2)
```

If `Unused files (0)` (types/index.ts deleted), and `Unused exported types (3)` (9 dead removed from composables.ts → 12 - 9 = 3 remain), that's Phase 103 success.

If `Unused exported types` still shows 12, the 9 type strip didn't take effect — investigate.

- [ ] **Step 6.3: Tests still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: 1545 tests pass.

- [ ] **Step 6.4: Build succeeds**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -10
```

Expected: build completes successfully (~20s). No errors.

- [ ] **Step 6.5: vue-tsc clean**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -5
```

Expected: empty output (0 errors).

- [ ] **Step 6.6: ESLint clean (incl. fixtures)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run lint:all 2>&1 | tail -10
```

Expected: no errors.

```bash
cd /home/ailearn/projects/LingWen && pnpm lint:testid 2>&1 | tail -5
```

Expected: lint:testid still functions (may report 0 violations due to `/* eslint-disable */` in dirty.spec.ts as noted in Phase 102 review).

- [ ] **Step 6.7: ESLint rule's string reference to `useDashboardRole` is harmless dead string**

```bash
cd /home/ailearn/projects/LingWen && grep -n "useDashboardRole" apps/dashboard/eslint-rules/no-store-value-access.js 2>/dev/null || \
  grep -rn "useDashboardRole" apps/dashboard/eslint-rules/ 2>/dev/null
```

Expected: the string check still exists in ESLint rule (it's a string literal, not an import; deletion of source file is harmless).

- [ ] **Step 6.8: Verify deleted whole files are gone**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/src/composables/useApiConnectivity.js \
  apps/dashboard/src/composables/useDashboardRole.js \
  apps/dashboard/src/composables/useWidgetRegistry.js \
  apps/dashboard/src/config/creatorPanelMatrix.js \
  apps/dashboard/src/types/index.ts; do \
  test ! -f "$f" || { echo "STILL EXISTS: $f"; exit 1; }; \
done && echo "All 5 files deleted"
```

Expected: `All 5 files deleted`.

- [ ] **Step 6.9: Verify partial edits' key exports are gone**

```bash
cd /home/ailearn/projects/LingWen && for sym in API_ERROR_EVENT BRAND_PRODUCT_NAME TIER_ORDER DEFAULT_CHAPTER_WORD_GOALS hasAnyWriteResume LIVE_LLM_E2E_ENABLED QUARANTINE_TAG; do \
  echo "--- $sym ---"; \
  grep -rln "export.*$sym\|export const $sym\|export function $sym\|export class $sym" apps/dashboard/src apps/dashboard/tests 2>/dev/null | grep -v node_modules | head -3; \
done
```

Expected: each symbol either not exported (no match) or only exists in non-public location. Specific symbols to check:
- `API_ERROR_EVENT`: should be `const` not `export const`
- `BRAND_PRODUCT_NAME`: removed entirely
- `TIER_ORDER`: should be `const` not `export const`
- `DEFAULT_CHAPTER_WORD_GOALS`: should be `const` not `export const`
- `hasAnyWriteResume`: removed entirely
- `LIVE_LLM_E2E_ENABLED`: should be `const` not `export const`
- `QUARANTINE_TAG`: removed entirely

- [ ] **Step 6.10: Diff stat — expected size**

```bash
cd /home/ailearn/projects/LingWen && git diff --stat
```

Expected: ~25 files modified (5 deleted + 20 partial + 1 knip.json), net ~200-300 deletions (each dead export is a few lines + comment blocks + file deletions).

---

## Task 7: Commit + push

**Files:**
- Commit: ~25 modified files + 5 deletes

- [ ] **Step 7.1: Stage all changes**

```bash
cd /home/ailearn/projects/LingWen && git add -A && git status --short | wc -l
```

Expected: ~26 entries (5 deletes + 20 partial edits + 1 knip.json).

- [ ] **Step 7.2: Commit with the spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): delete 47 unused exports + 1 dead file (Phase 103)" -m "Phase 103 — reduce knip Unused exports from 27 files (130+ exports):

Delete 4 whole files (only export was dead):
- src/composables/useApiConnectivity.js (1 export dead)
- src/composables/useDashboardRole.js (1 export dead)
- src/composables/useWidgetRegistry.js (17 exports dead)
- src/config/creatorPanelMatrix.js (10 exports dead)

Strip dead exports in 19 source files:
- src/api/core.js (8 error classes + 3 duplicate re-exports)
- src/composables/useCreatorProductTools.js (1)
- src/composables/useCreatorProductTools/useProductPublish.ts (1, → local)
- src/composables/useCreatorWrite/index.ts (1 re-export)
- src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts (1, → local)
- src/composables/useDashboardWidgets.js (1)
- src/composables/useEventBus.js (2)
- src/composables/useTierBudgetAlerts.js (3)
- src/composables/index.ts (all barrel re-exports of dead sources stripped)
- src/config/brand.js (3 deprecated BRAND_*)
- src/config/dashboardNav.js (2)
- src/config/dashboardNavByMode.js (2)
- src/config/dashboardNavTitles.js (1)
- src/config/humanFirstNav.js (2)
- src/utils/cascadeGraphUtils.js (3, → local)
- src/utils/creatorMicroTaskUtils.js (1, → local)
- src/utils/writeResumeStorage.js (1)
- tests/e2e-smoke/helpers/live-backend.js (1, → local)
- tests/e2e-smoke/helpers/quarantine.js (1, → removed)
- tests/visual-audit/helpers/capture-ui-audit.js (1, → local)

Delete 1 dead file:
- src/types/index.ts (whole barrel file has 0 consumers)

Strip 9 dead types in src/types/composables.ts:
- WorkspaceTab, StudioProjectState, DashboardNavState, PulseEntry,
  ReviewDecision, CostWindowReturn, RippleStoreReturn,
  SplitTabsResult, CreatorUiProfile

Add src/composables/index.ts to apps/dashboard/knip.json#ignore:
- Remaining ~50 public-API barrel re-exports are intentional for
  downstream consumers; knip can't trace cross-package usage.

All deletions verified via grep (0 external consumers per Phase 103
explore subagent). ~47 individual exports removed across 24 files.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors. knip output:
Unused exports (0) ✅ (or single-digit residual if barrel ignore
syntax needs adjustment — Phase 103.1 follow-up if so)." 2>&1 | tail -5
```

- [ ] **Step 7.3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

- [ ] **Step 7.4: Final state check**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -5 && git status
```

Expected: 5 commits visible. Tree clean.

---

## Success Criteria

- [ ] 5 files deleted (Groups 1 + 3)
- [ ] 19 partial source edits + 1 type strip completed (Groups 2 + 4)
- [ ] `composables/index.ts` barrel re-exports of dead sources stripped
- [ ] `apps/dashboard/knip.json#ignore` includes `src/composables/index.ts`
- [ ] `pnpm exec knip` reports `Unused exports (0)`
- [ ] `Unused exported types` count drops from 12 → ~3 (9 dead types removed)
- [ ] `Unused files` count drops from 1 → 0 (`types/index.ts` deleted)
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] ESLint fixtures still work
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## Rollback

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit (all 25 file operations + knip.json edit). No data loss.

---

## Self-Review Notes

**Spec coverage**:
- §4.1 Group 1 (4 whole-file deletes) → Task 2 ✅
- §4.1 Group 2 (19 partial edits) → Task 3 + Task 4 (barrel) ✅
- §4.1 Group 3 (types/index.ts) → Task 2 ✅
- §4.1 Group 4 (types/composables.ts) → Task 3.20 ✅
- §4.2 knip.json ignore → Task 5 ✅
- §4.4 Verification → Task 6 ✅
- §7 Commit Strategy → Task 7 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only deletions + const reclassification.

**Edge cases handled**:
- Task 1.2/1.3 file existence checks — catch path typos before deletion
- Task 1.5 test baseline — catch pre-existing breakage
- Task 1.6 knip baseline — catch scope drift
- Task 4.4 verify barrel no longer references deleted sources (avoid dangling imports)
- Task 6.2 knip other categories unchanged — catch scope bleed
- Task 6.6 ESLint + fixtures still work — catch test infra breakage
- Task 6.7 ESLint rule's string reference is harmless dead string — confirms safe
- Task 6.9 verify partial edits' key exports are gone — catch missed Edit
- Rollback section