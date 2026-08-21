# Phase 84 Implementation Plan — Dead `mergePreset*` Refs Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete 7 dead `mergePreset*` refs (4 main + 3 loading flags) in BOTH parent `useCreatorSettings.js` + submodule `useMergePresets.ts`. Remove from declarations, panelContext returns, Ref<...> type defs.

**Architecture:** Surgical deletions only. No behavior change. 1 atomic commit (both files logically related).

**Tech Stack:** Vue 3 + Pinia + TypeScript submodule, Edit tool, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase84-dead-mergepreset-refs-cleanup-design.md` (commit `8d45cb42`)

---

## File Structure

| File | Action | Lines Deleted |
|------|--------|----------------|
| `apps/dashboard/src/composables/useCreatorSettings.js` | **Modify** (delete 4 declarations + 4 panelContext returns) | ~8 |
| `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts` | **Modify** (delete 4 declarations + 4 panelContext returns + 7 type defs + 3 loading flag declarations) | ~16 |

**Total**: 2 files modified, ~24 lines deleted, 1 atomic commit.

---

## Task 1: Pre-flight verify (no external consumers)

**Files:** None (verification only)

- [ ] **Step 1.1: Verify all 7 refs are dead**

Run:
```bash
cd /home/ailearn/projects/LingWen
echo "=== Main refs (Graph/Conflicts/ConflictFixes/Toposort) ==="
grep -rn "mergePresetGraph\|mergePresetConflicts\|mergePresetConflictFixes\|mergePresetToposort" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null \
  | grep -vE "(useCreatorSettings\.js:|useMergePresets\.ts:)"

echo "=== Loading flags ==="
grep -rn "mergePresetGraphLoading\|mergePresetConflictsLoading\|mergePresetConflictFixesLoading" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null
```

Expected: **Empty output** for both (no other consumers).

- [ ] **Step 1.2: Verify 1549 tests don't reference these refs**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -rn "mergePresetGraph\|mergePresetConflicts\|mergePresetConflictFixes\|mergePresetToposort" \
  apps/dashboard/tests --include="*.ts" --include="*.js" 2>/dev/null
```

Expected: **Empty output** (no test references).

---

## Task 2: Edit useCreatorSettings.js (parent) - delete 8 lines

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings.js`

- [ ] **Step 2.1: Read declarations section (around line 93-100)**

Run: `sed -n '90,105p' apps/dashboard/src/composables/useCreatorSettings.js`
Confirm exact text for 4 declaration lines (mergePresetToposort + Graph + Conflicts + ConflictFixes).

- [ ] **Step 2.2: Delete 4 declarations**

Use Edit tool to delete lines 93, 98, 99, 100 (4 shallowRef declarations).

For each declaration line:
- **old_string**: `  const <name> = shallowRef(<init>); // Phase 77: shallowRef — wholesale replacement\n`
- **new_string**: (empty, just remove the line)

Note: For mergePresetToposort (line 93), use the exact line as old_string.

- [ ] **Step 2.3: Read panelContext return section (around line 595-610)**

Run: `sed -n '590,612p' apps/dashboard/src/composables/useCreatorSettings.js`

- [ ] **Step 2.4: Delete 4 panelContext return entries**

Use Edit tool. For each entry:
- **old_string**: `    <name>,\n`
- **new_string**: (empty)

Targets: `mergePresetToposort,`, `mergePresetGraph,`, `mergePresetConflicts,`, `mergePresetConflictFixes,` (in panelContext return object).

- [ ] **Step 2.5: Verify file syntax**

Run: `node -c apps/dashboard/src/composables/useCreatorSettings.js && echo "syntax OK"`
Expected: `syntax OK`

---

## Task 3: Edit useMergePresets.ts (submodule) - delete ~16 lines

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`

- [ ] **Step 3.1: Read return type def section (around line 45-75)**

Run: `sed -n '45,80p' apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`
Confirm exact text for Ref<...> type defs (4 main + 3 loading flags = 7 type defs).

- [ ] **Step 3.2: Delete 7 Ref<...> type defs**

Use Edit tool to remove lines 49, 52-54 (main refs) + 70-72 (loading flags).

For each type def line:
- **old_string**: `  <name>: Ref<...>;\n`
- **new_string**: (empty)

- [ ] **Step 3.3: Read declarations section (around line 93-120)**

Run: `sed -n '93,122p' apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`

- [ ] **Step 3.4: Delete 4 main ref declarations**

For lines 95, 98, 99, 100:
- **old_string**: `  const <name> = ref(<init>);\n`
- **new_string**: (empty)

Targets: `mergePresetConflicts`, `mergePresetToposort`, `mergePresetGraph`, `mergePresetConflictFixes`.

- [ ] **Step 3.5: Delete 3 loading flag declarations**

For lines 117, 118, 119:
- **old_string**: `  const <name> = ref(false);\n`
- **new_string**: (empty)

Targets: `mergePresetGraphLoading`, `mergePresetConflictsLoading`, `mergePresetConflictFixesLoading`.

- [ ] **Step 3.6: Read panelContext return section (around line 290-320)**

Run: `sed -n '290,320p' apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`

- [ ] **Step 3.7: Delete 7 panelContext return entries**

For each entry:
- **old_string**: `    <name>,\n`
- **new_string**: (empty)

Targets: `mergePresetConflicts,`, `mergePresetToposort,`, `mergePresetGraph,`, `mergePresetConflictFixes,`, `mergePresetGraphLoading,`, `mergePresetConflictsLoading,`, `mergePresetConflictFixesLoading,`.

- [ ] **Step 3.8: Verify TS syntax**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

---

## Task 4: Final verifications

**Files:** None (verification only)

- [ ] **Step 4.1: grep verification — main refs**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -rn "mergePresetGraph\|mergePresetConflicts\|mergePresetConflictFixes\|mergePresetToposort" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```
Expected: `0`

- [ ] **Step 4.2: grep verification — loading flags**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -rn "mergePresetGraphLoading\|mergePresetConflictsLoading\|mergePresetConflictFixesLoading" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
```
Expected: `0`

- [ ] **Step 4.3: pnpm test**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)` (unchanged)

- [ ] **Step 4.4: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3`
Expected: 0 errors

- [ ] **Step 4.5: build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>`

- [ ] **Step 4.6: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat`
Expected: 2 files modified, negative line count (deletions only).

---

## Task 5: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 5.1: Stage 2 files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useCreatorSettings.js \
        apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
```

- [ ] **Step 5.2: Verify staged**

Run: `git status -s`
Expected: 2 modified files.

- [ ] **Step 5.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(useCreatorSettings): delete 7 dead mergePreset* refs (Phase 84)" \
    -m "Phase 84 dead ref cleanup (per Phase 78 review):

Delete 4 main refs (never written, never read):
- mergePresetGraph
- mergePresetConflicts
- mergePresetConflictFixes
- mergePresetToposort

Delete 3 loading flags (never set, never read):
- mergePresetGraphLoading
- mergePresetConflictsLoading
- mergePresetConflictFixesLoading

Removed from:
- useCreatorSettings.js (parent): declarations + panelContext returns
- useMergePresets.ts (submodule): declarations + panelContext returns + Ref<...> type defs

Total: ~24 lines deleted across 2 files. No behavior change.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 5.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 2 files changed, negative line counts.

- [ ] **Step 5.5: Final log**

Run: `git log --oneline -3`

---

## Self-Review

**Spec coverage**:
- Spec §4.1 (parent deletions) → Task 2
- Spec §4.2 (submodule deletions) → Task 3
- Spec §5 (verification) → Task 4
- Spec §7 (1 atomic commit) → Task 5

**Placeholder scan**:
- All Edit patterns have actual code from spec §4
- All grep commands have expected output

**Type consistency**:
- Same shallowRef (parent) vs ref (submodule) types preserved for kept refs
- Loading flags are `ref(false)` — preserve type

**Risks covered**:
- Step 1.1 verifies no other consumers before delete
- Step 1.2 verifies no test references
- Step 4.4 catches TS errors post-delete
- Step 4.5 catches build errors

## Rollback Strategy

If issues:
```bash
cd /home/ailearn/projects/LingWen
git checkout apps/dashboard/src/composables/useCreatorSettings.js \
              apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
```
