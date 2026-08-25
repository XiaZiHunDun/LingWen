# Phase 97 — api/index.js Barrel Re-export Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]` ) syntax for tracking.

**Goal:** Remove 4 truly-dead functions (delete entirely) and 7 redundant barrel entries (drop from barrel, keep submodule export). End-state: barrel drops 11 of 158 lines; 4 dead functions removed from codebase.

**Architecture:** Single atomic commit. 5 file operations: 1 barrel edit + 4 submodule edits.

**Tech Stack:** Vue 3, JavaScript, knip 6.32.2, pnpm.

---

## File Structure

**Files modified (5):**
- `apps/dashboard/src/api/index.js` — drop 11 re-export entries
- `apps/dashboard/src/api/health.js` — drop `export` on `fetchHealth`
- `apps/dashboard/src/api/workflows.js` — drop `export` on `fetchActiveWorkflow`
- `apps/dashboard/src/api/studio.js` — drop `export` on `fetchStudioActive`
- `apps/dashboard/src/api/creator.js` — drop `export` on `exportCreatorTemplateApprovalAudit`

---

## Task 1: Pre-flight — git state + baselines

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `eb41f75c docs(spec): Phase 97 — ...`. Tree clean.

- [ ] **Step 1.2: Confirm all 5 target files exist + grep baseline for 4 dead functions**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/src/api/index.js \
  apps/dashboard/src/api/health.js \
  apps/dashboard/src/api/workflows.js \
  apps/dashboard/src/api/studio.js \
  apps/dashboard/src/api/creator.js; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "All 5 files exist"
```

Expected: `All 5 files exist`.

```bash
cd /home/ailearn/projects/LingWen && for sym in fetchHealth fetchActiveWorkflow fetchStudioActive exportCreatorTemplateApprovalAudit; do \
  echo "--- $sym ---"; \
  grep -rn "\b${sym}\b" apps/dashboard/src --include="*.vue" --include="*.js" --include="*.ts" 2>/dev/null | head -3; \
done
```
Expected: each shows only 1 match (the defining file + barrel entry). If any match appears in additional files, STOP — scope drift.

- [ ] **Step 1.3: Capture knip + test baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```
Expected: 0 matches (knip still clean from Phase 105a).

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`. If red, STOP.

---

## Task 2: Edit 4 submodule files — drop `export` on 4 Bucket 4 functions

**Files:**
- Modify: 4 source files (1 line each)

For each file, the `export function` declaration becomes a plain `function` declaration (drop `export` keyword). Function body unchanged.

- [ ] **Step 2.1: Edit `health.js`**

Use Edit tool.

- **Find (old_string)**:
```
export function fetchHealth
```

- **Replace (new_string)**:
```
function fetchHealth
```

If the line format differs (e.g., has additional whitespace or modifier), use `head -45 apps/dashboard/src/api/health.js | tail -10` to view actual line and adapt.

- [ ] **Step 2.2: Edit `workflows.js`**

- **Find (old_string)**:
```
export function fetchActiveWorkflow
```

- **Replace (new_string)**:
```
function fetchActiveWorkflow
```

- [ ] **Step 2.3: Edit `studio.js`**

- **Find (old_string)**:
```
export function fetchStudioActive
```

- **Replace (new_string)**:
```
function fetchStudioActive
```

- [ ] **Step 2.4: Edit `creator.js`**

- **Find (old_string)**:
```
export function exportCreatorTemplateApprovalAudit
```

- **Replace (new_string)**:
```
function exportCreatorTemplateApprovalAudit
```

- [ ] **Step 2.5: Verify all 4 `export` keywords removed**

```bash
cd /home/ailearn/projects/LingWen && grep -nE "^export function (fetchHealth|fetchActiveWorkflow|fetchStudioActive|exportCreatorTemplateApprovalAudit)" apps/dashboard/src/api/health.js apps/dashboard/src/api/workflows.js apps/dashboard/src/api/studio.js apps/dashboard/src/api/creator.js
```
Expected: 0 matches.

---

## Task 3: Edit `api/index.js` — drop 11 barrel re-export entries

**Files:**
- Modify: 1 barrel file (11 line edits across multiple `export { ... } from '...'` blocks)

The barrel has 8 `export { ... } from '...'` blocks (one per sub-module). Each block uses multi-line formatting. Need to remove specific names from each block.

**Strategy**: Read the barrel file, identify each block, and remove the appropriate names per the spec's decision matrix.

- [ ] **Step 3.1: View the barrel to identify exact line locations**

```bash
cd /home/ailearn/projects/LingWen && cat -n apps/dashboard/src/api/index.js | head -30
```

This shows the first `export { ... } from './connectivity.js'` block (where `apiConnectivity`, `markApiOffline`, `markApiOnline` are re-exported).

- [ ] **Step 3.2: Edit barrel — drop `apiConnectivity`, `markApiOffline`, `markApiOnline` (Bucket 2)**

The first block in the barrel is:
```
export { apiConnectivity, markApiOffline, markApiOnline } from './connectivity.js';
```

Replace with:
```
export { } from './connectivity.js';
```

This removes all 3 names from the barrel. The submodule file `connectivity.js` retains the `export` keyword on each function (consumers using direct path still work).

Actually, if the export block becomes empty (`export { } from './connectivity.js'`), that's stylistically odd. Better to remove the entire line.

Use Edit tool:

- **Find (old_string)**:
```
export { apiConnectivity, markApiOffline, markApiOnline } from './connectivity.js';
```

- **Replace (new_string)**:
```

```

(empty — removes the line entirely; the next line `export { ... } from './health.js'` follows directly)

- [ ] **Step 3.3: Edit barrel — drop `fetchHealth` (Bucket 4)**

The health.js export block is:
```
export {
  fetchOverview,
  fetchChapters,
  fetchProductionRecords,
  fetchProductionRollup,
  fetchProductionCostTrend,
  fetchHealth,
} from './health.js';
```

Use Edit tool:

- **Find (old_string)**:
```
  fetchProductionCostTrend,
  fetchHealth,
} from './health.js';
```

- **Replace (new_string)**:
```
  fetchProductionCostTrend,
} from './health.js';
```

(Just remove the `fetchHealth,` line.)

- [ ] **Step 3.4: Edit barrel — drop `fetchActiveWorkflow` (Bucket 4)**

The workflows.js block:
```
export {
  fetchWorkflows,
  runWorkflow,
  resumeWorkflow,
  fetchActiveWorkflow,
  fetchWorkflowGraph,
} from './workflows.js';
```

- **Find (old_string)**:
```
  resumeWorkflow,
  fetchActiveWorkflow,
  fetchWorkflowGraph,
} from './workflows.js';
```

- **Replace (new_string)**:
```
  resumeWorkflow,
  fetchWorkflowGraph,
} from './workflows.js';
```

- [ ] **Step 3.5: Edit barrel — drop `exportCreatorTemplateApprovalAudit` (Bucket 4)**

The creator.js block has MANY exports. Need to drop ONE specific name.

First, locate the line:
```bash
cd /home/ailearn/projects/LingWen && grep -n "exportCreatorTemplateApprovalAudit," apps/dashboard/src/api/index.js
```
Expected: 1 match showing the line within the creator.js export block.

Then use Edit tool to remove that line:
- **Find (old_string)** — include surrounding context (prev line + the line + next line) for unambiguous match:
```
  exportCreatorTemplateApprovalChainConfig,
  exportCreatorTemplateApprovalAudit,
  exportCreatorTemplateApprovalHistory,
```

- **Replace (new_string)**:
```
  exportCreatorTemplateApprovalChainConfig,
  exportCreatorTemplateApprovalHistory,
```

(Just removes the middle line.)

- [ ] **Step 3.6: Edit barrel — drop 4 Bucket 2 names from creator.js block**

These are also in the creator.js export block:
- `deleteCreatorFactoryMergePresetPackage`
- `fetchCreatorFactoryVolumeTemplates`
- `fetchCreatorGlobalMergePreferences`
- `resolveCreatorFactoryMergePresetConflict`

Use 4 separate Edit tool calls (or batch if lines are adjacent).

For each, use Edit tool:
- **Find (old_string)**: include surrounding context (prev line + the line + next line) to disambiguate.
- **Replace (new_string)**: removes the middle line.

The exact lines can be located with:
```bash
cd /home/ailearn/projects/LingWen && grep -n "deleteCreatorFactoryMergePresetPackage\|fetchCreatorFactoryVolumeTemplates\|fetchCreatorGlobalMergePreferences\|resolveCreatorFactoryMergePresetConflict" apps/dashboard/src/api/index.js
```

For each match, the Edit pattern is the line + its 2 surrounding lines.

- [ ] **Step 3.7: Verify all 11 barrel entries removed**

```bash
cd /home/ailearn/projects/LingWen && for sym in fetchHealth fetchActiveWorkflow fetchStudioActive exportCreatorTemplateApprovalAudit apiConnectivity markApiOffline markApiOnline deleteCreatorFactoryMergePresetPackage fetchCreatorFactoryVolumeTemplates fetchCreatorGlobalMergePreferences resolveCreatorFactoryMergePresetConflict; do \
  count=$(grep -c "\b${sym}\b" apps/dashboard/src/api/index.js 2>/dev/null); \
  echo "$sym: barrel count = $count"; \
done
```
Expected: all 11 show `barrel count = 0`.

- [ ] **Step 3.8: Verify barrel size decreased**

```bash
cd /home/ailearn/projects/LingWen && wc -l apps/dashboard/src/api/index.js
```
Expected: ~155 lines (was 161, dropped 11 lines but may have minor variation).

---

## Task 4: Verify post-edit state

**Files:**
- Read-only verification.

- [ ] **Step 4.1: All 4 dead functions are now local (no `export` keyword)**

```bash
cd /home/ailearn/projects/LingWen && grep -nE "^function (fetchHealth|fetchActiveWorkflow|fetchStudioActive|exportCreatorTemplateApprovalAudit)" apps/dashboard/src/api/health.js apps/dashboard/src/api/workflows.js apps/dashboard/src/api/studio.js apps/dashboard/src/api/creator.js
```
Expected: 4 matches (one per function, all now local without `export`).

- [ ] **Step 4.2: All 4 dead functions have zero non-defining references (no consumer)**

```bash
cd /home/ailearn/projects/LingWen && for sym in fetchHealth fetchActiveWorkflow fetchStudioActive exportCreatorTemplateApprovalAudit; do \
  refs=$(grep -rn "\b${sym}\b" apps/dashboard/src apps/dashboard/tests --include="*.vue" --include="*.js" --include="*.ts" 2>/dev/null | grep -v "^apps/dashboard/src/api/" | wc -l); \
  echo "$sym: external refs = $refs"; \
done
```
Expected: all 4 show `external refs = 0` (only the defining file + barrel entry existed; barrel is now removed too).

- [ ] **Step 4.3: All 7 Bucket 2 functions still work via direct submodule imports**

Verify each Bucket 2 function is still exported from its submodule:
```bash
cd /home/ailearn/projects/LingWen && for sym in apiConnectivity markApiOffline markApiOnline deleteCreatorFactoryMergePresetPackage fetchCreatorFactoryVolumeTemplates fetchCreatorGlobalMergePreferences resolveCreatorFactoryMergePresetConflict; do \
  echo "--- $sym ---"; \
  grep -rn "^export.*\b${sym}\b\|export const ${sym}\|export function ${sym}\|export { .*\b${sym}\b" apps/dashboard/src/api/ 2>/dev/null | head -3; \
done
```
Expected: each shows the function is still `export`-ed from its submodule.

Verify each direct-path consumer can still import it (no syntax errors):
```bash
cd /home/ailearn/projects/LingWen && grep -rn "from.*api/connectivity\|from.*mergePreset\|from.*volumeTemplate" apps/dashboard/src apps/dashboard/tests --include="*.vue" --include="*.js" --include="*.ts" 2>/dev/null | head -10
```
Expected: matches for each of the 7 Bucket 2 consumers (verified in spec).

- [ ] **Step 4.4: Tests still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`. If any test fails, STOP — the deletion may have broken a consumer.

- [ ] **Step 4.5: Build + tsc + lint + knip all clean**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run build 2>&1 | tail -3
```
Expected: build OK.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -3
```
Expected: 0 errors.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm run lint:all 2>&1 | tail -3
```
Expected: clean.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted)"
```
Expected: 0 matches (knip still clean; `api/index.js` still in `knip.json#ignore`).

---

## Task 5: Commit + push

**Files:**
- Commit: 5 modified files (1 barrel + 4 submodule edits)

- [ ] **Step 5.1: Stage all 5 files**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/src/api/index.js apps/dashboard/src/api/health.js apps/dashboard/src/api/workflows.js apps/dashboard/src/api/studio.js apps/dashboard/src/api/creator.js && git status
```

Expected: 5 files modified, all staged.

- [ ] **Step 5.2: Commit with spec-defined message**

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): remove 4 dead functions + 7 redundant barrel entries from api/ (Phase 97)" -m "Phase 97 — api/index.js barrel re-export audit (158 exports):

Delete 4 truly-dead functions (zero consumers anywhere):
- fetchHealth (api/health.js)
- fetchActiveWorkflow (api/workflows.js)
- fetchStudioActive (api/studio.js)
- exportCreatorTemplateApprovalAudit (api/creator.js)

Remove 7 functions from barrel only (still consumed via direct submodule path):
- apiConnectivity (4 direct consumers: SettingsPage.vue,
  useFilteredPageError.js, 2 tests)
- markApiOffline (api/core.js internal consumer)
- markApiOnline (api/core.js + api/agent.js internal consumers)
- deleteCreatorFactoryMergePresetPackage (1 test direct consumer)
- fetchCreatorFactoryVolumeTemplates (1 test direct consumer)
- fetchCreatorGlobalMergePreferences (1 test direct consumer)
- resolveCreatorFactoryMergePresetConflict (1 test direct consumer)

Net: barrel drops 11 of 158 lines; 4 dead functions removed entirely.

All consumers verified by grep before edit. No callers of the 4 dead functions
exist. The 7 barrel-only-removals have no barrel consumers (verified).

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 5.3: Push to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```
Expected: push succeeds.

- [ ] **Step 5.4: Final state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```
Expected: 3 most recent commits include the Phase 97 commit. Tree clean.

---

## Success Criteria

- [ ] `apps/dashboard/src/api/index.js` drops 11 re-export entries (4 Bucket 4 + 7 Bucket 2)
- [ ] 4 submodule files drop `export` keyword on the 4 Bucket 4 functions
- [ ] All grep checks per spec §4.4 return expected counts
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] knip `api/index.js` still in ignore; other categories unchanged
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## Rollback

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## Self- Review Notes

**Spec coverage**:
- §4.1 Bucket 4 (4 deletes from BOTH barrel + submodule) → Task 2 (4 submodule edits) + Task 3.3/3.4/3.5 (3 barrel edits) ✅
- §4.1 Bucket 2 (7 barrel removals) → Task 3.2 (connectivity) + Task 3.6 (creator 4 names) ✅
- §4.4 Verification → Task 4.1-4.5 ✅
- §7 Commit Strategy → Task 5 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: No new types/functions. Only `export` keyword removals + barrel entry drops.

**Edge cases handled**:
- Task 1.2 confirm 4 dead functions have only 1 reference each (the defining file)
- Task 1.3 baseline tests + knip clean
- Task 2.5 verify all 4 `export` keywords removed (catch missed edit)
- Task 3.7 verify all 11 barrel entries removed
- Task 3.8 verify barrel size decreased (~155 lines)
- Task 4.1 verify 4 functions are now local
- Task 4.2 verify 4 dead functions have zero external refs (post-edit)
- Task 4.3 verify 7 Bucket 2 functions still work via direct submodule paths
- Task 4.4 tests pass (catch broken consumer)
- Task 4.5 full verification suite
- Rollback section