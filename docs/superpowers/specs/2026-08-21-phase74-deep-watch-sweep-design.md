# Phase 74 — 9 Sibling Deep Watch Sweep 设计

> **日期**: 2026-08-21
> **范围**: 9 files 10 sites `deep: true` 移除. 1 原子 commit.
> **基础**: Phase 60-73 完整闭环 + Phase 73 ImpactGraph 已修
> **版本**: master（Phase 73 收官后）

---

## 1. 背景

Phase 73 reviewer 列出 **9 sibling `deep: true` sites + 1 page-level site (RipplesPage.vue)**:

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
```

加 **1 page site**: `apps/dashboard/src/pages/RipplesPage.vue:77` (v-model property assignment, deep 必要)

总 **10 sites**: **9 sites 安全移除 deep** + **1 site 保留 deep** (见 §3.3 新增). Phase 73 已修 ImpactGraph. 此 phase 攻其余 9 files.

> **注**: `RipplesPage.vue:77` 在本 spec §1/§3.1 列出, 但实际 commit `3ae7f8b6` 仅改 9 files (漏改 RipplesPage). 经 Phase 75 Vue 3 语义分析, 该 site `deep: true` 必要, **保留** (见 §3.3). Phase 75 spec `2026-08-21-phase75-phase74-doc-drift-decision.md` §1.3.1 记录决策.

## 2. 目标 & 非目标

### 目标
1. **9 sites `deep: true` 移除** (sibling sites, 见 §3.1)
2. **1 site `deep: true` 保留** (RipplesPage.vue:77, 见 §3.3 新增)
3. 每个 site 逐 file verify parent pattern
4. 1 原子 commit
5. `pnpm test` 1549 PASS
6. `pnpm exec vue-tsc --noEmit` 0 errors
7. 全 codebase `grep -rnE 'deep.*true'` **2 hits** (RipplesPage.vue:77 + useCreatorPage.js:449, 经 Phase 75 Vue 3 语义分析确认 deep 必要)

### 非目标
- 不动 `ImpactGraph.vue` (Phase 73 已修)
- 不动 `immediate: true` watches (e.g., SidebarTierBudgetAlerts 保留 `immediate`)
- 不动 `deep: false` watches
- 不动 其他 `watch` 配置

## 3. 修复模式

### 3.1 Standard pattern (8 sites)

```js
- watch(() => props.X, initChart, { deep: true })
+ watch(() => props.X, initChart)
```

**Sites**:
- CoolpointChart.vue:154
- HookTrendChart.vue:166
- ScoreRadarChart.vue:128
- WidgetRenderer.vue:287
- ProductionCostTrendChart.vue:67
- CostTrendChart.vue:299
- creator/CreatorWriteChat.vue:129
- CostBarChart.vue:244

> **注**: `pages/RipplesPage.vue:77` 原在 §1/§3.1 列出, 但 commit `3ae7f8b6` 未改. 该 site `deep: true` 必要 (v-model property assignment), **保留** (见 §3.3). 本 spec 修正时从 §3.1 sites 列表移除.

### 3.2 Special pattern (1 site: SidebarTierBudgetAlerts)

```js
- watch(() => props.X, fn, { deep: true, immediate: true })
+ watch(() => props.X, fn, { immediate: true })
```

**Rationale**: 保留 `immediate: true` (Phase 73 修复仅移除 `deep:`, 不动 `immediate`)。

### 3.3 Preserved site (1: RipplesPage.vue:77)

```js
// apps/dashboard/src/pages/RipplesPage.vue:74
const filter = ref({ status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' });
// template: v-model:status="filter.status" 等 5 个 v-model 绑定
watch(filter, (f) => {
  store.refresh(filterToFilters(f));
  loadReferenceGraph();
}, { deep: true });  // KEEP — v-model property assignment requires deep
```

**Rationale**: `filter = ref({...})` + 5 v-model bindings (`v-model:status="filter.status"` 等). Vue 3 watch on ref 默认 shallow, 不追踪 reactive property setter. 移除 deep 会导致 v-model 修改不触发 `loadReferenceGraph()`.

> **注**: `useCreatorPage.js:449` `watch(editableVolumes, ..., { deep: true })` 同样保留 (push + property assignment nested mutations, deep 必要). 见 Phase 75 spec (`2026-08-21-phase75-phase74-doc-drift-decision.md`) §1.3.2.

## 4. 验证流程 (per-file)

实施前逐 file verify parent pattern:

```bash
# 1. 读 parent code 中的 props.X 赋值 (top-level ref reassignment)
grep -rnE "props\.\w+ =" apps/dashboard/src

# 2. 验证 X 不 nested mutated (e.g., props.X.nodes.push)
grep -rnE "props\.X\." apps/dashboard/src
```

**Decision rule**:
- `props.X = ref(...)` 或 `props.X.value = newData` (top-level ref reassignment) → 安全移除 deep
- `props.X.nodes.push(...)` (nested mutation) → 不动 deep (Vue 3 design 期望 shallow + nested mutation)

## 5. 1 原子 commit

### 5.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Per-file verification (Step 4)
for file in apps/dashboard/src/components/CoolpointChart.vue \
              apps/dashboard/src/components/HookTrendChart.vue \
              apps/dashboard/src/components/ScoreRadarChart.vue \
              apps/dashboard/src/components/WidgetRenderer.vue \
              apps/dashboard/src/components/ProductionCostTrendChart.vue \
              apps/dashboard/src/components/CostTrendChart.vue \
              apps/dashboard/src/components/SidebarTierBudgetAlerts.vue \
              apps/dashboard/src/components/creator/CreatorWriteChat.vue \
              apps/dashboard/src/components/CostBarChart.vue; do
  echo "---verify $file---"
  grep -nE "deep.*true" "$file"
  # Read parent code (manually) to verify pattern
done

# 2. Apply edits per Site 3.1 / 3.2 pattern

# 3. Verify
grep -rnE "deep.*true" apps/dashboard/src --include="*.vue" --include="*.ts" | wc -l
echo "---should be 0---"

# 4. Run tests
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm test 2>&1 | tail -10
pnpm run build 2>&1 | tail -10
cd /home/ailearn/projects/LingWen

# 5. 1 atomic commit
git add apps/dashboard/src/components/CoolpointChart.vue \
        apps/dashboard/src/components/HookTrendChart.vue \
        apps/dashboard/src/components/ScoreRadarChart.vue \
        apps/dashboard/src/components/WidgetRenderer.vue \
        apps/dashboard/src/components/ProductionCostTrendChart.vue \
        apps/dashboard/src/components/CostTrendChart.vue \
        apps/dashboard/src/components/SidebarTierBudgetAlerts.vue \
        apps/dashboard/src/components/creator/CreatorWriteChat.vue \
        apps/dashboard/src/components/CostBarChart.vue

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf: remove deep:true from 9 sibling watch sites (Phase 74)" \
    -m "9 sibling deep watch sites 移除 deep:true (Vue 3 反模式). 1 commit per-file verification. ImpactGraph phase 73 已修, 此 commit 攻其它 9."

git show --stat HEAD
```

### 5.2 Commit 详情

- **Files**: 9 (9 sites removed, 1 site `RipplesPage.vue:77` preserved, deep 必要 — 见 §3.3)
- **Lines**: per-file -1 / -1 (each removes `, { deep: true }`)
- **Special**: SidebarTierBudgetAlerts 保留 `immediate: true`, 1 line still `-1` (just removes `deep: true` part)
- **Method**: Surgical edits per file

## 6. 测试策略

### 6.1 无新增 tests

10 line changes 不动 test logic.

### 6.2 验证

- `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts'` 0 hits
- `pnpm test` 1549 PASS
- `pnpm exec vue-tsc --noEmit` 0 errors
- `pnpm run build` 0 errors

## 7. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts' --include='*.js' \| wc -l` | **2** (RipplesPage.vue:77 + useCreatorPage.js:449, deep 必要, 不动) |
| `git show --stat HEAD` | 9 files changed |
| `pnpm test` | 1549 tests PASS |
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm run build` | 0 errors |

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Parent 实际 nested mutate prop | 极低 | 反模式不再触发 | 9 files per-file verification before edit (Spec §4) |
| `immediate: true` 误删 | 极低 | watch 不立即触发 | SidebarTierBudgetAlerts 保留 `immediate` (Spec §3.2) |
| build 验证 | 1 | 0 | run `pnpm run build` 验证 |

## 9. 后续 Phase 75+ 候选

- `markRaw` / `shallowRef` 优化其他 component
- Performance profiling 真实化
- Live e2e verification
