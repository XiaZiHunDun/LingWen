# Phase 86 Implementation Plan — Stale Header Comment Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix stale header comment in `mergePreset.js:7` (MergePreset (25) → (22), remove "+ Graph"). 1 atomic commit. docs-only.

**Architecture:** 1 line edit. No code change. No test change.

**Tech Stack:** Markdown, Edit tool, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase86-stale-header-fix-design.md` (commit `6402d2ec`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/src/api/mergePreset.js` | **Modify** (line 7 only) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Verify current state

**Files:** None (verification only)

- [ ] **Step 1.1: Read current line 7**

Run: `sed -n '7p' apps/dashboard/src/api/mergePreset.js`
Expected: ` * - MergePreset (25): CRUD + Factory + Conflicts + Fixes + Graph + Toposort + Import/Export + Preflight + Diff`

- [ ] **Step 1.2: Confirm actual MergePreset function count = 22**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -c "^export async function" apps/dashboard/src/api/mergePreset.js
echo "(total exports)"
grep -A 2 "^// --- SettingsDocs" apps/dashboard/src/api/mergePreset.js | head -3
```

Expected: total exports = 36, of which 22 in MergePreset (per Phase 85 review).

---

## Task 2: Edit mergePreset.js line 7

**Files:**
- Modify: `apps/dashboard/src/api/mergePreset.js`

- [ ] **Step 2.1: Apply Edit**

Use Edit tool:
- **old_string**: ` * - MergePreset (25): CRUD + Factory + Conflicts + Fixes + Graph + Toposort + Import/Export + Preflight + Diff`
- **new_string**: ` * - MergePreset (22): CRUD + Factory + Conflicts + Fixes + Toposort + Import/Export + Preflight + Diff`

- [ ] **Step 2.2: Verify edit**

Run: `sed -n '7p' apps/dashboard/src/api/mergePreset.js`
Expected: ` * - MergePreset (22): CRUD + Factory + Conflicts + Fixes + Toposort + Import/Export + Preflight + Diff`

---

## Task 3: Final verifications

**Files:** None (verification only)

- [ ] **Step 3.1: grep — new count present**

Run: `grep "MergePreset (22)" apps/dashboard/src/api/mergePreset.js | wc -l`
Expected: `1`

- [ ] **Step 3.2: grep — old count absent**

Run: `grep "MergePreset (25)" apps/dashboard/src/api/mergePreset.js | wc -l`
Expected: `0`

- [ ] **Step 3.3: pnpm test**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1546 passed (1546)` (unchanged)

- [ ] **Step 3.4: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors

- [ ] **Step 3.5: build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>`

- [ ] **Step 3.6: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat`
Expected: 1 file modified.

---

## Task 4: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 4.1: Stage mergePreset.js**

Run: `git add apps/dashboard/src/api/mergePreset.js`

- [ ] **Step 4.2: Verify staged**

Run: `git status -s`
Expected: 1 modified file.

- [ ] **Step 4.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(api): fix stale header comment count in mergePreset.js (Phase 86)" \
    -m "Phase 86 docs-only fix (per Phase 85 review MEDIUM):

mergePreset.js:7 header comment update:
- MergePreset (25) → MergePreset (22)
- Remove '+ Graph' from sub-function list

Per Phase 85 implementer report:
- 22 actual MergePreset functions (was 25)
- 0 Graph functions remaining (fetchCreatorMergePresetGraph deleted)

Phase 85 deletion count: 36 export async function total in mergePreset.js
- MergePreset: 22 (CRUD + Factory + Conflicts + Fixes + Toposort + Import/Export + Preflight + Diff)
- SettingsDocs: 7
- DiffCollab: 2
- Wizard: 2
- Preferences: 3

测试基线不变: 1546 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 4.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 1 file changed.

- [ ] **Step 4.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §4 (line 7 change) → Task 2
- Spec §5 (verification) → Task 3
- Spec §7 (1 atomic commit) → Task 4

**Placeholder scan**:
- All Edit patterns have actual code from spec §4
- All grep commands have expected output

**Type consistency**:
- Single line comment change, no syntax risk

**Risks covered**:
- Step 1.2 verifies count is actually 22 (catches wrong-count spec assumption)
- Step 3.1-3.2 confirm both old/new counts (catches accidental duplication)

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/api/mergePreset.js
```
