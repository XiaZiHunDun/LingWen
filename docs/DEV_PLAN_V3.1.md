# 灵文工作室 V3.1 开发计划

> **版本**: V3.1 | **日期**: 2026-07-30
> **基于**: LINGWEN_V3.1_ARCHITECTURE_OPTIMIZATION.md
> **状态**: 执行中

---

## Phase 1: 创作体验优化（P0）

### 1.1 useCreatorWriteWorkbench 拆分

**当前**: `useCreatorWriteWorkbench.ts` — 680 行，49 个返回字段
**目标**: 拆分为 4 个子模块 + 1 聚合入口

```
composables/creator/
├── useCreatorWriteWorkbench.ts    (保留，聚合入口，~200 行)
├── useWorkbenchSelection.ts       (新增，选区 + Intent 管理)
├── useWorkbenchCheckpoint.ts      (新增，检查点 + Diff)
├── useWorkbenchValidation.ts      (新增，轻量校验 + 冲突标记)
└── useWorkbenchAgent.ts           (新增，Agent 控制 + 生成)
```

### 1.2 上下文缓存层

**文件**: `infra/prompt_engineering/cache.py`
**功能**: 三层缓存（永久/卷级/章节级），哈希校验，减少 token 消耗

### 1.3 上下文压缩

**文件**: `infra/prompt_engineering/compressor.py`
**功能**: head-tail 截断 + 伏笔保护 + 摘要替代

### 1.4 高频 Composable TS 迁移

**目标文件** (8 个高频使用):
- `useCreatorPage.js` → `.ts`
- `useCreatorVolumePlan.js` → `.ts`
- `useRippleSocket.js` → `.ts`
- `useWorkflowSocket.js` → `.ts`
- `useStudioProject.js` → `.ts`
- `useDashboardWidgets.js` → `.ts`
- `useAskAssistant.js` → `.ts`
- `useApiConnectivity.js` → `.ts`

---

## Phase 2: 质量与防错（P1）

### 2.1 AGENTS.md
### 2.2 类型系统强化
### 2.3 守卫测试
### 2.4 错误分类系统

---

## 验证标准

- vue-tsc --noEmit: 零错误
- vitest run: 918/918 通过
- ESLint: 无新增错误