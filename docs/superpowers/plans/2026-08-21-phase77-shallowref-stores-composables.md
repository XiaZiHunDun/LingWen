# Phase 77 Implementation Plan — shallowRef for Wholesale-Replaced Refs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert 7+15+ wholesale-replaced `ref()` to `shallowRef()` in 2 files (useStudioStore.js + useCreatorSettings.js), reducing Vue 3 deep reactive proxy overhead for large nullable objects.

**Architecture:** Per-ref decision rule (wholesale replacement pattern verified via grep + manual read). Each conversion adds a `// Phase 77: shallowRef — wholesale replacement (line X)` comment. Two atomic commits per file (per spec §9).

**Tech Stack:** Vue 3 shallowRef, Pinia, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase77-shallowref-stores-composables-design.md` (commit `7d0c897b`)

---

## File Structure

| File | Action | Refs |
|------|--------|------|
| `apps/dashboard/src/stores/useStudioStore.js` | **Modify** (imports + 7 conversions + comments) | projects/summary/overview/quality/qualityReport/proseDiff/proseJudge |
| `apps/dashboard/src/composables/useCreatorSettings.js` | **Modify** (imports + 15+ conversions + comments) | settingsDocs/settingsDiffPreview/settingsHistory + 9+ mergePreset* refs |

**Total**: 2 files modified, 1-2 atomic commits.

---

## Task 1: Verify + edit useStudioStore.js

**Files:**
- Modify: `apps/dashboard/src/stores/useStudioStore.js`

- [ ] **Step 1.1: Read full useStudioStore.js**

Run: `wc -l apps/dashboard/src/stores/useStudioStore.js`
Expected: ~240 lines

Read full file to identify all ref declarations and their mutation patterns.

- [ ] **Step 1.2: Per-ref verify — check each candidate has NO property mutation**

For each of the 7 candidate refs (projects, summary, overview, quality, qualityReport, proseDiff, proseJudge), run:

```bash
# Pattern: .value.<property> = ... (property mutation)
grep -nE "\b(projects|summary|overview|quality|qualityReport|proseDiff|proseJudge)\.value\.\w+\s*=" apps/dashboard/src/stores/useStudioStore.js
```

Expected: **0 hits** for each ref. If any ref has property mutation, mark it as KEEP.

- [ ] **Step 1.3: Per-ref verify — confirm wholesale assignment exists**

```bash
grep -nE "\b(projects|summary|overview|quality|qualityReport|proseDiff|proseJudge)\.value\s*=" apps/dashboard/src/stores/useStudioStore.js
```

Expected: At least 1 hit per ref. Documents wholesale replacement pattern.

- [ ] **Step 1.4: Update spec table if any candidate is invalid**

If any candidate fails verify, update the spec table to mark it as KEEP with reason.

- [ ] **Step 1.5: Edit imports — add shallowRef**

Use Edit tool:
- **old_string**: `import { ref, computed, watch } from 'vue'` (or whatever current import is)
- **new_string**: `import { ref, shallowRef, computed, watch } from 'vue'`

Note: Read current import first to match exact text.

- [ ] **Step 1.6: Convert 7 refs to shallowRef**

For each candidate ref, use Edit tool:
- Pattern: `const <name> = ref(<init>)` → `const <name> = shallowRef(<init>) // Phase 77: shallowRef — wholesale replacement (line X)`

Do all 7 conversions. Each conversion is 1 Edit tool call.

- [ ] **Step 1.7: Verify file syntax**

Run: `node -c apps/dashboard/src/stores/useStudioStore.js 2>&1 && echo "syntax OK"`
Expected: `syntax OK`

---

## Task 2: Test useStudioStore.js changes

**Files:** None (verification only)

- [ ] **Step 2.1: Run unit tests**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -10`
Expected: `Tests  1549 passed (1549)` (unchanged)

- [ ] **Step 2.2: If tests fail, ROLLBACK**

If tests fail, the conversion has a reactivity bug:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/stores/useStudioStore.js
# Investigate which ref conversion caused the failure
# Either revert to ref() for that specific ref, or document the issue
```

---

## Task 3: Verify + edit useCreatorSettings.js

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings.js`

- [ ] **Step 3.1: Read full useCreatorSettings.js**

Run: `wc -l apps/dashboard/src/composables/useCreatorSettings.js`
Expected: ~651 lines (this is a big file — read fully or in sections)

- [ ] **Step 3.2: Per-ref verify — check each candidate has NO property mutation**

For each candidate ref (settingsDocs, settingsBaseline, settingsDiffPreview, settingsHistory, mergePresetPackages, factoryMergePresetPackages, mergePresetImportDiff, mergePresetToposort, mergePresetChangelog, mergePresetChangelogDiff, factoryMergePresetPullConflicts, mergePresetImportPreflight, mergePresetGraph, mergePresetConflicts, mergePresetConflictFixes), run:

```bash
grep -nE "\b(<ref_name>)\.value\.\w+\s*=" apps/dashboard/src/composables/useCreatorSettings.js
```

Expected: **0 hits** for each candidate. If any ref has property mutation, mark as KEEP.

- [ ] **Step 3.3: Per-ref verify — confirm wholesale assignment exists**

For each candidate, confirm at least 1 `\.value\s*=` assignment exists.

- [ ] **Step 3.4: Update spec table if any candidate is invalid**

If any candidate fails verify, update spec table.

- [ ] **Step 3.5: Edit imports — add shallowRef**

Use Edit tool. Read current import first.

- [ ] **Step 3.6: Convert 15+ refs to shallowRef**

For each candidate, use Edit tool:
- Pattern: `const <name> = ref(<init>);` → `const <name> = shallowRef(<init>); // Phase 77: shallowRef — wholesale replacement`

Note: useCreatorSettings uses semicolons (per spec line 77-102 listing).

- [ ] **Step 3.7: Verify file syntax**

Run: `node -c apps/dashboard/src/composables/useCreatorSettings.js 2>&1 && echo "syntax OK"`
Expected: `syntax OK`

---

## Task 4: Test useCreatorSettings.js changes

**Files:** None (verification only)

- [ ] **Step 4.1: Run unit tests**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -10`
Expected: `Tests  1549 passed (1549)` (unchanged)

- [ ] **Step 4.2: If tests fail, ROLLBACK**

```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/composables/useCreatorSettings.js
```

---

## Task 5: Final verifications

**Files:** None (verification only)

- [ ] **Step 5.1: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

- [ ] **Step 5.2: Build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -5`
Expected: `✓ built in <time>`

- [ ] **Step 5.3: Verify shallowRef counts**

Run:
```bash
echo "useStudioStore.js shallowRef count:"
grep -c "shallowRef" apps/dashboard/src/stores/useStudioStore.js
echo "useCreatorSettings.js shallowRef count:"
grep -c "shallowRef" apps/dashboard/src/composables/useCreatorSettings.js
```

Expected: ≥7 for useStudioStore.js, ≥15 for useCreatorSettings.js (counts include import + each conversion).

- [ ] **Step 5.4: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat`
Expected: 2 files changed (useStudioStore.js + useCreatorSettings.js), small line counts (~10-30 lines per file).

---

## Task 6: Commit (1-2 atomic commits)

**Files:** None (commits existing working tree)

- [ ] **Step 6.1: Stage 2 modified files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useStudioStore.js \
        apps/dashboard/src/composables/useCreatorSettings.js
```

- [ ] **Step 6.2: Verify staged**

Run: `git status -s`
Expected: 2 modified files, no other changes.

- [ ] **Step 6.3: Commit (combined — both files in 1 atomic commit)**

Per spec §9, can be 1 combined commit or 2 per-file commits. Default to combined for atomicity:

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf(stores,useCreatorSettings): convert 22 wholesale-refs to shallowRef (Phase 77)" \
    -m "Phase 77 shallowRef optimization (per Phase 76 baseline §6):

useStudioStore.js (7 conversions):
- projects, summary, overview, quality, qualityReport, proseDiff, proseJudge
- All wholesale-replaced (x.value = newData)

useCreatorSettings.js (15+ conversions):
- settingsDocs, settingsDiffPreview, settingsHistory, settingsBaseline
- mergePresetPackages, factoryMergePresetPackages
- mergePresetImportDiff, Toposort, Changelog, ChangelogDiff
- factoryMergePresetPullConflicts, ImportPreflight
- mergePresetGraph, Conflicts, ConflictFixes

KEEP (wholesale pattern violated):
- useStudioStore.cacheTimestamps (property mutation cacheTimestamps.value[key] = Date.now())
- All primitives (loading/error/activeSlug/booleans/strings)

Vue 3 default ref(obj) is deep reactive — entire object tree wrapped in Proxy.
shallowRef only tracks .value reference change, not internal properties.
For wholesale-replaced refs, this eliminates proxy overhead.

Per-ref '// Phase 77: shallowRef — wholesale replacement' comments added.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 6.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 2 files changed, all `.js`, ~22 conversions total.

- [ ] **Step 6.5: Final log check**

Run: `git log --oneline -3`
Expected:
```
<new-hash> perf(stores,useCreatorSettings): convert 22 wholesale-refs to shallowRef (Phase 77)
7d0c897b docs(spec): Phase 77 — shallowRef for wholesale-replaced refs design
c9884e87 test(perf): Playwright Web Vitals baseline for 4 representative routes (Phase 76)
```

- [ ] **Step 6.6: Confirm no auto-push**

Run: `git status -sb | head -3`
Expected: `## master...origin/master [ahead N]` (user pushes manually)

---

## Task 7: (Optional) Re-run Phase 76 baseline

**Files:** None (verification only)

- [ ] **Step 7.1: Start dev server**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm dev --port 5173 --strictPort &
PREVIEW_PID=$!
sleep 5
```

- [ ] **Step 7.2: Run web-vitals spec**

```bash
PW_BASE_URL=http://localhost:5173 pnpm exec playwright test --project=web-vitals --reporter=line --workers=1 2>&1 | grep -E "lcp.*ms|passed|failed" | head -20
```

Expected: 12 tests PASS. Compare LCP medians to Phase 76 baseline (per `docs/perf/playwright-web-vitals-baseline.md`).

- [ ] **Step 7.3: Kill dev server**

```bash
kill $PREVIEW_PID 2>/dev/null
```

- [ ] **Step 7.4: Document perf comparison in spec or follow-up doc**

If LCPs changed (better or worse), note in `docs/perf/playwright-web-vitals-baseline.md` §5 Top Issues or create follow-up.

---

## Self-Review

**Spec coverage**:
- Spec §2 Goal 1 (useStudioStore 7 ref) → Task 1 (verify + edit)
- Spec §2 Goal 2 (useCreatorSettings 15+ ref) → Task 3 (verify + edit)
- Spec §2 Goal 3 (KEEP cacheTimestamps) → Step 1.2 verify (no property mutation allowed)
- Spec §2 Goal 4 (KEEP primitives) → Step 1.2 + Step 3.2 verify (no need to convert)
- Spec §2 Goal 5 (1549 tests unchanged) → Tasks 2 + 4
- Spec §2 Goal 6 (1-2 atomic commits) → Task 6

**Placeholder scan**:
- Step 1.6/3.6 Edit pattern has actual code (`shallowRef(<init>)`)
- All grep commands have expected output

**Type consistency**:
- `shallowRef` API consistent across both files
- Per-ref comment format consistent (`// Phase 77: shallowRef — wholesale replacement`)

**Risks covered**:
- Test rollback in Tasks 2.2 + 4.2 catches reactivity bugs early
- Per-ref verify in 1.2/3.2 catches wholesale pattern violations
- File syntax check in 1.7/3.7 catches typos
- Optional baseline re-run in Task 7 quantifies impact
