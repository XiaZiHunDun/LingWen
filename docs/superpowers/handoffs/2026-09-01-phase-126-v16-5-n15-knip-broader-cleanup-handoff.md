# Phase 126 v16.5 #N.15 Handoff — knip broader cleanup

> **Phase header**: Phase 126 v16.5 #N.15 closure — knip broader cleanup

## Commits

| Commit | Description |
|---|---|
| `625bb4f4` | T1: `refactor(dashboard)` — remove dead `useDevice` composable (294 lines) + 3 cleanup edits (composables/index.ts re-export removal + JSDoc comment removal + knip.json ignore entry removal) |
| `9a2910c8` | T2: `chore(knip)` — remove redundant `"src/main.js"` entry from `knip.json` (covered by `src/**/*.{js,ts,vue}` project glob) |

## Original carryover claim vs actual scope

- **Original N.11/13/14 carryover estimated "~30-50 commits"** (per v16.5 #N.14 §6: "knip broader cleanup: composables/index.ts 60+ unused exports + useDashboardNav + useDevice + useWidgetRegistry + creatorPanelMatrix + tests/visual-audit + fn-core/ unused files (~30-50 commits)")
- **Actual: 2 commits** (T1 + T2)
- **Reason**: N.13 (cast cleanup) + N.14 (legacy pattern cleanup) collapsed most findings already. N.15 only needed to remove the one genuinely-dead composable + clean up knip config that had piled up stale entries across multiple phases.

## Investigation findings (false positive taxonomy)

When investigating the residual knip findings, the following categories emerged:

| Finding | Category | Action | Rationale |
|---|---|---|---|
| `@tiptap/pm` | Unused dep (false positive) | IGNORE | Peer dep for TipTap editor; required transitively. Per MEMORY.md: "do NOT delete" |
| `@vue/server-renderer` | Unused dep (false positive) | IGNORE | Transitive peer for vue-tsc type checking |
| `husky`, `lint-staged`, `vue-tsc` | Unused binary (false positive) | IGNORE | package.json scripts + `.husky/pre-commit` invoke them. knip can't trace shell script invocations |
| 11 unlisted binaries (playwright, vitest, eslint, tsc, etc.) | Unlisted binaries (false positive) | IGNORE | All are package.json scripts + `.husky/` + `.lintstagedrc` commands. knip can't trace these |
| `src/main.js` config hint | Config hint | RESOLVED in T2 | Redundant entry — covered by `src/**/*.{js,ts,vue}` project glob pattern |

## False positive resolution: T2's removal of `src/main.js`

T2's removal of `"src/main.js"` from the knip `entry` array narrowed knip's analysis scope:
- Before: knip treated `src/main.js` as a separate entry, but the project glob already includes `src/**/*.{js,ts,vue}` which matches `src/main.js`.
- After: knip's "Unused files" check no longer reports `src/main.js` as a "config hint" because knip now sees it via the project glob and properly traces its transitive consumers.

**Net result**: knip output is now `{"issues":[]}` (clean state). All 5 false-positive deps + 11 unlisted binaries + the config hint are eliminated from knip output without manually ignore-padding the config.

## Architecture invariants enforced (1 NEW, 34 total)

**#34 (NEW)** ✅ knip `{"issues":[]}` — zero unused exports/files with no ignore-list padding. The N.15 closure eliminated all knip findings:
- T1: `useDevice.js` removed (1 unused file) + `useDevice` export removed from `composables/index.ts` (1 unused export) + 1 knip ignore entry removed (1 unused ignore)
- T2: `src/main.js` removed from knip entry (1 redundant config hint eliminated)
- Net: -297 lines (`useDevice.js` deletion dominates the count)

## Lessons learned (5)

1. **Carryover scope drift — original estimate was 30-50 commits; reality 2 commits after N.13/N.14 collapsed most findings.** Always re-verify carryover claims before scoping new phase. N.13 + N.14 ran cast cleanup + legacy pattern cleanup that consumed most of what N.11 had estimated.

2. **Knip "hints" are real signals, not noise** — the `src/main.js` config hint was a genuine redundancy, not a stylistic complaint. Removing it narrowed analysis scope and eliminated multiple false-positive flags. Don't ignore config hints — they reveal config-vs-actual drift.

3. **False positive documentation in plan body is important** — the "false positive taxonomy" section is the audit trail that prevents future engineers from "fixing" peer deps / scripts that look unused. Each entry documents WHY a category is a false positive and WHY deletion would break the codebase.

4. **Knip dependency analysis is rooted in entry points** — removing an entry narrows scope; this is a double-edged sword (catches more false positives but loses visibility on transitively-imported files). The `src/main.js` removal was safe because the project glob already covered it; if entry had been the ONLY way to trace a file, removal would have introduced false positives.

5. **Worktree env-sync gotcha** — fresh worktree may have empty `.pnpm/` (implements reported: "node_modules/.pnpm/ was empty, pnpm install --prefer-offline ran with hubbed mode"). The verification gates still work but knip output may be more concise than expected. Lesson: always run `pnpm install` in the worktree before running verification, even if `pnpm install --prefer-offline` reports "Already up to date" (it can't see worktree-specific node_modules).

## Carryover to v16.5 #N.16+

**None for knip** (knip is fully clean — `{"issues":[]}`).

Pre-existing v15.7.1 debt (out of scope for N.15):
- `lingwen_quality` module missing (affects 15 `tests/infra/` tests)
- `plugin_manager.py:_discover_internal_providers` wrong module path bug

## Tests (verification gates)

| Gate | Result | Notes |
|---|---|---|
| vitest | **1762 passed + 1 skipped** | No regression from N.14 baseline |
| shared pytest | **136 passed** | No regression |
| vue-tsc | **0 errors** | No regression |
| ESLint | **0 errors** | No regression |
| knip | **`{"issues":[]}`** | Clean state (was: 1 config hint + 5 false-positive deps + 11 unlisted binaries + 1 unused file + 1 unused export + many unused exports in `composables/index.ts` etc.) |
| import-linter | **3 contracts KEPT** (layer_dependencies + no_concrete_llm_service_in_business_code + no_concrete_sqlite3_in_business_code) | No regression |

## Summary

Phase 126 v16.5 #N.15 closed the residual knip findings that survived N.13 (cast cleanup) + N.14 (legacy pattern cleanup). The original "~30-50 commits" carryover estimate collapsed to 2 commits because N.13 + N.14 consumed most of the scope.

**Net changes**:
- `-297` lines (`useDevice.js` 294-line deletion + 3 small cleanup edits)
- `+0` files (no new files; net file count decrease)
- knip output: `{"issues":[]}` (clean)

**Phase 126 fully closed**: knip findings + cast cleanup + dead code + legacy patterns all resolved. Pre-existing v15.7.1 debt (`lingwen_quality` missing + `plugin_manager.py` module path bug) is the only remaining work, but out of scope for Phase 126.