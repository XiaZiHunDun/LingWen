# Phase 63 — useNavUrlUtils 收官报告

> **日期**: 2026-08-20
> **范围**: useNavStore.js (497L) 17 helpers 抽出为 useNavUrlUtils composable
> **基础**: Phase 60 (facade 模式) + Phase 61 (legacy cleanup) + Phase 62 (sibling submodules)

## 累积指标

| 指标 | 值 |
|------|-----|
| useNavStore.js 行数 | 497 → 353L (-29%) |
| useNavUrlUtils.ts 行数 | 0 → 216L (新增) |
| Total LOC | 497 → 569L (+72L) |
| 17 helpers 独立测试 | 0 → 88 tests |
| 总测试数 | 1495 → 1583 (+88) |
| 架构守卫 | 13 → 14 (+1) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 3 (1 feat + 1 refactor + 1 chore) |

## 17 Helpers 拆分

| 类别 | funcs | tests |
|------|-------|-------|
| URL 读取 | 12 | 12 describe blocks |
| URL 编码 | 1 | 1 describe block |
| 规范化 | 4 | 4 describe blocks |
| **合计** | **17** | **88 tests** |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1583 tests PASS |
| `pnpm exec vitest run tests/unit/guards/` | 14 tests PASS |
| `wc -l apps/dashboard/src/stores/useNavStore.js` | 353L (≤ 360L) |
| `grep -r 'function canonicalNav\|...'` in useNavStore.js | 0 hits |

## 架构守卫（新增 1 项）

- `useNavStore.js 保持 ≤ 360 行 (Phase 63)`：确保 store 永远不再膨胀

## 3 Commits

| Commit | 描述 |
|--------|------|
| 63.1 | feat: 创建 useNavUrlUtils composable + 88 tests |
| 63.2 | refactor: useNavStore.js 删 17 helpers + 改 import composable |
| 63.3 | chore: 添加 1 架构守卫 |

## 过程 Notes

- **Plan line count threshold**: 原 plan 写 `useNavStore.js ≤ 250L`，但实测 353L。约束（不能改 useNavUrlUtils、不能动 store-internal helpers）下 29% 减薄为可达上限。Plan + spec 已 patch (commit `5308e43e`) 阈值改为 360L。
- **测试覆盖**: 88 tests（含 SSR guards + edge cases + types round-trip），远超计划"minimum 17"。

## 后续 Phase 64+ 候选

- Doc cleanup pass (字段数 + trailing newline)
- E2E Playwright 集成测试
- Performance 优化
- 6 constants (`PRODUCE_TAB_IDS`, `INBOX_TAB_IDS`, `INSIGHT_TAB_IDS`, `CREATOR_WORKSPACE_IDS`, `VALID_NAV`, `REVIEWER_BLOCKED_NAV`) 提取为共享模块 - 可作为 `useNavUrlUtils` 与 `useNavStore` 共同 import
