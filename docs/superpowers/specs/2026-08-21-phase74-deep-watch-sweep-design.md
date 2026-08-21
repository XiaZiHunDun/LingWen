# Phase 74 — 9 Sibling Deep Watch Sweep 设计

> **日期**: 2026-08-21
> **范围**: 9 files 10 sites `deep: true` 移除. 1 原子 commit.
> **基础**: Phase 60-73 完整闭环 + Phase 73 ImpactGraph 已修
> **版本**: master（Phase 73 收官后）

---

## 1. 背景

Phase 73 reviewer 列出 9 sibling `deep: true` sites (10 sites in 9 files):

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

总 10 sites. Phase 73 已修 ImpactGraph. 此 phase 攻其余 9 files.

## 2. 目标 & 非目标

### 目标
1. 9 files 10 sites `deep: true` 移除
2. 每个 site 逐 file verify parent pattern
3. 1 原子 commit
4. `pnpm test` 1549 PASS
5. `pnpm exec vue-tsc --noEmit` 0 errors
6. 全 codebase `grep -rnE 'deep.*true'` 0 hits

### 非目标
- 不动 `ImpactGraph.vue` (Phase 73 已修)
- 不动 `immediate: true` watches (e.g., SidebarTierBudgetAlerts 保留 `immediate`)
- 不动 `deep: false` watches
- 不动 其他 `watch` 配置

## 3. 修复模式

### 3.1 Standard pattern (9 sites)

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
- pages/RipplesPage.vue:77

### 3.2 Special pattern (1 site: SidebarTierBudgetAlerts)

```js
- watch(() => props.X, fn, { deep: true, immediate: true })
+ watch(() => props.X, fn, { immediate: true })
```

**Rationale**: 保留 `immediate: true` (Phase 73 修复仅移除 `deep:`, 不动 `immediate`)。

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
              apps/dashboard/src/components/CostBarChart.vue \
              apps/dashboard/src/pages/RipplesPage.vue; do
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
        apps/dashboard/src/components/CostBarChart.vue \
        apps/dashboard/src/pages/RipplesPage.vue

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf: remove deep:true from 9 sibling watch sites (Phase 74)" \
    -m "9 sibling deep watch sites 移除 deep:true (Vue 3 反模式). 1 commit per-file verification. ImpactGraph phase 73 已修, 此 commit 攻其它 9."

git show --stat HEAD
```

### 5.2 Commit 详情

- **Files**: 9 (10 sites)
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
| `grep -rnE 'deep.*true' apps/dashboard/src --include='*.vue' --include='*.ts' \| wc -l` | 0 |
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
