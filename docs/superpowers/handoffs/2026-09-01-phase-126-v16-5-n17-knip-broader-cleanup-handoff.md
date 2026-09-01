# Phase 126 v16.5 #N.17 — knip Broader Cleanup Handoff

## Summary

Closed the carryover from Phase 126 v16.5 #N.15 ("knip broader cleanup: composables/index.ts 60+ unused exports + useDashboardNav + useWidgetRegistry + creatorPanelMatrix + tests/visual-audit + fn-core/ — ~30-50 commits") via **verify-before-design** discipline (N.14 lesson 1) that revealed the actual scope is much smaller.

**5 source commits** (1 spec + 1 plan + 4 deletions, 0 implementation commits needed for knip config):

```
6c304ea6 chore(scripts): remove dead check-frontend-runtime + check-null-access + frontend-smoke
08df0431 chore(dashboard-contracts): remove redundant export.ts + memory.ts shims
a4eaeb7e chore(dead-code): remove trae比赛 trae AI competition submission
f183272e chore(dead-code): remove fn-core Effect-TS experiment
6f96f6c6 docs(phase-126): N.17 knip broader cleanup implementation plan
0006dbe1 docs(phase-126): N.17 knip broader cleanup design spec
```

Plus this handoff doc (T6).

## What Was Actually Done

### T1: `chore(dead-code)` Remove `fn-core/` Effect-TS experiment — 29 files

```
rm 'fn-core/src/main.ts'
rm 'fn-core/src/middleware/auth.ts'
rm 'fn-core/src/routing/stranglerRouter.ts'
rm 'fn-core/src/runtime.ts'
rm 'fn-core/tsconfig.json'
... (29 total deletions)
```

- **22 .ts source files**: Comment/Story/User aggregates, command handlers, event bus, snapshot service, sqlite event store, routing (stranglerRouter), middleware (auth), runtime, main entry
- **3 SQLite .db files** (lingwen.db + shm + wal from local experiment)
- **package.json** (declares `lingwen-fn-core` standalone with Effect-TS deps: `@effect/cluster`, `@effect/platform`, `@effect/platform-node`, `better-sqlite3`, `effect`)
- **package-lock.json** + **tsconfig.json**

Verified dead via:
- `grep -rln 'fn-core\|lingwen-fn-core' apps/ packages/` → 0 matches
- `pnpm-workspace.yaml` does NOT list `fn-core` as a workspace member
- No app or package imports anything from `fn-core`

### T2: `chore(dead-code)` Remove `trae比赛/` trae AI competition submission — 13 files

```
rm "trae比赛/novel-writing-assistant/assets/scenario_1024x768.jpg"
rm "trae比赛/novel-writing-assistant/novel-writing-assistant.html"
rm "trae比赛/novel-writing-assistant/报名帖内容.txt"
... (13 total deletions)
```

- **5 TTF font files**: CrimsonPro Bold/Italic/Regular, IBMPlexMono Regular, YoungSerif Regular
- **2 vendored .min.js libraries**: echarts + mermaid
- **3 JPG product screenshot assets**: hero, product_ui, scenario
- **charts.js** + **novel-writing-assistant.html** + **报名帖内容.txt**

Verified dead via:
- `grep -rln 'trae比赛\|trae-competition' apps/ packages/` → 0 matches
- Subdirectory name is Chinese `trae比赛` (trae competition)
- No app, package, or workflow references these assets

### T3: `chore(dashboard-contracts)` Remove redundant `export.ts` + `memory.ts` shims — 2 files

```
rm 'packages/dashboard-contracts/src/shared/export.ts'
rm 'packages/dashboard-contracts/src/shared/memory.ts'
```

- **Both files were redundant re-export shims**:
  - `export.ts` re-exports 8 types (CreatorDocxExportRequest, CreatorEpubExportRequest, CreatorPublish*) from `lingwen-shared` TS codegen
  - `memory.ts` re-exports 7 types (CreatorMemoryAnnotationRequest, CreatorMemoryAssetItem, etc.) from `lingwen-shared` TS codegen
  - **However**, all 15 types are ALSO already present in `creator.ts` (which IS in `index.ts` re-export chain)
  - `index.ts` (the unified `@lingwen/dashboard-contracts/shared` entry point) does NOT re-export from `export.ts` or `memory.ts`

Verified via:
- `grep -rln 'dashboard-contracts/shared/export\|dashboard-contracts/shared/memory' apps/dashboard/src/` → 0 matches
- Dashboard imports use `@lingwen/dashboard-contracts/shared` (no subpath), which resolves to `index.ts` → `creator.ts` — never touches `export.ts` or `memory.ts`

### T4: `chore(scripts)` Remove dead scripts — 3 files

```
rm 'scripts/check-frontend-runtime.js'
rm 'scripts/check-null-access.js'
rm 'scripts/frontend-smoke.spec.js'
```

3 files added in commit `257aa70c` P2 修复 bundle but never wired into any CI workflow, root package.json script, turbo pipeline, or app test infra.

Verified zero references:
- `grep -rln 'scripts/check-frontend-runtime\|scripts/check-null-access\|scripts/frontend-smoke' .github/ package.json turbo.json pnpm-workspace.yaml apps/` → 0 matches

## What Was NOT Done (And Why)

### NOT Deleted (in `apps/dashboard/knip.json` ignore list — legitimate false positives)

| Path | Reason |
|------|--------|
| `src/composables/index.ts` | Barrel re-exports consumed via `@/composables/*` Vite alias — knip can't trace alias without explicit entry config |
| `src/composables/useDashboardNav.js` | Same — alias consumption |
| `src/composables/useWidgetRegistry.js` | Same |
| `src/config/creatorPanelMatrix.js` | Same |
| `src/api/index.js` | Same — barrel re-export via `@/api` |
| `src/api/{cvg,decisions,health,workflows}.ts` | Typed wrappers consumed via `@/api/cvg` etc. |
| `tests/visual-audit/{capture,regression,ui-metrics}.spec.js` | Intentionally-kept design-quality audit specs |
| `tests/visual-audit/helpers/capture-ui-audit.js` | Same |
| `tests/fixtures/lint-testid/{clean,dirty}.spec.ts` | ESLint rule test fixtures (`eslint-rules/testid-class-sync.js`) |
| `tests/e2e/write-workspace.spec.ts` | BLOCKED by Phase 114 prod preview regression (accepted debt) |
| `tests/helpers/strict-test-types.ts` | Test helper types consumed in 10+ test specs |

### NOT Touched (T5 reverted — knip.json didn't need updating)

Originally planned to add `ignoreDependencies: ["openapi-typescript", "zod"]` + extend `ignoreBinaries: ["knip", "playwright", "vitest", "eslint", "tsc"]` to suppress "Unused devDependencies" + "Unlisted binaries" categories.

**T5 was implemented in commit 75b89314 then REVERTED via `git reset --hard HEAD~1`.** Reason: knip emitted **Configuration hints** (6 entries: `Remove from ignoreDependencies/Binaries — these are actually used`) instead of the expected clean output. knip can detect usage via:
- `openapi-typescript`: used by `tooling/contracts/dump_openapi.py` via subprocess
- `zod`: used by `tooling/contracts/zod_revalidate.py` via Python import
- `playwright` + `vitest` + `eslint` + `tsc`: invoked directly by `.github/workflows/*.yml` CI steps (NOT via pnpm scripts)

Adding these to the ignore list is technically incorrect — knip correctly identifies them as USED. The previous state (knip.json with `ignoreBinaries: ["knip"]` only, 0-line output) is the correct baseline.

**This was a verify-before-design failure** — I assumed these were false positives without empirical verification. The "Unused devDependencies" + "Unlisted binaries" categories in the original N.15 carryover were reported correctly; they just reflect the legitimate usage pattern that knip can detect.

## Final State

### Verification Gates

| Gate | Result |
|------|--------|
| `cd apps/dashboard && pnpm exec knip` | 0 lines (clean) |
| `cd apps/dashboard && pnpm vitest run` | 1762 passed + 1 skipped (no regression) |
| `cd apps/dashboard && pnpm tsc --noEmit` | 0 errors |
| `cd apps/dashboard && pnpm eslint .` | 0 errors |
| `cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n17 && pnpm knip` | 0 lines (CI gate, root context) |
| git status | clean |

### Architecture Invariants (35 total — all preserved from N.16)

No new invariants added in N.17. The deletions don't add constraints; they remove dead code. The knip CI gate stays `{"issues":[]}` (already green, must stay green after deletions).

## Net Diff

| Metric | Before | After |
|--------|-------:|------:|
| `fn-core/` tracked files | 29 | 0 |
| `trae比赛/` tracked files | 13 | 0 |
| `packages/dashboard-contracts/src/shared/export.ts` | exists | deleted |
| `packages/dashboard-contracts/src/shared/memory.ts` | exists | deleted |
| `scripts/{check-frontend-runtime,check-null-access,frontend-smoke}` | exists | deleted |
| **Total tracked file deletions** | | **47** |
| `apps/dashboard/knip.json` ignoreBinaries | `["knip"]` | `["knip"]` (unchanged) |
| `apps/dashboard/knip.json` ignoreDependencies | (none) | (none) (unchanged) |

## Lessons (carryover to N.18+)

### 1. Verify-before-design (N.14 lesson 1 — re-confirmed)

The N.15 carryover claim of "~30-50 commits" was way overestimated. Actual scope: **5 source commits** (4 deletions + spec + plan). The "60+ unused exports in composables/index.ts" was a false positive list, not a work list.

**Empirical method**:
1. Run `pnpm exec knip` from the right context (`apps/dashboard/`) — already 0 lines, ignore list already correct
2. Run from project root — produces 180+ findings, ALL are false positives caused by missing root knip.json
3. Check `git ls-files <path>` for each suspected dead directory — 47 files actually tracked
4. Cross-verify with `grep -rln <dir> apps/ packages/`
5. For each candidate file, trace its actual imports (`index.ts` chain for re-exports)

### 2. knip Configuration hints reveal usage (N.17 T5 lesson)

When knip emits "Configuration hints" instead of "Unused devDependencies" or "Unlisted binaries", it means:
- The dep/binary IS used somewhere knip can detect
- Adding it to ignoreDependencies/ignoreBinaries is **incorrect**
- The hint suggests removal from the ignore list

**Pattern**: only add to ignoreDependencies/ignoreBinaries when knip CANNOT detect usage (e.g., dynamic subprocess invocation in Python files that don't go through package.json scripts). For tools invoked directly in CI workflows, leave them — knip CAN trace workflow invocations.

### 3. Chinese path quoting in shell

`git rm -r trae比赛` requires quoting: `git rm -r 'trae比赛'`. Without quotes, shell tries to interpret the Chinese characters as wildcards.

### 4. Redundant re-export detection

`export.ts` + `memory.ts` shims in dashboard-contracts were created in v16.2.5/v16.2.6 but:
- `index.ts` re-exports from `creator.ts` (which contains all the types)
- `index.ts` does NOT re-export from `export.ts` or `memory.ts`
- Dashboard imports use `@lingwen/dashboard-contracts/shared` (no subpath) → `index.ts` → `creator.ts` chain
- Therefore the shims were unreachable

**Detection method**: `cat packages/dashboard-contracts/src/shared/index.ts | grep export.*ts` to see what the index re-exports. If a file isn't in the index, check if anyone imports it via subpath.

### 5. git ls-files vs git status

Initially I ran `git ls-files fn-core/` and got 0 — misleading first read. The correct command is `git ls-files --stage <path>` or `git ls-tree HEAD <path>` to verify if files are in the index. Or just `git ls-files` (no args) to count all tracked files in current state.

### 6. The 18-item knip.json ignore list was ALREADY correct

N.15 carryover claimed "knip broader cleanup" but the existing `apps/dashboard/knip.json` (with 18 ignore entries) was already the canonical solution. The 60+ barrel exports + 4 typed wrapper files are all legitimately consumed via Vite `@/` alias.

**The `pnpm knip` CI gate was already `{"issues":[]}` from N.16 closure.** N.17 added 47 file deletions but zero knip config changes.

## Carryover to v16.5 #N.18+

**No more knip carries** — knip gate is locked at `{"issues":[]}` and CI enforces it.

Remaining LingWen debt (post-N.17):
- **Phase 114 prod preview regression** (accepted, cytoscape-fcose CJS + rollup commonjs incompatibility, 5+ phases invested)

Future phase candidates:
- **Phase 127**: New feature work (would require brainstorming + spec + plan)
- **Phase 128**: Phase 114 prod preview regression re-attempt (high-effort / low-reward)
- **Phase 129+**: Architectural refactors (e.g., consolidating typed wrappers, eliminating barrel exports where possible)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
