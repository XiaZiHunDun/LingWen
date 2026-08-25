# Phase 109 — Make root `pnpm knip` cwd-safe

> **Date**: 2026-08-25
> **Branch**: master (post-Phase 106)
> **Trigger**: Phase 106 discovered root `pnpm knip` script also produces 48 false-positive unused entries (same root-cause as CI; not unique to CI)
> **Status**: spec → user review
> **Scope**: 1 line change in root `package.json#scripts.knip`

---

## 1. Background

Phase 106 fixed the CI knip gate by changing the workflow step from `pnpm exec knip` (broken from root) to `pnpm -C apps/dashboard exec knip` (works).

Phase 106 §1.2 noted the same bug also affects the **root** `package.json#scripts.knip`:

```json
"knip": "pnpm exec knip --config apps/dashboard/knip.json"
```

When developers run `pnpm knip` from the repo root (the natural place to invoke it), they hit the same false-positive path-resolution bug:

```
$ pnpm knip --reporter=compact
Unused files (34)
Unlisted binaries (7)
Unused exports (6)
Unused exported types (1)
ELIFECYCLE  Command failed with exit code 1.
```

All 48 entries are listed in `apps/dashboard/knip.json#ignore`. None are actually unused.

The Phase 102.1 delegation added the `--config apps/dashboard/knip.json` flag, but it doesn't fix the path resolution issue. The only working invocation from root is one that changes cwd before running knip:

```
$ pnpm -C apps/dashboard exec knip --reporter=compact
(exit 0, no output)
```

This is what CI now does. Phase 109 brings the **root script** in line with CI behavior.

## 2. Goal & non-target

### 2.1 Goal

Make `pnpm knip` from repo root produce the same clean output as CI. After the fix:

- `pnpm knip` from any directory runs `pnpm -C apps/dashboard exec knip` (or equivalent)
- knip auto-discovers `apps/dashboard/knip.json`
- `ignore` paths resolve correctly → all 7 categories = 0
- Local dev experience matches CI

### 2.2 Non-target

- No changes to knip.json itself
- No changes to CI workflow (already fixed in Phase 106)
- No changes to dashboard's own `package.json#scripts.knip` (it's `"knip": "knip"` and already works from `apps/dashboard/`)
- No new packages installed
- No workflow restructuring

## 3. Proposed change

### 3.1 File: `package.json` (root)

**Single-line edit** in the `knip` script:

```diff
-    "knip": "pnpm exec knip --config apps/dashboard/knip.json"
+    "knip": "pnpm -C apps/dashboard exec knip"
```

`pnpm -C apps/dashboard` changes cwd to `apps/dashboard/` before running the binary. knip auto-discovers `apps/dashboard/knip.json` from the new cwd.

### 3.2 Mirrors Phase 106 CI fix

Phase 106 changed the CI workflow line from `pnpm exec knip` to `pnpm -C apps/dashboard exec knip`. This phase applies the same change to the root `package.json` script, so:

| Invocation | Before | After |
|------------|--------|-------|
| CI: `pnpm exec knip` (workflow) | 48 false-positives | fixed in Phase 106 |
| Local: `pnpm knip` from root | 48 false-positives | **fixed in Phase 109** |

## 4. Verification

After applying the fix:

```bash
cd /home/ailearn/projects/LingWen
pnpm knip --reporter=compact 2>&1 | tail -5
echo "Exit: $?"
```

**Expected**: empty output, exit code 0.

### 4.1 Sanity checks

- `pnpm -C apps/dashboard exec vitest run`: 1545 passed (unchanged)
- `pnpm -C apps/dashboard run build`: succeeds (unchanged)
- `git show HEAD:.github/workflows/dashboard-frontend-ci.yml | grep -A1 "Run knip"`: still shows `pnpm -C apps/dashboard exec knip` (Phase 106 unchanged)

### 4.2 Regression risk

Minimal. The change is purely the command line; no config or behavior changes for knip itself. Worst case: the new command exits non-zero for a new reason that the old command didn't surface — but that's unlikely given the command is exactly what CI uses successfully.

## 5. Risk & mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Other workflows or scripts invoke `pnpm knip` (root) and rely on the old behavior | Very low | Those callers see different output (clean vs 48 false-positives) | Search repo for `pnpm knip` references; verify none rely on specific output format |
| CI invocation changes (root script used in CI?) | Low | CI breakage | Phase 106 already fixed CI independently with `pnpm -C apps/dashboard exec knip`; root script is for local dev only |
| `pnpm -C` not supported in some pnpm version | Very low | Local devs on old pnpm versions break | Phase 99.1 already pinned `packageManager: pnpm@9.0.0`; `-C` is supported since pnpm 7+ |

## 6. Rollback

If the fix breaks local dev:

```bash
git revert <sha>
```

The root script reverts to `pnpm exec knip --config apps/dashboard/knip.json` (Phase 102.1 delegation). Same false-positives return.

## 7. Output

- 1 atomic commit: `fix(build): make root pnpm knip cwd-safe (Phase 109)`
- 1 line changed in `package.json` (root)
- 0 files added
- 0 files deleted

## 8. Commit message template

```text
fix(build): make root pnpm knip cwd-safe (Phase 109)

Phase 109 — root package.json#scripts.knip was 'pnpm exec knip
--config apps/dashboard/knip.json'. The --config flag is correct but
insufficient: knip 6.32.2 resolves 'ignore' paths relative to the
config file's containing directory, but reports 'Unused' entries
relative to invocation cwd. When invoked from repo root, the
comparison fails → 48 false-positive unused entries.

Phase 106 fixed this in CI by changing the workflow step to
'pnpm -C apps/dashboard exec knip'. This phase applies the same
fix to the root script so 'pnpm knip' from root also produces
clean output.

Verification: 'pnpm knip' (root) → exit 0, no output.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

## 9. Why not the alternatives

### 9.1 Why not "rewrite root script to also fix --config behavior"

The `--config` flag IS correct — knip loads the right config file. The bug is in path resolution after loading. There's no flag to fix this; the only fix is cwd.

### 9.2 Why not "use `cd apps/dashboard && ...` instead of `pnpm -C`"

- `pnpm -C` is the modern, idiomatic pnpm way (Phase 99.1 already standardized on it)
- `cd` requires shell evaluation (`cd apps/dashboard && pnpm exec knip`); more fragile if pnpm ever changes how it parses script bodies
- `pnpm -C` is exactly what Phase 106 used for CI; symmetry reduces cognitive load

### 9.3 Why not "leave as-is and tell devs to use `pnpm -C ...`"

- Surprises devs who follow CLAUDE.md / handoff / docs that say `pnpm knip` works from root
- Drift between local dev experience and CI behavior
- One-line fix is cheaper than ongoing documentation overhead

## 10. Future phases (out of scope)

- **Phase 110**: Audit root `package.json` for other scripts that might suffer from similar cwd-related issues (none expected — other scripts use `pnpm -r --filter ...` which handles workspace iteration)
- **Phase 111**: Consider whether `pnpm -C apps/dashboard exec knip` is the canonical knip invocation everywhere — could centralize as a `tooling/run-knip.sh` helper script

---

**Next step**: Phase 109 plan → user review → execute.