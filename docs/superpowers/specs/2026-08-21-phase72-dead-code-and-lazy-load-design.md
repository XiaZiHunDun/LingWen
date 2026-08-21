# Phase 72 — Dead Code 删除 + Lazy Load 设计

> **日期**: 2026-08-21
> **范围**: 2-pronged — 删 2 dead creator panels (1620L) + lazy load 2 large panels (1324L → async)
> **基础**: Phase 60-71 完整闭环（12 phases 推送完成）
> **版本**: master（Phase 71 收官后）

---

## 1. 背景

Phase 71 已 closed Vite build config. 剩余 substantive performance work 是 sub-component lazy load.

实测（2026-08-21）`apps/dashboard/src/components/creator/` 4 大 panel files:
- `CreatorBatchHistoryPanel.vue` 855L — **orpha**, 无 imports (除 self + injection key files)
- `CreatorSettingsPanel.vue` 765L — **orphan**, 无 imports (除 self + injection key files)
- `CreatorVolumePlanTemplatesPanel.vue` 781L — sync imported by `CreatorVolumePlanPanel.vue:27`
- `CreatorFactoryPipeline.vue` 543L — sync imported by `CreatorWriteSidebar.vue:139`

Pattern 已存在: `CreatorPageLayout.vue` 已有 4 modals 用 `defineAsyncComponent` (line 34-37). 同样的 pattern 适用 2 large panels.

## 2. 目标 & 非目标

### 目标
1. **Delete 2 dead-code panels**: `CreatorBatchHistoryPanel.vue` 855L + `CreatorSettingsPanel.vue` 765L (`-1620L`)
2. **Lazy load 2 large panels**: `CreatorVolumePlanTemplatesPanel.vue` 781L + `CreatorFactoryPipeline.vue` 543L (sync → `defineAsyncComponent`)
3. 1 原子 commit
4. `pnpm test` 1549 PASS + `pnpm run build` 0 errors

### 非目标
- 不动 other creator components
- 不动 `creatorBatchHistoryKey.js` / `creatorSettingsKey.js` (injection key infrastructure 保留 for future use)
- 不动 providers in `useCreatorPageProviders.js`
- 不动 `CreatorPageLayout.vue` 的 4 modals (已 async)
- 不动 任何 non-creator 代码

## 3. 4 处修改

### 3.1 Delete `CreatorBatchHistoryPanel.vue`

```
delete apps/dashboard/src/components/creator/CreatorBatchHistoryPanel.vue
```

**Rationale**: 0 imports (除 self + `creatorBatchHistoryKey.js` 注释). 验证:

```bash
grep -rnE "CreatorBatchHistoryPanel" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" | grep -v "CreatorBatchHistoryPanel.vue:"
```

Expected: 0 hits (除 self + `creatorBatchHistoryKey.js` 注释引用).

### 3.2 Delete `CreatorSettingsPanel.vue`

```
delete apps/dashboard/src/components/creator/CreatorSettingsPanel.vue
```

**Rationale**: 同 3.1. 0 imports (除 self + `creatorSettingsKey.js` 注释).

### 3.3 Lazy load `CreatorVolumePanel.vue` 内的 `CreatorVolumePlanTemplatesPanel`

**File**: `apps/dashboard/src/components/creator/CreatorVolumePlanPanel.vue`

**Current** (line 27):
```js
import CreatorVolumePlanTemplatesPanel from './CreatorVolumePlanTemplatesPanel.vue';
```

**After**:
```js
import { defineAsyncComponent } from 'vue';
const CreatorVolumePlanTemplatesPanel = defineAsyncComponent(() => import('./CreatorVolumePlanTemplatesPanel.vue'));
```

> **Note**: If `CreatorVolumePlanPanel.vue` already imports `defineAsyncComponent` from `'vue'`, just add the const line. Otherwise add the import.

### 3.4 Lazy load `CreatorWriteSidebar.vue` 内的 `CreatorFactoryPipeline`

**File**: `apps/dashboard/src/components/creator/CreatorWriteSidebar.vue`

**Current** (line 139):
```js
import CreatorFactoryPipeline from './CreatorFactoryPipeline.vue';
```

**After**:
```js
import { defineAsyncComponent } from 'vue';
const CreatorFactoryPipeline = defineAsyncComponent(() => import('./CreatorFactoryPipeline.vue'));
```

> **Note**: Same as 3.3 — check existing `defineAsyncComponent` import.

## 4. 1 原子 commit

### 4.1 Commit

```bash
cd /home/ailearn/projects/LingWen

# 1. Verify dead code (no imports)
echo "---CreatorBatchHistoryPanel imports (should be 0)---"
grep -rnE "CreatorBatchHistoryPanel" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" | grep -v "CreatorBatchHistoryPanel.vue:" | wc -l

echo "---CreatorSettingsPanel imports (should be 0)---"
grep -rnE "CreatorSettingsPanel" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" | grep -v "CreatorSettingsPanel.vue:" | wc -l

# 2. Check existing defineAsyncComponent import in 2 panel files
echo "---CreatorVolumePlanPanel existing imports---"
grep -nE "defineAsyncComponent|^import" apps/dashboard/src/components/creator/CreatorVolumePlanPanel.vue | head -10

echo "---CreatorWriteSidebar existing imports---"
grep -nE "defineAsyncComponent|^import" apps/dashboard/src/components/creator/CreatorWriteSidebar.vue | head -10

# 3. Implementer makes 4 changes:
#    - Delete CreatorBatchHistoryPanel.vue
#    - Delete CreatorSettingsPanel.vue
#    - CreatorVolumePlanPanel.vue: import + defineAsyncComponent
#    - CreatorWriteSidebar.vue: import + defineAsyncComponent

# 4. Verify
ls apps/dashboard/src/components/creator/CreatorBatchHistoryPanel.vue 2>&1 | head -1
ls apps/dashboard/src/components/creator/CreatorSettingsPanel.vue 2>&1 | head -1
echo "---CreatorVolumePlanPanel defineAsyncComponent (should be 1)---"
grep -c "defineAsyncComponent" apps/dashboard/src/components/creator/CreatorVolumePlanPanel.vue
echo "---CreatorWriteSidebar defineAsyncComponent (should be 1)---"
grep -c "defineAsyncComponent" apps/dashboard/src/components/creator/CreatorWriteSidebar.vue

# 5. 1 atomic commit
git add apps/dashboard/src/components/creator/

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "perf: delete 2 dead panels + lazy load 2 large panels (Phase 72)" \
    -m "2-pronged: 1) delete CreatorBatchHistoryPanel 855L + CreatorSettingsPanel 765L (orphan, no imports) 2) lazy load CreatorVolumePlanTemplatesPanel 781L + CreatorFactoryPipeline 543L via defineAsyncComponent. 净 -2944L 同步加载, +1324L 转 async 加载."

git show --stat HEAD
```

### 4.2 Commit 详情

- **Files**: 4 changes (2 deletes + 2 lazy-load refactors)
- **Lines**: -1620L (deletes) + 2 small rewrites (sync → async)
- **Method**: 4 surgical edits

## 5. 测试策略

### 5.1 无新增 tests

Dead code + lazy load 不动 test logic.

### 5.2 验证

- 删除 panel 0 imports (除 self)
- 2 large panels 改 `defineAsyncComponent`
- `pnpm test` 1549 PASS
- `pnpm run build` 0 errors + 验证 chunks

## 6. 验证清单

| 检查 | 期望 |
|------|------|
| `ls CreatorBatchHistoryPanel.vue` | NOT exist |
| `ls CreatorSettingsPanel.vue` | NOT exist |
| `grep -c 'CreatorBatchHistoryPanel' apps/dashboard/src --include='*.vue' --include='*.ts' -r \| grep -v 'CreatorBatchHistoryPanel.vue:'` | 0 |
| `grep -c 'CreatorSettingsPanel' apps/dashboard/src --include='*.vue' --include='*.ts' -r \| grep -v 'CreatorSettingsPanel.vue:'` | 0 |
| `grep -c 'defineAsyncComponent' CreatorVolumePlanPanel.vue` | 1 |
| `grep -c 'defineAsyncComponent' CreatorWriteSidebar.vue` | 1 |
| `pnpm test` | 1549 tests PASS |
| `pnpm run build` | 0 errors |

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 删除的 panel 有 hidden usage | 极低 | 测试 fail | grep 0 命中 (除 self + key files) |
| `defineAsyncComponent` async 失败 | 极低 | 渲染 fail | 沿用 `CreatorPageLayout.vue` 已有 4 modals 的 pattern |
| Caller hooked into detail | 0 | 0 | 测试 + build 验证 |

## 8. 后续 Phase 73+ 候选

- Memoize 优化 (`markRaw` / `shallowRef`)
- Performance profiling 真实化
- Live e2e verification
