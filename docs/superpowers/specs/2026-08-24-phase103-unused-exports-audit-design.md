# Phase 103 — Audit & Resolve Unused Exports (27 files)

> **Date**: 2026-08-24
> **Phase**: 103
> **Source**: Phase 99 knip CI integration (`b2110c20`) follow-up — `Unused exports (27)` (actually ~130 individual exports across 27 files)
> **Status**: Design

---

## 1. Context

Phase 99 promoted knip to hard-blocking CI gate. Phase 99.1 fixed pnpm setup. Phase 102 reduced `Unused files` from 36 → 1. Phase 102.1 added root knip delegation + cleaned stale comments. **Phase 103 reduces `Unused exports` from 27 source files to a much smaller count by deleting truly-dead exports and adding legitimate public-API barrel re-exports to knip.json ignore.**

`pnpm exec knip --reporter=compact` reports `Unused exports (27)` (27 source files with unused exports). Total individual exports flagged: ~130.

**Investigation result** (via Phase 103 explore subagent):

| Bucket | Count | Action |
|--------|-------|--------|
| TRULY DEAD (zero consumers anywhere) | ~47 individual exports | Delete |
| PUBLIC API / KNIP FALSE POSITIVE (intentional exports, knip can't trace downstream consumers) | ~83 individual exports | Ignore in knip.json |

Plus 1 truly dead file (`src/types/index.ts`) and 9 dead types in `src/types/composables.ts`.

**Why this matters**:
- Knip gate currently fails on this category, blocking CI from going green
- After cleanup, only the genuinely intentional public-API barrel re-exports remain flagged
- Those get added to knip.json#ignore (same pattern as Phase 102 ignored 5 test fixtures)

---

## 2. Goal

Reduce knip's `Unused exports` count substantially:
- Delete all ~47 truly-dead exports + 1 truly-dead file
- Strip the corresponding barrel re-exports from `composables/index.ts` (so deleted exports don't leave dangling re-exports)
- Add remaining barrel re-exports that point to *live* source files but knip can't trace to knip.json#ignore (those are intentional public API)

End-state target: `Unused exports` reports 0 (or a small bounded count if knip config syntax can't fully suppress barrel re-exports — at most a single-digit residual that requires Phase 103.1 follow-up).

---

## 3. Non-Goals

- **NOT** deleting the `composables/index.ts` barrel itself — it's the legitimate public API surface, just needs re-export cleanup + ignore entry.
- **NOT** deleting `useCreatorPage.js` (parent facade that consumes many barrel re-exports) — it's a live consumer.
- **NOT** modifying `types/composables.ts`'s 25+ public-API types (the agent flagged them as public; they're re-exported through composables barrel).
- **NOT** investigating dead types further — this spec handles only `src/types/composables.ts` types (9 dead) and `src/types/index.ts` (whole file dead).
- **NOT** modifying `eslint-rules/no-store-value-access.js` even though it may reference `'useDashboardRole'` as a string literal (it's an ESLint rule, not source code; deletion of source file leaves string check as harmless dead-reference).
- **NOT** touching the 12 Unused exported types beyond the 9 dead ones in `types/composables.ts` — the rest are public API (deferred to Phase 104 if needed).

---

## 4. Design

### 4.1 Decision Matrix (47 dead exports + 9 dead types + 1 dead file)

**Group 1 — Delete whole file (4 files)**:
| File | Reason |
|------|--------|
| `src/composables/useApiConnectivity.js` | Only export is `useApiConnectivity`, which has zero consumers (the actual API connectivity logic lives in `src/api/connectivity.js` directly imported by `SettingsPage.vue`, `useApiConnectivity.js`'s role is duplicating it). |
| `src/composables/useDashboardRole.js` | Only export is `useDashboardRole`, which has zero consumers. ESLint rule's string check `"useDashboardRole"` becomes a harmless dead reference (no import). |
| `src/composables/useWidgetRegistry.js` | All 17 exports (`useWidgetRegistry`, `defineWidget`, `registerWidget`, `getWidget`, etc.) + the composable function have zero consumers across 25+ Vue components and composables. The widget system was designed but never invoked. |
| `src/config/creatorPanelMatrix.js` | All 10 exports (`CREATOR_WORKSPACE_TAB_DEFS`, `DASHBOARD_HUB_MATRIX`, etc.) have zero consumers. |

**Group 2 — Delete specific exports (knip `Unused exports`) + strip barrel re-exports**:

| File | Lines to remove |
|------|-----------------|
| `src/api/core.js` | `export const API_ERROR_EVENT` (line 17); `export class ApiError, NetworkError, TimeoutError, AuthError, ForbiddenError, NotFoundError, ServerError` (lines 37-126); `export { apiConnectivity, markApiOffline, markApiOnline }` duplicate re-export from `connectivity.js` (line 255) |
| `src/composables/useCreatorProductTools.js` | `export { CREATOR_PUBLISH_PLATFORMS }` (line 29) |
| `src/composables/useCreatorProductTools/useProductPublish.ts` | `export const CREATOR_PUBLISH_PLATFORMS` (line 21) → convert to local `const` |
| `src/composables/useCreatorWrite/index.ts` | `useWriteValidation` re-export (line 15) |
| `src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts` | `export const VALID_CREATION_MODES` (line 27) → convert to local `const` |
| `src/composables/useDashboardWidgets.js` | `export { getDefaultDashboardLayout }` |
| `src/composables/useEventBus.js` | `onWsConnected`, `onWsDisconnected` exports (kept in barrel re-export of `useEventBus.js`) |
| `src/composables/useTierBudgetAlerts.js` | `export const TIER_ORDER, TIER_ALARM_WARNING_PCT, TIER_ALARM_EXCEEDED_PCT` (lines 19, 25, 26) |
| `src/composables/index.ts` | Remove re-exports of: `useApiConnectivity`, `useDashboardRole`, `useDevice`, `useEventBus`'s `onWsConnected`/`onWsDisconnected`, `useWidgetRegistry` + 15 widget functions, `getDefaultDashboardLayout`, plus all 47 source-export re-exports for deleted exports |
| `src/config/brand.js` | `export const BRAND_PRODUCT_NAME, BRAND_PRODUCT_TAGLINE, BRAND_FEATURE_READING_POWER` (lines 49, 51, 53) + deprecated comment block |
| `src/config/dashboardNav.js` | `export const DASHBOARD_NAV_GROUPS, DASHBOARD_NAV_IDS` |
| `src/config/dashboardNavByMode.js` | `export const MODE_NAV_ITEM_IDS, MODE_MORE_LINK_IDS` |
| `src/config/dashboardNavTitles.js` | `export const NAV_CONTEXT_TITLES` |
| `src/config/humanFirstNav.js` | `export const HUMAN_FIRST_NAV_IDS, NAV_WRITE_ALIASES` |
| `src/utils/cascadeGraphUtils.js` | Convert `export const DEPTH_LAYER_COLORS, ACTION_TYPE_COLORS, ACTION_TYPE_ORDER` (lines 19, 26, 33) to local consts |
| `src/utils/creatorMicroTaskUtils.js` | Convert `export const DEFAULT_CHAPTER_WORD_GOALS` (line 4) to local const |
| `src/utils/writeResumeStorage.js` | `export function hasAnyWriteResume` (line 51) |
| `tests/e2e-smoke/helpers/live-backend.js` | `export const LIVE_LLM_E2E_ENABLED` (line 11) → make local |
| `tests/e2e-smoke/helpers/quarantine.js` | `export const QUARANTINE_TAG` (line 2) → remove entirely (playwright.config.js uses string literal `/@quarantine/`) |
| `tests/visual-audit/helpers/capture-ui-audit.js` | `export const VISUAL_AUDIT_OUTPUT_DIR` (line 7) → make local const |

**Group 3 — Delete whole file (1 dead file)**:
| File | Reason |
|------|--------|
| `src/types/index.ts` | Re-exports `api.js` + `composables.js` types but zero consumers import from this barrel. |

**Group 4 — Strip dead types in `src/types/composables.ts`**:
Remove 9 type exports: `WorkspaceTab`, `StudioProjectState`, `DashboardNavState`, `PulseEntry`, `ReviewDecision`, `CostWindowReturn`, `RippleStoreReturn`, `SplitTabsResult`, `CreatorUiProfile`.

### 4.2 knip.json ignore addition

After Group 1-4 deletions, knip will still report the remaining ~83 public-API barrel re-exports in `src/composables/index.ts` that knip can't trace downstream. Add `src/composables/index.ts` to the existing `ignore` array so knip stops reporting this file.

**Proposed ignore addition** (extending the existing array):
```json
"ignore": [
  "tests/fixtures/lint-testid/clean.spec.ts",
  "tests/fixtures/lint-testid/dirty.spec.ts",
  "tests/visual-audit/capture.spec.js",
  "tests/visual-audit/regression.spec.js",
  "tests/visual-audit/ui-metrics.spec.js",
  "src/composables/index.ts"
]
```

### 4.3 Risk Analysis

- **Build risk**: Low. All deleted exports have 0 consumers verified via grep. Build impact verified by `pnpm run build`.
- **Test risk**: Low. ESLint rule's string reference to `'useDashboardRole'` (in `eslint-rules/no-store-value-access.js`) becomes a dead string but doesn't break lint. Tests for knip-ignored files (`tests/visual-audit/*`, `tests/fixtures/lint-testid/*`) still work via ESLint/Playwright config.
- **Behavioral risk**: Very low. These exports have been "dead" in the runtime — deleting them doesn't change what users see.
- **Type-check risk**: Low. `types/composables.ts` removal of 9 types + `types/index.ts` whole-file deletion could cause compile errors if any file imports those types — but explore agent verified zero importers.
- **Barrel re-export risk**: Low. After deleting dead source exports, the corresponding barrel re-exports are also removed (so no dangling imports). For remaining barrel re-exports (live source, public API), adding the file to knip.json ignore handles the false-positive report.
- **knip config risk**: Low. Adding `src/composables/index.ts` to ignore is justified (the barrel is intentional public API).

### 4.4 Verification Strategy

After change:
1. `pnpm exec knip --reporter=compact 2>&1 | grep "^Unused exports"` — expect `Unused exports (0)` or single-digit residual.
2. `pnpm exec vitest run` — 1545+ tests pass.
3. `pnpm run build` — build succeeds (~20s).
4. `pnpm exec vue-tsc --noEmit` — 0 type errors.
5. `pnpm lint:all` — 0 lint errors.
6. ESLint test fixtures still work: `pnpm lint:testid` should still report violations in `dirty.spec.ts`.
7. `node --check` on each surviving file (skip the 4 deleted whole-files).
8. grep verify: each deleted export has 0 remaining references in source/tests.
9. knip's other categories unchanged (deps, devDeps, binaries, types, files).

### 4.5 Rollback Plan

If a deletion breaks runtime or test:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit (all 24 file operations + knip.json edit). No data loss.

If only the knip.json ignore addition causes new CI behavior:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit  # reverts knip.json
# or restore specific barrel re-exports by reverting individual lines
```

---

## 5. Files Touched

| Category | Count | Operation |
|----------|-------|-----------|
| Whole-file deletes (Group 1) | 4 | `git rm` |
| Partial source edits (Group 2) | 19 files | Edit specific lines |
| Whole-file delete (Group 3) | 1 | `git rm` |
| Type strip (Group 4) | 1 | Edit specific lines |
| **Total file operations** | **24 distinct files** | |
| knip.json edit | 1 | Add to `ignore` array |

**Total**: 25 file operations (4 deletes + 1 knip.json edit + 20 partial edits).

**Files NOT touched**:
- `src/composables/useCreatorPage.js` (parent facade — consumer of public API)
- `src/types/composables.ts`'s ~25 live types
- `apps/dashboard/package.json`
- ESLint config
- All tests (the 5 ignored test files retain their original behavior)

---

## 6. Test Strategy

**No new tests**. Rationale:
- All deleted exports have zero consumers — existing tests cannot assert behavior on absent code.
- The 4 deleted whole files had no test coverage (else knip wouldn't have flagged their exports).
- Existing 1545 tests still cover all production behavior.
- 1545 tests passing after deletion is the test.

---

## 7. Commit Strategy

**Single atomic commit** (despite scope, all changes are coordinated — knip.json ignore entry depends on deletions being done first; if split, intermediate state would have dangling barrel re-exports):

```
refactor(cleanup): delete 47 unused exports + 1 dead file (Phase 103)

Phase 103 — reduce knip Unused exports from 27 files (130+ exports):

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
syntax needs adjustment — Phase 103.1 follow-up if so).
```

Single commit chosen because:
- knip.json ignore addition depends on deletions being done first (intermediate state would have dangling barrel re-exports)
- All changes are coordinated toward single goal (clear knip's Unused exports category)
- Easier to revert if any single deletion turns out wrong

---

## 8. Open Questions

None. Scope confirmed (Option A — full audit 27 files). 3 whole-file decisions confirmed (creatorPanelMatrix, useDashboardRole, useWidgetRegistry all deleted).

---

## 9. Success Criteria

- [ ] 4 files deleted (Group 1)
- [ ] 19 files have specific export lines removed (Group 2)
- [ ] `src/composables/index.ts` has re-exports of dead sources stripped
- [ ] `src/types/index.ts` deleted (Group 3)
- [ ] 9 dead types stripped from `src/types/composables.ts` (Group 4)
- [ ] `apps/dashboard/knip.json#ignore` includes `src/composables/index.ts`
- [ ] `pnpm exec knip` reports `Unused exports (0)` or single-digit residual
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] ESLint fixtures still work (lint:testid reports violations)
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 99 spec: `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md` (§4.4 follow-up queue)
- Phase 99.1 spec: `docs/superpowers/specs/2026-08-24-phase99.1-pnpm-setup-fix-design.md`
- Phase 102 spec: `docs/superpowers/specs/2026-08-24-phase102-unused-files-audit-design.md` (precedent: deleted 30 + ignored 5 in knip.json)
- Phase 102.1 spec: `docs/superpowers/specs/2026-08-24-phase102.1-knip-config-and-comment-cleanup-design.md`
- Phase 103 exploration: explore subagent output (decision matrix of 130+ exports across 27 files)
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5
- knip ignore docs: https://knip.dev/reference/configuration#ignore