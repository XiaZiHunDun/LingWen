# v16.5 #N.15 — knip broader cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate remaining knip-detected dead code (`useDevice.js`) and apply knip configuration hint (`src/main.js` redundant entry); document why remaining flagged deps/binaries are legitimate false positives.

**Architecture:** Pure cleanup phase — no new code. N.13 + N.14 already collapsed the bulk of knip findings (cast removal + dead export cleanup). N.15 closes the residual 2 actionable items.

**Tech Stack:** Vue 3 / TypeScript / knip / vitest

---

## Scope Discovery (N.15 reality vs N.11/13/14 carryover)

The original v16.5 #N.11 carryover estimated "~30-50 commits" for knip broader cleanup. After N.13 + N.14 collapsed most findings, **actual residual scope is 2 tasks / 2 commits**.

### Current knip findings (master, 2026-09-01, `7b1f79b8`)

```
Unused dependencies (1)
@tiptap/pm  package.json:38:6           ← KEEP (peer dep for TipTap editor)
Unused devDependencies (4)
@vue/server-renderer  package.json:60:6 ← KEEP (transitive peer for vue-tsc)
husky               package.json:64:6   ← KEEP (package.json prepare script)
lint-staged         package.json:66:6   ← KEEP (.husky/pre-commit runs it)
vue-tsc             package.json:71:6   ← KEEP (multiple type-check scripts)
Unlisted binaries (11)                   ← KEEP (package.json scripts + .husky + .lintstagedrc — all scripts, not real binaries)
Configuration hints (1)
src/main.js    knip.json                 ← ACT (redundant entry covered by project glob)
```

### Actionable findings (the only 2):

| Item | Action | Reason |
|------|--------|--------|
| `src/composables/useDevice.js` | **DELETE** | Only re-exported by `composables/index.ts`; no Vue/components/stores import it; no tests |
| knip config hint: `src/main.js` redundant entry | **REMOVE from knip.json entry array** | `project: ["src/**/*.{js,ts,vue}"]` already covers it |

### Verified false positives (documented, NOT removed):

- **`@tiptap/pm`** — TipTap `@tiptap/vue-3` re-exports `pm` types. peer dep. Per MEMORY.md: "do NOT delete."
- **`@vue/server-renderer`** — Peer dep for vue-tsc's SSR type checking (`vue-tsc/package.json` peerDeps + `pnpm-lock.yaml` confirms `@vue/server-renderer@3.5.40` resolved). Removing breaks vue-tsc type checking.
- **`husky`** — package.json `"prepare": "husky"` script + `.husky/` directory. knip can't trace package.json scripts.
- **`lint-staged`** — `.husky/pre-commit` runs `pnpm lint-staged`. knip can't trace husky pre-commit hooks.
- **`vue-tsc`** — Multiple scripts: `pnpm typecheck`, `pnpm typecheck:app`, etc. knip can't trace package.json scripts.
- **Unlisted binaries (11)** — All scripts in package.json + .husky + .lintstagedrc. knip config needs `"entry"` patterns adjusted to recognize them (out of scope for N.15; can be addressed via knip `"binaries"` field if desired later).

---

## File Structure

| File | Action | Reason |
|------|--------|--------|
| `apps/dashboard/src/composables/useDevice.js` | DELETE | No consumers anywhere in src/ |
| `apps/dashboard/src/composables/index.ts` | MODIFY (remove 2 lines + comment ref) | Remove `useDevice` re-export + comment mention |
| `apps/dashboard/knip.json` | MODIFY (2 edits) | Remove `src/main.js` from entry + remove `useDevice.js` from ignore |

No new files. No test changes (no tests exist for `useDevice`).

---

### Task 1: Delete `useDevice.js` (dead composable)

**Files:**
- Delete: `apps/dashboard/src/composables/useDevice.js`
- Modify: `apps/dashboard/src/composables/index.ts:28` (remove comment reference)
- Modify: `apps/dashboard/src/composables/index.ts:93` (remove re-export)
- Modify: `apps/dashboard/knip.json:18` (remove from ignore)

**Investigation (already completed, recorded for audit):**

```bash
# Find all references to useDevice outside its own file:
grep -rn "useDevice" apps/dashboard/src apps/dashboard/tests \
  --include="*.vue" --include="*.ts" --include="*.js" \
  --include="*.tsx" --include="*.jsx" --include="*.json" \
  | grep -v node_modules | grep -v "useDevice.js:"

# Result (3 hits, all dead):
#   knip.json:18  ← ignore entry (will be removed)
#   src/composables/index.ts:28  ← comment mention (will be removed)
#   src/composables/index.ts:93  ← re-export (will be removed)
```

No Vue file imports `useDevice`. No store uses it. No tests exist.

- [ ] **Step 1: Delete `useDevice.js`**

```bash
git rm apps/dashboard/src/composables/useDevice.js
```

- [ ] **Step 2: Remove the re-export from `src/composables/index.ts`**

Open `apps/dashboard/src/composables/index.ts`. Locate line 93:
```ts
export { useDevice } from './useDevice.js';
```
Delete that line.

- [ ] **Step 3: Remove the comment reference from `src/composables/index.ts`**

Open `apps/dashboard/src/composables/index.ts`. Locate line 28:
```ts
 * - 业务工具: useAskPageTab, useStudioProject, useFilteredPageError, useDevice,
```
Edit to:
```ts
 * - 业务工具: useAskPageTab, useStudioProject, useFilteredPageError,
```

- [ ] **Step 4: Remove `useDevice.js` from `knip.json` ignore**

Open `apps/dashboard/knip.json`. Delete line 18:
```json
    "src/composables/useDevice.js",
```

- [ ] **Step 5: Run vitest to confirm no regressions**

Run from `apps/dashboard/`:
```bash
cd apps/dashboard
pnpm vitest run
```
Expected: **1762 passed + 1 skipped** (no change from baseline).

- [ ] **Step 6: Run vue-tsc to confirm no type errors**

Run from `apps/dashboard/`:
```bash
cd apps/dashboard
pnpm tsc --noEmit
```
Expected: **0 errors**.

- [ ] **Step 7: Run ESLint to confirm no new violations**

Run from `apps/dashboard/`:
```bash
cd apps/dashboard
pnpm eslint .
```
Expected: **0 errors, 0 warnings**.

- [ ] **Step 8: Run knip to confirm no new unused-export findings**

Run from `apps/dashboard/`:
```bash
cd apps/dashboard
pnpm exec knip 2>&1 | tee /tmp/n15-t1-knip.txt
```

Expected output (useDevice.js removed from ignore → knip won't try to flag it as unused because the file no longer exists):

```
Unused dependencies (1)
@tiptap/pm  package.json:38:6
Unused devDependencies (4)
@vue/server-renderer  package.json:60:6
husky                 package.json:64:6
lint-staged           package.json:66:6
vue-tsc               package.json:71:6
Unlisted binaries (11)
... (same as before)
Configuration hints (1)
src/main.js    knip.json  Remove redundant entry pattern
```

If a NEW "unused exports" or "unused files" finding appears in the output, **stop and re-investigate** — that means something was consuming `useDevice` that we missed.

- [ ] **Step 9: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/index.ts apps/dashboard/knip.json
git commit -m "refactor(dashboard): N.15 T1 remove dead useDevice composable + knip ignore entry"
```

Commit body should reference investigation grep output and the N.15 plan task ID.

---

### Task 2: Apply knip config hint — remove `src/main.js` redundant entry

**Files:**
- Modify: `apps/dashboard/knip.json:2` (remove `"src/main.js"`)

**Investigation (already completed):**

Current `apps/dashboard/knip.json`:
```json
{
  "entry": [
    "src/main.js",                ← redundant (project glob covers it)
    "src/router/index.js"
  ],
  "project": [
    "src/**/*.{js,ts,vue}",
    "tests/**/*.{js,ts}"
  ],
  ...
}
```

knip config documentation: `entry` patterns are root analysis points; when `project` glob already covers the same files, entry is redundant.

- [ ] **Step 1: Edit `knip.json` to remove `"src/main.js"` from entry array**

Open `apps/dashboard/knip.json`. Locate:
```json
{
  "entry": [
    "src/main.js",
    "src/router/index.js"
  ],
```

Edit to:
```json
{
  "entry": [
    "src/router/index.js"
  ],
```

Keep `"src/router/index.js"` (knip recommends explicit entry for entry-point files; "src/router/index.js" is the actual router root that may not be properly traced through "src/**/*.{js,ts,vue}" glob).

- [ ] **Step 2: Run knip to verify config hint is gone**

Run from `apps/dashboard/`:
```bash
cd apps/dashboard
pnpm exec knip 2>&1 | tee /tmp/n15-t2-knip.txt
```

Expected output (the `src/main.js  knip.json  Remove redundant entry pattern` hint should now be GONE):

```
Unused dependencies (1)
@tiptap/pm  package.json:38:6
Unused devDependencies (4)
@vue/server-renderer  package.json:60:6
husky                 package.json:64:6
lint-staged           package.json:66:6
vue-tsc               package.json:71:6
Unlisted binaries (11)
... (same as before)
```

(The "Configuration hints (1)" section should now be empty or absent.)

- [ ] **Step 3: Run vitest to confirm no behavior change**

Run from `apps/dashboard/`:
```bash
cd apps/dashboard
pnpm vitest run
```
Expected: **1762 passed + 1 skipped** (unchanged).

- [ ] **Step 4: Run vue-tsc + ESLint to confirm no new errors**

```bash
cd apps/dashboard
pnpm tsc --noEmit
pnpm eslint .
```
Expected: **0 errors** for both.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/knip.json
git commit -m "chore(knip): N.15 T2 remove redundant src/main.js entry pattern"
```

---

### Task 3: Verification + handoff

- [ ] **Step 1: Run full verification suite from worktree HEAD**

```bash
cd /home/ailearn/projects/LingWen
pnpm vitest --filter dashboard run
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q
cd apps/dashboard && pnpm tsc --noEmit && pnpm eslint . && pnpm exec knip
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/hygiene/ -q  # import-linter contracts
```

Expected:
- vitest: 1762 passed + 1 skipped
- shared pytest: 136 passed
- vue-tsc: 0 errors
- ESLint: 0 errors
- knip: 0 unused exports / 0 unused files (deps/devDeps/binaries documented as false positives above)
- import-linter: 3 contracts KEPT

- [ ] **Step 2: Write handoff doc**

Save to `docs/superpowers/handoffs/2026-09-01-phase-126-v16-5-n15-knip-broader-cleanup-handoff.md` with:
- Original carryover claim (~30-50 commits) vs actual scope (2 commits)
- Investigation grep outputs
- False positive taxonomy (peer deps, scripts, transitive deps)
- knip config changes
- Architecture invariant added: **#34** — `useDevice` composable removed; knip unused exports = 0 with no ignore-list padding
- Lessons learned (carryover scope drift, knip "hints" are real signals, false positive documentation)

- [ ] **Step 3: Update MEMORY.md + CLAUDE.md**

Add to `MEMORY.md`:
- Link to handoff doc
- Final N.15 state (knip: 0 unused exports/files; deps/devDeps/binaries documented as legitimate false positives)

Update `CLAUDE.md` "更新" section with v16.5 #N.15 entry.

- [ ] **Step 4: Merge to master via PR**

```bash
cd /home/ailearn/projects/LingWen
git push origin phase-126-v16-5-n15
gh pr create --title "Phase 126 v16.5 #N.15: knip broader cleanup (residual scope)" \
  --body "Closes the residual knip findings after N.13/N.14. 2 commits: T1 remove dead useDevice composable + T2 remove redundant knip entry. Documented false positives for deps/devDeps/binaries."
```

After PR merge, remove worktree and local branch (per N.14 pattern).

---

## Self-Review

**1. Spec coverage:**
- ✅ N.15 spec = "knip broader cleanup" → all actionable findings addressed (T1 + T2)
- ✅ False positives documented (no action needed; comments in plan body)
- ✅ Carryover claims reconciled (original ~30-50 commits estimate → actual 2 commits)
- ✅ Pre-existing v15.7.1 debt (lingwen_quality + plugin_manager bug) explicitly out-of-scope per user choice

**2. Placeholder scan:**
- No "TBD" / "TODO" / "fill in details" in plan body
- All commands have expected output
- No "similar to Task N" cross-references — each task is self-contained

**3. Type consistency:**
- `useDevice` referenced consistently across T1 (delete + re-export removal + comment + knip.json)
- `knip.json` referenced consistently in T2 + T1 (separate edits, both atomic)

**4. Risk assessment:**
- **T1 risk: LOW** — `useDevice` has zero consumers (verified via 3 separate greps: src/, tests/, all relevant file extensions). Failure mode: knip would surface a new "unused exports" finding → user must investigate the new consumer.
- **T2 risk: LOW** — knip config hint is a documented best practice. Failure mode: knip might fail to analyze main.js properly → user must add `"src/main.js"` back to entry.

Both risks have explicit "stop and re-investigate" gates in their respective verification steps.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-01-phase-126-v16-5-n15-knip-broader-cleanup.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?