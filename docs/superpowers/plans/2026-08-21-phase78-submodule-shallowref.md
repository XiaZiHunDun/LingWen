# Phase 78 Implementation Plan — Submodule shallowRef Extension

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Phase 77 shallowRef sweep to 3 submodule `.ts` files (10 wholesale-replaced refs → shallowRef).

**Architecture:** Mirror Phase 77 pattern: per-ref decision rule (wholesale replacement pattern verified via grep + manual read). Each conversion adds a `// Phase 78: shallowRef — wholesale replacement` comment. One atomic commit per Phase 78 implementation.

**Tech Stack:** Vue 3 shallowRef, TypeScript, grep, vitest, vue-tsc, vite.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase78-submodule-shallowref-design.md` (commit `560b0111`)

---

## File Structure

| File | Action | Refs |
|------|--------|------|
| `apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts` | **Modify** (4 conversions + comment) | pillarsText/settingsDocs + 2 verify |
| `apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts` | **Modify** (1 conversion + comment) | settingsHistory |
| `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts` | **Modify** (5 conversions + comments) | mergePresetPackages/factoryMergePresetPackages/mergePresetImportPreview/mergePreferences/mergePresetImportPreflight |

**Total**: 3 files modified, 1 atomic commit.

---

## Task 1: Verify + edit useSettingsDocs.ts

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts`

- [ ] **Step 1.1: Read full file**

Run: `wc -l apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts`
Expected: ~200 lines

Read full file to identify all ref declarations and mutation patterns.

- [ ] **Step 1.2: Per-ref verify — check NO property mutation on candidates**

For each candidate (pillarsText, settingsDocs, settingsDiffPreview, mergeStrategyPreview, threeWayPreview), run:

```bash
cd /home/ailearn/projects/LingWen
for ref in pillarsText settingsDocs settingsDiffPreview mergeStrategyPreview threeWayPreview; do
  echo "=== $ref ==="
  grep -nE "\b${ref}\.value\.\w+\s*=" apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts
done
```

Expected: **0 hits** for each candidate. If any ref has property mutation, mark as KEEP.

- [ ] **Step 1.3: Confirm wholesale assignment exists**

```bash
for ref in pillarsText settingsDocs settingsDiffPreview mergeStrategyPreview threeWayPreview; do
  echo "=== $ref ==="
  grep -nE "\b${ref}\.value\s*=" apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts
done
```

Expected: at least 1 hit per ref.

- [ ] **Step 1.4: Edit imports — add `shallowRef` to vue import**

Use Edit tool. Read current import first.

- [ ] **Step 1.5: Convert 4 refs to shallowRef**

For each verified candidate, use Edit tool:
- Pattern: `const <name> = ref(<init>);` or `const <name> = ref<...>(<init>);` → `const <name> = shallowRef<...>(<init>); // Phase 78: shallowRef — wholesale replacement`

For `.ts` files with TypeScript types:
```ts
const x = ref<T>([])
// becomes
const x = shallowRef<T>([]) // Phase 78: shallowRef — wholesale replacement
```

- [ ] **Step 1.6: Verify file syntax (TS-aware)**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

---

## Task 2: Verify + edit useSettingsHistory.ts

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts`

- [ ] **Step 2.1: Read full file**

Run: `wc -l apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts`

- [ ] **Step 2.2: Per-ref verify `settingsHistory`**

```bash
grep -nE "\bsettingsHistory\.value\.\w+\s*=" apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts
grep -nE "\bsettingsHistory\.value\s*=" apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts
```

Expected: 0 property mutations, ≥1 wholesale assignment (lines 54, 57).

- [ ] **Step 2.3: Edit imports — add `shallowRef`**

Use Edit tool.

- [ ] **Step 2.4: Convert 1 ref**

For `settingsHistory`: `ref<Array<Snapshot>>([])` → `shallowRef<Array<Snapshot>>([]) // Phase 78: shallowRef — wholesale replacement`

- [ ] **Step 2.5: Verify syntax**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`

---

## Task 3: Verify + edit useMergePresets.ts

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`

- [ ] **Step 3.1: Read full file**

Run: `wc -l apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`
Expected: ~200+ lines (largest submodule)

- [ ] **Step 3.2: Per-ref verify 5 candidates**

```bash
for ref in mergePresetPackages factoryMergePresetPackages mergePresetImportPreview mergePreferences mergePresetImportPreflight; do
  echo "=== $ref ==="
  grep -nE "\b${ref}\.value\.\w+\s*=" apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
  grep -nE "\b${ref}\.value\s*=" apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
done
```

Expected: 0 property mutations, ≥1 wholesale assignment per candidate.

- [ ] **Step 3.3: Edit imports — add `shallowRef`**

Use Edit tool.

- [ ] **Step 3.4: Convert 5 refs**

For each verified candidate, Edit with pattern:
```ts
const x = ref<...>(...) // becomes
const x = shallowRef<...>(...) // Phase 78: shallowRef — wholesale replacement
```

- [ ] **Step 3.5: Verify syntax**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`

---

## Task 4: Final verifications

**Files:** None (verification only)

- [ ] **Step 4.1: Run unit tests**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -10`
Expected: `Tests  1549 passed (1549)` (unchanged)

- [ ] **Step 4.2: vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

- [ ] **Step 4.3: Build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -5`
Expected: `✓ built in <time>`

- [ ] **Step 4.4: Verify shallowRef counts**

Run:
```bash
echo "useSettingsDocs.ts:"; grep -c "shallowRef" apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts
echo "useSettingsHistory.ts:"; grep -c "shallowRef" apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts
echo "useMergePresets.ts:"; grep -c "shallowRef" apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
```

Expected: ≥4, ≥1, ≥5 respectively.

- [ ] **Step 4.5: git diff stat**

Run: `cd /home/ailearn/projects/LingWen && git diff --stat`
Expected: 3 files modified.

---

## Task 5: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 5.1: Stage 3 modified files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts \
        apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts \
        apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts
```

- [ ] **Step 5.2: Verify staged**

Run: `git status -s`
Expected: 3 modified files, no other changes.

- [ ] **Step 5.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf(submodules): convert 10 wholesale-refs to shallowRef (Phase 78)" \
    -m "Phase 78 submodule shallowRef extension (per Phase 77 code review M1):

useSettingsDocs.ts (4 conversions):
- pillarsText, settingsDocs, settingsDiffPreview, mergeStrategyPreview, threeWayPreview

useSettingsHistory.ts (1 conversion):
- settingsHistory

useMergePresets.ts (5 conversions):
- mergePresetPackages, factoryMergePresetPackages
- mergePresetImportPreview, mergePreferences
- mergePresetImportPreflight

KEEP (primitives — no Proxy overhead):
- showSettingsDiff, settingsSaving (booleans)
- mergePresetFactoryPublishing, mergePresetFactoryPulling, etc (loading flags)

Vue 3 default ref(obj) is deep reactive — entire object tree wrapped in Proxy.
shallowRef only tracks .value reference change.
For wholesale-replaced refs, this eliminates proxy overhead.

Same Phase 77 decision rule applied to submodule layer.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

- [ ] **Step 5.4: Verify commit**

Run: `git show --stat HEAD`
Expected: 3 files changed, all `.ts`.

- [ ] **Step 5.5: Final log check**

Run: `git log --oneline -3`

- [ ] **Step 5.6: Confirm no auto-push**

Run: `git status -sb | head -3`

---

## Self-Review

**Spec coverage**:
- Spec §4.1 useSettingsDocs.ts (4 conversions) → Task 1
- Spec §4.2 useSettingsHistory.ts (1 conversion) → Task 2
- Spec §4.3 useMergePresets.ts (5 conversions) → Task 3
- Spec §2 Goal 5 (1549 tests) → Task 4.1
- Spec §2 Goal 6 (1 atomic commit) → Task 5

**Placeholder scan**:
- All Edit patterns have actual code
- All grep commands have expected output

**Type consistency**:
- `shallowRef<T>` syntax matches Vue 3 + TypeScript
- Comment format consistent with Phase 77

**Risks covered**:
- Per-ref verify in Tasks 1.2-3.2 catches property mutation
- Test check in Task 4.1 catches regression early
- vue-tsc checks after each file catch type issues
