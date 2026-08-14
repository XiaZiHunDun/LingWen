# Phase 19 设计 — Composable 拆分（超 500 行）

> **日期**: 2026-08-14
> **基于**: V3.1 §F.3 (Composable ≤300 行) + V3.1 §F.4 (高频 TS 迁移) + moling-studio-redesign §19
> **范围**: 仅 8 个超 500 行的 composable
> **不包含**: API 拆分、Pinia 迁移、OpenAPI codegen（这些是 Phase 19.2+）

---

## 1. 背景

### 现状（Phase 18 后）

`apps/dashboard/src/composables/` 目录共 11785 行 / 44 文件：

| 文件 | 行数 | exports |
|------|------|---------|
| useCreatorProductTools.js | 788 | 2 |
| useCreatorVolumePlanTemplates.js | 723 | 1 |
| useCreatorSettings.js | 711 | 1 |
| useCreatorBatchHistory.js | 629 | 1 |
| useCreatorWrite.js | 599 | 1 |
| useCreatorAgent.js | 564 | 1 |
| useCreatorOnboarding.js | 555 | 1 |
| useCreatorWriteWorkbench.js | 529 | 1 |

这些文件违反 V3.1 §F.3（≤300 行）和 AGENTS.md "代码可维护性" 原则。

### 已存在的 Phase 18 资产

- `apps/dashboard/src/composables/useWorkbench{Agent,Checkpoint,Selection,Validation}.ts`（4 个 .ts 子模块）
- `apps/dashboard/src/composables/index.js`（re-export 入口）
- 已 commit 但**未实际接入** `useCreatorWriteWorkbench.js`（仍 529 行原版）

---

## 2. 目标

| 指标 | 当前 | 目标 |
|------|------|------|
| 8 个超 500 行 composable 行数 | 529~788 | ≤ 300 |
| 8 个原文件 facade | 不存在 | 仅 re-export，< 30 行 |
| 子模块 .ts 占比 | 4 个（已存在但未接入） | 40+ 个 |
| vitest 测试 | 918/918 | 100% 通过 |
| vue-tsc --noEmit | 0 错误 | 0 错误 |
| 下游 import 兼容性 | n/a | 零修改 |

---

## 3. 架构

### 3.1 目录结构

```
apps/dashboard/src/composables/
├── useCreatorProductTools.js              (facade, ≤30 行 re-export)
├── useCreatorProductTools/
│   ├── index.ts                            (re-export 入口)
│   ├── useProductList.ts                   (~150 行, 商品列表)
│   ├── useProductPublish.ts                (~200 行, 发布管理)
│   ├── usePlatformBindings.ts              (~150 行, 平台绑定)
│   └── useProductSync.ts                   (~150 行, 同步逻辑)
├── useCreatorVolumePlanTemplates.js        (facade)
├── useCreatorVolumePlanTemplates/
│   ├── index.ts
│   ├── useTemplateList.ts                  (~200 行)
│   ├── useTemplateEditor.ts                (~250 行)
│   └── useTemplateImport.ts                (~200 行)
├── ... (其他 6 个类似)
└── useWorkbenchAgent.ts                    (Phase 18 已存在 .ts, 不动)
```

### 3.2 Facade 模式

每个原 `.js` 文件改为：

```javascript
// useCreatorProductTools.js (~25 行)
// Phase 19: facade — 所有逻辑已迁移到 .ts 子模块
// 下游 import 无需修改
export {
  useCreatorProductTools as default,
  CREATOR_PUBLISH_PLATFORMS,
} from './useCreatorProductTools/index.ts';
```

### 3.3 子模块原则

每个 `<name>.ts` 文件：
- **单一职责**：一个 use 函数 + 配套的 type
- **依赖注入**：通过参数 `deps` 而非全局访问
- **类型导出**：`export interface UseXxxReturn { ... }`
- **行数上限**：≤ 300 行
- **测试文件**：`<name>.spec.ts` 同目录

### 3.4 8 个 composable 拆分计划

| 原文件 | 拆为 | 子模块划分依据 |
|--------|------|---------------|
| useCreatorProductTools.js | 4 | product list / publish / platform bindings / sync |
| useCreatorVolumePlanTemplates.js | 3 | template list / editor / import |
| useCreatorSettings.js | 3 | settings history / merge presets / docs |
| useCreatorBatchHistory.js | 3 | batch list / diff / restore |
| useCreatorWrite.js | 3 | write flow / validation / tools |
| useCreatorAgent.js | 3 | agent config / task / tools |
| useCreatorOnboarding.js | 3 | wizard steps / progress / notifications |
| useCreatorWriteWorkbench.js | 4 | 接入已有 4 个 useWorkbench*.ts（不重复实现） |

**总计**：8 facade + 26 .ts 子模块 + 26 .spec.ts = 60 个新文件

---

## 4. 测试策略

每个子 composable：

```typescript
// useProductList.spec.ts
import { describe, it, expect } from 'vitest';
import { useProductList } from './useProductList';

describe('useProductList', () => {
  it('returns empty list initially', () => { ... });
  it('loads products on demand', async () => { ... });
  it('handles load errors', async () => { ... });
});
```

Facade 测试：

```typescript
// useCreatorProductTools.spec.ts
describe('facade re-exports', () => {
  it('re-exports default and named exports', () => {
    const mod = await import('./useCreatorProductTools.js');
    expect(mod.default).toBe(useCreatorProductTools);
    expect(mod.CREATOR_PUBLISH_PLATFORMS).toBeDefined();
  });
});
```

---

## 5. 风险评估

| 风险 | 缓解 |
|------|------|
| 8 个 composable 同时改易冲突 | 每个 PR 拆 1-2 个，避免巨型 diff |
| 下游 import 兼容性 | facade 模式保留所有原导出 |
| 类型推断丢失 | 显式 `export interface` + 每个子模块独立 .d.ts |
| 测试覆盖率下降 | 每个子模块强制要求 spec.ts；无 spec 不允许 commit |
| TypeScript 渐进迁移引入 new bugs | vue-tsc --noEmit 强制；Phase 18 mypy 范式延伸 |
| 已有 useWorkbench*.ts 重复实现 | Task 19.8 专门处理：删除 useCreatorWriteWorkbench.js 中重复逻辑，仅 re-export |

---

## 6. 任务列表（计划阶段）

见 docs/superpowers/plans/2026-08-14-phase19-composable-split-plan.md（writing-plans skill 输出）

**预估**：8 个 Task / 2 周

---

## 7. 不在 Phase 19 范围内

明确不做，留给 Phase 19.2+：

- ❌ Pinia store 拆分（→ Phase 19.2）
- ❌ api/*.js 拆分（→ Phase 19.3）
- ❌ OpenAPI codegen（→ Phase 19.4）
- ❌ 角色白名单单点化（→ Phase 19.5）
- ❌ 错误分类系统 V3.1 P1（→ Phase 19.6）
- ❌ 类型系统深度强化（→ Phase 19.7）
- ❌ V3.1 §F.3 的其他 composable（剩余 36 个 < 500 行可后续处理）

---

## 8. 关联文档

- V3.1 路线图：[`docs/LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md`](../LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md) §F
- moling-redesign §19：[`docs/superpowers/plans/2026-08-08-moling-studio-redesign-implementation-plan.md`](../superpowers/plans/2026-08-08-moling-studio-redesign-implementation-plan.md)
- Phase 18 plan：[`docs/superpowers/plans/2026-08-14-phase18-business-boundary-interface-plan.md`](../superpowers/plans/2026-08-14-phase18-business-boundary-interface-plan.md)
- AI 契约：[`AGENTS.md`](../../AGENTS.md)