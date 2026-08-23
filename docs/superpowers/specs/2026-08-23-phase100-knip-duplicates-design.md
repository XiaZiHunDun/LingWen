# Phase 100 — Fix knip Duplicate Exports (Real)

> **Date**: 2026-08-23
> **Phase**: 100
> **Source**: Phase 95 knip CI integration (`b2110c20`) finding — Duplicate exports (2)
> **Status**: Design

---

## 1. Context

Phase 95 added knip 6.32.2 as a non-blocking CI check (`b2110c20`). knip reported exactly 2 real duplicate exports (everything else is intentionally exported or known false positive):

```
Duplicate exports (2)
useWidgetRegistry|default  apps/dashboard/src/composables/useWidgetRegistry.js
logger|default             apps/dashboard/src/utils/logger.js
```

Both default exports are unused — every consumer uses named imports:

| File | Default export | All consumer imports use named form |
|------|----------------|-------------------------------------|
| `composables/useWidgetRegistry.js:375` | `export default useWidgetRegistry;` | `import { useWidgetRegistry, defineWidget, registerWidgets, ... } from '...'`. Verified across 4 import sites: `composables/index.ts:82`, `components/WidgetRenderer.vue:76`, `composables/useDashboardWidgets.js:1`. |
| `utils/logger.js:83` | `export default logger;` | `import { logger } from '../utils/logger.js'`. Verified across 26 import sites (all use named form). |

**Why this is the right next phase**:
- Clear scope: 2 single-line removals.
- Real win: eliminates 100% of knip's "Duplicate exports" report.
- Atomic: one commit, one PR, one reviewer pass.
- No risk: zero behavioral change (default exports are unreferenced).
- Phase 99 (promote knip to error) is blocked on Phase 100 landing first.

---

## 2. Goal

Eliminate the 2 knip-reported real duplicate exports so knip's "Duplicate exports" report returns zero, while preserving all current import behavior.

---

## 3. Non-Goals

- **NOT** addressing knip's 160 "Unused exports" entries. Many are intentional (composable barrel re-exports for downstream consumers, error classes for type guards, etc.). Out of scope per user decision (Option 1).
- **NOT** addressing knip's "Unused files (36)" / "Unused dependencies (3)" / "Unlisted binaries (9)" categories. Out of scope per user decision.
- **NOT** promoting knip to error. That is Phase 99.
- **NOT** adding tests. Removing 2 unused `export default` lines has zero behavioral impact — adding tests for absence-of-export would be testing a syntactic property, not a behavioral one.

---

## 4. Design

### 4.1 Change Set

Two surgical edits, one per file:

**File 1**: `apps/dashboard/src/composables/useWidgetRegistry.js`
- Remove line 375: `export default useWidgetRegistry;`
- Keep line 343: `export function useWidgetRegistry() { ... }`

**File 2**: `apps/dashboard/src/utils/logger.js`
- Remove line 83: `export default logger;`
- Keep line 41: `export const logger = { ... }`

### 4.2 Risk Analysis

- **Build risk**: None. Default exports are unused — removing them is equivalent to deleting unreferenced code. Vite tree-shaking already excludes them from production bundle.
- **Test risk**: None. No test imports the default exports (verified via grep across `apps/dashboard/src` and `apps/dashboard/tests`).
- **Behavioral risk**: None. ESM tree-shaking means unreferenced exports have zero runtime effect.
- **Lint/type-check risk**: None. vue-tsc and ESLint do not enforce "you must have a default export" or "you must have only one default export" — only knip reports it.

### 4.3 Verification Strategy

After change:
1. `pnpm exec knip` — "Duplicate exports (0)" expected (was 2).
2. `pnpm exec vitest run` — 1545+ tests pass, no test broken.
3. `pnpm run build` — build succeeds (~20s).
4. `pnpm exec vue-tsc --noEmit` — 0 type errors.
5. `pnpm lint:all` — 0 lint errors.
6. Manual grep: `grep -rn "import.*useWidgetRegistry\|import.*logger" apps/dashboard` — all imports still resolve to named exports.

### 4.4 Rollback Plan

If a downstream consumer breaks (unlikely — both default exports are unreferenced in the dashboard codebase):
- Revert the single commit. No data loss, no migration needed.

---

## 5. Files Touched

| File | Change | Lines |
|------|--------|-------|
| `apps/dashboard/src/composables/useWidgetRegistry.js` | Delete line 375 | -1 |
| `apps/dashboard/src/utils/logger.js` | Delete line 83 | -1 |

**Total**: 2 files, 2 lines deleted. No new files.

---

## 6. Test Strategy

**No new tests**. Rationale:
- Behavior is unchanged (unreferenced exports have no runtime effect).
- Existing 1545 tests verify all consumer behavior (all consumers use named imports, which still work).
- Adding "test that default export doesn't exist" would test the syntactic shape of a file, not a behavioral property. The knip run itself is the test.

---

## 7. Commit Strategy

Single atomic commit:
```
refactor(cleanup): remove 2 unused default exports (Phase 100)

Phase 100 — fix knip duplicate exports:

- Delete `export default useWidgetRegistry` (composables/useWidgetRegistry.js:375)
- Delete `export default logger` (utils/logger.js:83)

Both defaults were unreferenced — all consumer import sites use named form.
knip output: Duplicate exports (2 → 0) ✅

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

---

## 8. Open Questions

None. Scope confirmed (Option 1: fix only the 2 real duplicates).

---

## 9. Success Criteria

- [ ] `pnpm exec knip` reports `Duplicate exports (0)`
- [ ] 1545+ tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 95 spec: `docs/superpowers/specs/2026-08-23-phase95-knip-ci-design.md` (knip integration that surfaced this finding)
- Phase 95 plan: `docs/superpowers/plans/2026-08-23-phase95-knip-ci.md`
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5 (Phase 100 candidate #1)
- knip docs: https://knip.dev/reference/configuration#ignore (for Phase 99 follow-up)