# Phase 93 Implementation Plan — Comprehensive API Orphan Audit (Delete `onApiError`)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete orphan `onApiError` function from `core.js`. 1 file change, ~5-7 line deletions. 1 atomic commit.

**Architecture:** Surgical deletion. No new code. No test change.

**Tech Stack:** JavaScript, Edit tool, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-23-phase93-comprehensive-api-orphan-audit-design.md` (commit `297eca2c`)

---

## File Structure

| File | Action |
|------|--------|
| `apps/dashboard/src/api/core.js` | **Modify** (delete `onApiError` function + references) |

**Total**: 1 file modified, 1 atomic commit.

---

## Task 1: Pre-flight verify

**Files:** None (verification only)

- [ ] **Step 1.1: Verify 0 consumers (excluding self file)**

```bash
cd /home/ailearn/projects/LingWen
grep -rn "\bonApiError\b" apps/dashboard/src apps/dashboard/tests \
  --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```

Expected: 0 hits (or only hits in `core.js` itself).

- [ ] **Step 1.2: Read current `onApiError` location**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
grep -n "onApiError" src/api/core.js
```

Note all line numbers (function def + any internal references).

---

## Task 2: Edit core.js

**Files:**
- Modify: `apps/dashboard/src/api/core.js`

- [ ] **Step 2.1: Read function definition + context**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
sed -n '1,15p' src/api/core.js
```

Get exact text of `onApiError` function and any internal references.

- [ ] **Step 2.2: Delete `onApiError` function definition**

Use Edit tool:
- **old_string**: full function block (signature + body + closing brace)
- **new_string**: (empty)

- [ ] **Step 2.3: Delete any internal reference**

If `onApiError` is referenced inside the `request` function (per `core.js` earlier read showed `markApiOnline()` call in request), check if `onApiError` is also called there. If so, delete that call too.

Use Edit tool:
- **old_string**: line(s) referencing `onApiError(`
- **new_string**: (empty)

- [ ] **Step 2.4: Verify file syntax**

```bash
node -c /home/ailearn/projects/LingWen/apps/dashboard/src/api/core.js && echo "syntax OK"
```

---

## Task 3: Final verifications

**Files:** None (verification only)

- [ ] **Step 3.1: grep — 0 hits overall**

```bash
cd /home/ailearn/projects/LingWen
grep -rn "\bonApiError\b" apps/dashboard/src apps/dashboard/tests \
  --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```

Expected: `0`

- [ ] **Step 3.2: pnpm test**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm test 2>&1 | tail -5
```

Expected: `Tests  1545 passed (1545)` (unchanged)

- [ ] **Step 3.3: vue-tsc**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
```

Expected: 0 errors

- [ ] **Step 3.4: build**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```

Expected: `✓ built in <time>`

- [ ] **Step 3.5: git diff stat**

```bash
cd /home/ailearn/projects/LingWen && git diff --stat apps/dashboard/src/api/core.js
```

Expected: 1 file changed, negative line count (~5-7).

---

## Task 4: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 4.1: Stage core.js**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/core.js
```

- [ ] **Step 4.2: Verify staged**

```bash
git status -s
```

Expected: 1 modified file.

- [ ] **Step 4.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): delete orphan onApiError (Phase 93)" \
    -m "Phase 93 comprehensive api orphan audit. Only 1 true orphan found:
- onApiError (core.js) — 0 consumers (not re-exported, no internal call site)

10 other candidates have test consumers (NOT orphans):
- markApiOnline/Offline (connectivity.js): internal core.js callers
- exportCreatorTemplateApprovalAudit (creator.js): tests
- 4 mergePreset.js functions: tests
- fetchCreatorFactoryVolumeTemplates: tests
- fetchActiveWorkflow: tests
- fetchHealth: tests + app code
- fetchStudioActive: tests
- applyCreatorVolumeTemplate: tests + app code

Total: 1 file modified, ~5-7 lines deleted.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

NOTE: bash may misinterpret `delete` keyword. Use heredoc if needed:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" commit --file=- <<'COMMIT_EOF'
refactor(api): delete orphan onApiError (Phase 93)

Phase 93 comprehensive api orphan audit. Only 1 true orphan found:
- onApiError (core.js) — 0 consumers (not re-exported, no internal call site)

10 other candidates have test consumers (NOT orphans):
- markApiOnline/Offline (connectivity.js): internal core.js
- exportCreatorTemplateApprovalAudit (creator.js): tests
- 4 mergePreset.js functions: tests
- fetchCreatorFactoryVolumeTemplates: tests
- fetchActiveWorkflow: tests
- fetchHealth: tests + app code
- fetchStudioActive: tests
- applyCreatorVolumeTemplate: tests + app code

Total: 1 file modified, ~5-7 lines deleted.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
COMMIT_EOF
```

- [ ] **Step 4.4: Verify commit**

```bash
git show --stat HEAD
```

Expected: 1 file changed.

- [ ] **Step 4.5: Final log**

```bash
git log --oneline -3
```

---

## Self-Review

**Spec coverage**:
- Spec §5 (Specific Removal) → Task 2
- Spec §6 (Verification) → Task 3
- Spec §8 (Commit) → Task 4

**Placeholder scan**:
- All Edit patterns reference actual file content (Step 1.2 verifies)
- All grep commands have expected output

**Type consistency**:
- Single file, single function
- Match existing comment + code style

**Risks covered**:
- Step 1.1 verifies no other consumers
- Step 2.4 verifies syntax
- Step 3.1 verifies 0 hits after edit

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/api/core.js
```
