# Phase 106 — Implementation Plan

> **Phase**: 106 — Fix CI knip gate invocation
> **Spec**: `docs/superpowers/specs/2026-08-25-phase106-fix-ci-knip-gate-design.md`
> **Date**: 2026-08-25
> **Author**: 主控调度
> **Note**: Initial Option A (`pnpm knip`) was verified to NOT solve the bug. Refined fix is `pnpm -C apps/dashboard exec knip`.

---

## 1. Pre-flight checks

```bash
cd /home/ailearn/projects/LingWen
git status --porcelain | wc -l
# Expected: 16 (12 JSON + 1 audit doc + 1 spec + 1 plan + 1 .phase76-baseline/)
# These will be committed in separate commits per Task 8 plan
```

Verify the CI step is the exact line we expect to change:

```bash
grep -n -B1 -A1 "pnpm exec knip" .github/workflows/dashboard-frontend-ci.yml
# Expected: line 52 shows `run: pnpm exec knip`
```

## 2. Implementation steps

### Step 1 — Edit CI workflow

Use Edit tool to replace the exact `run:` line:

```diff
       - name: Run knip (dead-export detection)
-        run: pnpm exec knip
+        run: pnpm -C apps/dashboard exec knip
```

**File**: `.github/workflows/dashboard-frontend-ci.yml`
**Change**: 1 line
**No other file changes**

### Step 2 — Verify locally

```bash
cd /home/ailearn/projects/LingWen
pnpm -C apps/dashboard exec knip --reporter=compact 2>&1 | tail -5
```

**Expected output**: empty (exit 0; no `Unused`/`Unlisted`/`Duplicate` headers).

If output shows ANY of those headers, STOP — investigation needed.

### Step 3 — Test baseline verification (per handoff convention)

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm exec vitest run 2>&1 | tail -3
# Expected: Test Files 189 passed (189) | Tests 1545 passed (1545)
```

(No source changes → 1545 should still hold; this is a safety net.)

### Step 4 — Diff review

```bash
cd /home/ailearn/projects/LingWen
git diff .github/workflows/dashboard-frontend-ci.yml
# Expected: ONLY the `pnpm exec knip` → `pnpm -C apps/dashboard exec knip` change
```

If diff shows more than that change, STOP and investigate.

### Step 5 — Stage + commit (Phase 106)

Commit the spec, plan, and CI fix together as a logical unit:

```bash
cd /home/ailearn/projects/LingWen
git add .github/workflows/dashboard-frontend-ci.yml
git add docs/superpowers/specs/2026-08-25-phase106-fix-ci-knip-gate-design.md
git add docs/superpowers/plans/2026-08-25-phase106-fix-ci-knip-gate.md
git commit -m "fix(ci): run knip from apps/dashboard cwd for proper path resolution (Phase 106)" \
           -m "Phase 106 — CI knip gate was invoking bare 'pnpm exec knip' from
workspace root. knip 6.32.2 resolves 'ignore' paths relative to the
config file's containing directory, but reports 'Unused' entries
relative to invocation cwd. When invoked from repo root, the
comparison fails → 48 false-positive unused entries, all listed in
apps/dashboard/knip.json#ignore.

Initial brainstorm-chosen fix was 'pnpm knip' (root delegation script).
Verified empirically this does NOT solve the bug — same false-positives.

Working fix: 'pnpm -C apps/dashboard exec knip' — pnpm -C changes cwd
to apps/dashboard/ before invoking knip. From there, knip auto-discovers
knip.json and resolves ignore paths correctly.

Verification: 'pnpm -C apps/dashboard exec knip' → exit 0, no output.

Includes:
- docs/superpowers/specs/2026-08-25-phase106-fix-ci-knip-gate-design.md
- docs/superpowers/plans/2026-08-25-phase106-fix-ci-knip-gate.md

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

## 3. Post-execution: commit the audit findings (separate commit)

Commit the Web Vitals audit output as a separate, independent commit:

```bash
cd /home/ailearn/projects/LingWen

# Add the audit doc + regenerated JSON files
git add docs/perf/playwright/*.json
git add docs/superpowers/audit/2026-08-25-post-knip-vitals-rebaseline.md

# DO NOT add .phase76-baseline/ — those are local-only reference backups

git commit -m "test(perf): Web Vitals re-baseline after Phase 100-105b (no regressions)" \
           -m "Phase 106 precursor — re-ran apps/dashboard/tests/e2e-smoke/web-vitals.spec.js
(4 routes × 3 runs × 5 metrics) against master post-knip-gate-closure.

Results: 4/4 routes × 5/5 metrics pass Web Rules targets.
Largest deltas vs Phase 76 baseline: +14.9% (still within noise).
No regressions detected. INP capture improved 7/12 → 9/12.

New artifacts:
- docs/perf/playwright/*.json (12 regenerated)
- docs/superpowers/audit/2026-08-25-post-knip-vitals-rebaseline.md

Test baseline unchanged: 1545 PASS, 0 type errors, 0 build errors."
```

### 3.1 Local backup handling

The `.phase76-baseline/` directory contains 12 backup JSONs. They're untracked and useful for future diff. Options:

- **(A) Keep local-only** (no .gitignore change): backups stay untracked but visible via `git status`
- **(B) Add to .gitignore**: clean status; remove from disk eventually
- **(D) Delete now**: minimal clutter; lose diff capability

**Recommendation: (A)** for this PR. Leave them as local-only references; future phase can decide.

## 4. Final verification

```bash
cd /home/ailearn/projects/LingWen

git log --oneline -3
# Expected: audit commit → Phase 106 commit

git log --stat -2
# Expected: 
#   Phase 106: 3 files (1 workflow + 1 spec + 1 plan)
#   audit: 13 files (12 JSON + 1 audit doc)

git show HEAD~1:.github/workflows/dashboard-frontend-ci.yml | grep -A1 "Run knip"
# Expected: shows `run: pnpm -C apps/dashboard exec knip`
```

## 5. Push decision

DO NOT push until:
- Both commits succeed locally
- Test baseline unchanged (1545 PASS)
- User confirms

Then:

```bash
git push origin master
```

## 6. Estimated time

- Edit: 30 seconds
- Verify: 60 seconds (knip + vitest)
- Commit (×2): 30 seconds
- Push: 5 seconds
- **Total**: ~2-3 minutes

## 7. Rollback

If Phase 106 commit breaks CI:

```bash
git revert HEAD  # or git revert <sha>
git push origin master
```

CI returns to broken state but functional. Next session investigates the actual failure mode.

---

**Status**: Plan written, currently being executed. Phase 106 fix applied locally + verified clean (exit 0). Spec/plan updated to reflect actual fix.