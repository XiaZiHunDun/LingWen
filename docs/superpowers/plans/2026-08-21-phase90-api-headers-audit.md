# Phase 90 Implementation Plan — API Headers Audit (Verified State)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 1 final-state doc documenting Phase 90 api headers audit (verified state — no stale counts found).

**Architecture:** Docs only. 1 new file. 1 atomic commit.

**Tech Stack:** Markdown, Write tool, grep.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-verified-state-design.md` (commit `378afcb4`)

---

## File Structure

| File | Action |
|------|--------|
| `docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md` | **Create** |

**Total**: 1 file created, 1 atomic commit.

---

## Task 1: Create final-state doc

**Files:**
- Create: `docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md`

- [ ] **Step 1.1: Write final-state doc**

Use Write tool with content from spec §4 (Implementation section).

Content includes:
- Title: "Phase 90 — API Headers Audit Final State"
- Audit results table (6 files with headers, all correct)
- Files without header comments table (10 files, out of scope)
- Verification commands
- Conclusion (no stale counts found)
- Follow-up candidates

- [ ] **Step 1.2: Verify file created**

Run: `ls -la docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md`
Expected: file exists.

---

## Task 2: Final verifications

**Files:** None (verification only)

- [ ] **Step 2.1: git status — 1 new file**

Run: `cd /home/ailearn/projects/LingWen && git status -s`
Expected: `?? docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md`

- [ ] **Step 2.2: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git status --short --branch`
Expected: `## master...origin/master [ahead N]` + 1 untracked doc

- [ ] **Step 2.3: pnpm test sanity**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -3`
Expected: `Tests  1546 passed (1546)` (unchanged)

- [ ] **Step 2.4: vue-tsc sanity**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors

---

## Task 3: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 3.1: Stage doc**

Run: `git add docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md`

- [ ] **Step 3.2: Verify staged**

Run: `git status -s`
Expected: `A  docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md`

- [ ] **Step 3.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 90 — api headers audit final state" \
    -m "Phase 90 audit complete — all 6 api files with header comments have correct counts.

| File | Listed | Actual | Status |
|------|--------|--------|--------|
| agent.js | 5 | 5 | OK |
| onboarding.js | 19 | 19 | OK |
| publish.js | 9 | 9 | OK |
| templateApproval.js | 15 | 15 | OK |
| volumePlan.js | 7 | 7 | OK |
| volumeTemplate.js | 15 | 15 | OK |

10 files without header comments (out of Phase 90 scope):
budgets.js, connectivity.js, core.js, creator.js, cvg.js,
decisions.js, health.js, index.js, memory.js, studio.js, workflows.js

No code change. No stale counts found.

测试基线不变: 1546 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 3.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed.

- [ ] **Step 3.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §4 (Implementation) → Task 1
- Spec §5 (Verification) → Task 2
- Spec §7 (Commit) → Task 3

**Placeholder scan**:
- Step 1.1 has actual content (from spec §4)
- Step 2.x commands have expected output

**Risks covered**:
- Step 2.1 verifies only 1 new file (no accidental edits to other files)
- Step 2.3 confirms baseline unchanged

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout docs/superpowers/specs/2026-08-21-phase90-api-headers-audit-final-state.md
```
