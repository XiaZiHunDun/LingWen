# Phase 77 — shallowRef for Wholesale-Replaced Refs 设计

> **日期**: 2026-08-21
> **范围**: 2 files code change (useStudioStore.js + useCreatorSettings.js). Code only.
> **基础**: master = `c9884e87` (Phase 76 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

---

## 1. 背景

Phase 76 baseline 揭示 Vue 3 reactive proxy overhead 在 4 routes × 3 runs × 5 metrics 共 60 measurements 中体现。所有 4 routes pass Core Web Vitals targets，但:
- 485 reactives 仅 1 file 用 markRaw (`useWidgetRegistry.js`)
- useStudioStore 11+ refs 中 7 个 large nullable objects 用 `ref()` (deep reactive by default)
- useCreatorSettings 26 refs 中多个 large object/array refs 同样深度响应式

Vue 3 中 `ref(obj)` 默认 deep reactive — 整个 object tree 都被 Proxy 包装, 每个 property access 都触发 reactive getter. 对仅**整批替换** (`x.value = newData`) 的 ref, 这是浪费的。

Phase 76 baseline §6 已识别 Phase 77 候选 (markRaw/shallowRef 优化).

---

## 2. 目标 & 非目标

### 目标

1. **useStudioStore.js**: 7 ref → shallowRef (wholesale-replaced large nullable objects)
2. **useCreatorSettings.js**: ~10-15 ref → shallowRef (wholesale-replaced object/array)
3. **保留**: 1 个 `cacheTimestamps` ref (nested property mutation)
4. **保留**: 所有 primitives (`loading/error/activeSlug/projectRevision/...`)
5. **不破坏**: 1549 unit tests + 31 e2e specs (含 Phase 76 baseline)
6. **1-2 atomic commits**

### 非目标

- 不改 chart components (Phase 76 已确认最优 — `let chartInstance` 本地变量)
- 不改其他 stores (useNavStore Phase 64 已优化; useConnectivityStore/useRoleStore 简单)
- 不集成 VueUse `toShallow` 等第三方工具
- 不做 comprehensive 485 reactives audit (Phase 78+ 可选)
- 不强行 before/after perf 对比 (环境 noise 风险)
- 不加 `effectScope` 或其他 advanced patterns

---

## 3. Decision Rule

**shallowRef 适用条件** (all 必须满足):
1. Variable declared 为 `ref(initialValue)` (not `reactive()`)
2. Mutation pattern: **wholesale replacement** (`x.value = newData`), NOT property mutation (`x.value.foo = bar`)
3. No `computed()`/`watch()` reading `.value.<property>` to track inner changes (would need deep reactive)
4. Initial value: `null`, simple object, or array

**NOT 适用**:
- `cacheTimestamps.value[key] = Date.now()` (line 73 useStudioStore) — property mutation
- `reactive({})` — already shallow in different sense
- Nested mutations anywhere
- Templates that access `.value.foo.bar` AND need reactivity (would need deep)

---

## 4. File 1: `apps/dashboard/src/stores/useStudioStore.js` (240 lines)

### 4.1 Pre-scan (line 46-66)

```js
const projects = ref([])
const activeSlug = ref(null)
const summary = ref(null)
const overview = ref(null)
const loading = ref(false)
const quality = ref(null)
const qualityReport = ref(null)
const proseDiff = ref(null)
const proseJudge = ref(null)
const error = ref(null)
const projectRevision = ref(0)

const cacheTimestamps = ref({...})
```

### 4.2 Conversion Table (Phase 77 candidates)

| Line | Ref | Current | Proposed | Justification |
|------|-----|---------|----------|---------------|
| 46 | `projects` | `ref([])` | `shallowRef([])` | Wholesale: `projects.value = data.projects` (line 95) |
| 47 | `activeSlug` | `ref(null)` | **KEEP** | Primitive string, cheap |
| 48 | `summary` | `ref(null)` | `shallowRef(null)` | Wholesale: `summary.value = data` (line 123) |
| 49 | `overview` | `ref(null)` | `shallowRef(null)` | Wholesale (verify line ~130) |
| 50 | `loading` | `ref(false)` | **KEEP** | Primitive boolean |
| 51 | `quality` | `ref(null)` | `shallowRef(null)` | Wholesale (verify line ~135) |
| 52 | `qualityReport` | `ref(null)` | `shallowRef(null)` | Wholesale (verify line ~140) |
| 53 | `proseDiff` | `ref(null)` | `shallowRef(null)` | Wholesale (verify line ~145) |
| 54 | `proseJudge` | `ref(null)` | `shallowRef(null)` | Wholesale (verify line ~150) |
| 55 | `error` | `ref(null)` | **KEEP** | Primitive (error message string) |
| 56 | `projectRevision` | `ref(0)` | **KEEP** | Primitive number |
| 58 | `cacheTimestamps` | `ref({...})` | **KEEP** | Property mutation (line 73: `cacheTimestamps.value[key] = Date.now()`) |

**Total conversions**: 7 refs → shallowRef

### 4.3 Verify Required

Before commit, confirm each conversion:
1. Read full useStudioStore.js
2. For each candidate ref, grep `\.value\.\w+\s*=` (property mutation pattern) → must be 0 hits
3. Grep `\.value\s*=` (wholesale) → must be present
4. Grep `computed\(\(\) =>.*\.value\.` → check if inner properties accessed

---

## 5. File 2: `apps/dashboard/src/composables/useCreatorSettings.js` (651 lines)

### 5.1 Pre-scan (line 77-102)

26 refs total. Most are wholesale-replaced objects/arrays.

### 5.2 Conversion Table (Phase 77 candidates)

| Line | Ref | Current | Proposed | Justification |
|------|-----|---------|----------|---------------|
| 77 | `settingsDocs` | `ref(null)` | `shallowRef(null)` | Wholesale: `settingsDocs.value = docs` (line 238) |
| 79 | `settingsBaseline` | `ref({...})` | **VERIFY** | Line 243: `settingsBaseline.value = {pillars: ..., outline: ...}` — wholesale ✓ |
| 80 | `settingsDiffPreview` | `ref(null)` | `shallowRef(null)` | Wholesale: `settingsDiffPreview.value = threeWay` (line 302) |
| 81 | `showSettingsDiff` | `ref(false)` | **KEEP** | Primitive boolean |
| 82 | `settingsSaving` | `ref(false)` | **KEEP** | Primitive boolean |
| 83 | `settingsHistory` | `ref([])` | `shallowRef([])` | Wholesale: `settingsHistory.value = list` (line 226) |
| 84 | `settingsRestoring` | `ref(false)` | **KEEP** | Primitive boolean |
| 85 | `usesGlobalMergeDefault` | `ref(false)` | **KEEP** | Primitive boolean |
| 86 | `mergePresetPackages` | `ref([])` | `shallowRef([])` | Wholesale: `mergePresetPackages.value = data?.packages || []` (line 262) |
| 87 | `factoryMergePresetPackages` | `ref([])` | `shallowRef([])` | Wholesale: line 264 |
| 88 | `selectedMergePresetPackage` | `ref('')` | **KEEP** | Primitive string |
| 89 | `showImportMergePresetPackages` | `ref(false)` | **KEEP** | Primitive boolean |
| 90 | `importMergePresetPackagesJson` | `ref('')` | **KEEP** | Primitive string |
| 91 | `mergePresetPackagesImporting` | `ref(false)` | **KEEP** | Primitive boolean |
| 92 | `mergePresetImportDiff` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 93 | `mergePresetToposort` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 94 | `mergePresetChangelog` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 95 | `mergePresetChangelogDiff` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 96 | `factoryMergePresetPullConflicts` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 97 | `mergePresetImportPreflight` | `ref(null)` | `shallowRef(null)` | Wholesale (verify) |
| 98 | `mergePresetGraph` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 99 | `mergePresetConflicts` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 100 | `mergePresetConflictFixes` | `ref({...})` | `shallowRef({...})` | Wholesale (verify) |
| 101 | `mergePresetFactoryPublishing` | `ref(false)` | **KEEP** | Primitive boolean |
| 102 | `mergePresetFactoryPulling` | `ref(false)` | **KEEP** | Primitive boolean |

**Total conversions**: 15+ refs → shallowRef (subject to per-ref verify)

### 5.3 Verify Required (CRITICAL — 651L file)

Before commit:
1. Read full useCreatorSettings.js (lines 1-651)
2. For each candidate ref:
   - Grep `\.value\.\w+\s*=` → must be 0 hits (no property mutation)
   - Grep `\.value\s*=` → must have at least 1 wholesale assignment
   - Grep `\.value\.\w+\s*[=,)]` in computed/watch → check no deep tracking
3. If any candidate has property mutation, **KEEP** (not shallowRef)

---

## 6. Implementation Strategy

### 6.1 Order

1. **Read full source**: useStudioStore.js + useCreatorSettings.js (verify table)
2. **Update spec table** with final verified candidates (in implementation plan)
3. **Edit file 1**: useStudioStore.js (7 conversions, atomic per ref OR batch)
4. **Run tests**: pnpm test (immediate feedback)
5. **Edit file 2**: useCreatorSettings.js (15+ conversions)
6. **Run tests**: pnpm test
7. **vue-tsc + build**: verify type + bundle
8. **Re-run Phase 76 baseline** (optional): compare LCP medians
9. **1-2 atomic commits** (per file or combined)

### 6.2 Edit Pattern

For each conversion:
```diff
- import { ref, computed, watch } from 'vue'
+ import { ref, shallowRef, computed, watch } from 'vue'

- const projects = ref([])
+ const projects = shallowRef([])
```

### 6.3 Per-ref Verify Doc

Each conversion adds a `// Phase 77: shallowRef — wholesale replacement (line X)` comment.

---

## 7. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm test` 1549 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep -c "shallowRef" apps/dashboard/src/stores/useStudioStore.js` | ≥ 7 |
| `grep -c "shallowRef" apps/dashboard/src/composables/useCreatorSettings.js` | ≥ 15 |
| Phase 76 baseline re-run (optional) | LCP median ≤ Phase 76 (no regression) |
| Per-ref comment added | ✓ (Phase 77 marking) |
| 1-2 atomic commits | ✓ |

---

## 8. 风险 & 缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 漏 verify wholesale pattern, 改后 reactivity 丢失 | **Medium** | 运行时 bug (UI 不更新) | 每个 ref 单独 read code, 写 justification table, tests 立即发现 |
| `useCreatorSettings` 651L 单文件, 难审计 | **High** | 漏过 nested mutation | 全文件 read + 列出每个 ref 的 mutation pattern 在 spec table |
| Template 中 `.value.foo.bar` 访问需要 reactivity | Low | shallowRef 不触发 | 检查 template 渲染处 |
| `computed()` 依赖 inner property | Medium | computed 不更新 | grep `computed.*\.value\.` 检查 |
| Before/after perf 对比无效 (环境 noise) | Medium | 难以量化收益 | 接受 Phase 76 数据作为 baseline, 不强行对比 |
| 引入 TypeScript 类型问题 | Low | compile error | vue-tsc check after edit |
| 1549 tests 中有 mock 假设 deep reactive | Low | 测试失败 | 优先 pnpm test 早反馈 |

---

## 9. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Commit 1: useStudioStore.js
git add apps/dashboard/src/stores/useStudioStore.js
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf(useStudioStore): convert 7 wholesale-refs to shallowRef (Phase 77)" \
    -m "Phase 77 shallowRef optimization (per Phase 76 baseline §6):

useStudioStore.js 7 ref → shallowRef:
- projects (line 46): wholesale projects.value = data.projects
- summary, overview, quality, qualityReport, proseDiff, proseJudge (lines 48-54)

KEEP:
- cacheTimestamps (line 58): property mutation cacheTimestamps.value[key] = ...
- loading, error, activeSlug, projectRevision: primitives
- activeSlug: primitive string

Vue 3 默认 ref(obj) 是 deep reactive — 整个 object tree 被 Proxy 包装.
这些 refs 仅整批替换, shallowRef 减少 proxy 开销.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."

# Commit 2: useCreatorSettings.js (separate for cleaner history)
git add apps/dashboard/src/composables/useCreatorSettings.js
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf(useCreatorSettings): convert 15+ wholesale-refs to shallowRef (Phase 77)" \
    -m "Phase 77 shallowRef optimization (per Phase 76 baseline §6):

useCreatorSettings.js 15+ ref → shallowRef:
- settingsDocs, settingsDiffPreview, settingsHistory (lines 77-83)
- mergePresetPackages, factoryMergePresetPackages (lines 86-87)
- mergePresetImportDiff, Toposort, Changelog, ChangelogDiff (lines 92-95)
- factoryMergePresetPullConflicts, ImportPreflight (lines 96-97)
- mergePresetGraph, Conflicts, ConflictFixes (lines 98-100)

KEEP:
- showSettingsDiff, settingsSaving, settingsRestoring (booleans)
- selectedMergePresetPackage, importMergePresetPackagesJson (strings)
- usesGlobalMergeDefault, mergePresetPackagesImporting, etc (booleans)

Each conversion verified to be wholesale replacement pattern.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

---

## 10. 测试策略

无新增 tests (code refactor). 现有 1549 tests 验证 behavior unchanged.

**Verification**:
- `pnpm test` (immediate feedback per file)
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- Phase 76 baseline re-run (optional, accept noise)

---

## 11. 后续

Phase 78+ 候选 (per Phase 76 baseline + this Phase 77):

1. **Phase 78**: Bundle split (vendor 407kB / mermaid 390kB → lazy load)
2. **Phase 79**: INP 测量改进 (use `page.click()` 替代 synthetic click)
3. **Phase 80**: Live e2e verification (Phase 66 6 specs)
4. **Phase 81**: CLAUDE.md v13.1 housekeeping
5. **Phase 82+**: Comprehensive 485 reactives audit (residual shallowRef opportunities)
