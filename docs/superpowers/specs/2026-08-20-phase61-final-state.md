# Phase 61 — Legacy Workbench Cleanup 收官报告

> **日期**: 2026-08-20
> **范围**: 5 源 + 2 测删除 + index.ts 清理 + 6 守卫
> **基础**: Phase 60 完整闭环

## 累积指标

| 指标 | 值 |
|------|-----|
| Legacy 源文件 | 5 → 0 (-717L) |
| Legacy 测试 | 2 → 0 (-22 tests: 14 + 8) |
| 总测试数 | 1343 → 1328 (-15) |
| 总测试文件 | 182 → 180 (-2) |
| 架构守卫 | 5 → 11 (+6) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 1 (单原子) |

## 改动文件清单

| 文件 | 动作 |
|------|------|
| useWorkbenchCheckpoint.ts | deleted (107L) |
| useWorkbenchValidation.ts | deleted (333L) |
| useWorkbenchAgent.ts | deleted (161L) |
| useWorkbenchSelection.ts (legacy) | deleted (102L) |
| useWorkbenchIndex.ts | deleted (14L) |
| use-workbench-checkpoint.spec.ts | deleted (Phase 38, 14 tests) |
| use-workbench-selection-intent.spec.ts | deleted (Phase 18.9, 8 tests) |
| composables/index.ts | 4 处清理 (line 17, 83, 130-132, 135) |
| architecture-guards.spec.ts | +6 guards (148L) |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 180 files / 1328 tests PASS |
| `pnpm exec vitest run tests/unit/guards/` | 11 tests PASS |
| `grep -r useWorkbenchIndex apps/dashboard/src` | 0 hits |
| `grep -r useCreatorWorkbenchSelection apps/dashboard/src` | 0 hits |
| `grep -r useWorkbenchCheckpoint/Validation/Agent/Selection/Index( apps/dashboard/src` | 2 hits（均为 Phase 60.5 新模块 `useCreatorWriteWorkbench/useWorkbenchSelection.ts` 及其调用方 — 非 legacy） |

## 架构守卫（新增 6 项）

- 5 项断言：5 个 legacy 文件不存在（`useWorkbenchCheckpoint/Validation/Agent/Selection/Index.ts`）
- 1 项断言：`composables/index.ts` 不再 re-export `useWorkbenchIndex`

## 过程 Notes

- 任务顺序修正：Task 1 (index.ts) 先于 Task 2 (delete files)。原计划是 delete-first，触发 vue-tsc 报 `Cannot find module './useWorkbenchIndex.js'` 后被 plan patch (commit `ce7e4330`) 修正为先清理 index.ts。
- 测试数修正：原计划预期 1343 → 1321（delta -22）配 -6 guards 净得 1327；实测 2 个 legacy spec 含 14 + 8 = 22 tests + 6 guards = 1328。计划与 spec 已 patch（commit `0986ac47`）记录中间值 1322；最终实际值为 1328（多 1 项 guard 计数变化）。
- 收尾 commit 模式：单原子 commit 与 Phase 60 的 6-子 phase 拆分相反，因为本阶段范围小、动作原子。
- grep 误报说明：第 3 条 grep 命中 2 处实际为新模块（`useCreatorWriteWorkbench.js:50` 调用 + `useCreatorWriteWorkbench/useWorkbenchSelection.ts:58` 导出），名称同名但路径在子目录下，与已删除的 legacy `useWorkbenchSelection.ts`（顶层）不冲突。

## 后续 Phase 62+ 候选

- `api/creator.js` (686L, 114 functions) 拆分
- `useCreatorSettings.js` (650L) approval 流程独立
- `useNavStore.js` (497L) 拆分
- E2E Playwright 集成测试
- Performance 优化
- Doc cleanup pass（字段数 51/56/55→59 + trailing newline 全修）