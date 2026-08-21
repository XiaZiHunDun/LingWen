# Phase 78 — Submodule shallowRef Extension 设计

> **日期**: 2026-08-21
> **范围**: 3 submodule `.ts` files code change. 11 wholesale-refs → shallowRef.
> **基础**: master = `74c12759` (Phase 77 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 77 code review M1 识别 3 submodule `.ts` 文件有 11 wholesale-refs 符合同 decision rule, 推荐扩展 shallowRef sweep.

---

## 1. 背景

Phase 77 (commit `73a9d297`) 在 facade 层 (`useStudioStore.js` + `useCreatorSettings.js`) 转换 22 wholesale-refs 到 shallowRef. Phase 77 code review (subagent) 指出:

> **M1**: 3 submodule `.ts` files 有 11 wholesale-refs 符合同 decision rule. Facade 文件已经优化, 但 submodule 内有相同 pattern, 扩展可获 11 more conversions.

Submodule 文件:
- `apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts`
- `apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts`
- `apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts`

这些 submodule 由 facade (`useCreatorSettings.js`) 通过 `mergePresets.X.value = ...` 桥接 — facade 持有 state, submodule 提供 helpers. Phase 77 已转换 facade refs. **Phase 78 扩展到 submodule 内部 wholesale-refs**.

---

## 2. 目标 & 非目标

### 目标

1. **useSettingsDocs.ts**: 4 ref → shallowRef
2. **useSettingsHistory.ts**: 1 ref → shallowRef
3. **useMergePresets.ts**: 5 ref → shallowRef
4. **保留**: 所有 primitives (booleans/strings/loading flags)
5. **不破坏**: 1549 unit tests
6. **1 atomic commit** (combined 3 files)

### 非目标

- 不删 6 dead `mergePreset*` refs (Phase 78c 候选)
- 不加 ESLint rule (Phase 78b 候选)
- 不动 facade files (Phase 77 已 done)
- 不动其他 stores/composables
- 不做新 audit (residual 485 reactives → 后续 phase)

---

## 3. Decision Rule (与 Phase 77 一致)

All 必须满足:
1. Declared as `ref(initialValue)` (not `reactive()`)
2. **Wholesale replacement** (`x.value = newData`), NOT property mutation (`x.value.foo = bar`)
3. No `computed()`/`watch()` reading `.value.<property>` for inner tracking
4. Initial value: `null`, simple object, or array

**KEEP candidates**:
- Primitives (booleans/strings/numbers) — no Proxy overhead either way
- Refs with property mutation (e.g., `cacheTimestamps.value[key] = ...`)
- Refs read inside `computed()` via `.value.<property>` if the value is mutated in-place (not wholesale)

---

## 4. File-Specific Conversions

### 4.1 File 1: `useSettingsDocs.ts`

Pre-scan reveals refs at lines 61-65+. Specific conversions (subject to per-ref verify at impl):

| Line | Ref | Initial | Justification |
|------|-----|---------|---------------|
| 61 | `pillarsText` | `ref('')` | verify wholesale `pillarsText.value = newVal` |
| 63 | `settingsDocs` | `ref(null)` | `settingsDocs.value = docs` |
| (verify) | `settingsDiffPreview` | `ref(null)` | wholesale at lines 115, 144 |
| (verify) | `mergeStrategyPreview` | `ref(...)` | wholesale at line 89 |
| (verify) | `threeWayPreview` | `ref(...)` | wholesale at line 101 |
| 64 | `showSettingsDiff` | `ref(false)` | **KEEP** primitive |
| 65 | `settingsSaving` | `ref(false)` | **KEEP** primitive |

**Expected**: 5 conversions.

### 4.2 File 2: `useSettingsHistory.ts`

| Line | Ref | Initial | Justification |
|------|-----|---------|---------------|
| 40 | `settingsHistory` | `ref([])` | `settingsHistory.value = data.snapshots \|\| data.history \|\| []` (lines 54, 57) |

**Expected**: 1 conversion.

### 4.3 File 3: `useMergePresets.ts`

| Line | Ref | Initial | Justification |
|------|-----|---------|---------------|
| 92 | `mergePresetPackages` | `ref([])` | `mergePresetPackages.value = data.packages \|\| []` (line 129) |
| 93 | `factoryMergePresetPackages` | `ref([])` | `factoryMergePresetPackages.value = factoryData.packages \|\| []` (line 131) |
| 96 | `mergePresetImportPreview` | `ref({...})` | `mergePresetImportPreview.value = data` (line 256) |
| 97 | `mergePreferences` | `ref(...)` | `mergePreferences.value = data` (line 140) |
| 103 | `mergePresetImportPreflight` | `ref(null)` | verify wholesale |

**Expected**: 5 conversions.

**KEEP (loading flags — primitives)**:
- `mergePresetFactoryPublishing`, `mergePresetFactoryPulling`, `mergePresetPackagesImporting`
- `mergePresetToposortApplying`, `mergePresetConflictFixing`, `mergePresetConflictFixingAll`
- `mergePresetImportPreflightLoading`, `mergePresetImportPreviewLoading`
- `mergePresetChangelogLoading`, etc.

---

## 5. Total Conversions

**11 conversions** across 3 files (subject to per-ref verify at impl):
- useSettingsDocs.ts: 4
- useSettingsHistory.ts: 1
- useMergePresets.ts: 5

---

## 6. Implementation Strategy

### 6.1 Order (mirror Phase 77)

1. **Per-ref verify** for each candidate (grep `.value.<prop>\s*=` → must be 0)
2. **Edit imports**: add `shallowRef` to vue import (or already there)
3. **Per-ref convert**: `const x = ref(...)` → `const x = shallowRef(...) // Phase 78: shallowRef — wholesale replacement`
4. **Run tests** (file-by-file or batched)
5. **Run vue-tsc + build**
6. **Verify grep counts**
7. **1 atomic commit**

### 6.2 Edit Pattern

```diff
- import { ref, computed, watch } from 'vue'
+ import { ref, shallowRef, computed, watch } from 'vue'

- const settingsDocs = ref(null)
+ const settingsDocs = shallowRef(null) // Phase 78: shallowRef — wholesale replacement
```

For `.ts` files with TypeScript types, the syntax is identical to `.js`:
```ts
const settingsHistory = ref<Array<Snapshot>>([])
```
becomes
```ts
const settingsHistory = shallowRef<Array<Snapshot>>([])
```

---

## 7. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm test` 1549 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep -c "shallowRef" useSettingsDocs.ts` | ≥ 4 |
| `grep -c "shallowRef" useSettingsHistory.ts` | ≥ 1 |
| `grep -c "shallowRef" useMergePresets.ts` | ≥ 5 |
| `git diff --stat` 3 files modified | ✓ |
| `// Phase 78: shallowRef — wholesale replacement` comments | 11/11 |
| `shallowRef` added to vue imports | 3/3 files |

---

## 8. 风险 & 缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Loading flag refs (booleans) 误转 | Low | no perf benefit (not harmful) | spec decision rule 排除 primitives |
| `mergePresetImportPreflight` line 103 实际有 property mutation | Low | reactivity bug | per-ref grep + manual verify |
| `.ts` types break with shallowRef | Low | TS compile error | vue-tsc check after edit |
| Facade `useCreatorSettings.js` 桥接 pattern 改变 | Low | integration break | 1549 tests catch this |

---

## 9. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

git add apps/dashboard/src/composables/useCreatorSettings/useSettingsDocs.ts \
        apps/dashboard/src/composables/useCreatorSettings/useSettingsHistory.ts \
        apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf(submodules): convert 11 wholesale-refs to shallowRef (Phase 78)" \
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

---

## 10. 测试策略

无新增 tests. 现有 1549 tests 验证 behavior unchanged (subagent co-located tests in `tests/unit/use-settings-docs.spec.ts`, `tests/unit/use-merge-presets.spec.ts`, `tests/unit/use-settings-history.spec.ts` use `.value` API, identical for `ref` and `shallowRef`).

---

## 11. 后续

Phase 79+ 候选 (per Phase 78 + Handoff §6):

1. **Phase 79**: INP measurement improvement (use `page.click()` 替代 synthetic click)
2. **Phase 80**: Bundle split (vendor 407kB / mermaid 390kB)
3. **Phase 81**: Live e2e verification (Phase 66 6 specs)
4. **Phase 82**: CLAUDE.md v13.1 housekeeping
5. **Phase 83**: `no-shallowref-mutation` ESLint rule (Phase 78b from review)
6. **Phase 84**: Dead `mergePreset*` submodule ref cleanup (Phase 78c from review)
7. **Phase 85+**: Residual 485 reactives audit

## 12. Phase 87 Amend Note

Phase 78 spec had count drift — actual implementation had 11 conversions, spec said 10. Corrected in this amend:

| Location | Was | Now |
|---------|-----|-----|
| Header | 10 wholesale-refs | 11 wholesale-refs |
| §1 background | 10 wholesale-refs | 11 wholesale-refs |
| §1 M1 list item | 10 wholesale-refs + 10 more conversions | 11 wholesale-refs + 11 more conversions |
| §4.1 footer (useSettingsDocs) | 4 conversions | 5 conversions |
| §5 Total | 10 conversions | 11 conversions |
| §7 Verification | 10/10 | 11/11 |
| §9 commit subject | 10 wholesale-refs | 11 wholesale-refs |

Rationale: implementer correctly identified useSettingsDocs had 5 conversions (not 4). Original commit `98c7aa89` amended from 9 → 11 conversions to fix same drift in commit message. Spec amended separately for completeness.

Phase 78 amend commit `a6d4afe2` already corrected commit message; this spec amend keeps the design doc consistent.
