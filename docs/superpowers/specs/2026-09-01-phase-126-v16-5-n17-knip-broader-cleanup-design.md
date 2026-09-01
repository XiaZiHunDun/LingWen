# Phase 126 v16.5 #N.17 — knip Broader Cleanup Design

## Context

Phase 126 v16.5 #N.15 closed the immediate `knip` output gap (3 → 0 issues via `useDevice` deletion + 3 reference cleanup edits + 1 knip config hint) but left a large carryover claim: "knip broader cleanup: composables/index.ts 60+ unused exports + useDashboardNav + useWidgetRegistry + creatorPanelMatrix + tests/visual-audit + fn-core/ — ~30-50 commits".

**Verify-before-design** (per N.14 lesson 1 + N.14 lesson 5): the N.15 carryover description was imprecise. Re-running `pnpm exec knip` from the right context (`apps/dashboard/`) returns **0 issues** — the 18-item `ignore` list in `apps/dashboard/knip.json` already suppresses the 60+ barrel exports, the 4 typed wrapper files, the 5 visual-audit specs, the 2 lint-testid fixtures, and the blocked Phase 114 e2e spec. They are legitimate false positives caused by knip not understanding Vite `@/` alias consumption.

**But `pnpm exec knip` from the project root returns ~180 findings** because root has no knip.json. This is misleading — the actual CI gate is `pnpm knip` which uses `pnpm -C apps/dashboard exec knip`, and that is clean.

The N.17 work targets the **actual remaining dead code** in the repo, not the false positives:

| Category | Count | Source | Status |
|----------|------:|--------|--------|
| `fn-core/` (Effect-TS experiment) | 29 | commit `257aa70c` P2 fixes bundle | dead, 0 importers |
| `trae比赛/novel-writing-assistant/` (trae AI competition) | 13 | commit `257aa70c` P2 fixes bundle | dead, 0 importers |
| `packages/dashboard-contracts/src/shared/{export,memory}.ts` | 2 | v16.2.5/v16.2.6 re-export shims | redundant (types already in `creator.ts` chain) |
| `scripts/{check-frontend-runtime,check-null-access,frontend-smoke}.{js,spec.js}` | 3 | old check scripts | dead, 0 CI references |
| `apps/dashboard/knip.json` ignoreDependencies + ignoreBinaries | 0 | config | new — suppress legitimate false positives |

**Total: 47 tracked file deletions + 1 knip.json config update.**

## Goals

1. Remove 4 dead-code locations (47 tracked files) verified via `git ls-files` + cross-repo grep.
2. Suppress remaining legitimate false positives in `apps/dashboard/knip.json` (2 devDeps + 9 workflow binaries).
3. Keep all architecture invariants from v16.5 #N.0..#N.16 intact (35 invariants).
4. Maintain `pnpm knip` CI gate at `{"issues":[]}` (already green; must stay green after deletions).

## Non-Goals

1. **NOT** eliminating knip false positives by deleting the 60+ barrel exports. They are legitimate alias-consumption surfaces — composables are imported via `@/composables/*` and the `index.ts` barrel is the canonical re-export. Knip can't trace Vite alias without explicit `entry` config.
2. **NOT** migrating typed wrappers (cvg/decisions/health/workflows.ts) to direct paths. They're the canonical typed wrapper layer (v16.2.x + v16.5 #7-13 work).
3. **NOT** deleting the `visual-audit/*` infrastructure. These are intentionally-kept design-quality audit specs — used in pre-Phase-126 design validation.
4. **NOT** deleting the `lint-testid/{clean,dirty}.spec.ts` fixtures. They are the canonical ESLint rule test fixtures (`eslint-rules/testid-class-sync.js`).
5. **NOT** fixing `e2e/write-workspace.spec.ts`. BLOCKED by Phase 114 prod preview regression (accepted debt).
6. **NOT** touching the `useDashboardNav` / `useWidgetRegistry` / `creatorPanelMatrix` / `strict-test-types.ts` ignore entries. They are all consumed via Vite alias or test fixtures.
7. **NOT** introducing any new feature work. This is debt closure only.

## Verification Before Deletion

### fn-core/

- `git log --all --oneline -- fn-core/` → only commit `257aa70c` (2026-07-27) introduced it, never modified since.
- `grep -rln "fn-core\|lingwen-fn-core" --include="*.ts" --include="*.js" /home/ailearn/projects/LingWen/apps/ /home/ailearn/projects/LingWen/packages/` → 0 matches.
- No `apps/dashboard` import, no `packages/dashboard-contracts` import, no `packages/lingwen-*` import.
- `package.json` declares `lingwen-fn-core` standalone (Effect-TS framework deps: `@effect/cluster`, `@effect/platform`, `@effect/platform-node`, `better-sqlite3`, `effect`). Never wired into LingWen monorepo's pnpm workspace.
- `pnpm-workspace.yaml` does not list `fn-core` as a workspace member.
- **Verdict**: 29 files safe to delete via `git rm -r fn-core`.

### trae比赛/

- `git log --all --oneline -- trae比赛/` → only commit `257aa70c` introduced it, never modified since.
- `grep -rln "trae比赛\|trae-competition\|trae_comp" /home/ailearn/projects/LingWen/apps/ /home/ailearn/projects/LingWen/packages/` → 0 matches.
- 13 files include vendored assets: 5 TTF fonts (CrimsonPro Bold/Italic/Regular + IBMPlexMono + YoungSerif), 2 min.js (echarts + mermaid), 3 JPGs (hero + product_ui + scenario), charts.js, novel-writing-assistant.html, 报名内容.txt.
- Subdirectory name is Chinese "trae比赛" (trae competition). May need quoting in shell commands.
- **Verdict**: 13 files safe to delete via `git rm -r 'trae比赛'`.

### packages/dashboard-contracts/src/shared/{export,memory}.ts

- Created in v16.2.5 (export) and v16.2.6 (memory) as "TS re-export shim" to bridge `lingwen-shared` Python Pydantic codegen → TypeScript.
- Both files re-export 7-8 types from `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator`.
- **However**, all those types are ALSO already re-exported from `packages/dashboard-contracts/src/shared/creator.ts` (lines 110 + 119-120 verified).
- `packages/dashboard-contracts/src/shared/index.ts` (the unified entry point) re-exports from `creator.ts` (line 12) but does NOT re-export from `export.ts` or `memory.ts`.
- `grep -rln "from '@lingwen/dashboard-contracts/shared/export\|from '@lingwen/dashboard-contracts/shared/memory" /home/ailearn/projects/LingWen/apps/dashboard/` → 0 matches.
- Dashboard imports via `@lingwen/dashboard-contracts/shared` (no subpath) which goes through `index.ts` → `creator.ts` chain.
- **Verdict**: 2 files are redundant (types duplicated in `creator.ts`), safe to delete.

### scripts/{check-frontend-runtime,check-null-access,frontend-smoke}

- `grep -rln "scripts/check-frontend-runtime\|scripts/check-null-access\|scripts/frontend-smoke" /home/ailearn/projects/LingWen/.github/ /home/ailearn/projects/LingWen/package.json /home/ailearn/projects/LingWen/turbo.json /home/ailearn/projects/LingWen/pnpm-workspace.yaml /home/ailearn/projects/LingWen/apps/` → 0 matches.
- Not referenced in any CI workflow, root package.json scripts, or turbo pipeline.
- Likely leftovers from older pre-Phase-99 hygiene script infrastructure.
- **Verdict**: 3 files safe to delete.

### knip.json ignoreDependencies + ignoreBinaries

- `openapi-typescript` (root devDep) — used by `tooling/contracts/dump_openapi.py` (subprocess `npx openapi-typescript`). Not used by any `package.json` script.
- `zod` (root devDep) — used by `tooling/contracts/zod_revalidate.py` and tests. Not used by any `package.json` script.
- 9 workflow binaries in `.github/workflows/*.yml` (playwright × 5, vitest × 3, eslint, tsc) — invoked directly by CI steps, not via `package.json` scripts.
- **Verdict**: Add `ignoreDependencies: ["openapi-typescript", "zod"]` and extend `ignoreBinaries: ["knip"]` → `["knip", "playwright", "vitest", "eslint", "tsc"]`.

## Implementation

### Commit Structure (Atomic 1-task-per-commit, per N.13/N.14/N.15/N.16 pattern)

| Commit | Type | Description | Files |
|---|---|---|---|
| T1 | `chore(dead-code)` | Remove `fn-core/` Effect-TS experiment | 29 files via `git rm -r fn-core` |
| T2 | `chore(dead-code)` | Remove `trae比赛/novel-writing-assistant/` trae AI competition submission | 13 files via `git rm -r 'trae比赛'` |
| T3 | `chore(dashboard-contracts)` | Remove redundant `export.ts` + `memory.ts` shims (types already in `creator.ts`) | 2 files via `git rm` |
| T4 | `chore(scripts)` | Remove dead scripts (no CI references) | 3 files via `git rm` |
| T5 | `chore(knip)` | Add `ignoreDependencies` + `ignoreBinaries` to suppress legitimate false positives | 1 file modified |
| T6 | `docs(phase-126)` | Handoff doc + CLAUDE.md update | 2 files modified |

**Estimated total: 6 commits.** Significantly smaller than N.15 carryover's ~30-50 estimate — verified-vs-claimed scope discipline (N.14 lesson 1) reveals the actual scope.

### Pre-Commit Verification Per Commit

After each commit:
1. `pnpm exec knip` from `apps/dashboard/` → must still report 0 issues (CI gate stays green).
2. `pnpm vitest run` from `apps/dashboard/` → no regression (target: 1762 passing + 1 skipped).
3. `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/` → no regression (target: 136 passing).
4. `pnpm tsc --noEmit` from `apps/dashboard/` → 0 errors.
5. `pnpm eslint .` from `apps/dashboard/` → 0 errors.

## Architecture Invariants Preserved (35 total)

All 35 architecture invariants from v16.5 #N.0..#N.16 stay intact:
- #35: `lingwen_quality` symbols importable + CI-guarded
- #36: `plugin_manager` canonical module path + regression test
- #33: knip unused exports count = 0 (N.14 carryover)
- #32: `ChapterData.has_body` Pydantic field
- #28: `ReferenceGraphResponse` canonical presentation shape
- ... (all prior)

**No NEW architecture invariants** for N.17 — the deletions don't add constraints; they remove dead code. The existing knip CI gate (must remain `{"issues":[]}`) is the only enforcement.

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Hidden importer of `fn-core` | Very Low | Triple-verified: `git grep` + `pnpm grep` + workspace config check |
| Hidden importer of `trae比赛` | Very Low | Triple-verified: same checks; Chinese dir name unlikely to have imports |
| Dashboard consumer using `@lingwen/dashboard-contracts/shared/export` subpath | Low | Verified: 0 matches in apps/dashboard/src/ |
| CI uses scripts/check-frontend-runtime.js | Low | Verified: 0 references in .github/workflows/ |
| `git rm -r` Chinese path issues | Medium | Use quoted paths: `git rm -r 'trae比赛'` |
| Worktree env-sync | High (recurring per N.14 lesson 4) | Use worktree's `.venv/bin/python`, NOT conda's `/home/ailearn/miniconda3/bin/python` |

## Carryover to v16.5 #N.18+

After N.17 closes, LingWen will be at true zero-knip-debt state. Remaining LingWen debt is only Phase 114 prod preview regression (accepted).

**No more knip carries** — knip gate is locked at `{"issues":[]}` and CI enforces it.

Future phases could address:
- Phase 114 prod preview regression (high-effort / low-reward, accepted)
- New feature work (would require brainstorming + spec + plan)
- Architectural refactors (e.g., consolidating typed wrappers, eliminating barrel exports where possible)
