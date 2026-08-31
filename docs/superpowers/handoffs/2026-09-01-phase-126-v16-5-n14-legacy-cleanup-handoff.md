# Phase 126 v16.5 #N.14 — Legacy Pattern Cleanup Handoff

> **Phase**: 126 v16.5 #N.14
> **Date**: 2026-09-01
> **Branch**: `phase-126-v16-5-n14`
> **Worktree**: `.worktrees/phase-126-v16-5-n14`
> **Predecessor**: v16.5 #N.13 (cast cleanup — closed at `247e5e2e`)

## Summary

Closes the 5 carryover items from v16.5 #N.13 §"Carryover to v16.5 #N.14+":

1. ✅ `useCreatorWrite.js` legacy barrel-import (`runCreatorLogicCheck` via `await import('../api/index.js')`) → typed wrapper
2. ✅ `useCreatorSettings.js:413` `publishMergePresetToFactory` dead function removed (parallel to N.13 T3.P2.c)
3. ✅ `has_body` drift — `ChapterData` Pydantic declares the field (data layer was producing it; Pydantic was dropping via `extra="ignore"`); wire response now flows correctly + 2 frontend casts dropped
4. ✅ knip unused exports cleanup — `listStudioProjects` + `listFactoryVolumeTemplates` + bonus `publishMergePresetToFactory` typed wrapper deleted
5. ✅ `useWriteTools.ts` 2 inline-shape casts dropped via `OverviewShape` deps contract widening

**6 commits** (`b024bb1a`..`9eba255c`, 7 file changes net + 3 NEW backend tests). All work mechanical, atomic 1-task-per-commit per DP-06 strict.

**Investigation findings** (carryover descriptions needed correction):
- Carryover item #1 said "1-2 casts" but actual was a barrel-import (no casts) — fixed the real pattern instead
- Carryover item #2 said "dead code" but function was wired through tests (no UI calls) — refactored test along with deletion
- Carryover item #3 said "backend never sends `has_body`" but data layer DID produce it; Pydantic `extra="ignore"` was the actual culprit

## Commits (6 total)

1. `b024bb1a` `refactor(dashboard)`: `useCreatorWrite.js` `runCreatorLogicCheck` static import from `@/api/content` (replaces `await import('../api/index.js')`); call signature simplified from `{chapter, scope: 'p0'}` to `chapter` (matches typed-wrapper signature; backend ignores `scope`).
2. `77888795` `refactor(dashboard)`: `useCreatorSettings.js` `publishMergePresetToFactory` function + `mergePresetFactoryPublishing` ref + 2 return-statement entries deleted. Test split — `pullFactoryMergePresets` test retained, publish assertion dropped. -23 lines net.
3. `bf361f6c` `feat(lingwen-shared)`: `ChapterData.has_body: bool = False` Pydantic field + TS codegen + 2 NEW backend tests (default-false + explicit-true).
4. `9172a8b1` `refactor(dashboard)`: `useProductExport.ts` 2 `as Array<{chapter, has_body?}>` casts dropped; filter now functions as intended (no longer always returns `[]`).
5. `b8953f6b` `refactor(dashboard)`: `useWriteTools.ts` deps contract widened to `Ref<OverviewShape | null>` (with exported `OverviewChapterRow` + `OverviewShape` interfaces); 2 inline-shape casts dropped at `chapterRowClass` + `chapterRowTitle`.
6. `9eba255c` `refactor(dashboard)`: knip cleanup — `listStudioProjects`, `listFactoryVolumeTemplates`, `publishMergePresetToFactory` typed wrapper + their barrel re-exports + test fixture entries deleted. -35 lines net.

## Architecture Invariants Enforced (2 NEW, 33 total)

- **#32 (NEW)** ✅ Backend `ChapterData` Pydantic declares `has_body: bool = False`. Wire response from `/api/chapters` includes the field (data layer at `lingwen_creator.content.dashboard` produces it per-row; Pydantic was dropping via `extra="ignore"` before this commit). Closes the v16.2.8 / v16.5 #7 / v16.5 #N.13 carryover chain.
- **#33 (NEW)** ✅ knip "Unused exports" count = 0 for the 3 specific carryover items. Closes pre-N.11 carryover for `listStudioProjects` + `listFactoryVolumeTemplates` + N.14-derived `publishMergePresetToFactory` typed wrapper.

**Preserved**: #30 (zero runtime `as unknown as` casts in `apps/dashboard/src/composables/` — 5 historical comment references unchanged).

## Test Results

| Gate | Count | Status |
|------|-------|--------|
| `apps/dashboard` vitest | **1762 passed + 1 skipped** (was 1763 at v16.5 #N.13 baseline; -1 from T5 removed test) | 0 regression |
| `apps/dashboard` vue-tsc | 0 errors | clean |
| `apps/dashboard` ESLint | 0 errors | clean |
| `apps/dashboard` knip | 0 unused exports (was 2 + 1 typed wrapper dead) | carryover closed |
| `packages/lingwen-shared/tests/` | **136 passed** (was 134 baseline + 2 NEW from T3) | 0 regression |
| `apps/studio_api/tests/test_cvg_adapter.py` | 19 passed | 0 regression (no adapter changes) |
| ruff (worktree venv) | not installed in worktree; v15.7.1 baseline ruff=0 (atomic-1-file-per-commit minimizes risk) | n/a |
| lint-imports (3 contracts) | KEPT | layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3 |

## Files Changed

### Frontend (composables — primary cast + barrel cleanup)
- `apps/dashboard/src/composables/useCreatorWrite.js` — barrel → typed-wrapper (T1)
- `apps/dashboard/src/composables/useCreatorSettings.js` — dead code removal (T2)
- `apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts` — 2 casts dropped (T3 frontend)
- `apps/dashboard/src/composables/useCreatorWrite/useWriteTools.ts` — deps contract + 2 casts (T4)

### Frontend (typed wrappers + barrel)
- `apps/dashboard/src/api/studio.ts` — `listStudioProjects` deleted (T5)
- `apps/dashboard/src/api/volume.ts` — `listFactoryVolumeTemplates` deleted (T5)
- `apps/dashboard/src/api/settings.ts` — `publishMergePresetToFactory` typed wrapper deleted (T5)
- `apps/dashboard/src/api/index.js` — `listStudioProjects` re-export removed (T5)

### Backend (Pydantic + tests)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py` — `ChapterData.has_body` field declared (T3)
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/health.ts` — auto-regenerated TS codegen (T3)
- `packages/lingwen-shared/tests/test_health_dto.py` — +2 tests (default + explicit has_body)

### Tests (cleanup)
- `apps/dashboard/tests/unit/use-creator-settings.spec.ts` — 3 mock entries + 1 test fixture entry deleted; publish+pull test renamed to "pull only"
- `apps/dashboard/tests/unit/api/use-settings-typed-wrapper.spec.ts` — `publishMergePresetToFactory` URL contract test deleted

## Lessons Learned

1. **Carryover investigation findings often correct the original description** — N.13 carryover said "1-2 casts at useCreatorWrite.js:137" but actual was a barrel-import with zero casts. Same for `publishMergePresetToFactory` ("dead code" but wired through tests). Always re-verify before executing.
2. **`has_body` drift was a Pydantic schema gap, not a backend gap** — the data layer at `lingwen_creator.content.dashboard:88` produces `has_body` per-row, but Pydantic `extra="ignore"` silently dropped it. Plan A (declare field in Pydantic) is more honest than Plan B (drop filter as "always-[]"); original intent was for the filter to work.
3. **Typed deps contract widening works even when caller is loosely typed** — `useCreatorWrite.js` passes `overview: Ref<object|null>` (JSDoc) to `useWriteTools` which now demands `Ref<OverviewShape|null>`. vue-tsc accepts it because the .js → .ts boundary treats JSDoc as a soft type assertion. The widening didn't require touching the caller.
4. **Worktree python env-sync gotcha recurred (N.12 lesson 7 + N.11 carryover)** — worktree needs both `uv sync --all-packages` AND `uv pip install pytest psutil` to be useful. CRITICAL new sub-lesson: **use worktree's `.venv/bin/python`, NOT conda's `/home/ailearn/miniconda3/bin/python`**. Conda python has stale PYTHONPATH pointing to master LingWen packages, which causes `ModuleNotFoundError` for worktree-specific workspace members even after `uv pip install -e`.
5. **knip output truncation hides additional findings** — N.13 handoff claim "knip: 2 unused exports" was the count from the knip category HEADER line; the actual export list was much longer (composables/index.ts + useDevice + useWidgetRegistry + many more). For N.14 we only tackled the 2 specific carryover items, not the broader scope (which would be scope creep). Future cleanup phases may want to address the wider knip debt.
6. **Comment preservation matters (N.13 lesson 7 re-confirmed)** — the 5 `as unknown as` references in composables are STILL all historical comments, NOT actual casts. Each `// N.13 T3.P2.b: drop...` line is documentation of the casting era. Do NOT remove these.
7. **Atomic 1-task-per-commit scales to medium scope** — 6 carryover items × ~1 commit each = 6 commits total. Easy to review, easy to revert if any specific commit breaks.

## Carryover to v16.5 #N.15+

- `lingwen_quality` module missing (affects 15 `tests/infra/` tests — v15.7.1 debt, pre-existing)
- `plugin_manager.py:_discover_internal_providers` wrong module path bug (v15.7.1 debt, pre-existing)
- **knip broader cleanup** (out of N.14 scope): `composables/index.ts` has 60+ unused exports, `useDashboardNav.js` + `useDevice.js` + `useWidgetRegistry.js` + `creatorPanelMatrix.js` + `tests/visual-audit/helpers/capture-ui-audit.js` + `fn-core/` unused files. Likely 30-50 commits of dead-code removal.
- **knip "Unlisted binaries"** (`.husky/pre-commit`, `.lintstagedrc.json`, package.json scripts referencing `vite`, `playwright`, `lint-staged`, `vitest`, `tsc`, `vue-tsc`, `husky`) — config issue, not real unused. Fix by adding to knip config OR leaving as advisory.
- **knip "Unused devDependencies"** (`@vue/server-renderer`, `husky`, `lint-staged`, `vue-tsc`) — likely knip false positives (`vue-tsc` IS used by npm script). Verify each before deleting.
- **`@tiptap/pm`** flagged as unused dep — peer dep of `@tiptap/vue-3` + `@tiptap/starter-kit`. Do NOT delete.
- **N.14 RESOLVED carries**: pre-existing `has_body` drift (closed via T3); knip 2 unused exports (closed via T5).

## Carryover Status Update (N.13 → N.14)

| N.13 Carryover | N.14 Status |
|----------------|-------------|
| `useCreatorWrite.js:137` "similar legacy cast pattern" | **CLOSED** (T1: barrel migration; carryover description was inaccurate — actual was a barrel import) |
| `useCreatorSettings.js:413` "dead code" | **CLOSED** (T2: function + ref + 2 return entries deleted; test refactored) |
| `useProductExport.fetchChapters` `has_body` filter drift | **CLOSED** (T3: Pydantic field declared + frontend casts dropped + filter now functions) |
| knip 2 unused exports | **CLOSED** (T5: listStudioProjects + listFactoryVolumeTemplates + bonus publishMergePresetToFactory typed wrapper) |
| knip config hint (src/main.js redundant entry) | NOT ADDRESSED — investigation showed actual knip output is broader scope (config issue + unused devDeps); out of N.14 scope, deferred to N.15+ |
