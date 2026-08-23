# Phase 100 — Fix knip Duplicate Exports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate 2 knip-reported real duplicate exports so `pnpm exec knip` reports `Duplicate exports (0)`, without changing any runtime behavior.

**Architecture:** Surgical 2-line removal in 2 source files. No new modules, no API surface change, no test additions. Verified by re-running knip + the existing test/build/lint baseline (1545 tests must still pass, build must still succeed).

**Tech Stack:** JavaScript (ESM), Vue 3, Vite, knip 6.32.2, pnpm.

---

## File Structure

**Files modified (2):**
- `apps/dashboard/src/composables/useWidgetRegistry.js` — delete line 375 (`export default useWidgetRegistry;`)
- `apps/dashboard/src/utils/logger.js` — delete line 83 (`export default logger;`)

**Files NOT created.** No test file additions (rationale per spec §6: behavior unchanged, knip itself is the test).

---

## Task 1: Pre-flight — confirm knip baseline shows 2 duplicates

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -1 && git status
```

Expected: HEAD on commit `5225aaeb docs(spec): Phase 100 — fix knip duplicate exports design`. Working tree clean except for known untracked files.

- [ ] **Step 1.2: Run knip and confirm 2 duplicates**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip 2>&1 | grep -A 3 "Duplicate exports"
```

Expected output:
```
Duplicate exports (2)
useWidgetRegistry|default  apps/dashboard/src/composables/useWidgetRegistry.js
logger|default             apps/dashboard/src/utils/logger.js
```

If output differs (e.g., a third duplicate appeared), STOP and report back to user — the spec scope may need to change.

- [ ] **Step 1.3: Confirm no consumer imports the default exports**

```bash
cd /home/ailearn/projects/LingWen && grep -rn "import useWidgetRegistry from" apps/dashboard/src apps/dashboard/tests 2>/dev/null
cd /home/ailearn/projects/LingWen && grep -rn "import logger from" apps/dashboard/src apps/dashboard/tests 2>/dev/null
```

Expected: zero matches for both. If any match exists, STOP — it means a default-import consumer exists and removing the default export will break it.

- [ ] **Step 1.4: Capture pre-flight test baseline (sanity)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -5
```

Expected: `Tests  1545 passed (189 files)` (or higher — must be a green run). If red, STOP — fix baseline first.

---

## Task 2: Delete default export from `useWidgetRegistry.js`

**Files:**
- Modify: `apps/dashboard/src/composables/useWidgetRegistry.js:375`

- [ ] **Step 2.1: View the lines around line 375 to confirm exact content**

```bash
cd /home/ailearn/projects/LingWen && sed -n '370,376p' apps/dashboard/src/composables/useWidgetRegistry.js
```

Expected:
```js
    // 依赖检查
    checkWidgetDependencies,
  };
}

export default useWidgetRegistry;
```

- [ ] **Step 2.2: Delete line 375**

Use Edit tool:

- **Find (old_string)**:
```
}

export default useWidgetRegistry;
```
(appears at end of `useWidgetRegistry.js`)

- **Replace (new_string)**:
```
}
```

This keeps the closing `}` of `useWidgetRegistry()` (line 373) and removes the `export default useWidgetRegistry;` line + the blank line above it. The file now ends with the closing `}` of the function.

- [ ] **Step 2.3: Verify line 375 no longer exists and function is intact**

```bash
cd /home/ailearn/projects/LingWen && sed -n '370,378p' apps/dashboard/src/composables/useWidgetRegistry.js
```

Expected: file ends at line 374 with the function's closing `}`. No `export default` line remains in the file.

```bash
cd /home/ailearn/projects/LingWen && grep -n "export default" apps/dashboard/src/composables/useWidgetRegistry.js
```

Expected: no output (zero matches).

- [ ] **Step 2.4: Confirm named export still present**

```bash
cd /home/ailearn/projects/LingWen && grep -n "export function useWidgetRegistry" apps/dashboard/src/composables/useWidgetRegistry.js
```

Expected: one match, line 343 (unchanged).

---

## Task 3: Delete default export from `logger.js`

**Files:**
- Modify: `apps/dashboard/src/utils/logger.js:83`

- [ ] **Step 3.1: View the lines around line 83 to confirm exact content**

```bash
cd /home/ailearn/projects/LingWen && sed -n '78,84p' apps/dashboard/src/utils/logger.js
```

Expected:
```js
  groupEnd() {
    if (shouldLog(LOG_LEVELS.DEBUG)) {
      console.groupEnd();
    }
  },
};

export default logger;
```

- [ ] **Step 3.2: Delete line 83**

Use Edit tool:

- **Find (old_string)**:
```

export default logger;
```
(the leading blank line + the default export line — appears at end of `logger.js`)

- **Replace (new_string)**:
```
(empty — delete both the blank line and the export line)

The file now ends with `};` of the logger object literal.

- [ ] **Step 3.3: Verify file ends correctly**

```bash
cd /home/ailearn/projects/LingWen && tail -5 apps/dashboard/src/utils/logger.js
```

Expected:
```js
  groupEnd() {
    if (shouldLog(LOG_LEVELS.DEBUG)) {
      console.groupEnd();
    }
  },
};
```

```bash
cd /home/ailearn/projects/LingWen && grep -n "export default" apps/dashboard/src/utils/logger.js
```

Expected: no output (zero matches).

- [ ] **Step 3.4: Confirm named export still present**

```bash
cd /home/ailearn/projects/LingWen && grep -n "^export const logger" apps/dashboard/src/utils/logger.js
```

Expected: one match, line 41 (unchanged).

---

## Task 4: Verify knip now reports zero duplicates

**Files:**
- Read-only verification.

- [ ] **Step 4.1: Re-run knip**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip 2>&1 | grep -A 3 "Duplicate exports"
```

Expected output:
```
Duplicate exports (0)
```

(Or the entire "Duplicate exports" section is absent.) If still shows 2, STOP — investigate.

- [ ] **Step 4.2: Confirm both targets removed from knip report**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip 2>&1 | grep -E "useWidgetRegistry|logger" | head -20
```

Expected: lines mentioning `useWidgetRegistry` only as named export from `useWidgetRegistry.js` (no `default` tag) and `logger` only as named export from `logger.js` (no `default` tag). No `default` line.

---

## Task 5: Run full verification suite (tests + build + type-check + lint)

**Files:**
- Read-only verification.

- [ ] **Step 5.1: Run vitest — all 1545+ tests must pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -10
```

Expected: `Tests  1545 passed` (no test broken). If any test fails, STOP and investigate.

- [ ] **Step 5.2: Run vue-tsc — 0 type errors**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -5
```

Expected: empty output (0 errors). If any errors, STOP.

- [ ] **Step 5.3: Run build — must succeed**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -10
```

Expected: build completes successfully (~20s). No errors.

- [ ] **Step 5.4: Run lint — must be clean**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run lint:all 2>&1 | tail -10
```

Expected: no errors. If any errors, STOP.

---

## Task 6: Commit + push

**Files:**
- Commit: 2 file modifications.

- [ ] **Step 6.1: Stage the 2 modified files**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/src/composables/useWidgetRegistry.js apps/dashboard/src/utils/logger.js && git status
```

Expected: 2 modified files staged.

- [ ] **Step 6.2: Commit with the spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): remove 2 unused default exports (Phase 100)" -m "Phase 100 — fix knip duplicate exports:

- Delete \`export default useWidgetRegistry\` (composables/useWidgetRegistry.js:375)
- Delete \`export default logger\` (utils/logger.js:83)

Both defaults were unreferenced — all 29 import sites use named form.
knip output: Duplicate exports (2 → 0) ✅

测试基线不变: 1545 PASS, 0 type errors, 0 build errors." 2>&1 | tail -5
```

Expected: one commit created. Single line subject + multi-line body.

- [ ] **Step 6.3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

Expected: push succeeds. `origin/master` advances by 1 commit.

- [ ] **Step 6.4: Final state check**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: 3 most recent commits include the Phase 100 refactor commit. Working tree clean.

---

## Success Criteria

- [ ] `pnpm exec knip` reports `Duplicate exports (0)`
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## Rollback

If any verification step fails after deletion:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts the single commit and pushes the revert. No data loss.

---

## Self-Review Notes

**Spec coverage**:
- §4.1 Change Set → Task 2 + Task 3 ✅
- §4.3 Verification Strategy → Task 4 + Task 5 ✅
- §7 Commit Strategy → Task 6 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions introduced. Only deletion. No consistency risk.

**Edge cases handled**:
- Task 1.3 explicit grep for default-import consumers (catch unseen break risk)
- Task 1.4 pre-flight test baseline (catch pre-existing breakage not caused by us)
- Rollback section included (low-cost insurance)