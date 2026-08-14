# Phase 19 Implementation Plan — Composable 拆分（超 500 行）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 7 个超 500 行的 monolithic composable 拆为 .ts 子模块，main hook 仍返回原 shape 保证下游零修改。

**Architecture:** 每个 monolithic .js 文件保持 main hook 不变（返回原 refs/computed/methods shape），但内部逻辑改为"组合 3-4 个 .ts 子模块"。子模块是私有实现细节，main hook 通过调用子模块组合完整功能。Facade 模式仅在 main hook 简化到 ≤30 行时才使用（否则保留原 200-500 行 main hook）。

**Tech Stack:** Vue 3.5+ Composition API、TypeScript 5.x、Vitest 4.x、vue-tsc

**前置依赖：** Phase 18 v12.0 已合并到 master（commit 6210e941）

**Run in worktree:** `.claude/worktrees/moling-redesign-phase19`

**重要更新 (2026-08-14)：**
Task 8 试点发现 plan 假设错误——useWorkbench*.ts 不是 useCreatorWriteWorkbench.js 的子模块。Task 8 调整为仅添加 useWorkbenchIndex.ts（commit 0761d0f7）。
Tasks 1-7（7 个其他 composable）已验证为真正 monolithic（无 .ts 子模块），原 plan 假设正确，但需要明确"提取 + 组合"语义。

---

## 文件结构

```
apps/dashboard/src/composables/
├── useCreatorProductTools.js              (Modify: 重构为 sub-module 组合)
├── useCreatorProductTools/                (Create dir)
│   ├── index.ts                            (子模块聚合)
│   ├── useProductList.ts                   (新)
│   ├── useProductList.spec.ts              (新)
│   ├── useProductPublish.ts                (新)
│   ├── useProductPublish.spec.ts           (新)
│   ├── usePlatformBindings.ts              (新)
│   ├── usePlatformBindings.spec.ts         (新)
│   ├── useProductSync.ts                   (新)
│   └── useProductSync.spec.ts              (新)
├── ... (其他 6 个 composable 类似结构)
└── useCreatorWriteWorkbench.js            (Task 8 维持原状)
```

---

## 通用模式（每个 Task 1-7 共用）

每个 monolithic .js 文件拆分流程：

### Step 1: 阅读原文件理解结构

```bash
cd apps/dashboard/src/composables
grep -nE "^function|^const|^export" useCreatorProductTools.js | head -30
```

识别 3-4 个**功能分组**（每个对应一个子模块）：
- Group 1: state + actions（一个职责域）
- Group 2: state + actions
- ...

### Step 2: 创建子目录与 `index.ts`

```typescript
// useCreatorProductTools/index.ts
export { useProductList } from './useProductList';
export type { ProductListItem } from './useProductList';
export { useProductPublish } from './useProductPublish';
// ...
```

### Step 3: TDD 创建第一个子模块

写 .spec.ts → 跑 FAIL → 写 .ts 实现 → 跑 PASS

### Step 4: 重复 Step 3 创建其余子模块

### Step 5: 修改原 .js 为主 hook（保持原 API）

```javascript
// useCreatorProductTools.js — 重构后
import { useProductList } from './useCreatorProductTools/useProductList.js';
import { useProductPublish } from './useCreatorProductTools/useProductPublish.js';
// ...

/**
 * Phase 19: 重构为 sub-module 组合。原 788 行逻辑分散到 4 个 .ts 子模块。
 * 下游 API（返回值 shape）保持完全兼容：所有 refs/computed/methods 名称不变。
 */
export function useCreatorProductTools(deps) {
  const list = useProductList(deps);
  const publish = useProductPublish(deps);
  const bindings = usePlatformBindings(deps);
  const sync = useProductSync(deps);

  return {
    ...list.refs,
    ...list.actions,
    ...publish.refs,
    ...publish.actions,
    ...bindings.refs,
    ...bindings.actions,
    ...sync.refs,
    ...sync.actions,
  };
}
```

关键：**返回原 shape**，下游不破坏。

### Step 6: 全量验证

```bash
cd apps/dashboard && pnpm test      # 922+ pass
pnpm typecheck:app                  # 0 errors
```

### Step 7: 提交

```bash
git commit -m "refactor(composables): split useCreatorProductTools into 4 .ts submodules"
```

---

## Task 1: 拆分 `useCreatorProductTools.js` (788 行 → 4 子模块)

预计 2-3 天。参考上方通用模式。

**子模块划分：**
- `useProductList` (商品列表加载/过滤)
- `useProductPublish` (发布逻辑)
- `usePlatformBindings` (平台绑定)
- `useProductSync` (同步状态)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorProductTools.js`
- Create: `apps/dashboard/src/composables/useCreatorProductTools/{index.ts, useProductList.ts+spec, useProductPublish.ts+spec, usePlatformBindings.ts+spec, useProductSync.ts+spec}`

---

## Task 2: 拆分 `useCreatorVolumePlanTemplates.js` (723 行 → 3 子模块)

**子模块划分：**
- `useTemplateList` (模板列表)
- `useTemplateEditor` (模板编辑)
- `useTemplateImport` (模板导入)

预计 2 天。

---

## Task 3: 拆分 `useCreatorSettings.js` (711 行 → 3 子模块)

**子模块划分：**
- `useSettingsHistory` (设置历史)
- `useMergePresets` (合并预设)
- `useSettingsDocs` (设置文档)

预计 2 天。

---

## Task 4: 拆分 `useCreatorBatchHistory.js` (629 行 → 3 子模块)

**子模块划分：**
- `useBatchList` (批次列表)
- `useBatchDiff` (批次 diff)
- `useBatchRestore` (批次恢复)

预计 1.5 天。

---

## Task 5: 拆分 `useCreatorWrite.js` (599 行 → 3 子模块)

**子模块划分：**
- `useWriteFlow` (写作流)
- `useWriteValidation` (写作验证)
- `useWriteTools` (写作工具)

预计 1.5 天。

---

## Task 6: 拆分 `useCreatorAgent.js` (564 行 → 3 子模块)

**子模块划分：**
- `useAgentConfig` (Agent 配置)
- `useAgentTask` (Agent 任务)
- `useAgentTools` (Agent 工具)

预计 1.5 天。

---

## Task 7: 拆分 `useCreatorOnboarding.js` (555 行 → 3 子模块)

**子模块划分：**
- `useWizardSteps` (向导步骤)
- `useOnboardingProgress` (引导进度)
- `useOnboardingNotifications` (引导通知)

预计 1.5 天。

---

## Phase 19 Gate

完成后：

```bash
# 8 个 composable 全部 ≤ 500 行（理想 ≤ 300 行）
for f in useCreatorProductTools useCreatorVolumePlanTemplates useCreatorSettings \
         useCreatorBatchHistory useCreatorWrite useCreatorAgent \
         useCreatorOnboarding useCreatorWriteWorkbench; do
  lines=$(wc -l < apps/dashboard/src/composables/${f}.js)
  echo "$f.js: $lines lines"
done

# 子模块 ≤ 300 行
find apps/dashboard/src/composables -name "*.ts" -type f | xargs wc -l | sort -rn | head -20

# 全量验证
cd apps/dashboard && pnpm test         # 922+ pass
pnpm typecheck:app                     # 0 errors
pnpm lint:all                          # clean

# 下游 import 兼容性
grep -rE "from.*useCreatorProductTools|/useCreator.*\.js" apps/dashboard/src apps/dashboard/tests | wc -l
# 应保持与 baseline 相同（约 22 处）
```

**Phase 19 Gate PASS 条件：**
- 8 个原文件 ≤ 500 行（≤ 300 行更佳）
- 24 个新 .ts 子模块每个 ≤ 300 行
- vitest 922+ pass
- vue-tsc --noEmit 0 errors
- 下游 22 处 import 零修改
- 24 个 .spec.ts 覆盖

---

## Self-Review Notes (修订后)

1. **Spec coverage:** ✅ 7 个 composable 全部覆盖（Task 1-7），Task 8 已调整（仅 useWorkbenchIndex.ts）
2. **Placeholder scan:** 无 TBD/TODO
3. **Type consistency:** 所有子模块导出 `function useXxx()` + `interface`
4. **关键澄清：** main hook 返回值 shape 不变（保证下游兼容）
5. **DRY:** 7 个 Task 结构相同
6. **Frequent commits:** 每个 Task 一个 commit

---

## 预计时间

| Task | 文件 | 工作量 |
|------|------|--------|
| 1 | useCreatorProductTools (788L) | 2-3 天 |
| 2 | useCreatorVolumePlanTemplates (723L) | 2 天 |
| 3 | useCreatorSettings (711L) | 2 天 |
| 4 | useCreatorBatchHistory (629L) | 1.5 天 |
| 5 | useCreatorWrite (599L) | 1.5 天 |
| 6 | useCreatorAgent (564L) | 1.5 天 |
| 7 | useCreatorOnboarding (555L) | 1.5 天 |

**总：12-14 天（2 周 + buffer）**

每个 Task 都涉及：
- 读 500-800 行 monolith
- 识别 3-4 个 logical groupings
- 提取每个到 .ts 子模块
- 改写 main hook 组合 sub-modules
- 验证 22 处下游 import

建议：每次会话执行 1 个 Task（确保质量）。