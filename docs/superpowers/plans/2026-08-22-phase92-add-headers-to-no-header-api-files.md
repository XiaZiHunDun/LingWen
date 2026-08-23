# Phase 92 Implementation Plan — Add Headers to 10 No-Header API Files

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `(N funcs)` line to 9 files + full header to 1 file (`connectivity.js`). 1 atomic commit.

**Architecture:** Docs only. No code change. No test change.

**Tech Stack:** JavaScript JSDoc, Edit tool, grep.

**Reference spec**: `docs/superpowers/specs/2026-08-22-phase92-add-headers-to-no-header-api-files-design.md` (commit `e283c3a8`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/src/api/budgets.js` | **Modify** (add `(4 funcs)` line) |
| `apps/dashboard/src/api/connectivity.js` | **Modify** (add new full header) |
| `apps/dashboard/src/api/core.js` | **Modify** (add `(2 funcs)` line) |
| `apps/dashboard/src/api/creator.js` | **Modify** (add `(2 funcs, re-export only)` line) |
| `apps/dashboard/src/api/cvg.js` | **Modify** (add `(14 funcs)` line) |
| `apps/dashboard/src/api/decisions.js` | **Modify** (add `(5 funcs)` line) |
| `apps/dashboard/src/api/health.js` | **Modify** (add `(6 funcs)` line) |
| `apps/dashboard/src/api/index.js` | **Modify** (add `(0 funcs, re-export only)` line) |
| `apps/dashboard/src/api/memory.js` | **Modify** (add `(3 funcs)` line) |
| `apps/dashboard/src/api/studio.js` | **Modify** (add `(12 funcs)` line) |
| `apps/dashboard/src/api/workflows.js` | **Modify** (add `(5 funcs)` line) |

**Total**: 10 files modified, 1 atomic commit.

---

## Task 1: Pre-flight verify counts

**Files:** None (verification only)

- [ ] **Step 1.1: Verify all 10 file export counts match spec table**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
for f in budgets connectivity core creator cvg decisions health index memory studio workflows; do
  COUNT=$(grep -c "^export async function\|^export function" src/api/$f.js)
  echo "$f: $COUNT"
done
```

Expected output matches spec §4.1 table (4/3/2/2/14/5/6/0/3/12/5).

---

## Task 2: Edit 9 files with existing header (add `(N funcs)` line)

**Files:**
- Modify: 9 files (budgets, core, creator, cvg, decisions, health, index, memory, studio, workflows — wait, that's 10. connectivity is the new-header file. Let me re-count.)

Per spec §4.1, 9 files with existing header:
- budgets.js (4), core.js (2), creator.js (2), cvg.js (14), decisions.js (5), health.js (6), index.js (0), memory.js (3), studio.js (12), workflows.js (5)

That's 10 files with existing header. connectivity.js is the 11th file (no header).

- [ ] **Step 2.1: Edit budgets.js (add `* (4 funcs)` after header)**

```bash
head -5 /home/ailearn/projects/LingWen/apps/dashboard/src/api/budgets.js
```

Use Edit tool. Add line after current header closing `*/`.

- [ ] **Step 2.2: Edit core.js**

```bash
head -7 /home/ailearn/projects/LingWen/apps/dashboard/src/api/core.js
```

Use Edit tool. Add line after `* @module api/core` (before closing `*/`).

- [ ] **Step 2.3: Edit creator.js**

Use Edit tool. Add `(2 funcs, re-export only)` after current header.

- [ ] **Step 2.4: Edit cvg.js**

Use Edit tool. Add `(14 funcs)` after current header.

- [ ] **Step 2.5: Edit decisions.js**

Use Edit tool. Add `(5 funcs)` after current header.

- [ ] **Step 2.6: Edit health.js**

Use Edit tool. Add `(6 funcs)` after current header.

- [ ] **Step 2.7: Edit index.js**

Use Edit tool. Add `(0 funcs, re-export only)` after current header.

- [ ] **Step 2.8: Edit memory.js**

Use Edit tool. Add `(3 funcs)` after current header.

- [ ] **Step 2.9: Edit studio.js**

Use Edit tool. Add `(12 funcs)` after current header.

- [ ] **Step 2.10: Edit workflows.js**

Use Edit tool. Add `(5 funcs)` after current header.

---

## Task 3: Edit connectivity.js (add new full header)

**Files:**
- Modify: `apps/dashboard/src/api/connectivity.js`

- [ ] **Step 3.1: Read current state**

```bash
head -10 /home/ailearn/projects/LingWen/apps/dashboard/src/api/connectivity.js
```

- [ ] **Step 3.2: Add new header at top**

Use Edit tool. Add at the very top of file (before `import { ref } from 'vue';`):

```js
/**
 * Connectivity API
 * (3 funcs)
 */

```

(Original import statement follows.)

---

## Task 4: Final verifications

**Files:** None (verification only)

- [ ] **Step 4.1: All 10 files have `(N funcs)` line**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard/src/api
for f in budgets connectivity core creator cvg decisions health index memory studio workflows; do
  if grep -q "([0-9]* funcs)" "$f.js"; then
    echo "OK $f"
  else
    echo "MISSING $f"
  fi
done
```

Expected: All 11 lines (1 per file).

- [ ] **Step 4.2: Counts still match**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
for f in budgets connectivity core creator cvg decisions health index memory studio workflows; do
  COUNT=$(grep -c "^export async function\|^export function" src/api/$f.js)
  echo "$f: $COUNT"
done
```
Expected: 4/3/2/2/14/5/6/0/3/12/5 (matches spec).

- [ ] **Step 4.3: pnpm test**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -5
```
Expected: `Tests  1545 passed (1545)` (unchanged)

- [ ] **Step 4.4: vue-tsc**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
```
Expected: 0 errors

- [ ] **Step 4.5: build**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```
Expected: `✓ built in <time>`

- [ ] **Step 4.6: git diff stat**

```bash
cd /home/ailearn/projects/LingWen && git diff --stat
```
Expected: 10 files modified (small line counts).

---

## Task 5: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 5.1: Stage 10 files**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/budgets.js \
        apps/dashboard/src/api/connectivity.js \
        apps/dashboard/src/api/core.js \
        apps/dashboard/src/api/creator.js \
        apps/dashboard/src/api/cvg.js \
        apps/dashboard/src/api/decisions.js \
        apps/dashboard/src/api/health.js \
        apps/dashboard/src/api/index.js \
        apps/dashboard/src/api/memory.js \
        apps/dashboard/src/api/studio.js \
        apps/dashboard/src/api/workflows.js
```

- [ ] **Step 5.2: Verify staged**

```bash
git status -s
```
Expected: 10 modified files.

- [ ] **Step 5.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(api): add function counts to 10 api file headers (Phase 92)" \
    -m "Phase 92 api header housekeeping (per Phase 90 follow-up):

Added '(N funcs)' line to 9 files + full header to connectivity.js.

10 files updated:
- budgets.js: (4 funcs)
- connectivity.js: (3 funcs) [new header]
- core.js: (2 funcs)
- creator.js: (2 funcs, re-export only)
- cvg.js: (14 funcs)
- decisions.js: (5 funcs)
- health.js: (6 funcs)
- index.js: (0 funcs, re-export only)
- memory.js: (3 funcs)
- studio.js: (12 funcs)
- workflows.js: (5 funcs)

Total: 10 files modified. No body code changes.
Aligns with Phase 90 audit + Phase 80/86/91 header conventions.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 5.4: Verify commit**

```bash
git show --stat HEAD
```
Expected: 10 files changed.

- [ ] **Step 5.5: Final log**

```bash
git log --oneline -3
```

---

## Self-Review

**Spec coverage**:
- Spec §4.1 (9 files with existing header) → Task 2 (Steps 2.1-2.10)
- Spec §4.2 (1 file new header) → Task 3
- Spec §5 (verification) → Task 4
- Spec §7 (commit) → Task 5

**Placeholder scan**:
- All Edit patterns reference actual file structure (Step 1 verifies counts)
- All grep commands have expected output

**Type consistency**:
- Header format consistent across all 10 files
- `(N funcs)` line matches existing convention

**Risks covered**:
- Step 1.1 verifies all 10 counts before edit
- Step 4.1 verifies all 10 files have header after edit
- Step 4.2 re-verifies counts unchanged after edit

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/api/budgets.js \
              apps/dashboard/src/api/connectivity.js \
              apps/dashboard/src/api/core.js \
              apps/dashboard/src/api/creator.js \
              apps/dashboard/src/api/cvg.js \
              apps/dashboard/src/api/decisions.js \
              apps/dashboard/src/api/health.js \
              apps/dashboard/src/api/index.js \
              apps/dashboard/src/api/memory.js \
              apps/dashboard/src/api/studio.js \
              apps/dashboard/src/api/workflows.js
```
