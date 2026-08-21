# Phase 85 Implementation Plan — Orphaned Fetch Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete 3 dead fetches (`fetchCreatorMergePresetGraph`, `fetchCreatorMergePresetConflicts`, `fetchCreatorMergePresetConflictFixes`) from 3 files. Per Phase 84 code review MEDIUM.

**Architecture:** Surgical deletions only. 1 atomic commit (3 files logically related).

**Tech Stack:** JavaScript/TypeScript, Edit tool, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase85-orphaned-fetch-cleanup-design.md` (commit `574d082d`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts` | **Modify** (delete 3 imports from `api/index.js`) |
| `apps/dashboard/src/api/index.js` | **Modify** (delete 3 re-exports from `mergePreset.js`) |
| `apps/dashboard/src/api/mergePreset.js` | **Modify** (delete 3 function definitions) |

**Total**: 3 files modified, 1 atomic commit.

---

## Task 1: Pre-flight verify

**Files:** None (verification only)

- [ ] **Step 1.1: Verify 0 other consumers**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -rn "fetchCreatorMergePresetGraph\|fetchCreatorMergePresetConflicts\|fetchCreatorMergePresetConflictFixes" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null \
  | grep -vE "(useMergePresets\.ts:|api/index\.js:|api/mergePreset\.js:)"
```

Expected: **Empty output** (no other consumers).

---

## Task 2: Edit useMergePresets.ts

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`

- [ ] **Step 2.1: Read import block (around lines 15-30)**

Run: `sed -n '14,32p' apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`
Confirm exact text for 3 import lines (lines 19-21).

- [ ] **Step 2.2: Delete 3 imports**

Use Edit tool:
- **old_string**: (3 lines + trailing newline):
  ```
    fetchCreatorMergePresetGraph,
    fetchCreatorMergePresetConflicts,
    fetchCreatorMergePresetConflictFixes,
  ```
- **new_string**: (empty)

Note: Lines 22+ (`applyCreatorMergePresetConflictFix`, `applyAllCreatorMergePresetConflictFixes`, etc.) are LIVE refs — must NOT be deleted.

- [ ] **Step 2.3: Verify file syntax**

Run: `node -c apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts && echo "syntax OK"`

---

## Task 3: Edit api/index.js

**Files:**
- Modify: `apps/dashboard/src/api/index.js`

- [ ] **Step 3.1: Read re-export block (around lines 140-155)**

Run: `sed -n '140,155p' apps/dashboard/src/api/index.js`
Confirm exact text for 3 re-export lines (146-148).

- [ ] **Step 3.2: Delete 3 re-exports**

Use Edit tool:
- **old_string**:
  ```
    fetchCreatorMergePresetGraph,
    fetchCreatorMergePresetConflicts,
    fetchCreatorMergePresetConflictFixes,
  ```
- **new_string**: (empty)

- [ ] **Step 3.3: Verify file syntax**

Run: `node -c apps/dashboard/src/api/index.js && echo "syntax OK"`

---

## Task 4: Edit api/mergePreset.js

**Files:**
- Modify: `apps/dashboard/src/api/mergePreset.js`

- [ ] **Step 4.1: Read function definitions (around lines 115-150)**

Run: `sed -n '115,150p' apps/dashboard/src/api/mergePreset.js`
Confirm exact text for 3 function definitions (lines 120, 124, 141).

- [ ] **Step 4.2: Delete function `fetchCreatorMergePresetConflicts` (line 120)**

Read the function block (likely 5-10 lines including body + closing brace). Use Edit tool:
- **old_string**: full function definition (`export async function fetchCreatorMergePresetConflicts() { ... }`)
- **new_string**: (empty)

- [ ] **Step 4.3: Delete function `fetchCreatorMergePresetConflictFixes` (line 124)**

Same pattern as 4.2.

- [ ] **Step 4.4: Delete function `fetchCreatorMergePresetGraph` (line 141)**

Same pattern. NOTE: After deleting earlier functions, line numbers may shift. Re-grep to find the function.

- [ ] **Step 4.5: Verify file syntax**

Run: `node -c apps/dashboard/src/api/mergePreset.js && echo "syntax OK"`

---

## Task 5: Final verifications

**Files:** None (verification only)

- [ ] **Step 5.1: grep verification — all 3 fetches**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -rn "fetchCreatorMergePresetGraph\|fetchCreatorMergePresetConflicts\|fetchCreatorMergePresetConflictFixes" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```
Expected: `0`

- [ ] **Step 5.2: pnpm test**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)` (unchanged)

- [ ] **Step 5.3: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors

- [ ] **Step 5.4: build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>`

- [ ] **Step 5.5: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat`
Expected: 3 files modified with negative line counts.

---

## Task 6: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 6.1: Stage 3 files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts \
        apps/dashboard/src/api/index.js \
        apps/dashboard/src/api/mergePreset.js
```

- [ ] **Step 6.2: Verify staged**

Run: `git status -s`
Expected: 3 modified files.

- [ ] **Step 6.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): delete 3 orphaned mergePreset fetch functions (Phase 85)" \
    -m "Phase 85 dead code sweep (per Phase 84 review MEDIUM):

Delete 3 fetch functions (only consumers were Phase 84-deleted refs):
- fetchCreatorMergePresetGraph
- fetchCreatorMergePresetConflicts
- fetchCreatorMergePresetConflictFixes

Removed from:
- useMergePresets.ts (submodule imports, lines 19-21)
- api/index.js (re-exports, lines 146-148)
- api/mergePreset.js (function definitions, lines 120/124/141)

Total: ~15-20 lines deleted across 3 files. No behavior change.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 6.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 3 files changed, negative line counts.

- [ ] **Step 6.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §4.1 (submodule deletions) → Task 2
- Spec §4.2 (api/index.js deletions) → Task 3
- Spec §4.3 (api/mergePreset.js deletions) → Task 4
- Spec §5 (verification) → Task 5
- Spec §7 (1 atomic commit) → Task 6

**Placeholder scan**:
- All Edit patterns have actual code from spec §4
- All grep commands have expected output

**Type consistency**:
- Same function signatures preserved for kept functions
- ESM imports/exports syntax preserved

**Risks covered**:
- Step 1.1 verifies no other consumers
- Step 5.3 catches vue-tsc errors post-delete
- Step 5.4 catches build errors
- Step 5.1 confirms 0 hits post-delete

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts \
              apps/dashboard/src/api/index.js \
              apps/dashboard/src/api/mergePreset.js
```
