# Phase 75 — Phase 74 Doc Drift 修正 + 2 Sites `deep:true` 决策记录

> **日期**: 2026-08-21
> **范围**: docs only. 1 atomic commit. **no code change**.
> **基础**: Phase 60-74 完整闭环 (master = `30b7c509`)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

---

## 1. 背景

Phase 74 close-out 存在 **3 处不一致**:

### 1.1 Spec vs Commit 不一致

Phase 74 spec `2026-08-21-phase74-deep-watch-sweep-design.md` §1/§2/§3.1/§5 列 **10 sites**:

```
apps/dashboard/src/components/CoolpointChart.vue:154
apps/dashboard/src/components/HookTrendChart.vue:166
apps/dashboard/src/components/ScoreRadarChart.vue:128
apps/dashboard/src/components/WidgetRenderer.vue:287
apps/dashboard/src/components/ProductionCostTrendChart.vue:67
apps/dashboard/src/components/CostTrendChart.vue:299
apps/dashboard/src/components/SidebarTierBudgetAlerts.vue:78  (also has `immediate: true`)
apps/dashboard/src/components/creator/CreatorWriteChat.vue:129
apps/dashboard/src/components/CostBarChart.vue:244
apps/dashboard/src/pages/RipplesPage.vue:77
```

但 Phase 74 commit `3ae7f8b6` `git show --stat` 实际改 **9 files** — **RipplesPage.vue:77 漏改**.

### 1.2 Handoff 测试基线错误

`docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md` §2 测试基线声称:

> `grep -rnE 'deep.*true' apps/dashboard/src ...`: 0 hits (Phase 74 已清)

但实际 `grep -rnE "deep.*true" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js"` 返回 **2 hits**:

```
apps/dashboard/src/composables/useCreatorPage.js:449:    { deep: true },
apps/dashboard/src/pages/RipplesPage.vue:77:}, { deep: true });
```

`useCreatorPage.js:449` 是 Phase 74 reviewer **漏审** 的 site (Phase 60 useCreatorWriteWorkbench 拆分遗留父文件).

### 1.3 经 Vue 3 语义分析, 2 sites `deep:true` 必要

#### 1.3.1 `RipplesPage.vue:74-77`

```js
const filter = ref({ status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' });
// template: v-model:status="filter.status" 等 5 个 v-model 绑定
watch(filter, (f) => {
  store.refresh(filterToFilters(f));
  loadReferenceGraph();
}, { deep: true });
```

**Mutation pattern**: `filter.status = newVal` (顶层 reactive object 的 property assignment, 5 个 v-model).

**Vue 3 行为**:
- `watch(ref, cb)` 默认 shallow, 仅追踪 `.value` 引用重赋值
- `ref.value.status = x` 触发 reactive proxy 的 property `set` trap, 但**不改变 `ref.value` 引用**
- Shallow watch on ref 不追踪 reactive property setter

**结论**: `deep: true` 必需, 否则 v-model 修改不触发 `loadReferenceGraph()`.

#### 1.3.2 `useCreatorPage.js:444-450`

```js
const editableVolumes = ref([]);  // useCreatorVolumePlan.js:48
// ...
editableVolumes.value.push({...});           // useCreatorVolumePlan.js:97
editableVolumes.value[idx].locked = !...;    // useCreatorVolumePlan.js:107
// ...
watch(editableVolumes, () => {
  refreshVolumePlanDiffPreview();
}, { deep: true });
```

**Mutation pattern**: `editableVolumes.value.push(...)` + `editableVolumes.value[idx].property = ...` (典型 nested mutation).

**Vue 3 行为**:
- `ref.value.push(...)` 不改变 `.value` 引用
- `ref.value[idx].property = x` 不改变 `.value` 引用
- Shallow watch on ref 都不追踪

**结论**: `deep: true` 必需, 否则 push/new property 不触发 `refreshVolumePlanDiffPreview()`.

---

## 2. 目标 & 非目标

### 目标

1. **不修改 code** — 2 sites `deep:true` 正确, 不移除
2. **新 spec 文件** `2026-08-21-phase75-phase74-doc-drift-decision.md` 记录分析 + 决策 (本文)
3. **修正 Phase 74 spec** §1/§2/§3.1/§5 中 "10 sites" → "9 sites removed + 1 preserved" (RipplesPage.vue:77 移入 preserved)
4. **修正 Handoff §2** 测试基线: 0 hits → **2 hits** (RipplesPage + useCreatorPage)
5. **1 atomic commit** (docs only, no code change)

### 非目标

- 不动 `RipplesPage.vue:77` (deep 必要)
- 不动 `useCreatorPage.js:449` (deep 必要)
- 不动 Phase 73-74 已修 9 sites (deep:true 已正确移除, top-level ref reassignment pattern)
- 不重写 Phase 74 spec 全文 (仅 §1/§2/§3.1/§5 局部修正)
- 不引入新 tests (无 code change)

---

## 3. 决策表

| Site | 状态 | Vue 3 理由 | Phase 74 遗漏类型 |
|------|------|------------|-------------------|
| `RipplesPage.vue:74-77` | **KEEP `deep: true`** | `filter = ref({...})` + 5 v-model property assignments | Spec 列了 (10 sites), commit 漏改 |
| `useCreatorPage.js:444-450` | **KEEP `deep: true`** | `editableVolumes.value.push(...)` + `[idx].locked = ...` nested mutations | Spec 没列, reviewer 漏审 (Phase 60 父文件) |

---

## 4. Phase 74 Spec 修正内容

### 4.1 §1 背景 — "9 files 10 sites" → 修正数字

**原文**:

> Phase 73 reviewer 列出 9 sibling `deep: true` sites (10 sites in 9 files):
>
> ```
> apps/dashboard/src/components/CoolpointChart.vue:154
> ...
> apps/dashboard/src/pages/RipplesPage.vue:77
> ```
>
> 总 10 sites. Phase 73 已修 ImpactGraph. 此 phase 攻其余 9 files.

**修正为**:

> Phase 73 reviewer 列出 **9 sibling `deep: true` sites + 1 page-level site (RipplesPage.vue)**:
>
> ```
> apps/dashboard/src/components/CoolpointChart.vue:154
> apps/dashboard/src/components/HookTrendChart.vue:166
> apps/dashboard/src/components/ScoreRadarChart.vue:128
> apps/dashboard/src/components/WidgetRenderer.vue:287
> apps/dashboard/src/components/ProductionCostTrendChart.vue:67
> apps/dashboard/src/components/CostTrendChart.vue:299
> apps/dashboard/src/components/SidebarTierBudgetAlerts.vue:78  (also has `immediate: true`)
> apps/dashboard/src/components/creator/CreatorWriteChat.vue:129
> apps/dashboard/src/components/CostBarChart.vue:244
> ```
>
> 加 **1 page site**: `apps/dashboard/src/pages/RipplesPage.vue:77` (v-model property assignment, deep 必要)
>
> 总 **10 sites**: **9 sites 安全移除 deep** + **1 site 保留 deep** (见 §3.3 新增)

### 4.2 §2.1 Goal 1 — "9 files 10 sites 移除" → 修正

**原文**:

> 1. 9 files 10 sites `deep: true` 移除

**修正为**:

> 1. **9 sites `deep: true` 移除** (sibling sites, 见 §3.1)
> 2. **1 site `deep: true` 保留** (RipplesPage.vue:77, 见 §3.3 新增)

### 4.3 §3.1 Sites 列表 — 移除 RipplesPage.vue:77

**原文**:

> **Sites**:
> - CoolpointChart.vue:154
> - HookTrendChart.vue:166
> - ScoreRadarChart.vue:128
> - WidgetRenderer.vue:287
> - ProductionCostTrendChart.vue:67
> - CostTrendChart.vue:299
> - creator/CreatorWriteChat.vue:129
> - CostBarChart.vue:244
> - pages/RipplesPage.vue:77   ← 移除

**修正为**: 移除 `pages/RipplesPage.vue:77`, 共 8 sites listed + SidebarTierBudgetAlerts (special pattern, 见 §3.2) = 9 total.

### 4.4 §3.3 新增 — Preserved sites (1)

**新增 §3.3**:

> ### 3.3 Preserved site (1: RipplesPage.vue:77)
>
> ```js
> // apps/dashboard/src/pages/RipplesPage.vue:74
> watch(filter, (f) => {
>   store.refresh(filterToFilters(f));
>   loadReferenceGraph();
> }, { deep: true });  // KEEP — v-model property assignment requires deep
> ```
>
> **Rationale**: `filter = ref({...})` + 5 v-model bindings (`v-model:status="filter.status"` 等). Vue 3 watch on ref 默认 shallow, 不追踪 reactive property setter. 移除 deep 会导致 v-model 修改不触发 `loadReferenceGraph()`.

### 4.5 §5.1 Commit files 列表 — 移除 RipplesPage.vue

**原文**: `git add` 列表含 `apps/dashboard/src/pages/RipplesPage.vue`.

**修正为**: 移除该 file (与实际 commit `3ae7f8b6` 一致).

---

## 5. Handoff 修正内容

### 5.1 §2 测试基线

**原文**:

> ```bash
> git log --oneline -5
> # 3ae7f8b6 perf: remove deep:true from 9 sibling watch sites (Phase 74)
> ...
> git status -s
> # clean
> ```
>
> **测试 baseline**:
> - `pnpm test`：1549 tests PASS（189 files）
> - `pnpm exec vue-tsc --noEmit`：0 errors
> - `pnpm run build`：0 errors

**修正为**: 在测试 baseline 后加 1 行:

> **测试 baseline**:
> - `pnpm test`：1549 tests PASS（189 files）
> - `pnpm exec vue-tsc --noEmit`：0 errors
> - `pnpm run build`：0 errors
> - `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts' --include='*.js' | wc -l`：**2** (RipplesPage.vue:77 + useCreatorPage.js:449, **Phase 75 已确认 deep 必要**)

### 5.2 §6 Phase 75+ 候选 — 新增本 phase

**新增** (作为新 #1):

> 1. **Phase 75 (本文)** — Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (no code change, 1 spec + 1 commit)

把原 5 个候选下移到 #2-6.

---

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts' --include='*.js' \| wc -l` | **2** (RipplesPage + useCreatorPage) |
| Phase 74 commit `git show --stat 3ae7f8b6` | 9 files changed (不变) |
| `pnpm test` | 1549 PASS (不变) |
| `pnpm exec vue-tsc --noEmit` | 0 errors (不变) |
| `pnpm run build` | 0 errors (不变) |
| `docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md` exists | ✓ |
| Phase 74 spec §1/§2/§3.1/§5 修正 | ✓ |
| Handoff §2/§6 修正 | ✓ |
| `git log --oneline -1` | "docs: Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (Phase 75)" |

---

## 7. 风险 & 缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Phase 74 spec 文字 rotation 错位 | 极低 | spec 不一致 | 4 处文字 changes per §4, 每处标 "原文/修正为" |
| Handoff §6 Phase 75+ 候选重排序 | 极低 | 候选编号错位 | 仅 #1 新增, #2-6 原 5 候选下移 |
| 1 atomic commit 误带 code | 极低 | 引入非预期 code change | `git diff --stat HEAD~1` 验证 0 code files |

---

## 8. 1 atomic commit 模板

```bash
cd /home/ailearn/projects/LingWen

# 1. 写新 spec
# Write: docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md

# 2. 修正 Phase 74 spec (4 处 per §4)
# Edit: docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md

# 3. 修正 Handoff (2 处 per §5)
# Edit: docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md

# 4. 验证
git diff --stat
# Should show 3 files changed (2 modified + 1 new), 0 .vue/.js/.ts files

# 5. 1 atomic commit
git add docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md \
        docs/superpowers/specs/2026-08-21-phase74-deep-watch-sweep-design.md \
        docs/superpowers/handoffs/2026-08-21-phase60-74-handoff.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs: Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (Phase 75)" \
    -m "Phase 74 close-out 3 处不一致修正 (no code change):
1. Phase 74 spec 列 10 sites (含 RipplesPage.vue:77), commit 3ae7f8b6 仅改 9 files. RipplesPage 漏改.
2. useCreatorPage.js:449 deep:true 未被 Phase 74 reviewer 审计 (Phase 60 父文件).
3. Handoff §2 测试基线声称 0 deep:true hits, 实际 2 hits.

经 Vue 3 语义分析:
- RipplesPage.vue:74-77 filter=ref({...}) + 5 v-model property assignments → deep 必要
- useCreatorPage.js:444-450 editableVolumes.value.push + [idx].locked nested mutations → deep 必要

决策: 2 sites KEEP deep:true. 不修改 code.

修正:
- 新 spec: docs/superpowers/specs/2026-08-21-phase75-phase74-doc-drift-decision.md (本文)
- Phase 74 spec §1/§2/§3.1/§3.3 新增 / §5 修正数字
- Handoff §2 测试基线 + §6 Phase 75+ 候选 #1 新增

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."

git show --stat HEAD
# Should show 3 files changed, all .md
```

---

## 9. 测试策略

无新增 tests (no code change).

## 10. 后续

Phase 76+ 候选 (per Handoff §6, 下移):
1. Phase 76: `markRaw` / `shallowRef` 优化其他 component (485 reactives, 1 file 已 markRaw)
2. Phase 77: Performance profiling baseline (Lighthouse 1 文件 doc)
3. Phase 78: Live e2e verification (Phase 66 6 specs 需 livebackend)
4. Phase 79: CLAUDE.md v13.0+ housekeeping (Phase 68 后 sections 待 review)

