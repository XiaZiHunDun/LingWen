# Phase 102 — Audit & Resolve 36 Unused Files

> **Date**: 2026-08-24
> **Phase**: 102
> **Source**: Phase 99 knip CI integration (`b2110c20`) follow-up — `Unused files (36)`
> **Status**: Design

---

## 1. Context

Phase 99 promoted knip to hard-blocking CI gate (`1772a86f`). Phase 99.1 fixed pre-existing pnpm setup conflict (`25d0f422`). With the gate now observable end-to-end, the next step is to resolve the 36 reported `Unused files` so knip's file count drops to zero.

Each of the 36 files was investigated via `grep -rln <filename>` to determine whether knip's report is correct (true dead code) or a knip config gap (knip can't see references in `eslint.config.js`, `playwright.config.js`, etc.).

**Investigation results** (verified by `grep` in this conversation):

| Category | Count | Files | Verdict |
|----------|-------|-------|---------|
| A. Creator sub-components | 20 | All 20 in `apps/dashboard/src/components/creator/` | All dead — delete |
| B. Generic components | 4 | `CreationModeHint`, `FieldHint`, `SkeletonLoader`, `WidgetRenderer` | All dead — delete |
| C. types/ files | 3 | `api.ts`, `branded.ts`, `creator.ts` | All dead — delete |
| C'. types/index.ts | 1 | (Ambiguous) | Keep — investigate in follow-up |
| D. utils/ files | 2 | `safeAccess.js`, `safeStore.js` | All dead — delete |
| E. test fixtures | 2 | `tests/fixtures/lint-testid/{clean,dirty}.spec.ts` | knip false positive — `eslint.config.js:29` references the glob `tests/fixtures/lint-testid/*.spec.ts` for ESLint rule `testid-class-sync` |
| F. test helpers | 1 | `tests/unit/helpers/creator-test-helper.ts` | Dead — delete |
| G. visual-audit tests | 3 | `tests/visual-audit/{capture,regression,ui-metrics}.spec.js` | knip false positive — `playwright.config.js` references via `testMatch: /capture\.spec\.js/` etc. |
| **Total** | **36** | | **30 delete + 5 ignore + 1 keep** |

**Key insights from grep** (to share with reviewers):

1. **Key-file decoupled panels (A2 subset)**: `CreatorAdvanceBatchPanel.vue`, `CreatorModeGuidePanel.vue`, `CreatorOnboardingWizardPanel.vue` have an associated `creatorXxxKey.js` Symbol file. The Symbol/key file IS used (in `useCreatorPageProviders.js` for provide/inject pattern), but the **panel component itself is never rendered** — knip correctly flags the panels as dead. Key files stay.

2. **`CreatorPreferencesSummary.vue`**: 3 grep hits (`useCreatorProductTools.js:20`, `creatorPreferencesSummaryUtils.js`, test file) reference the **utility function** `buildCreatorPreferencesSummary`, NOT the `.vue` component. Component uses `inject(CREATOR_PRODUCT_TOOLS_KEY)` but is never rendered. Confirmed dead.

3. **`tests/fixtures/lint-testid/*.spec.ts`**: Phase 8.31/8.32/8.33 added these as **permanent regression fixtures** for the `no-class-selector-in-test` ESLint rule. Comment in `dirty.spec.ts` explicitly says: *"Do not delete these — they are the regression test for Phase 8.31/8.32 rule."* knip doesn't parse `eslint.config.js`.

4. **`tests/visual-audit/*.spec.js`**: referenced in `playwright.config.js` via `testMatch` regex. knip doesn't parse Playwright config.

5. **`creator-test-helper.ts`**: zero imports found anywhere — dead.

---

## 2. Goal

Reduce knip's `Unused files` count from 36 to 0 by:
- **Deleting 30 truly-dead files** (Categories A, B, C, D, F)
- **Adding 5 false-positive files to `knip.json#ignore`** (Categories E, G) so knip stops reporting them
- **Keeping 1 ambiguous file** (`types/index.ts`) for follow-up investigation

---

## 3. Non-Goals

- **NOT** deleting any of the 5 false-positive files (E + G) — they're test infrastructure legitimately referenced by config files knip can't parse.
- **NOT** deleting key files (`creatorXxxKey.js`) — they are referenced and serve Vue provide/inject pattern. Only the unused `.vue` panels are deleted.
- **NOT** modifying the 27 unused exports / 12 unused exported types / unused deps / devDeps / unlisted binaries — these belong to Phase 103, 104, 105 per Phase 99 spec §4.4 follow-up queue.
- **NOT** modifying the unrelated `types/composables.ts` (which has unused exported types, not unused file).
- **NOT** investigating `types/index.ts` further in this phase — keep for follow-up.
- **NOT** removing orphaned `barrel re-exports` that may now exist after deletion — if a key file becomes orphaned, log it as observation but don't fix here (separate phase).

---

## 4. Design

### 4.1 Change Set

**30 file deletions** + **1 config edit** (`knip.json`).

**Group A — Delete 20 Creator sub-components**:
```
apps/dashboard/src/components/creator/CreatorAdvanceBatchPanel.vue
apps/dashboard/src/components/creator/CreatorAgentAnnotations.vue
apps/dashboard/src/components/creator/CreatorAgentStreamPreview.vue
apps/dashboard/src/components/creator/CreatorBatchSummaryPrompt.vue
apps/dashboard/src/components/creator/CreatorChapterBodyEditor.vue
apps/dashboard/src/components/creator/CreatorChapterBodySaveFooter.vue
apps/dashboard/src/components/creator/CreatorChapterEntityRail.vue
apps/dashboard/src/components/creator/CreatorChapterTaskCards.vue
apps/dashboard/src/components/creator/CreatorConsistencyRail.vue
apps/dashboard/src/components/creator/CreatorDeviationList.vue
apps/dashboard/src/components/creator/CreatorDirectorPaths.vue
apps/dashboard/src/components/creator/CreatorInlineConflictGutter.vue
apps/dashboard/src/components/creator/CreatorLightValidationBar.vue
apps/dashboard/src/components/creator/CreatorModeGuidePanel.vue
apps/dashboard/src/components/creator/CreatorOnboardingWizardPanel.vue
apps/dashboard/src/components/creator/CreatorPreferencesSummary.vue
apps/dashboard/src/components/creator/CreatorPulseIntro.vue
apps/dashboard/src/components/creator/CreatorWriteControlStrip.vue
apps/dashboard/src/components/creator/CreatorWriteMicroTaskBar.vue
apps/dashboard/src/components/creator/CreatorWriteScopeBar.vue
```

**Group B — Delete 4 generic components**:
```
apps/dashboard/src/components/CreationModeHint.vue
apps/dashboard/src/components/FieldHint.vue
apps/dashboard/src/components/SkeletonLoader.vue
apps/dashboard/src/components/WidgetRenderer.vue
```

**Group C — Delete 3 types files**:
```
apps/dashboard/src/types/api.ts
apps/dashboard/src/types/branded.ts
apps/dashboard/src/types/creator.ts
```

**Group D — Delete 2 utils files**:
```
apps/dashboard/src/utils/safeAccess.js
apps/dashboard/src/utils/safeStore.js
```

**Group F — Delete 1 test helper**:
```
apps/dashboard/tests/unit/helpers/creator-test-helper.ts
```

**Group E+G — Edit `knip.json`** to add 5 entries to an `ignore` array (or equivalent config knob):
- `tests/fixtures/lint-testid/clean.spec.ts`
- `tests/fixtures/lint-testid/dirty.spec.ts`
- `tests/visual-audit/capture.spec.js`
- `tests/visual-audit/regression.spec.js`
- `tests/visual-audit/ui-metrics.spec.js`

### 4.2 knip.json Edit

Add an `ignore` array. Existing config (root `/home/ailearn/projects/LingWen/knip.json`):
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
  ]
}
```

New config:
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

### 4.3 Risk Analysis

- **Build risk**: Low. All deleted files have 0 or 1 grep hit (where 1 hit was either self-reference or a chain to another deleted file). Build impact verified by `pnpm run build`.
- **Test risk**: Low. The 5 ignored test files retain their original behavior (run via ESLint config + Playwright config). The 1 deleted test helper (`creator-test-helper.ts`) had 0 importers — confirmed via grep. The 30 deleted source files had no test imports referencing them as production code (test files may mention them in comments/strings, but knip already shows zero real imports).
- **Behavioral risk**: Very low. These are 36 files that have been "dead" in the runtime — deleting them doesn't change what users see or what tests assert (existing 1545 tests must still pass).
- **Lint/type-check risk**: Low. ESLint config / TypeScript may flag unused imports from deleted files — but our grep investigation showed no source code imports them, so no `import` statement cleanup is needed.
- **knip config risk**: Low. The `ignore` array tells knip to stop checking those 5 paths. They're verified-referenced by config files knip doesn't parse, so the ignore is justified (not silencing real issues).

### 4.4 Verification Strategy

After change:
1. `pnpm exec knip` — `Unused files (0)` expected (was 36).
2. `pnpm exec vitest run` — 1545+ tests pass, no test broken.
3. `pnpm run build` — build succeeds (~20s).
4. `pnpm exec vue-tsc --noEmit` — 0 type errors.
5. `pnpm lint:all` — 0 lint errors (verifies ESLint fixtures still run correctly).
6. ESLint test fixtures still work: `pnpm lint:testid` should still report 2 violations in `dirty.spec.ts`.
7. Playwright config still references the visual-audit files: `grep "testMatch: /capture" playwright.config.js` returns the line.

### 4.5 Rollback Plan

If a deletion breaks a runtime or test (unlikely — all confirmed dead):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Single commit revert restores all 30 files + reverts knip.json. No data loss.

If only specific files need rollback:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit  # full revert
# then re-apply the safe deletions in a follow-up commit
```

---

## 5. Files Touched

| Category | File | Action |
|----------|------|--------|
| A | 20 `apps/dashboard/src/components/creator/Creator*.vue` files | Delete |
| B | 4 `apps/dashboard/src/components/{CreationModeHint,FieldHint,SkeletonLoader,WidgetRenderer}.vue` | Delete |
| C | 3 `apps/dashboard/src/types/{api,branded,creator}.ts` | Delete |
| D | 2 `apps/dashboard/src/utils/{safeAccess,safeStore}.js` | Delete |
| F | 1 `apps/dashboard/tests/unit/helpers/creator-test-helper.ts` | Delete |
| E+G | 1 `knip.json` | Add `ignore` array (5 paths) |
| **Total** | **31 file operations** | **30 delete + 1 edit** |

**Files NOT touched**: `package.json`, `eslint.config.js`, `playwright.config.js`, `vitest.config.js`, `tsconfig.json`, all `src/composables/**`, all stores, all routes, all existing tests, `types/index.ts` (kept for follow-up), `types/composables.ts` (out of scope).

---

## 6. Test Strategy

**No new tests**. Rationale:
- All 30 deleted files had no tests asserting their behavior (they were unused — no callers to test).
- The 5 ignored files retain their original test behavior (ESLint + Playwright still run them).
- Existing 1545 tests still cover the production code paths that remain.
- 1545 tests passing after deletion is the test.

---

## 7. Commit Strategy

**Two commits** for reviewability:

**Commit 1** — source code deletions (30 files):
```
refactor(cleanup): delete 30 unused files from knip report (Phase 102)

Phase 102 — resolve unused files (Category A, B, C, D, F):

- Delete 20 Creator sub-components (panels never rendered; some had
  decoupled key files which stay):
  CreatorAdvanceBatchPanel, CreatorAgentAnnotations,
  CreatorAgentStreamPreview, CreatorBatchSummaryPrompt,
  CreatorChapterBodyEditor, CreatorChapterBodySaveFooter,
  CreatorChapterEntityRail, CreatorChapterTaskCards,
  CreatorConsistencyRail, CreatorDeviationList,
  CreatorDirectorPaths, CreatorInlineConflictGutter,
  CreatorLightValidationBar, CreatorModeGuidePanel,
  CreatorOnboardingWizardPanel, CreatorPreferencesSummary,
  CreatorPulseIntro, CreatorWriteControlStrip,
  CreatorWriteMicroTaskBar, CreatorWriteScopeBar
- Delete 4 generic components:
  CreationModeHint, FieldHint, SkeletonLoader, WidgetRenderer
- Delete 3 dead types files:
  types/api.ts, types/branded.ts, types/creator.ts
- Delete 2 dead utils files:
  utils/safeAccess.js, utils/safeStore.js
- Delete 1 dead test helper:
  tests/unit/helpers/creator-test-helper.ts

All 30 files confirmed dead via grep (0-1 external refs; 1-ref cases
were either self-refs or chains to other deleted files).

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

**Commit 2** — knip config update:
```
build(ci): add 5 entries to knip.json ignore (Phase 102)

Phase 102 — resolve knip false-positive Unused files (Category E, G):

knip doesn't parse ESLint config or Playwright config, so it can't
see legitimate references for these 5 test files:

- tests/fixtures/lint-testid/{clean,dirty}.spec.ts
  (referenced via glob in eslint.config.js:29 for rule
   testid-class-sync regression testing — Phase 8.31/8.32 fixtures;
   do NOT delete per Phase 8.33 decision)
- tests/visual-audit/{capture,regression,ui-metrics}.spec.js
  (referenced via testMatch regex in playwright.config.js)

Add them to `ignore` array in knip.json so knip stops reporting them.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors. knip output:
Unused files (0) ✅.
```

Two-commit split allows the deletion commit to be reverted independently if a deletion turns out wrong, without losing the knip config improvement.

---

## 8. Open Questions

None. Scope confirmed (Option A: full audit of 36 files → 30 delete + 5 ignore + 1 keep).

---

## 9. Success Criteria

- [ ] 30 files deleted (Categories A, B, C, D, F)
- [ ] `knip.json` `ignore` array contains 5 entries (Categories E, G)
- [ ] `types/index.ts` preserved (Category C' — keep for follow-up)
- [ ] `pnpm exec knip` reports `Unused files (0)`
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean (ESLint fixtures still work)
- [ ] Two atomic commits on master
- [ ] Pushed to origin/master
- [ ] First post-merge CI run: Setup pnpm passes, knip PASSES (no findings) — proves Phase 99 gate + Phase 102 cleanup

---

## 10. References

- Phase 95 spec: `docs/superpowers/specs/2026-08-23-phase95-knip-ci-design.md`
- Phase 99 spec: `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md` (§4.4 follow-up queue)
- Phase 99.1 spec: `docs/superpowers/specs/2026-08-24-phase99.1-pnpm-setup-fix-design.md`
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5 (Phase 102 candidate)
- knip docs: https://knip.dev/reference/configuration#ignore (for `ignore` array semantics)
- Phase 8.31/8.32/8.33 ESLint fixtures: `tests/fixtures/lint-testid/dirty.spec.ts` (comment header documents history)