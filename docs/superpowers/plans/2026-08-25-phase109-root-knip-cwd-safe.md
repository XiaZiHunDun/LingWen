# Phase 109 — Implementation Plan

> **Phase**: 109 — Make root `pnpm knip` cwd-safe
> **Spec**: `docs/superpowers/specs/2026-08-25-phase109-root-knip-cwd-safe-design.md`
> **Date**: 2026-08-25
> **Author**: 主控调度

---

## 1. Pre-flight checks

```bash
cd /home/ailearn/projects/LingWen

# Verify current root knip script is the broken version
grep '"knip":' package.json
# Expected: "knip": "pnpm exec knip --config apps/dashboard/knip.json"

# Search for any other pnpm knip invocations in the repo
grep -rn "pnpm knip\|pnpm exec knip" .github/ apps/ packages/ tooling/ scripts/ 2>/dev/null | grep -v node_modules | head -10
# Expected: only .github/workflows/dashboard-frontend-ci.yml (already fixed Phase 106)
```

## 2. Implementation steps

### Step 1 — Edit root package.json

Use Edit tool to replace the `knip` script line:

```diff
-    "knip": "pnpm exec knip --config apps/dashboard/knip.json"
+    "knip": "pnpm -C apps/dashboard exec knip"
```

**File**: `package.json` (root)
**Change**: 1 line
**No other file changes**

### Step 2 — Verify locally

```bash
cd /home/ailearn/projects/LingWen
pnpm knip --reporter=compact 2>&1 | tail -5
echo "Exit: $?"
```

**Expected**: empty output, exit code 0.

If output shows ANY "Unused" or "Unlisted" headers, STOP — investigate.

### Step 3 — Sanity: CI step still works

The CI workflow (Phase 106) uses `pnpm -C apps/dashboard exec knip` directly. It does NOT depend on the root script. Verify by checking the committed CI file:

```bash
git show HEAD:.github/workflows/dashboard-frontend-ci.yml | grep -A1 "Run knip"
# Expected: shows `run: pnpm -C apps/dashboard exec knip`
```

This is informational only — no CI changes are needed.

### Step 4 — Test baseline verification

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vitest run 2>&1 | tail -3
# Expected: Test Files 189 passed (189) | Tests 1545 passed (1545)
```

(No source changes → 1545 should still hold.)

### Step 5 — Diff review

```bash
cd /home/ailearn/projects/LingWen
git diff package.json
# Expected: ONLY the `pnpm exec knip --config apps/dashboard/knip.json` → `pnpm -C apps/dashboard exec knip` change
```

If diff shows more than that change, STOP and investigate.

### Step 6 — Stage + commit

```bash
cd /home/ailearn/projects/LingWen
git add package.json
git add docs/superpowers/specs/2026-08-25-phase109-root-knip-cwd-safe-design.md
git add docs/superpowers/plans/2026-08-25-phase109-root-knip-cwd-safe.md
git commit -m "fix(build): make root pnpm knip cwd-safe (Phase 109)" \
           -m "Phase 109 — root package.json#scripts.knip was 'pnpm exec knip
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

Includes:
- docs/superpowers/specs/2026-08-25-phase109-root-knip-cwd-safe-design.md
- docs/superpowers/plans/2026-08-25-phase109-root-knip-cwd-safe.md

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

## 3. Final verification

```bash
cd /home/ailearn/projects/LingWen

git log --oneline -4
# Expected: 
#   Phase 109 commit (top)
#   Phase 106 housekeeping commit (a8af4669)
#   audit commit (dc824871)
#   Phase 106 CI fix commit (3a607819)
#   handoff commit (9ea11010)

# Verify the fix landed
git show HEAD:package.json | grep '"knip":'
# Expected: "knip": "pnpm -C apps/dashboard exec knip"

# Sanity: knip clean
pnpm knip --reporter=compact 2>&1 | tail -3
# Expected: empty, exit 0
```

## 4. Push decision

After local verification, push:

```bash
git push origin master
```

## 5. Estimated time

- Edit: 30 seconds
- Verify: 60 seconds (knip + vitest)
- Commit: 15 seconds
- Push: 5 seconds
- **Total**: ~2 minutes

## 6. Rollback

If Phase 109 commit breaks local dev:

```bash
git revert HEAD
git push origin master
```

Root script reverts to Phase 102.1 delegation (broken from root, works only with explicit `--config` and correct cwd).

---

**Status**: Plan ready, currently being executed.