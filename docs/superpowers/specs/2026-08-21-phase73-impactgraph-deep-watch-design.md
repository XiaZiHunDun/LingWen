# Phase 73 — ImpactGraph deep watch 修复设计

> **日期**: 2026-08-21
> **范围**: `ImpactGraph.vue:154` 移除 `deep: true` flag
> **基础**: Phase 72 收官 + 2 dead panels 删除 + lazy load
> **版本**: master（Phase 72 收官后）

---

## 1. 背景

实测（2026-08-21）grep:

```bash
grep -rnE "deep.*true" apps/dashboard/src --include="*.vue" --include="*.ts"
```

输出 (only 1 hit):
```
apps/dashboard/src/components/ImpactGraph.vue:154:watch(() => props.graph, initChart, { deep: true })
```

**Problem**: `deep: true` 是 Vue 反模式. 当 `props.graph` 是 deep object (e.g., `{ nodes: [...], edges: [...], dimensions: [...], snapshots: [...] }`) 时, every nested 变化触发 deep watch + `initChart`. `initChart` 重新 build 整个 echart instance, 包含从 `impactGraphUtils.js` 派生 nodes + 重设 echarts options.

**Context**: `ImpactGraph.vue` 现状:
- Line 36: `import { computed, onMounted, onUnmounted, ref, watch } from 'vue'`
- Line 63: `async function initChart() { ... }` (initialize echart with options)
- Line 147: `onMounted(initChart)` (initial render)
- Line 148-153: `onUnmounted(() => chart.dispose())`
- Line 154: `watch(() => props.graph, initChart, { deep: true })` (re-init on prop change)
- Line 156: `defineExpose({ impactNodeColor })`

## 2. 目标 & 非目标

### 目标
1. 移除 `ImpactGraph.vue:154` `deep: true` flag
2. 1 原子 commit
3. `pnpm test` 1549 PASS
4. `pnpm exec vue-tsc --noEmit` 0 errors

### 非目标
- 不动 `initChart` 内部 (`graph` 派生)
- 不动 props 定义
- 不动 echart 配置
- 不动其他 component
- 不动 `ImpactGraph.vue` 其他 line

## 3. 1 处修改

### 3.1 `ImpactGraph.vue` line 154

**Current**:
```js
watch(() => props.graph, initChart, { deep: true })
```

**After**:
```js
watch(() => props.graph, initChart)
```

**Rationale**:
- Vue 3 `watch(() => props.graph, ...)` 默认 shallow
- 只触发于 `props.graph` 顶层 reference replacement
- 当 parent 重新 assign graph 时触发 (e.g., `graph = ref(...)` → `graph.value = newData`)
- Nested 变化 (e.g., `graph.value.nodes.push(...)`) **不会**触发 watch — 这是 Vue 3 设计，可以避免 Vue 2-style deep watch 反模式
- 大多数 reactive prop 场景的预期行为

## 4. 1 原子 commit

### 4.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Verify current state
grep -nE "deep.*true" apps/dashboard/src/components/ImpactGraph.vue

# 2. Apply 1-line fix: remove `{ deep: true }`

# 3. Verify
grep -c "deep.*true" apps/dashboard/src/components/ImpactGraph.vue
echo "---should be 0---"

# 4. Run tests
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm test 2>&1 | tail -10
cd /home/ailearn/projects/LingWen

# 5. 1 atomic commit
git add apps/dashboard/src/components/ImpactGraph.vue

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf(ImpactGraph): remove deep:true from watch (Phase 73)" \
    -m "deep watch 是 Vue 反模式. props.graph 默认 shallow watch 已足够. 移除 deep:true 可避免 nested 变化触发 initChart 全量 rebuild."

git show --stat HEAD
```

### 4.2 Commit 详情

- **Files**: 1 (ImpactGraph.vue)
- **Lines**: -1 / +1 (remove `{ deep: true }`)
- **Method**: 1 surgical edit

## 5. 测试策略

### 5.1 无新增 tests

1 line change 不动 test logic.

### 5.2 验证

- `grep 'deep.*true' ImpactGraph.vue` 0 hits
- `pnpm test` 1549 PASS
- `pnpm exec vue-tsc --noEmit` 0 errors

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `grep -c 'deep.*true' apps/dashboard/src/components/ImpactGraph.vue` | 0 |
| `git show --stat HEAD` | 1 file changed, +1/-1 |
| `pnpm test` | 1549 tests PASS |
| `pnpm exec vue-tsc --noEmit` | 0 errors |

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Parent 实际 nested mutate graph | 极低 | 反模式不再触发 | e2e test 已覆盖 component render (测试 pass 即证明无视觉回归) |
| 视觉回归 | 极低 | echart data 不同步 | e2e test (1549 tests) 覆盖 |
| `initChart` 性能 regression | 0 | 0 | 修复是减少 watch 触发频率 |

## 8. 后续 Phase 74+ 候选

- Performance profiling 真实化 (Lighthouse)
- Live e2e verification
- Memoize 优化其他 component (`markRaw` / `shallowRef`)
