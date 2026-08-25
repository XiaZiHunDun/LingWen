# Phase 106 — Fix CI knip gate invocation

> **Date**: 2026-08-25
> **Branch**: master (post-Phase 105b)
> **Trigger**: Discovered during post-knip Web Vitals re-baseline (`docs/superpowers/audit/2026-08-25-post-knip-vitals-rebaseline.md`)
> **Status**: spec → user review
> **Decision**: Option A refined (per brainstorm AskUserQuestion 2026-08-25 + post-braintorm discovery)

---

## 1. Background

Phase 95-99 promoted the knip dead-export gate from "non-blocking scaffold" to "hard error". The handoff (`docs/superpowers/handoffs/2026-08-25-phase100-105b-handoff.md` §1.3, §4.1) describes:

> knip gate is now enforced (no `|| echo` fallback)
>
> `/home/ailearn/projects/LingWen/package.json` (root) — has `knip` script: `pnpm exec knip --config apps/dashboard/knip.json` (Phase 102.1 delegation)

During a Web Vitals re-baseline (Phase 106 precursor), the auditor ran `pnpm knip --reporter=compact` from the repo root and observed:

```
Unused files (34)
Unlisted binaries (7)
Unused exports (6)
Unused exported types (1)
ELIFECYCLE  Command failed with exit code 1.
```

All 6 unused-export files and all 5 unused files are listed in `apps/dashboard/knip.json#ignore`. None of them are actually unused — knip is **misresolving ignore paths**.

### 1.1 Root cause (confirmed empirically)

`apps/dashboard/knip.json#ignore` entries (e.g. `"src/composables/index.ts"`) are relative paths. knip 6.32.2 resolves `ignore` paths relative to **the config file's containing directory** (i.e. `apps/dashboard/`), but reports "Unused" entries relative to the **invocation cwd** (or the deepest scanned root).

| Invocation | Cwd | Config path | Result |
|------------|-----|-------------|--------|
| `cd apps/dashboard && pnpm exec knip --config knip.json` | `apps/dashboard/` | `apps/dashboard/knip.json` | **clean** (2 configuration hints) |
| `pnpm exec knip --config apps/dashboard/knip.json` (from root) | `/home/ailearn/projects/LingWen` | `apps/dashboard/knip.json` | **reports 48 false-positives** |
| `pnpm -C apps/dashboard exec knip` (from root) | `apps/dashboard/` | auto-discovered | **clean** (exit 0) |

The mismatch: knip auto-discovers `knip.json` from cwd when no `--config` is given. When run from `apps/dashboard/`, ignore paths resolve correctly. When run from repo root with `--config apps/dashboard/knip.json`, ignore paths are still resolved relative to `apps/dashboard/`, but the "Unused" output paths are reported relative to repo root, causing the comparison to fail.

### 1.2 Initial Option A (`pnpm knip`) doesn't actually work

The brainstorm-selected Option A was `pnpm exec knip` → `pnpm knip` (using root `package.json#scripts.knip` delegation). Verified empirically: this **also fails** because the root script invokes knip from repo root, which still triggers the same path-resolution mismatch (confirmed: 48 false-positives reported).

The minimal working fix is **`pnpm -C apps/dashboard exec knip`**: explicitly change cwd to `apps/dashboard/` before invoking knip. From there, knip auto-discovers `knip.json` and resolves `ignore` paths correctly.

### 1.3 Why CI may have appeared to pass before Phase 106

Three possibilities, all unverified:

1. **CI hasn't run** against the master HEAD since Phase 99 promoted knip to hard-error. The workflow file was edited in Phase 99/99.1 but may not have been triggered on subsequent commits.
2. **`pnpm exec knip` exits 0** when all categories are empty — but they're not (48 entries reported), so this is unlikely.
3. **Different cwd** in CI runner vs local — possible but unverified.

The Phase 99 spec promoted knip to "no `|| echo`" but did not specify a config path. The current CI step inherits the bare invocation from Phase 95.

## 2. Goal & non-target

### 2.1 Goal

Fix the CI knip step to invoke knip from the correct directory — without changing any other behavior. After the fix:

- CI runs `pnpm -C apps/dashboard exec knip` (changes cwd before invocation)
- knip auto-discovers `apps/dashboard/knip.json`
- `ignore` paths resolve correctly → all 7 categories = 0
- CI gate is genuinely enforced

### 2.2 Non-target

- No new knip rules
- No new ignore entries
- No config restructuring
- No new packages installed
- No changes to knip.json itself
- No workflow restructuring (single-line change only)
- No changes to root `package.json#scripts.knip` (it remains as the Phase 102.1 delegation, even though it produces false-positives when run from root — that's a separate concern)

## 3. Proposed change

### 3.1 File: `.github/workflows/dashboard-frontend-ci.yml`

**Single-line edit** in the `Run knip (dead-export detection)` step:

```diff
       - name: Run knip (dead-export detection)
-        run: pnpm exec knip
+        run: pnpm -C apps/dashboard exec knip
```

`pnpm -C apps/dashboard` tells pnpm to change cwd to `apps/dashboard/` before invoking the binary. knip auto-discovers `apps/dashboard/knip.json` from the new cwd, and `ignore` paths resolve correctly.

### 3.2 No other changes

- knip.json: unchanged (already correct)
- Root package.json: unchanged
- Other workflows: unchanged (no other workflow runs knip)
- Test baseline: unchanged

## 4. Verification

After applying the fix, run locally to verify the CI step would pass:

```bash
cd /home/ailearn/projects/LingWen
pnpm -C apps/dashboard exec knip --reporter=compact 2>&1 | tail -5
```

**Expected output**: empty (no "Unused" or "Unlisted" headers, no output at all beyond newline). Exit code 0.

Already verified during Phase 106 implementation: exit 0, no output.

### 4.1 Sanity checks

- `pnpm exec vitest run` (from `apps/dashboard/`): 1545 passed
- `pnpm exec vue-tsc --noEmit` (from `apps/dashboard/`): 0 errors (not re-run, no source changes)
- `pnpm run build` (from `apps/dashboard/`): succeeds (not re-run, no source changes)
- `pnpm lint:all` (from root): clean (not re-run, no source changes)

## 5. Risk & mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `pnpm -C` flag semantics differ in CI vs local | Very low | Fix doesn't propagate to CI | pnpm 9.x has stable `-C` semantics; CI uses same pnpm version (Phase 99.1 fix) |
| Future knip upgrade changes path resolution | Low | Fix becomes obsolete | Document the cwd requirement in spec §6 / CONTRIBUTING.md |
| Developers confused by `pnpm knip` (broken from root) vs `pnpm -C apps/dashboard exec knip` (works) | Medium | Local dev friction | Phase 109 candidate: also fix root `knip` script to be cwd-safe |

## 6. Rollback

If the fix causes CI to fail:

1. Revert the commit: `git revert <sha>`
2. CI returns to broken state (knip from root produces 48 false-positives)
3. Fallback: add `working-directory: apps/dashboard` to the CI step (Option B)

## 7. Output

- 1 atomic commit: `fix(ci): run knip from apps/dashboard cwd for proper path resolution (Phase 106)`
- 1 line changed in `.github/workflows/dashboard-frontend-ci.yml`
- 0 files added
- 0 files deleted

## 8. Commit message template

```text
fix(ci): run knip from apps/dashboard cwd for proper path resolution (Phase 106)

Phase 106 — CI knip gate was invoking bare 'pnpm exec knip' from
workspace root. knip 6.32.2 resolves 'ignore' paths relative to the
config file's containing directory, but reports 'Unused' entries
relative to invocation cwd (or scanned root). When invoked from repo
root, the comparison fails → 48 false-positive unused entries, all
listed in apps/dashboard/knip.json#ignore.

Initial brainstorm-chosen fix was 'pnpm knip' (root delegation script).
Verified empirically this does NOT solve the bug — same false-positives.

Working fix: 'pnpm -C apps/dashboard exec knip' — pnpm -C changes cwd
to apps/dashboard/ before invoking knip. From there, knip auto-discovers
knip.json and resolves ignore paths correctly.

Verification: 'pnpm -C apps/dashboard exec knip' → exit 0, no output.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

## 9. Why Option A (refined)

The user brainstorm-selected Option A (`pnpm exec knip` → `pnpm knip`) on the hypothesis that root script delegation would fix the bug. Empirical verification showed it doesn't. The refined fix (`pnpm -C apps/dashboard exec knip`) keeps Option A's spirit (minimal 1-line change, reuses existing infrastructure) while solving the actual bug.

### 9.1 Why not Option B (`working-directory: apps/dashboard`)

- Adds a new `working-directory:` block (3 lines vs 1)
- Touches more workflow structure
- Same end result but slightly more diff

### 9.2 Why not Option C (rewrite root script)

- Touches `package.json` (extra surface area)
- Doesn't help CI directly (CI bypasses the script)
- Phase 109 candidate if local dev friction becomes a problem

## 10. Future phases (out of scope)

- **Phase 107**: Fix vite preview JS error (sandbox-specific), enable prod-mode Web Vitals re-baseline
- **Phase 108**: Add CI step to actually run the Web Vitals spec on every PR (currently manual)
- **Phase 109**: Make root `package.json#scripts.knip` cwd-safe (e.g. `pnpm exec knip --config apps/dashboard/knip.json` → `cd apps/dashboard && pnpm exec knip`) so devs running `pnpm knip` from root also get clean output. Independent of CI step.

---

**Next step**: Phase 106 plan → user review → execute.