# Phase 64 — navConstants 收官报告

> **日期**: 2026-08-20
> **范围**: 6 nav constants 抽到 navConstants.ts 共享模块
> **基础**: Phase 63 (useNavUrlUtils composable) follow-up

## 累积指标

| 指标 | 值 |
|------|-----|
| navConstants.ts | 0 → 40L (新建) |
| useNavStore.js | 353 → 326L (-27L) |
| useNavUrlUtils.ts | 216 → 189L (-27L) |
| useDashboardNav.js | clean (dead CREATOR_WORKSPACE_IDS export removed) |
| Total LOC | 569 → 555L (-14L) |
| 6 consts source of truth | 2 → 1 |
| 总测试数 | 1549 (无新增) |
| 架构守卫 | 14 (无新增) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 2 (refactor + refactor) |

## 6 Constants 抽取

| Constant | Type | 单一 source |
|----------|------|------------|
| `PRODUCE_TAB_IDS` | `string[]` | `navConstants.ts:10` |
| `INBOX_TAB_IDS` | `string[]` | `navConstants.ts:11` |
| `INSIGHT_TAB_IDS` | `string[]` | `navConstants.ts:12` |
| `CREATOR_WORKSPACE_IDS` | `string[]` | `navConstants.ts:14` |
| `VALID_NAV` | `string[]` | `navConstants.ts:16` |
| `REVIEWER_BLOCKED_NAV` | `Set<string>` | `navConstants.ts:37` |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1549 tests PASS (189 files) |
| `grep '^const PRODUCE_TAB_IDS' useNavStore.js` | 0 hits |
| `grep '^const PRODUCE_TAB_IDS' useNavUrlUtils.ts` | 0 hits |
| `grep '^export const PRODUCE_TAB_IDS' navConstants.ts` | 1 hit |

## 2 Commits

| Commit | 描述 |
|--------|------|
| 64.1 | refactor: 建 navConstants.ts + 改 useNavUrlUtils.ts import |
| 64.2 | refactor: 改 useNavStore.js import + 删 6 consts + 清理 dead code |

## 过程 Notes

- **Task 1 reviewer 发现**: `useDashboardNav.js` 有第三份未使用 `CREATOR_WORKSPACE_IDS` export. Task 2 清理此 dead code 巩固了「单一 source of truth」。
- **Bonus cleanup**: `useNavUrlUtils.ts` 移除了 3 个 unused imports (`PRODUCE_TABS`/`INBOX_TABS`/`INSIGHT_TABS`)。

## 后续 Phase 65+ 候选

- Doc cleanup pass (trailing newline — 30+ 文件)
- E2E Playwright 集成测试
- Performance 优化