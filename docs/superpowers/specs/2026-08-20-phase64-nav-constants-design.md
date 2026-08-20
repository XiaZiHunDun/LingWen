# Phase 64 — 6 Nav Constants 共享模块设计

> **日期**: 2026-08-20
> **范围**: 从 `useNavStore.js` + `useNavUrlUtils.ts` 抽出 6 重复 nav constants 为独立 `navConstants.ts` 模块
> **基础**: Phase 60 (facade) + Phase 61 (legacy cleanup) + Phase 62 (sibling submodules) + Phase 63 (useNavUrlUtils composable) 已完整闭环
> **版本**: master（Phase 63 收官后）

---

## 1. 背景

Phase 63 把 `useNavStore.js` 的 17 helpers 拆出为 `useNavUrlUtils.ts` composable 时，**6 个 constants 仍重复定义**：

| Constant | Type | `useNavStore.js` line | `useNavUrlUtils.ts` line |
|----------|------|----------------------|--------------------------|
| `PRODUCE_TAB_IDS` | `string[]` | 36 | 17 |
| `INBOX_TAB_IDS` | `string[]` | 37 | 18 |
| `INSIGHT_TAB_IDS` | `string[]` | 38 | 19 |
| `CREATOR_WORKSPACE_IDS` | `string[]` | 40 | 21 |
| `VALID_NAV` | `string[]` | 42-51 | 23-32 |
| `REVIEWER_BLOCKED_NAV` | `Set<string>` | 63 | 44 |

如果未来 2 个文件中任一更新（添加新 tab、新的 reviewer-blocked nav），另一文件会 stale。Phase 63 reviewer 标记为 follow-up：

> "DRY: 6 constants duplicated in both files. Intentional (composable must be self-contained for reuse) but acceptable; could be a Phase 64 follow-up to extract shared constants."

## 2. 目标 & 非目标

### 目标
1. 6 constants 抽到独立 `apps/dashboard/src/stores/navConstants.ts` 模块
2. `useNavStore.js` 与 `useNavUrlUtils.ts` 都 import 自此 module
3. 2 commits（先 useNavUrlUtils 改，再 useNavStore 改）
4. vue-tsc 0 errors + 1583 tests PASS

### 非目标
- 不动 const 值本身（verbatim from source）
- 不重构 store 业务（store-internal helpers 保留）
- 不引入新依赖
- 不加测试（6 consts 已被 88 useNavUrlUtils tests + 现有 store tests 间接覆盖）

## 3. 文件结构

### 3.1 终态

```
apps/dashboard/src/stores/
├── navConstants.ts                ← 新建 ~30L（6 constants）
├── useNavStore.js                 ← 353L → 约 330L（删 6 consts + import navConstants）
└── useNavUrlUtils.ts              ← 216L → 约 200L（删 6 consts + import navConstants）
```

### 3.2 文档

```
docs/superpowers/specs/
├── 2026-08-20-phase64-nav-constants-design.md   ← 本 spec
└── 2026-08-20-phase64-final-state.md           ← 收官报告
```

## 4. navConstants.ts 结构

```ts
/**
 * navConstants — 6 nav-related constants shared between useNavStore and useNavUrlUtils
 *
 * Phase 64: 从 useNavStore.js (lines 36-63) + useNavUrlUtils.ts (lines 17-44) 抽取 6 重复 constants。
 * 单一 source of truth，杜绝两份定义 drift。
 */

import { PRODUCE_TABS, INBOX_TABS, INSIGHT_TABS } from '../config/dashboardNav';

export const PRODUCE_TAB_IDS: string[] = PRODUCE_TABS.map((t) => t.id);
export const INBOX_TAB_IDS: string[] = INBOX_TABS.map((t) => t.id);
export const INSIGHT_TAB_IDS: string[] = INSIGHT_TABS.map((t) => t.id);
export const CREATOR_WORKSPACE_IDS: string[] = ['write', 'pulse', 'settings'];

// VALID_NAV: derived from dashboardNav.js (LEGACY_*_NAV_IDS + canonical IDs)
// 复制 useNavStore.js verbatim
export const VALID_NAV: string[] = [
  // ... verbatim from source
];

export const REVIEWER_BLOCKED_NAV: Set<string> = new Set([
  // ... verbatim from source
]);
```

**TypeScript 类型**：
- `string[]` for TAB_IDS / CREATOR_WORKSPACE_IDS / VALID_NAV
- `Set<string>` for REVIEWER_BLOCKED_NAV
- 来源可以是 `import type *` 或 runtime value — 选择 runtime value（确保 jest mock 兼容）

## 5. 2 commits 流程

### 5.1 Commit 1: `refactor(stores): extract navConstants shared module (Phase 64.1)`

- Create `apps/dashboard/src/stores/navConstants.ts` (~30L)
- Modify `useNavUrlUtils.ts`:
  - Add `import { PRODUCE_TAB_IDS, INBOX_TAB_IDS, INSIGHT_TAB_IDS, CREATOR_WORKSPACE_IDS, VALID_NAV, REVIEWER_BLOCKED_NAV } from './navConstants';`
  - Delete 6 const definitions (lines 17-44)
- **DO NOT** modify `useNavStore.js`（避免两份 import 暂存）
- **Verify**: vue-tsc 0 errors + 88 useNavUrlUtils tests pass

### 5.2 Commit 2: `refactor(stores): useNavStore consumes navConstants (Phase 64.2)`

- Modify `useNavStore.js`:
  - Add `import { PRODUCE_TAB_IDS, INBOX_TAB_IDS, INSIGHT_TAB_IDS, CREATOR_WORKSPACE_IDS, VALID_NAV, REVIEWER_BLOCKED_NAV } from './navConstants.js';`
  - Delete 6 const definitions (lines 36-63)
- **Verify**: vue-tsc 0 errors + 1583 tests pass (no regression)

## 6. 测试策略

### 6.1 无新增测试

6 constants 已被现有测试覆盖：
- 88 tests in `use-nav-url-utils.spec.ts` 间接覆盖 `useNavUrlUtils.ts` 中的 const usage
- 现有 `useNavStore.js` 测试覆盖 `useNavStore.js` 中的 const usage

### 6.2 验证：原 1583 tests 全部 pass

## 7. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1583 tests PASS |
| `pnpm exec vitest run tests/unit/use-nav-url-utils.spec.ts` | 88 tests PASS |
| `grep 'PRODUCE_TAB_IDS = ' apps/dashboard/src/stores/useNavStore.js` | 0 hits |
| `grep 'PRODUCE_TAB_IDS = ' apps/dashboard/src/stores/useNavUrlUtils.ts` | 0 hits |
| `grep 'PRODUCE_TAB_IDS' apps/dashboard/src/stores/navConstants.ts` | 1 hit |
| `wc -l apps/dashboard/src/stores/useNavStore.js` | 353 → ~330L |
| `wc -l apps/dashboard/src/stores/useNavUrlUtils.ts` | 216 → ~200L |
| `git log --oneline -5` | 2 commits (64.1 + 64.2) |

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Constant 值 drift between 2 callers | 极低 | 编译/运行错 | 1 source of truth |
| Side effect on `useNavStore.js` (e.g., 删 6 consts 错删其他) | 低 | 编译错 | TypeScript 守卫 |
| import circular dependency | 低 | 编译错 | navConstants.ts 不依赖其他 nav module |
| `useNavStore.js` 是 JS，`navConstants.ts` 是 TS | 低 | 编译错 | Vue 3 + TS 兼容 JS import |

## 9. 后续 Phase 65+ 候选

- Doc cleanup pass (trailing newline — 30+ 文件)
- E2E Playwright 集成测试
- Performance 优化

## 10. 收官报告

实施完成后写 `docs/superpowers/specs/2026-08-20-phase64-final-state.md`：
- 累积指标（新增 navConstants.ts，store/composable 减薄）
- 6 constants 单一 source of truth
- 验证结果
- 后续 Phase 65+ 候选
