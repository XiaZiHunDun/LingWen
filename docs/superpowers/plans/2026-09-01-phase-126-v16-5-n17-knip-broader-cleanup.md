# Phase 126 v16.5 #N.17 — knip Broader Cleanup Implementation Plan

## Pre-flight

1. **Verify v16.5 #N.16 baseline** is at master HEAD `be2e4405`:
   ```bash
   git log --oneline -3
   ```
   Expected: `be2e4405 Merge origin/master: integrate Phase 126 v16.5 #N.16 (PR #6)`

2. **Create worktree** (per superpowers:using-git-worktrees):
   ```bash
   git worktree add .worktrees/phase-126-v16-5-n17 -b phase-126-v16-5-n17 master
   cd .worktrees/phase-126-v16-5-n17
   uv sync --all-packages
   ```

3. **Use worktree's `.venv/bin/python`** (per N.14 lesson 4) for backend tests:
   ```bash
   /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n17/.venv/bin/python -m pytest packages/lingwen-shared/tests/
   ```

4. **Baseline knip clean check**:
   ```bash
   cd apps/dashboard && pnpm exec knip
   ```
   Expected: 0 lines of output (clean).

## Commit Plan (6 commits)

### T1: `chore(dead-code)` Remove `fn-core/` Effect-TS experiment (29 files)

**Files**: `fn-core/` entire directory (29 files: 22 .ts source + 3 .db + package.json + package-lock.json + tsconfig.json + 1 main.ts + 1 runtime.ts + ...)

**Command**:
```bash
cd .worktrees/phase-126-v16-5-n17
git rm -r fn-core
git status  # confirm 29 deletions staged
git commit -m "chore(dead-code): remove fn-core Effect-TS experiment

fn-core/ (29 tracked files) was added in commit 257aa70c as part of the
P2 修复 bundle on 2026-07-27 but never wired into the LingWen monorepo.
- 22 .ts source files implementing event-sourced aggregates (Comment/Story/User),
  command handlers, event bus, snapshot service, sqlite event store,
  routing (stranglerRouter), middleware (auth), runtime, and main entry.
- 3 SQLite database files (lingwen.db + shm + wal) from local experiment.
- package.json declares 'lingwen-fn-core' standalone with Effect-TS framework
  dependencies (@effect/cluster, @effect/platform, @effect/platform-node,
  better-sqlite3, effect) — never listed in pnpm-workspace.yaml.
- package-lock.json + tsconfig.json.

Verified dead code:
- grep -rln 'fn-core\\|lingwen-fn-core' apps/ packages/ → 0 matches.
- pnpm-workspace.yaml does not list fn-core as a workspace member.
- No app or package imports anything from fn-core.

Ref: v16.5 #N.17 knip broader cleanup.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Post-T1 verification**:
```bash
cd apps/dashboard && pnpm exec knip  # must stay 0
pnpm vitest run 2>&1 | tail -5  # must stay 1762+1
```

---

### T2: `chore(dead-code)` Remove `trae比赛/` trae AI competition submission (13 files)

**Files**: `trae比赛/novel-writing-assistant/` (13 files: 5 TTF fonts + 2 min.js + 3 JPG assets + charts.js + HTML + 报名内容.txt)

**Command** (note Chinese path quoting):
```bash
cd .worktrees/phase-126-v16-5-n17
git rm -r 'trae比赛'
git status  # confirm 13 deletions staged
git commit -m "chore(dead-code): remove trae比赛 trae AI competition submission

trae比赛/novel-writing-assistant/ (13 tracked files) was added in
commit 257aa70c as part of the P2 修复 bundle but never used by LingWen.
Contents:
- 5 TTF font files (CrimsonPro Bold/Italic/Regular, IBMPlexMono Regular,
  YoungSerif Regular) for the competition HTML page.
- 2 vendored min.js libraries (echarts + mermaid) for charts/diagrams.
- 3 JPG product screenshot assets (hero, product_ui, scenario).
- charts.js + novel-writing-assistant.html + 报名内容.txt.

Verified dead code:
- grep -rln 'trae比赛\\|trae-competition' apps/ packages/ → 0 matches.
- Subdirectory name is Chinese 'trae比赛' (trae competition).
- No app, package, or workflow references these assets.

Ref: v16.5 #N.17 knip broader cleanup.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Post-T2 verification**:
```bash
cd apps/dashboard && pnpm exec knip  # must stay 0
```

---

### T3: `chore(dashboard-contracts)` Remove redundant `export.ts` + `memory.ts` shims (2 files)

**Files**: `packages/dashboard-contracts/src/shared/{export,memory}.ts`

**Rationale**: Both files were created in v16.2.5 (export) + v16.2.6 (memory) as "TS re-export shim" bridging lingwen-shared TS codegen → TypeScript. However:
- All types re-exported by `export.ts` (`CreatorEpubExportRequest`, `CreatorDocxExportRequest`, `CreatorPublish*` — 8 types) are ALSO already in `creator.ts`.
- All types re-exported by `memory.ts` (`CreatorMemoryAnnotationRequest`, `CreatorMemoryAssetItem`, etc. — 7 types) are ALSO already in `creator.ts`.
- `index.ts` (unified entry point) re-exports from `creator.ts` (line 12) but NOT from `export.ts` or `memory.ts`.
- Dashboard imports go through `@lingwen/dashboard-contracts/shared` (no subpath) → `index.ts` → `creator.ts` chain.

**Command**:
```bash
cd .worktrees/phase-126-v16-5-n17
git rm packages/dashboard-contracts/src/shared/export.ts packages/dashboard-contracts/src/shared/memory.ts
git status  # confirm 2 deletions staged
git commit -m "chore(dashboard-contracts): remove redundant export.ts + memory.ts shims

Both shims were created in v16.2.5 (export) and v16.2.6 (memory) to
re-export types from packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.
However, all 15 types (8 in export + 7 in memory) are ALREADY present in
packages/dashboard-contracts/src/shared/creator.ts and re-exported via
packages/dashboard-contracts/src/shared/index.ts (line 12).

Dashboard imports use '@lingwen/dashboard-contracts/shared' (no subpath),
which resolves to index.ts → creator.ts — never touches export.ts or memory.ts.
Verified: grep -rln 'dashboard-contracts/shared/export\\|dashboard-contracts/shared/memory'
apps/dashboard/src/ → 0 matches.

Ref: v16.5 #N.17 knip broader cleanup.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Post-T3 verification**:
```bash
cd apps/dashboard && pnpm exec knip  # must stay 0
pnpm tsc --noEmit  # 0 errors (verify no broken TS imports)
```

---

### T4: `chore(scripts)` Remove dead scripts (3 files)

**Files**: `scripts/check-frontend-runtime.js` + `scripts/check-null-access.js` + `scripts/frontend-smoke.spec.js`

**Verified dead**:
- `grep -rln "scripts/check-frontend-runtime\|scripts/check-null-access\|scripts/frontend-smoke"` across `.github/`, `package.json`, `turbo.json`, `pnpm-workspace.yaml`, `apps/` → 0 matches.
- Not in any CI workflow, root package.json scripts, turbo pipeline, or app test infrastructure.

**Command**:
```bash
cd .worktrees/phase-126-v16-5-n17
git rm scripts/check-frontend-runtime.js scripts/check-null-access.js scripts/frontend-smoke.spec.js
git status  # confirm 3 deletions staged
git commit -m "chore(scripts): remove dead check-frontend-runtime + check-null-access + frontend-smoke

3 files added in commit 257aa70c P2 修复 bundle but never wired into any
CI workflow, root package.json script, turbo pipeline, or app test infra.
- scripts/check-frontend-runtime.js — likely older hygiene script
- scripts/check-null-access.js — likely older hygiene script
- scripts/frontend-smoke.spec.js — likely pre-Phase-99 smoke spec

Verified zero references:
- grep -rln 'scripts/check-frontend-runtime\\|scripts/check-null-access\\|scripts/frontend-smoke'
  .github/ package.json turbo.json pnpm-workspace.yaml apps/ → 0 matches.

Ref: v16.5 #N.17 knip broader cleanup.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Post-T4 verification**:
```bash
cd apps/dashboard && pnpm exec knip  # must stay 0
pnpm vitest run 2>&1 | tail -5  # 1762+1 (no regression)
```

---

### T5: `chore(knip)` Add ignoreDependencies + ignoreBinaries for legitimate false positives

**File**: `apps/dashboard/knip.json`

**Edit**:
```json
{
  "entry": [
    "src/router/index.js"
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
    "tests/visual-audit/ui-metrics.spec.js",
    "src/composables/index.ts",
    "src/composables/useDashboardNav.js",
    "src/composables/useWidgetRegistry.js",
    "tests/e2e/write-workspace.spec.ts",
    "src/config/creatorPanelMatrix.js",
    "tests/visual-audit/helpers/capture-ui-audit.js",
    "tests/helpers/strict-test-types.ts",
    "src/api/index.js",
    "src/api/cvg.ts",
    "src/api/decisions.ts",
    "src/api/health.ts",
    "src/api/workflows.ts"
  ],
  "ignoreBinaries": ["knip", "playwright", "vitest", "eslint", "tsc"],
  "ignoreDependencies": ["openapi-typescript", "zod"]
}
```

**Note**: Adding `ignoreDependencies` for `openapi-typescript` + `zod` — both used by tooling/contracts/{dump_openapi,zod_revalidate}.py via subprocess, not via package.json scripts. Extending `ignoreBinaries` to cover the 9 workflow binaries invoked by `.github/workflows/*.yml` directly.

**Command**:
```bash
cd .worktrees/phase-126-v16-5-n17
# Edit apps/dashboard/knip.json per the diff above
git add apps/dashboard/knip.json
git diff --cached  # verify the change is correct
git commit -m "chore(knip): add ignoreDependencies + extend ignoreBinaries

Suppress legitimate knip false positives:
- ignoreDependencies: openapi-typescript, zod
  Both used by tooling/contracts/{dump_openapi,zod_revalidate}.py via
  subprocess (npx openapi-typescript, python import zod). Not declared
  in any package.json script → knip can't see usage.

- ignoreBinaries: extend from ['knip'] to ['knip', 'playwright', 'vitest',
  'eslint', 'tsc']
  These binaries are invoked directly by .github/workflows/*.yml CI steps
  (not via pnpm scripts), so knip reports them as 'Unlisted binaries'.
  This is the standard knip pattern for monorepo workflow binaries.

Ref: v16.5 #N.17 knip broader cleanup.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Post-T5 verification**:
```bash
cd apps/dashboard && pnpm exec knip  # must stay 0
# Also verify the gate works correctly from root context:
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n17 && pnpm knip  # must also be 0
```

---

### T6: `docs(phase-126)` Handoff + CLAUDE.md update (2 file changes)

**Files**:
- `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n17-knip-broader-cleanup-handoff.md` (NEW)
- `CLAUDE.md` (UPDATE — add v16.5 #N.17 entry)

**Command**:
```bash
cd .worktrees/phase-126-v16-5-n17
# Write handoff doc + update CLAUDE.md
git add docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n17-knip-broader-cleanup-handoff.md CLAUDE.md
git commit -m "docs(phase-126): N.17 knip broader cleanup handoff + CLAUDE.md

v16.5 #N.17 closed the carryover from N.15: 47 tracked files deleted
across fn-core/ (29) + trae比赛/ (13) + dashboard-contracts/{export,memory}.ts
(2) + scripts/{check-frontend-runtime,check-null-access,frontend-smoke} (3),
plus knip.json ignoreDependencies + ignoreBinaries added for legitimate
false positives.

Verified-vs-claimed scope discipline (N.14 lesson 1) reduced the N.15
carryover estimate of '~30-50 commits' to 6 actual commits — the
60+ composables/index.ts unused exports and 4 typed wrapper files are
all legitimate Vite @/ alias consumption, not real dead code.

Final gates: knip {\"issues\":[]} / vitest 1762+1 / shared 136 /
vue-tsc 0 / ESLint 0 / lint-imports 3 contracts KEPT.

Ref: v16.5 #N.17 knip broader cleanup handoff.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Final Verification (post-T6)

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n17

# 1. knip gate from CI context
pnpm knip  # 0 issues

# 2. Frontend tests
cd apps/dashboard && pnpm vitest run  # 1762+1

# 3. Frontend type check
pnpm tsc --noEmit  # 0 errors

# 4. Frontend lint
pnpm eslint .  # 0 errors

# 5. Backend shared tests
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n17
./.venv/bin/python -m pytest packages/lingwen-shared/tests/  # 136+ passing

# 6. import-linter
.lingwen/bin/import-linter lint --config pyproject.toml  # 3 contracts KEPT

# 7. git status — clean
git status  # nothing to commit, working tree clean
```

## Push + PR

```bash
cd .worktrees/phase-126-v16-5-n17
git push -u origin phase-126-v16-5-n17
gh pr create --base master --title "Phase 126 v16.5 #N.17: knip broader cleanup" --body "..."
```

## Cleanup

After PR merged:
```bash
cd /home/ailearn/projects/LingWen
git worktree remove .worktrees/phase-126-v16-5-n17
git branch -d phase-126-v16-5-n17
```

## Lessons Learned (record in handoff T6)

1. **Verify carryover claims (N.14 lesson 1)** — N.15 carryover estimate "~30-50 commits" was way overestimated. Actual scope: 6 commits. The "60+ unused exports in composables/index.ts" was a false positive list, not a work list.
2. **`git ls-files fn-core/` returns 0** was a misleading first read; the real check is `git ls-files --stage` which confirms files ARE in the index.
3. **knip.json `ignore` field semantics** — knip.json was correctly applied from `apps/dashboard/` context, producing 0 lines of output. Root-context runs without config show 180+ findings (misleading).
4. **Chinese path quoting matters** — `trae比赛` requires quoting in shell commands: `git rm -r 'trae比赛'`.
5. **Redundant re-export detection** — `export.ts` + `memory.ts` shims in dashboard-contracts were created but never indexed by `index.ts`. The types they re-export already exist in `creator.ts` (which IS in the index chain).
