# Phase 91 Implementation Plan — Orphan Fetch Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete orphan `fetchCreatorFactoryMergePresetConflicts` function from 3 files (production + test). Same pattern as Phase 85.

**Architecture:** 3 file edits, ~14 line deletions. 1 atomic commit.

**Tech Stack:** JavaScript/TypeScript, Edit tool, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase91-orphan-fetch-cleanup-design.md` (commit `91e14e40`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/src/api/mergePreset.js` | **Modify** (delete function definition ~5 lines) |
| `apps/dashboard/src/api/index.js` | **Modify** (delete re-export 1 line) |
| `apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts` | **Modify** (delete import + test case) |

**Total**: 3 files modified, 1 atomic commit.

---

## Task 1: Pre-flight verify

**Files:** None (verification only)

- [ ] **Step 1.1: Verify 0 other consumers**

```bash
cd /home/ailearn/projects/LingWen
grep -rn "fetchCreatorFactoryMergePresetConflicts" \
  apps/dashboard/src apps/dashboard/tests --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null \
  | grep -vE "(mergePreset\.js:|index\.js:|api-creator-merge-preset\.spec\.ts:)"
```

Expected: Empty output (no other consumers).

---

## Task 2: Edit mergePreset.js

**Files:**
- Modify: `apps/dashboard/src/api/mergePreset.js`

- [ ] **Step 2.1: Read function definition (around line 83)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
sed -n '80,90p' src/api/mergePreset.js
```

- [ ] **Step 2.2: Delete function definition**

Use Edit tool:
- **old_string**: full function block (signature + body + closing brace)
- **new_string**: (empty)

If 5-line function, just delete all 5 lines. If 6+ lines (with blank line separators), be careful to delete only the function block.

- [ ] **Step 2.3: Verify file syntax**

```bash
node -c /home/ailearn/projects/LingWen/apps/dashboard/src/api/mergePreset.js && echo "syntax OK"
```

---

## Task 3: Edit api/index.js

**Files:**
- Modify: `apps/dashboard/src/api/index.js`

- [ ] **Step 3.1: Read re-export block (around line 150-155)**

```bash
sed -n '148,158p' /home/ailearn/projects/LingWen/apps/dashboard/src/api/index.js
```

- [ ] **Step 3.2: Delete re-export entry**

Use Edit tool:
- **old_string**: `  fetchCreatorFactoryMergePresetConflicts,\n`
- **new_string**: (empty)

- [ ] **Step 3.3: Verify file syntax**

```bash
node -c /home/ailearn/projects/LingWen/apps/dashboard/src/api/index.js && echo "syntax OK"
```

---

## Task 4: Edit test file

**Files:**
- Modify: `apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts`

- [ ] **Step 4.1: Read import block (around line 15-25)**

```bash
sed -n '14,30p' /home/ailearn/projects/LingWen/apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts
```

- [ ] **Step 4.2: Delete import entry in vi.mock factory**

Use Edit tool:
- **old_string**: `      fetchCreatorFactoryMergePresetConflicts: (...args: unknown[]) => settingsMocks.fetchCreatorFactoryMergePresetConflicts(...args),\n`
- **new_string**: (empty)

- [ ] **Step 4.3: Read test case (around line 160-170)**

```bash
sed -n '160,175p' /home/ailearn/projects/LingWen/apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts
```

- [ ] **Step 4.4: Delete test case block**

Use Edit tool. Delete the complete `it('fetchCreatorFactoryMergePresetConflicts ...', async () => { ... });` block (~7 lines).

---

## Task 5: Final verifications

**Files:** None (verification only)

- [ ] **Step 5.1: grep — 0 hits**

```bash
cd /home/ailearn/projects/LingWen
grep -rn "fetchCreatorFactoryMergePresetConflicts" \
  apps/dashboard/src apps/dashboard/tests --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```

Expected: `0`

- [ ] **Step 5.2: pnpm test**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -5
```

Expected: `Tests  1543 passed (1543)` (was 1546, -3 deleted test cases)

- [ ] **Step 5.3: vue-tsc**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
```

Expected: 0 errors

- [ ] **Step 5.4: build**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```

Expected: `✓ built in <time>`

- [ ] **Step 5.5: git diff stat**

```bash
cd /home/ailearn/projects/LingWen && git diff --stat
```

Expected: 3 files modified, negative line counts.

---

## Task 6: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 6.1: Stage 3 files**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/mergePreset.js \
        apps/dashboard/src/api/index.js \
        apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts
```

- [ ] **Step 6.2: Verify staged**

```bash
git status -s
```

Expected: 3 modified files.

- [ ] **Step 6.3: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): delete orphan fetchCreatorFactoryMergePresetConflicts (Phase 91)" \
    -m "Phase 91 orphan fetch cleanup (per Phase 90 final-state doc):

Delete fetchCreatorFactoryMergePresetConflicts — only consumers were:
- mergePreset.js:83 (function definition)
- api/index.js:152 (re-export)
- api-creator-merge-preset.spec.ts:19 + 163-169 (test case + mock)

Removed from 3 files:
- mergePreset.js: function definition (~5 lines)
- api/index.js: re-export entry (1 line)
- api-creator-merge-preset.spec.ts: import (1 line) + test case (7 lines)

Same pattern as Phase 85. Total: ~14 lines deleted across 3 files. No behavior change.

测试基线: 1546 → 1543 (-3 deleted test cases)."
```

- [ ] **Step 6.4: Verify commit**

```bash
git show --stat HEAD
```

Expected: 3 files changed.

- [ ] **Step 6.5: Final log**

```bash
git log --oneline -3
```

---

## Self-Review

**Spec coverage**:
- Spec §4.1 (mergePreset.js) → Task 2
- Spec §4.2 (api/index.js) → Task 3
- Spec §4.3 (test file) → Task 4
- Spec §5 (verification) → Task 5
- Spec §7 (commit) → Task 6

**Placeholder scan**:
- All Edit patterns have actual code from spec §4
- All grep commands have expected output

**Type consistency**:
- Same pattern as Phase 85 (proven workflow)
- Test count math verified (-3 from 1546 = 1543)

**Risks covered**:
- Step 1.1 verifies no other consumers
- Step 5.1-5.5 catches regressions

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/api/mergePreset.js \
              apps/dashboard/src/api/index.js \
              apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts
```
