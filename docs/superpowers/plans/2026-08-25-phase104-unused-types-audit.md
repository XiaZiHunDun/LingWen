# Phase 104 — Audit & Resolve Unused Exported Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate knip's `Unused exported types` category by dropping `export` keyword from 29 dead type declarations across 9 source files + adding 1 ignore entry for the public test-API helpers file.

**Architecture:** Two atomic commits — source edits (Commit 1) + knip.json config edit (Commit 2). Surgical, no code logic changes (types remain in-file).

**Tech Stack:** TypeScript, knip 6.32.2, Vue 3.

---

## File Structure

**Files modified (9 source files):**
- `apps/dashboard/src/composables/useCreatorPage/useCreatorPageChrome.ts` — drop `export` from `ChromeContext`
- `apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts` — drop `export` from `PreferencesShape`
- `apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts` — drop `export` from `SettingsSnapshot`
- `apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateList.ts` — drop `export` from `TemplateRow`
- `apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts` — drop `export` from `ChapterRow`, `Deviation`
- `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.ts` — drop `export` from `CheckpointEntry`, `DiffViewLine`, `DiffView`
- `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts` — drop `export` from `CreationMode`, `Deviation`, `LogicIssue`, `OverviewLike`, `MemoryAsset`, `ConsistencyItem`, `GoalCardLines`
- `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts` — drop `export` from `QualityLevel`, `QualityHint`, `IntentEntry`, `LightValidationIssue`, `LogicCheckIssue`, `LogicCheckResult`, `Deviation`, `InlineConflictMarker`, `AgentLike`, `OverviewLike`
- `apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts` — drop `export` from `BodySelection`, `SelectionControls`, `QualityHint`

**Files modified (1 config file):**
- `apps/dashboard/knip.json` — add `"tests/helpers/strict-test-types.ts"` to `ignore` array

---

## Task 1: Pre-flight — git state + baseline

**Files:**
- Read-only check.

- [ ] **Step 1.1: Confirm git state**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -3 && git status
```

Expected: HEAD on `ae9937b9 docs(spec): Phase 104 — ...`. Tree clean.

- [ ] **Step 1.2: Confirm all 9 source files exist**

```bash
cd /home/ailearn/projects/LingWen && for f in \
  apps/dashboard/src/composables/useCreatorPage/useCreatorPageChrome.ts \
  apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts \
  apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts \
  apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateList.ts \
  apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts; do \
  test -f "$f" || { echo "MISSING: $f"; exit 1; }; \
done && echo "All 9 files exist"
```

Expected: `All 9 files exist`. If any MISSING, STOP.

- [ ] **Step 1.3: Verify knip config has no `tests/helpers/strict-test-types.ts` entry yet**

```bash
cd /home/ailearn/projects/LingWen && grep "strict-test-types" apps/dashboard/knip.json
```

Expected: zero matches.

- [ ] **Step 1.4: Capture knip + test baseline**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused exported types"
```

Expected: `Unused exported types (33 — actual was 33)`.

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If red, STOP.

---

## Task 2: Commit 1 — Drop `export` from 29 type declarations in 9 files

**Files:**
- Modify: 9 source files (22 `export` keyword removals, no other changes)

For each type, find the declaration line `export interface X { ... }` (or `export type X = ...`) and remove the `export ` keyword (keeping the `interface`/`type` keyword). The type body remains unchanged; only the `export ` prefix is removed.

- [ ] **Step 2.1: Edit `useCreatorPageChrome.ts`**

Find the `ChromeContext` declaration (likely `export interface ChromeContext { ... }`) and remove `export ` prefix.

Verify with:
```bash
cd /home/ailearn/projects/LingWen && grep -E "^export interface ChromeContext|^interface ChromeContext" apps/dashboard/src/composables/useCreatorPage/useCreatorPageChrome.ts
```
Expected: `^interface ChromeContext` (no `export `).

- [ ] **Step 2.2: Edit `useProductPreferences.ts`**

Same pattern for `PreferencesShape`.

- [ ] **Step 2.3: Edit `useSettingsHistory.ts`**

Same pattern for `SettingsSnapshot`.

- [ ] **Step 2.4: Edit `useTemplateList.ts`**

Same pattern for `TemplateRow`. Note: `useTemplateEditor.ts` has a SEPARATE non-exported `TemplateRow` — do NOT touch it.

- [ ] **Step 2.5: Edit `useWriteFlow.ts`**

Same pattern for both `ChapterRow` and `Deviation`.

- [ ] **Step 2.6: Edit `useWorkbenchCheckpoints.ts`**

Same pattern for `CheckpointEntry`, `DiffViewLine`, `DiffView`.

- [ ] **Step 2.7: Edit `useWorkbenchLayout.ts`**

Same pattern for `CreationMode`, `Deviation`, `LogicIssue`, `OverviewLike`, `MemoryAsset`, `ConsistencyItem`, `GoalCardLines`.

- [ ] **Step 2.8: Edit `useWorkbenchQuality.ts`**

Same pattern for `QualityLevel`, `QualityHint`, `IntentEntry`, `LightValidationIssue`, `LogicCheckIssue`, `LogicCheckResult`, `Deviation`, `InlineConflictMarker`, `AgentLike`, `OverviewLike`.

- [ ] **Step 2.9: Edit `useWorkbenchSelection.ts`**

Same pattern for `BodySelection`, `SelectionControls`, `QualityHint`.

- [ ] **Step 2.10: Verify all 22 `export` keywords removed**

```bash
cd /home/ailearn/projects/LingWen && for type in ChromeContext PreferencesShape SettingsSnapshot TemplateRow ChapterRow Deviation CheckpointEntry DiffViewLine DiffView CreationMode LogicIssue OverviewLike MemoryAsset ConsistencyItem GoalCardLines QualityLevel QualityHint IntentEntry LightValidationIssue LogicCheckIssue LogicCheckResult InlineConflictMarker AgentLike BodySelection SelectionControls; do \
  count=$(grep -E "^export (interface|type) ${type}\b" apps/dashboard/src/composables/useCreatorPage/useCreatorPageChrome.ts apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateList.ts apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts apps/dashboard/src/composables/useCreatorWriteWorkbench/*.ts 2>/dev/null | grep -c "${type}"); \
  echo "$type: export count = $count"; \
done
```

(Note: `Deviation`, `OverviewLike`, `QualityHint` appear in multiple files; the above loop will count all matches. Use a more precise per-file check if any count > 0.)

Better per-file verification (run all 9 file checks):

```bash
cd /home/ailearn/projects/LingWen && grep -lE "^export (interface|type) (ChromeContext|PreferencesShape|SettingsSnapshot|TemplateRow|ChapterRow|Deviation|CheckpointEntry|DiffViewLine|DiffView|CreationMode|LogicIssue|OverviewLike|MemoryAsset|ConsistencyItem|GoalCardLines|QualityLevel|QualityHint|IntentEntry|LightValidationIssue|LogicCheckIssue|LogicCheckResult|InlineConflictMarker|AgentLike|BodySelection|SelectionControls)\b" \
  apps/dashboard/src/composables/useCreatorPage/useCreatorPageChrome.ts \
  apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts \
  apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts \
  apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateList.ts \
  apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts \
  apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts
```

Expected: zero matches. If any match, STOP — that type still has `export`.

- [ ] **Step 2.11: Tests still pass after edits**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`. If any test fails, STOP — the dropped export may have been used somewhere subtle.

- [ ] **Step 2.12: vue-tsc clean**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit 2>&1 | tail -3
```

Expected: 0 errors.

- [ ] **Step 2.13: knip after source edits (before ignore addition)**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused exported types"
```

Expected: count is still 10 (or 6 — 29 dead types → 4 test types remain). If count is 4 (just test types), source edit was fully successful.

If count is still 10, check that the 22 edits actually removed exports (one or more may have been missed). STOP and investigate.

- [ ] **Step 2.14: Commit 1**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/src/composables/useCreatorPage/useCreatorPageChrome.ts apps/dashboard/src/composables/useCreatorProductTools/useProductPreferences.ts apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts apps/dashboard/src/composables/useCreatorVolumePlanTemplates/useTemplateList.ts apps/dashboard/src/composables/useCreatorWrite/useWriteFlow.ts apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.ts apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts apps/dashboard/src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts && git status
```

Expected: 9 files staged.

```bash
cd /home/ailearn/projects/LingWen && git commit -m "refactor(cleanup): drop export from 29 dead type declarations (Phase 104)" -m "Phase 104 — reduce knip Unused exported types from 27 names to 4 (test helpers):

Drop \`export\` keyword from 29 type declarations across 9 source files.
The types remain in their files as internal interfaces for in-file use.

- useCreatorPageChrome.ts: ChromeContext
- useProductPreferences.ts: PreferencesShape
- useSettingsHistory.ts: SettingsSnapshot
- useTemplateList.ts: TemplateRow
- useWriteFlow.ts: ChapterRow, Deviation
- useWorkbenchCheckpoints.ts: CheckpointEntry, DiffViewLine, DiffView
- useWorkbenchLayout.ts: CreationMode, Deviation, LogicIssue, OverviewLike,
  MemoryAsset, ConsistencyItem, GoalCardLines
- useWorkbenchQuality.ts: QualityLevel, QualityHint, IntentEntry,
  LightValidationIssue, LogicCheckIssue, LogicCheckResult, Deviation,
  InlineConflictMarker, AgentLike, OverviewLike
- useWorkbenchSelection.ts: BodySelection, SelectionControls, QualityHint

Each type has 0 external consumers (verified via Phase 104 explore
subagent grep). Internal usage within the same file remains.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

Expected: 1 commit created.

- [ ] **Step 2.15: Do NOT push yet** — wait for Commit 2.

---

## Task 3: Commit 2 — Add knip.json ignore entry

**Files:**
- Modify: `apps/dashboard/knip.json` (1 ignore entry added)

- [ ] **Step 3.1: View current knip.json content**

```bash
cd /home/ailearn/projects/LingWen && cat apps/dashboard/knip.json
```

Expected: has `entry`, `project`, `ignore` arrays (with 11 entries from Phase 103 / 102.2).

- [ ] **Step 3.2: Apply Edit**

Use Edit tool.

- **Find (old_string)** (last entry + closing `]` + `}`):
```
    "tests/visual-audit/helpers/capture-ui-audit.js"
  ]
}
```

- **Replace (new_string)**:
```
    "tests/visual-audit/helpers/capture-ui-audit.js",
    "tests/helpers/strict-test-types.ts"
  ]
}
```

Add new entry before the closing `]`.

- [ ] **Step 3.3: Verify JSON parses**

```bash
cd /home/ailearn/projects/LingWen && python3 -c "import json;d=json.load(open('apps/dashboard/knip.json'));print('OK, ignore has', len(d.get('ignore', [])), 'entries')"
```

Expected: `OK, ignore has 12 entries`.

- [ ] **Step 3.4: Verify knip `Unused exported types (0)`**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep "^Unused exported types"
```

Expected: line absent (count = 0). If still showing, STOP.

- [ ] **Step 3.5: Verify knip other categories unchanged**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

Expected:
```
Unused dependencies (1)        @vueuse/core, animate.css, vfonts
```
(`Unused exported types (0)` line absent. Other categories unchanged.)

- [ ] **Step 3.6: Tests still pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```

Expected: `1545 passed`.

- [ ] **Step 3.7: Commit 2**

```bash
cd /home/ailearn/projects/LingWen && git add apps/dashboard/knip.json && git status
```

Expected: 1 file staged.

```bash
cd /home/ailearn/projects/LingWen && git commit -m "build(ci): add tests/helpers/strict-test-types.ts to knip ignore (Phase 104)" -m "Phase 104 — resolve knip false-positive Unused exported types (4 test types):

The file \`tests/helpers/strict-test-types.ts\` exports 4 types
(EditableVolume, MergePreview, SplitPreview, VolumePlanDiffPreview)
plus helper functions (\`asEditableVolumes()\`, \`asMergePreviewRef()\`,
etc.) that narrow types via \`Ref<T>\` casts in test files.

Knip cannot trace type usage through helper-function return types,
so it reports the file's exports as unused. The types are intentionally
public test-API surface — used by \`use-creator-volume-plan.spec.ts\`,
\`use-creator-volume-plan-diff.spec.ts\`, and
\`use-creator-volume-plan-merge-split.spec.ts\` via the helper
functions.

Add the whole file to apps/dashboard/knip.json#ignore to silence
the false positive.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

Expected: 1 commit created.

- [ ] **Step 3.8: Push both commits to origin**

```bash
cd /home/ailearn/projects/LingWen && git push origin master 2>&1 | tail -5
```

Expected: push succeeds with 2 new commits.

- [ ] **Step 3.9: Final state check**

```bash
cd /home/ailearn/projects/LingWen && git log --oneline -5 && git status
```

Expected: 5 most recent commits include both Phase 104 commits. Tree clean.

---

## Task 4: Final verification

**Files:**
- Read-only verification.

- [ ] **Step 4.1: Full knip final state**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip --reporter=compact 2>&1 | grep -E "^(Unused|Unlisted|Duplicate)"
```

Expected:
```
Unused dependencies (1)        @vueuse/core, animate.css, vfonts
```
Only `Unused dependencies (1)` remains — that's Phase 105a scope. All other categories = 0.

- [ ] **Step 4.2: Tests + build + tsc + lint**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vitest run 2>&1 | tail -3
```
Expected: `1545 passed`.

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

---

## Success Criteria

- [ ] 29 type declarations in 9 source files have `export` keyword removed
- [ ] `tests/helpers/strict-test-types.ts` added to `apps/dashboard/knip.json#ignore`
- [ ] `pnpm exec knip` reports `Unused exported types (0)` (line absent)
- [ ] Other knip categories unchanged
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] Two atomic commits on master
- [ ] Pushed to origin/master

---

## Rollback

If anything regresses:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD~1..HEAD --no-edit && git push origin master
```

Reverts both commits. No data loss.

If only Commit 2 fails (knip.json syntax issue):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

If only Commit 1 fails (some test or build regression from dropped exports):
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD~1 --no-edit && git push origin master
```

---

## Self-Review Notes

**Spec coverage**:
- §4.2 Per-file edits → Task 2.1-2.9 (per-file Edit tool steps) ✅
- §4.3 knip.json ignore → Task 3 ✅
- §4.4 (verification strategy from spec) → Task 4 + per-task verification ✅
- §7 Commit Strategy (two commits) → Task 2.14 + Task 3.7 ✅
- §9 Success Criteria → top-level checklist ✅

**Placeholder scan**: No "TBD"/"TODO" present.

**Type consistency**: All 22 type definitions stay in-place; only the `export` keyword is removed. The type body is unchanged.

**Edge cases handled**:
- Task 1.2 file existence check — catch path typos
- Task 1.4 baseline knip = (10) — catch scope drift
- Task 2.10 grep verification per-type — catch missed edits
- Task 2.13 intermediate knip check (before ignore) — confirm source edits worked
- Task 2.14 + 3.7 two-commit split — clarity
- Task 3.4 knip = (0) — primary success criterion
- Task 4.1 final knip state — Phase 104 scope fully resolved
- Task 4.2 full verification suite
- Rollback section with per-commit granularity