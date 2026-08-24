# Phase 102 — Audit & Resolve 36 Unused Files Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce knip's `Unused files` count from 36 to 0 by deleting 30 truly-dead files and adding 5 false-positive files to `knip.json#ignore`.

**Architecture:** Bulk deletion of 30 source files (Categories A, B, C, D, F per spec §4.1) followed by a 5-entry `ignore` array addition to `knip.json` (Categories E, G). Two atomic commits for reviewability. No code logic changes — pure cleanup.

**Tech Stack:** Vue 3, TypeScript, JavaScript, knip 6.32.2, pnpm, ESLint, Playwright.

---

## File Structure

**Files deleted (30):**
- `apps/dashboard/src/components/creator/Creator*.vue` × 20
- `apps/dashboard/src/components/{CreationModeHint,FieldHint,SkeletonLoader,WidgetRenderer}.vue` × 4
- `apps/dashboard/src/types/{api,branded,creator}.ts` × 3
- `apps/dashboard/src/utils/{safeAccess,safeStore}.js` × 2
- `apps/dashboard/tests/unit/helpers/creator-test-helper.ts` × 1

**Files edited (1):**
- `knip.json` — add `ignore` array with 5 entries

**Files NOT touched:** `types/index.ts`, `types/composables.ts`, all `creatorXxxKey.js` files, all source code that is in active use.

---

## Task 1: Pre-flight — git state + verify all 36 files exist + tests baseline

**Files:**
- Read-only verification.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -1 && git status
```

Expected: HEAD on `d4a1495b docs(spec): Phase 102 — audit & resolve 36 unused files design`. Working tree clean.

- [ ] **Step 1.2: Confirm all 30 to-be-deleted files exist**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/src/components/creator/CreatorAdvanceBatchPanel.vue \
  apps/dashboard/src/components/creator/CreatorAgentAnnotations.vue \
  apps/dashboard/src/components/creator/CreatorAgentStreamPreview.vue \
  apps/dashboard/src/components/creator/CreatorBatchSummaryPrompt.vue \
  apps/dashboard/src/components/creator/CreatorChapterBodyEditor.vue \
  apps/dashboard/src/components/creator/CreatorChapterBodySaveFooter.vue \
  apps/dashboard/src/components/creator/CreatorChapterEntityRail.vue \
  apps/dashboard/src/components/creator/CreatorChapterTaskCards.vue \
  apps/dashboard/src/components/creator/CreatorConsistencyRail.vue \
  apps/dashboard/src/components/creator/CreatorDeviationList.vue \
  apps/dashboard/src/components/creator/CreatorDirectorPaths.vue \
  apps/dashboard/src/components/creator/CreatorInlineConflictGutter.vue \
  apps/dashboard/src/components/creator/CreatorLightValidationBar.vue \
  apps/dashboard/src/components/creator/CreatorModeGuidePanel.vue \
  apps/dashboard/src/components/creator/CreatorOnboardingWizardPanel.vue \
  apps/dashboard/src/components/creator/CreatorPreferencesSummary.vue \
  apps/dashboard/src/components/creator/CreatorPulseIntro.vue \
  apps/dashboard/src/components/creator/CreatorWriteControlStrip.vue \
  apps/dashboard/src/components/creator/CreatorWriteMicroTaskBar.vue \
  apps/dashboard/src/components/creator/CreatorWriteScopeBar.vue \
  apps/dashboard/src/components/CreationModeHint.vue \
  apps/dashboard/src/components/FieldHint.vue \
  apps/dashboard/src/components/SkeletonLoader.vue \
  apps/dashboard/src/components/WidgetRenderer.vue \
  apps/dashboard/src/types/api.ts \
  apps/dashboard/src/types/branded.ts \
  apps/dashboard/src/types/creator.ts \
  apps/dashboard/src/utils/safeAccess.js \
  apps/dashboard/src/utils/safeStore.js \
  apps/dashboard/tests/unit/helpers/creator-test-helper.ts; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "All 30 files exist"
```

Expected: `All 30 files exist`. If any MISSING, STOP — file already removed or path typo.

- [ ] **Step 1.3: Confirm all 5 to-be-ignored files exist**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/tests/fixtures/lint-testid/clean.spec.ts \
  apps/dashboard/tests/fixtures/lint-testid/dirty.spec.ts \
  apps/dashboard/tests/visual-audit/capture.spec.js \
  apps/dashboard/tests/visual-audit/regression.spec.js \
  apps/dashboard/tests/visual-audit/ui-metrics.spec.js; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "All 5 files exist"
```

Expected: `All 5 files exist`.

- [ ] **Step 1.4: Confirm knip.json is at root**

```bash
cd /home/ailearn/projects/LingWen && ls -la knip.json && cat knip.json
```

Expected: file exists at root. Content matches spec §4.2 (no `ignore` array yet).

- [ ] **Step 1.5: Capture pre-flight test baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed (1545)`. If red, STOP — pre-existing breakage not caused by us.

- [ ] **Step 1.6: Capture pre-flight knip baseline (should be 36)**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused files"
```

Expected: `Unused files (36)`. If different, STOP — scope drift.

---

## Task 2: Delete 30 source files (Categories A, B, C, D, F)

**Files:**
- Delete: 30 files (no replacement)

- [ ] **Step 2.1: Delete all 30 files via `git rm`**

```bash
cd /home/ailearn/projects/LingWen && git rm \
  apps/dashboard/src/components/creator/CreatorAdvanceBatchPanel.vue \
  apps/dashboard/src/components/creator/CreatorAgentAnnotations.vue \
  apps/dashboard/src/components/creator/CreatorAgentStreamPreview.vue \
  apps/dashboard/src/components/creator/CreatorBatchSummaryPrompt.vue \
  apps/dashboard/src/components/creator/CreatorChapterBodyEditor.vue \
  apps/dashboard/src/components/creator/CreatorChapterBodySaveFooter.vue \
  apps/dashboard/src/components/creator/CreatorChapterEntityRail.vue \
  apps/dashboard/src/components/creator/CreatorChapterTaskCards.vue \
  apps/dashboard/src/components/creator/CreatorConsistencyRail.vue \
  apps/dashboard/src/components/creator/CreatorDeviationList.vue \
  apps/dashboard/src/components/creator/CreatorDirectorPaths.vue \
  apps/dashboard/src/components/creator/CreatorInlineConflictGutter.vue \
  apps/dashboard/src/components/creator/CreatorLightValidationBar.vue \
  apps/dashboard/src/components/creator/CreatorModeGuidePanel.vue \
  apps/dashboard/src/components/creator/CreatorOnboardingWizardPanel.vue \
  apps/dashboard/src/components/creator/CreatorPreferencesSummary.vue \
  apps/dashboard/src/components/creator/CreatorPulseIntro.vue \
  apps/dashboard/src/components/creator/CreatorWriteControlStrip.vue \
  apps/dashboard/src/components/creator/CreatorWriteMicroTaskBar.vue \
  apps/dashboard/src/components/creator/CreatorWriteScopeBar.vue \
  apps/dashboard/src/components/CreationModeHint.vue \
  apps/dashboard/src/components/FieldHint.vue \
  apps/dashboard/src/components/SkeletonLoader.vue \
  apps/dashboard/src/components/WidgetRenderer.vue \
  apps/dashboard/src/types/api.ts \
  apps/dashboard/src/types/branded.ts \
  apps/dashboard/src/types/creator.ts \
  apps/dashboard/src/utils/safeAccess.js \
  apps/dashboard/src/utils/safeStore.js \
  apps/dashboard/tests/unit/helpers/creator-test-helper.ts
```

Expected: 30 `rm '...'` lines output.

- [ ] **Step 2.2: Verify all 30 files deleted from filesystem**

```bash
cd /home/ailearn/projects/LingWen && git status | grep "^[[:space:]]*deleted:" | wc -l
```

Expected: `30`.

- [ ] **Step 2.3: Verify no key files were accidentally deleted**

```bash
cd /home/ailearn/projects/LingWen && ls apps/dashboard/src/components/creator/creatorXxxKey.js 2>/dev/null
```

Specifically check that `creatorAdvanceBatchKey.js`, `creatorModeGuideKey.js`, `creatorOnboardingKey.js`, `creatorWriteKey.js`, `creatorProductToolsKey.js`, `creatorSettingsKey.js`, `creatorPulseKey.js`, `creatorPageChromeKey.js`, `creatorVolumePlanKey.js`, `creatorBatchHistoryKey.js` still exist:

```bash
cd /home/ailearn/projects/LingWen && for k in creatorAdvanceBatchKey creatorModeGuideKey creatorOnboardingKey creatorWriteKey creatorProductToolsKey creatorSettingsKey creatorPulseKey creatorPageChromeKey creatorVolumePlanKey creatorBatchHistoryKey; do \
  test -f "apps/dashboard/src/components/creator/${k}.js" && echo "OK: ${k}.js" || echo "MISSING: ${k}.js"; \
done
```

Expected: all 10 key files show `OK:`.

---

## Task 3: Verify post-deletion state (knip should now report 6 files, not 36)

**Files:**
- Read-only verification.

- [ ] **Step 3.1: knip reports 6 remaining (the to-be-ignored false positives)**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused files"
```

Expected: `Unused files (6)` (was 36; we deleted 30). If different count, STOP — investigate.

- [ ] **Step 3.2: knip's remaining 6 should be exactly the E + G categories**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep -E "^apps/dashboard/tests/(fixtures|visual-audit)/" | sort
```

Expected (5 lines):
```
apps/dashboard/tests/fixtures/lint-testid/clean.spec.ts
apps/dashboard/tests/fixtures/lint-testid/dirty.spec.ts
apps/dashboard/tests/visual-audit/capture.spec.js
apps/dashboard/tests/visual-audit/regression.spec.js
apps/dashboard/tests/visual-audit/ui-metrics.spec.js
```

Wait — the count was 6, but only 5 are listed. The 6th would be from a different category. STOP — investigate which 6th file appears, verify it should also be ignored.

Actually re-read spec: spec §1 table says 30 delete + 5 ignore + 1 keep = 36. The "1 keep" is `types/index.ts`. So after deletion of 30, knip should report 6 unused files = 5 ignore-candidates + 1 `types/index.ts` (which is the "keep for follow-up").

Wait, but spec §3 says "NOT deleting any of the 5 false-positive files" — so `types/index.ts` is the keep. After deletion of 30, knip reports 5 + 1 = 6. The 5 ignored are E+G. The 6th (`types/index.ts`) is left alone for follow-up.

If knip's actual output is 6 files and 5 match E+G, the 6th must be `types/index.ts`. Verify:
```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep "types/index"
```
Expected: line present. If different, STOP — investigate.

- [ ] **Step 3.3: Tests still pass after 30 deletions**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed (1545)`. If any test fails, STOP — find root cause before knip.json edit.

- [ ] **Step 3.4: Build still succeeds**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -10
```

Expected: build completes successfully (~20s). No errors.

---

## Task 4: Edit knip.json — add `ignore` array

**Files:**
- Modify: `knip.json`

- [ ] **Step 4.1: View current knip.json content**

```bash
cd /home/ailearn/projects/LingWen && cat knip.json
```

Expected:
```json
{
  "entry": [
    "src/main.js",
    "src/router/index.js",
    "src/router/routes.js"
  ],
  "project": [
    "src/**/*.{js,ts,vue}",
    "tests/**/*.{js,ts}"
  ]
}
```

- [ ] **Step 4.2: Apply Edit**

Use Edit tool. Add an `ignore` array (5 entries for Categories E + G).

- **Find (old_string)**:
```json
  "project": [
    "src/**/*.{js,ts,vue}",
    "tests/**/*.{js,ts}"
  ]
}
```

- **Replace (new_string)**:
```json
  "project": [
    "src/**/*.{js,ts,vue}",
    "tests/**/*.{js,ts}"
  ],
  "ignore": [
    "tests/fixtures/lint-testid/clean.spec.ts",
    "tests/fixtures/lint-testid/dirty.spec.ts",
    "tests/visual-audit/capture.spec.js",
    "tests/visual-audit/regression.spec.js",
    "tests/visual-audit/ui-metrics.spec.js"
  ]
}
```

The `ignore` array is appended after `project`, before the closing `}`. Each path is a string, comma-separated.

- [ ] **Step 4.3: Verify JSON parses**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import json;d=json.load(open('knip.json'));print('OK, ignore has', len(d.get('ignore', [])), 'entries')"
```

Expected: `OK, ignore has 5 entries`.

---

## Task 5: Verify knip now reports 0 unused files

**Files:**
- Read-only verification.

- [ ] **Step 5.1: knip `Unused files` count is 0**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused files"
```

Expected: `Unused files (0)`. If still showing files, STOP — investigate ignore semantics.

- [ ] **Step 5.2: Full knip report — verify no unused-file regressions in other categories**

```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

Expected output:
```
Unlisted binaries (7)
Unused dependencies (1)
Unused devDependencies (1)
Unused exports (27)
Unused exported types (12)
```
With `Unused files` absent (now 0).

The other categories (deps, devDeps, binaries, exports, types) should still report same counts as Phase 99.1 baseline — Phase 102 only addresses Unused files.

- [ ] **Step 5.3: ESLint fixtures still work (Phase 8.31/8.32 sanity check)**

```bash
cd /home/ailearn/projects/LingWen && pnpm lint:testid 2>&1 | tail -5
```

Expected: lint:testid reports 2 violations from `dirty.spec.ts` (confirming the fixture still serves its purpose).

- [ ] **Step 5.4: Tests still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed (1545)`.

---

## Task 6: Commit 1 — source code deletions

**Files:**
- Commit: 30 deleted files.

- [ ] **Step 6.1: Stage all deletions + verify exactly 30 files staged**

```bash
cd /home/ailearn/projects/LingWen && git add -u && git status --short | wc -l && git status --short | head -35
```

Expected: `30` (or `31` if knip.json also staged — if so, unstage knip.json with `git restore --staged knip.json` before committing).

Actually, since `knip.json` was just edited but not yet staged, `git add -u` should only stage the deletions. Verify with `git status` — expect only `deleted:` lines.

- [ ] **Step 6.2: Commit with the spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): delete 30 unused files from knip report (Phase 102)" -m "Phase 102 — resolve unused files (Category A, B, C, D, F):

- Delete 20 Creator sub-components (panels never rendered; some had
  decoupled key files which stay):
  CreatorAdvanceBatchPanel, CreatorAgentAnnotations,
  CreatorAgentStreamPreview, CreatorBatchSummaryPrompt,
  CreatorChapterBodyEditor, CreatorChapterBodySaveFooter,
  CreatorChapterEntityRail, CreatorChapterTaskCards,
  CreatorConsistencyRail, CreatorDeviationList,
  CreatorDirectorPaths, CreatorInlineConflictGutter,
  CreatorLightValidationBar, CreatorModeGuidePanel,
  CreatorOnboardingWizardPanel, CreatorPreferencesSummary,
  CreatorPulseIntro, CreatorWriteControlStrip,
  CreatorWriteMicroTaskBar, CreatorWriteScopeBar
- Delete 4 generic components:
  CreationModeHint, FieldHint, SkeletonLoader, WidgetRenderer
- Delete 3 dead types files:
  types/api.ts, types/branded.ts, types/creator.ts
- Delete 2 dead utils files:
  utils/safeAccess.js, utils/safeStore.js
- Delete 1 dead test helper:
  tests/unit/helpers/creator-test-helper.ts

All 30 files confirmed dead via grep (0-1 external refs; 1-ref cases
were either self-refs or chains to other deleted files).

测试基线不变: 1545 PASS, 0 type errors, 0 build errors." 2>&1 | tail -5
```

Expected: one commit created.

- [ ] **Step 6.3: Do NOT push yet**

Per spec §7 — two commits land separately. Commit 1 stays local until Commit 2 lands.

---

## Task 7: Commit 2 — knip.json edit + push both commits

**Files:**
- Commit: `knip.json` modification
- Push: both Commit 1 + Commit 2 to origin

- [ ] **Step 7.1: Stage knip.json**

```bash
cd /home/ailearn/projects/LingWen && git add knip.json && git status
```

Expected: 1 modified file staged (knip.json), 30 deleted files already committed.

- [ ] **Step 7.2: Commit with the spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "build(ci): add 5 entries to knip.json ignore (Phase 102)" -m "Phase 102 — resolve knip false-positive Unused files (Category E, G):

knip doesn't parse ESLint config or Playwright config, so it can't
see legitimate references for these 5 test files:

- tests/fixtures/lint-testid/{clean,dirty}.spec.ts
  (referenced via glob in eslint.config.js:29 for rule
   testid-class-sync regression testing — Phase 8.31/8.32 fixtures;
   do NOT delete per Phase 8.33 decision)
- tests/visual-audit/{capture,regression,ui-metrics}.spec.js
  (referenced via testMatch regex in playwright.config.js)

Add them to \`ignore\` array in knip.json so knip stops reporting them.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors. knip output:
Unused files (0) ✅." 2>&1 | tail -5
```

Expected: one commit created.

- [ ] **Step 7.3: Push both commits to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

Expected: push succeeds with 2 new commits. `origin/master` advances by 2.

- [ ] **Step 7.4: Final local state check**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -5 && git status
```

Expected: 5 most recent commits include both Phase 102 commits. Working tree clean.

---

## Task 8: Post-merge CI verification (gate observability end-to-end)

**Files:**
- Read-only verification (CI dashboard).

- [ ] **Step 8.1: Find latest CI run**

```bash
cd /home/ailearn/projects/LingWen && gh run list --workflow=dashboard-frontend-ci.yml --limit 3
```

(Use `gh` CLI; if not authenticated, report and skip dashboard verification.)

- [ ] **Step 8.2: Confirm Setup pnpm PASSED**

```bash
gh run view <run-id> --json jobs --jq '.jobs[] | {name, conclusion}'
```

Look for `Setup pnpm` step conclusion = `success`.

- [ ] **Step 8.3: Confirm Run knip PASSED (gate observes zero unused files)**

Same command. Look for `Run knip (dead-export detection)` step conclusion = `success`.

This is the Phase 99 gate now observing zero `Unused files` — proving Phase 102 cleanup resolved the issue end-to-end. Knip may still report Unused exports (27) / Unused exported types (12) etc., but those are out of Phase 102 scope.

Wait — Phase 99 promoted knip to hard error. If knip still reports 27 unused exports + 12 unused exported types + 1 dep + 1 devDep + 7 unlisted binaries, then knip step will STILL FAIL (different category though). Verify what knip now reports:
```bash
cd /home/ailearn/projects/LingWen && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

If `Unused files` is 0 but other categories still report, knip will still fail. This is expected (those are follow-up phases 103-105).

If `Unused files` is 0 AND all other categories are 0, knip passes (no findings). This would be ideal.

**Expected**: knip step FAILS but `Unused files` category is no longer the cause. The remaining failures are documented follow-ups.

- [ ] **Step 8.4: Document CI evidence in final report**

Save run ID + URL + relevant step conclusions.

---

## Success Criteria

- [ ] 30 files deleted (Categories A, B, C, D, F)
- [ ] `knip.json` `ignore` array contains 5 entries (Categories E, G)
- [ ] `types/index.ts` preserved
- [ ] `pnpm exec knip` reports `Unused files (0)`
- [ ] Other knip categories unchanged (deps, exports, types, binaries)
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean (lint:testid still reports 2 violations from dirty.spec.ts)
- [ ] Two atomic commits on master
- [ ] Pushed to origin/master
- [ ] Post-merge CI: Setup pnpm passes; Run knip observes zero Unused files

---

## Rollback

If a deletion breaks a runtime or test:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD~1 --no-edit && git push origin master
```

Reverts Commit 1 (deletions). Commit 2 (knip.json ignore) stays — its effect is benign (silences false positives).

If knip.json edit causes issues:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts the knip.json ignore commit. knip will report the 5 false positives again, but they don't cause runtime errors — only CI noise.

---

## Self-Review Notes

**Spec coverage**:
- §4.1 Change Set → Task 2 (30 deletes) + Task 4 (knip.json edit) ✅
- §4.4 Verification → Task 5 (knip counts + tests + lint:testid) ✅
- §7 Commit Strategy → Task 6 + Task 7 (two commits) ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only file deletions + JSON config addition.

**Edge cases handled**:
- Task 1.2/1.3 file existence checks — catch path typos before deletion
- Task 1.5 test baseline — catch pre-existing breakage not caused by us
- Task 1.6 knip baseline (36) — catch scope drift
- Task 2.3 key file verification — catch accidental key-file deletion (A2 risk)
- Task 3.2 knip count 6 — verify the math (30 deleted + 5 ignored still reported = 6 expected before knip.json edit)
- Task 4.3 JSON validity — catch JSON syntax errors
- Task 5.3 lint:testid sanity — verify ignored files still serve their purpose
- Task 8.3 knip step observation — verify Phase 102 cleanup actually reaches the gate
- Rollback section (per-commit granularity) — clean recovery options