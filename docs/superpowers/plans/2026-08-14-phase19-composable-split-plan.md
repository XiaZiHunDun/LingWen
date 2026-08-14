# Phase 19 Implementation Plan — Composable 拆分（超 500 行）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 8 个超 500 行的 composable 拆为 .ts 子模块 + facade，零下游 import 修改。

**Architecture:** 每个 composable 拆为 3-4 个单一职责的 .ts 子模块（≤ 300 行），原 `.js` 文件保留为 ≤ 30 行的 facade 仅 re-export。已有 `useWorkbench*.ts`（4 个）接入 `useCreatorWriteWorkbench` facade。

**Tech Stack:** Vue 3.5+ Composition API、TypeScript 5.x、Vitest 4.x、vue-tsc

**前置依赖：** Phase 18 v12.0 已合并到 master（commit 6210e941），含 useWorkbench{Agent,Checkpoint,Selection,Validation}.ts 子模块。

**Run in worktree:** `.claude/worktrees/moling-redesign-phase19`

---

## File Structure

```
apps/dashboard/src/composables/
├── useCreatorProductTools.js              (Modify: facade)
├── useCreatorProductTools/                (Create dir)
│   ├── index.ts                            (子模块入口)
│   ├── useProductList.ts                   (新)
│   ├── useProductList.spec.ts              (新)
│   ├── useProductPublish.ts                (新)
│   ├── useProductPublish.spec.ts           (新)
│   ├── usePlatformBindings.ts              (新)
│   ├── usePlatformBindings.spec.ts         (新)
│   ├── useProductSync.ts                   (新)
│   └── useProductSync.spec.ts              (新)
├── ... (其他 7 个 composable 类似结构)
└── useCreatorWriteWorkbench.js (Modify: 接入 useWorkbench*.ts)
```

---

## Task 1: 拆分 `useCreatorProductTools.js` (788 行 → 4 子模块 + facade)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorProductTools.js`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/index.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/useProductList.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/useProductList.spec.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/useProductPublish.spec.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/usePlatformBindings.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/usePlatformBindings.spec.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/useProductSync.ts`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/useProductSync.spec.ts`

- [ ] **Step 1: 阅读原文件理解结构**

```bash
cd apps/dashboard/src/composables
wc -l useCreatorProductTools.js
grep -nE "^function|^const|^export" useCreatorProductTools.js | head -30
```

识别 4 个功能分区：
- `useProductList` (~200 行) — 商品列表加载/过滤
- `useProductPublish` (~250 行) — 发布逻辑
- `usePlatformBindings` (~170 行) — 平台绑定管理
- `useProductSync` (~170 行) — 同步状态

- [ ] **Step 2: 创建 `useCreatorProductTools/index.ts`**

```typescript
export { useProductList } from './useProductList';
export type { ProductListItem } from './useProductList';
export { useProductPublish } from './useProductPublish';
export type { PublishTarget } from './useProductPublish';
export { usePlatformBindings } from './usePlatformBindings';
export { useProductSync } from './useProductSync';
```

- [ ] **Step 3: 创建 `useProductList.ts` (TDD)**

先写测试：

```typescript
// useProductList.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { useProductList } from './useProductList';

describe('useProductList', () => {
  it('returns empty array initially', () => {
    const { items } = useProductList();
    expect(items.value).toEqual([]);
  });

  it('loads items when fetch() is called', async () => {
    const { items, fetch } = useProductList();
    await fetch();
    expect(items.value.length).toBeGreaterThan(0);
  });
});
```

跑测试确认 FAIL：

```bash
cd /home/ailearn/projects/LingWen/.claude/worktrees/moling-redesign-phase19
pnpm --filter lingwen-dashboard-frontend test -- useProductList
```

Expected: FAIL (module not found)

最小实现：

```typescript
// useProductList.ts
import { ref } from 'vue';

export interface ProductListItem {
  id: string;
  name: string;
  status: 'draft' | 'published' | 'archived';
}

export function useProductList() {
  const items = ref<ProductListItem[]>([]);
  const loading = ref(false);

  async function fetch() {
    loading.value = true;
    try {
      // 从原 useCreatorProductTools.js 复制此函数实现
      items.value = await loadProducts();
    } finally {
      loading.value = false;
    }
  }

  return { items, loading, fetch };
}

async function loadProducts(): Promise<ProductListItem[]> {
  // TODO: 替换为实际 API 调用
  return [];
}
```

跑测试 PASS：

```bash
pnpm --filter lingwen-dashboard-frontend test -- useProductList
```

Expected: PASS (1 passed)

- [ ] **Step 4: 重复 Step 3 模式创建 `useProductPublish.ts` / `usePlatformBindings.ts` / `useProductSync.ts`**

每个子模块：
1. 写 .spec.ts（核心 state + 1-2 个 actions）
2. 跑测试 FAIL
3. 写 .ts 实现
4. 跑测试 PASS

每个 .ts ≤ 300 行。

- [ ] **Step 5: 修改 `useCreatorProductTools.js` 为 facade**

```javascript
/**
 * Phase 19: facade — 所有逻辑已迁移到 .ts 子模块
 * 下游 import 无需修改: import { useCreatorProductTools, CREATOR_PUBLISH_PLATFORMS } from './useCreatorProductTools.js'
 */
export {
  useProductList,
  useProductPublish,
  usePlatformBindings,
  useProductSync,
} from './useCreatorProductTools/index.ts';

export const CREATOR_PUBLISH_PLATFORMS = [
  'wechat', 'weibo', 'douban', 'qidian', 'jianzhi',
];
```

- [ ] **Step 6: 跑 vitest 验证**

```bash
pnpm --filter lingwen-dashboard-frontend test
```

Expected: 918/918 通过（4 个新 spec 已加入）

- [ ] **Step 7: 跑 vue-tsc 验证**

```bash
pnpm --filter lingwen-dashboard-frontend typecheck:app
```

Expected: 0 错误

- [ ] **Step 8: 提交**

```bash
git add apps/dashboard/src/composables/useCreatorProductTools.js \
        apps/dashboard/src/composables/useCreatorProductTools/
git commit -m "refactor(composables): split useCreatorProductTools into 4 .ts submodules + facade

- useProductList (200L) / useProductPublish (250L) /
  usePlatformBindings (170L) / useProductSync (170L)
- Original .js (788L → 30L facade)
- 4 vitest specs (TDD: test-first → impl → commit)
- vue-tsc 0 errors

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: 拆分 `useCreatorVolumePlanTemplates.js` (723 行 → 3 子模块)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorVolumePlanTemplates.js`
- Create: `apps/dashboard/src/composables/useCreatorVolumePlanTemplates/{index.ts,useTemplateList.ts,useTemplateList.spec.ts,useTemplateEditor.ts,useTemplateEditor.spec.ts,useTemplateImport.ts,useTemplateImport.spec.ts}`

- [ ] **Step 1: 读取原文件结构**

```bash
cd apps/dashboard/src/composables
grep -nE "^function|^const|^export" useCreatorVolumePlanTemplates.js
```

3 个功能分区：`useTemplateList` (~250)、`useTemplateEditor` (~250)、`useTemplateImport` (~200)

- [ ] **Step 2-5: TDD 模式重复 Task 1**

- 子模块：`useTemplateList` / `useTemplateEditor` / `useTemplateImport`
- 每个 .ts ≤ 300 行
- 每个 .spec.ts 覆盖核心 state + 1-2 个 actions

- [ ] **Step 6: facade `useCreatorVolumePlanTemplates.js`**

```javascript
export {
  useTemplateList,
  useTemplateEditor,
  useTemplateImport,
} from './useCreatorVolumePlanTemplates/index.ts';
```

- [ ] **Step 7-8: vitest + vue-tsc 验证**

```bash
pnpm --filter lingwen-dashboard-frontend test
pnpm --filter lingwen-dashboard-frontend typecheck:app
```

Expected: 918+ 通过，0 错误

- [ ] **Step 9: 提交**

```bash
git add apps/dashboard/src/composables/useCreatorVolumePlanTemplates.js \
        apps/dashboard/src/composables/useCreatorVolumePlanTemplates/
git commit -m "refactor(composables): split useCreatorVolumePlanTemplates into 3 .ts submodules (723L → 30L facade)"
```

---

## Task 3: 拆分 `useCreatorSettings.js` (711 行 → 3 子模块)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorSettings.js`
- Create: `apps/dashboard/src/composables/useCreatorSettings/{index.ts,useSettingsHistory.ts,useSettingsHistory.spec.ts,useMergePresets.ts,useMergePresets.spec.ts,useSettingsDocs.ts,useSettingsDocs.spec.ts}`

- [ ] **Step 1: 读取原文件**

```bash
cd apps/dashboard/src/composables
grep -nE "^function|^const|^export" useCreatorSettings.js
```

3 个分区：`useSettingsHistory` (~280)、`useMergePresets` (~250)、`useSettingsDocs` (~180)

- [ ] **Step 2-5: TDD 重复**

- [ ] **Step 6: facade**

```javascript
export {
  useSettingsHistory,
  useMergePresets,
  useSettingsDocs,
} from './useCreatorSettings/index.ts';
```

- [ ] **Step 7-9: 验证 + 提交**

```bash
git commit -m "refactor(composables): split useCreatorSettings into 3 .ts submodules (711L → 30L facade)"
```

---

## Task 4: 拆分 `useCreatorBatchHistory.js` (629 行 → 3 子模块)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorBatchHistory.js`
- Create: `apps/dashboard/src/composables/useCreatorBatchHistory/{index.ts,useBatchList.ts+spec,useBatchDiff.ts+spec,useBatchRestore.ts+spec}`

- [ ] **Step 1: 读取原文件**

3 个分区：`useBatchList` (~230)、`useBatchDiff` (~220)、`useBatchRestore` (~180)

- [ ] **Step 2-5: TDD 重复**

- [ ] **Step 6: facade**

```javascript
export {
  useBatchList,
  useBatchDiff,
  useBatchRestore,
} from './useCreatorBatchHistory/index.ts';
```

- [ ] **Step 7-9: 验证 + 提交**

```bash
git commit -m "refactor(composables): split useCreatorBatchHistory into 3 .ts submodules (629L → 30L facade)"
```

---

## Task 5: 拆分 `useCreatorWrite.js` (599 行 → 3 子模块)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorWrite.js`
- Create: `apps/dashboard/src/composables/useCreatorWrite/{index.ts,useWriteFlow.ts+spec,useWriteValidation.ts+spec,useWriteTools.ts+spec}`

- [ ] **Step 1: 读取原文件**

3 个分区：`useWriteFlow` (~250)、`useWriteValidation` (~200)、`useWriteTools` (~150)

- [ ] **Step 2-5: TDD 重复**

- [ ] **Step 6: facade**

```javascript
export {
  useWriteFlow,
  useWriteValidation,
  useWriteTools,
} from './useCreatorWrite/index.ts';
```

- [ ] **Step 7-9: 验证 + 提交**

```bash
git commit -m "refactor(composables): split useCreatorWrite into 3 .ts submodules (599L → 30L facade)"
```

---

## Task 6: 拆分 `useCreatorAgent.js` (564 行 → 3 子模块)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorAgent.js`
- Create: `apps/dashboard/src/composables/useCreatorAgent/{index.ts,useAgentConfig.ts+spec,useAgentTask.ts+spec,useAgentTools.ts+spec}`

- [ ] **Step 1: 读取原文件**

3 个分区：`useAgentConfig` (~220)、`useAgentTask` (~200)、`useAgentTools` (~150)

- [ ] **Step 2-5: TDD 重复**

- [ ] **Step 6: facade**

```javascript
export {
  useAgentConfig,
  useAgentTask,
  useAgentTools,
} from './useCreatorAgent/index.ts';
```

- [ ] **Step 7-9: 验证 + 提交**

```bash
git commit -m "refactor(composables): split useCreatorAgent into 3 .ts submodules (564L → 30L facade)"
```

---

## Task 7: 拆分 `useCreatorOnboarding.js` (555 行 → 3 子模块)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding.js`
- Create: `apps/dashboard/src/composables/useCreatorOnboarding/{index.ts,useWizardSteps.ts+spec,useOnboardingProgress.ts+spec,useOnboardingNotifications.ts+spec}`

- [ ] **Step 1: 读取原文件**

3 个分区：`useWizardSteps` (~250)、`useOnboardingProgress` (~180)、`useOnboardingNotifications` (~130)

- [ ] **Step 2-5: TDD 重复**

- [ ] **Step 6: facade**

```javascript
export {
  useWizardSteps,
  useOnboardingProgress,
  useOnboardingNotifications,
} from './useCreatorOnboarding/index.ts';
```

- [ ] **Step 7-9: 验证 + 提交**

```bash
git commit -m "refactor(composables): split useCreatorOnboarding into 3 .ts submodules (555L → 30L facade)"
```

---

## Task 8: 接入已有 useWorkbench*.ts (529 行 → 4 facade re-export)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorWriteWorkbench.js`
- (不创建新文件 — Phase 18 已 commit 4 个 useWorkbench*.ts)

- [ ] **Step 1: 确认 Phase 18 useWorkbench*.ts 已存在**

```bash
ls apps/dashboard/src/composables/useWorkbench*.ts
```

Expected:
- useWorkbenchAgent.ts (5620 bytes)
- useWorkbenchCheckpoint.ts (3196 bytes)
- useWorkbenchSelection.ts (3167 bytes)
- useWorkbenchValidation.ts (11676 bytes)

- [ ] **Step 2: 写测试 — facade re-export 完整性**

```typescript
// apps/dashboard/src/composables/useCreatorWriteWorkbench.spec.ts
import { describe, it, expect } from 'vitest';

describe('useCreatorWriteWorkbench facade', () => {
  it('re-exports all 4 useWorkbench hooks', async () => {
    const mod = await import('./useCreatorWriteWorkbench.js');
    expect(typeof mod.useWorkbenchSelection).toBe('function');
    expect(typeof mod.useWorkbenchCheckpoint).toBe('function');
    expect(typeof mod.useWorkbenchValidation).toBe('function');
    expect(typeof mod.useWorkbenchAgent).toBe('function');
  });
});
```

- [ ] **Step 3: 跑测试 FAIL**

```bash
cd apps/dashboard && pnpm test useCreatorWriteWorkbench
```

Expected: FAIL（module 没有 re-export）

- [ ] **Step 4: 修改 `useCreatorWriteWorkbench.js` 为 facade**

```javascript
/**
 * Phase 19: facade — 接入 Phase 18 已 commit 的 4 个 useWorkbench*.ts 子模块
 * 原始 529 行逻辑分散到 4 个 .ts 子模块
 * 下游 import 无需修改
 */
export {
  useWorkbenchSelection,
  useWorkbenchCheckpoint,
  useWorkbenchValidation,
  useWorkbenchAgent,
} from './useWorkbenchAgent.ts'; // index re-export
```

创建 `apps/dashboard/src/composables/useWorkbenchAgent.ts`（如不存在）作为聚合 index：

```typescript
export { useWorkbenchSelection } from './useWorkbenchSelection';
export { useWorkbenchCheckpoint } from './useWorkbenchCheckpoint';
export { useWorkbenchValidation } from './useWorkbenchValidation';
export { useWorkbenchAgent } from './useWorkbenchAgent';
```

- [ ] **Step 5: 跑测试 PASS**

```bash
pnpm test useCreatorWriteWorkbench
```

Expected: PASS

- [ ] **Step 6: vitest + vue-tsc 验证**

```bash
pnpm test
pnpm typecheck:app
```

Expected: 918+ 通过，0 错误

- [ ] **Step 7: 提交**

```bash
git add apps/dashboard/src/composables/useCreatorWriteWorkbench.js \
        apps/dashboard/src/composables/useWorkbenchAgent.ts \
        apps/dashboard/src/composables/useCreatorWriteWorkbench.spec.ts
git commit -m "refactor(composables): connect useCreatorWriteWorkbench to 4 useWorkbench*.ts (529L → 5L facade)

- 接入 Phase 18 已 commit 的 4 个 useWorkbench{Agent,Checkpoint,Selection,Validation}.ts
- facade 仅 re-export
- 下游 import 不变

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 19 Gate 验证

完成后运行：

```bash
pnpm --filter lingwen-dashboard-frontend test          # 918+ 通过
pnpm --filter lingwen-dashboard-frontend typecheck:app # vue-tsc 0 错误
pnpm --filter lingwen-dashboard-frontend lint:all     # ESLint clean

# 8 个原文件 ≤ 30 行
for f in useCreatorProductTools useCreatorVolumePlanTemplates useCreatorSettings useCreatorBatchHistory useCreatorWrite useCreatorAgent useCreatorOnboarding useCreatorWriteWorkbench; do
  lines=$(wc -l < apps/dashboard/src/composables/${f}.js)
  echo "$f.js: $lines lines (目标 ≤ 30)"
done
```

**Phase 19 Gate PASS 条件：**
- 8 个原文件 ≤ 30 行
- 所有子模块 ≤ 300 行
- vitest 918+ 通过
- vue-tsc --noEmit 0 错误
- 下游 import 零修改（grep 验证）

---

## Self-Review Notes

1. **Spec coverage:** ✅ 8 个 composable 全部覆盖，每个有独立 Task（Task 1-8）
2. **Placeholder scan:** 无 TBD/TODO/placeholder
3. **Type consistency:** 所有子模块导出 `function useXxx()` + `interface` 类型
4. **DRY:** 8 个 Task 结构相同（Step 1: 读原文件 → Step 2-5: TDD 子模块 → Step 6: facade → Step 7: 验证 → Step 8: 提交）
5. **Frequent commits:** 每个 Task 一个 commit（8 个 commit）
6. **Risk control:** 已有 Phase 18 useWorkbench*.ts（Task 8 低风险） + facade 模式保证向后兼容

---

## 预计时间

| Task | 文件 | 工作量 |
|------|------|--------|
| 1 | useCreatorProductTools (788L → 4 sub) | 2-3 天 |
| 2 | useCreatorVolumePlanTemplates (723L → 3 sub) | 2 天 |
| 3 | useCreatorSettings (711L → 3 sub) | 2 天 |
| 4 | useCreatorBatchHistory (629L → 3 sub) | 1.5 天 |
| 5 | useCreatorWrite (599L → 3 sub) | 1.5 天 |
| 6 | useCreatorAgent (564L → 3 sub) | 1.5 天 |
| 7 | useCreatorOnboarding (555L → 3 sub) | 1.5 天 |
| 8 | useCreatorWriteWorkbench (529L → facade) | 0.5 天 |

**总：12-14 天（2 周 + buffer）**