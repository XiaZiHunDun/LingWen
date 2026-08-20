# Phase 64 — 6 Nav Constants 共享模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从 `useNavStore.js` + `useNavUrlUtils.ts` 抽出 6 重复 nav constants 为独立 `navConstants.ts` 模块；2 commits；vue-tsc 0 errors；1583 tests PASS。

**Architecture:** 单一 source of truth。`navConstants.ts` 导出 6 constants（基于 `dashboardNav.js` 派生 + verbatim 常量）。`useNavStore.js` + `useNavUrlUtils.ts` 都 import 自此 module。

**Tech Stack:** Vue 3 + TypeScript + Pinia + Vitest + vue-tsc。

**Spec:** `docs/superpowers/specs/2026-08-20-phase64-nav-constants-design.md`

---

## 文件结构（终态）

```
apps/dashboard/src/stores/
├── navConstants.ts                ← 新建 ~30L（6 constants）
├── useNavStore.js                 ← 353L → ~330L（删 6 consts + import navConstants）
└── useNavUrlUtils.ts              ← 216L → ~200L（删 6 consts + import navConstants）
```

---

## Task 1: 建 `navConstants.ts` + 改 `useNavUrlUtils.ts` import

**Files:**
- Create: `apps/dashboard/src/stores/navConstants.ts`
- Modify: `apps/dashboard/src/stores/useNavUrlUtils.ts`

**Strict rule**: DO NOT modify `useNavStore.js` in this task. The 6 consts remain duplicated in store (avoid temporary triple-import).

- [ ] **Step 1.1: 读取 6 consts 完整值**

```bash
cd /home/ailearn/projects/LingWen
sed -n '15,46p' apps/dashboard/src/stores/useNavUrlUtils.ts
```

记录 6 consts 的完整值（verbatim from source）。

- [ ] **Step 1.2: 创建 `apps/dashboard/src/stores/navConstants.ts`**

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

// VALID_NAV: derived from dashboardNav.js — 复制 source verbatim
export const VALID_NAV: string[] = [
  // ... verbatim from useNavStore.js lines 42-51
];

export const REVIEWER_BLOCKED_NAV: Set<string> = new Set([
  // ... verbatim from useNavStore.js line 63
]);
```

> **CRITICAL**: 6 consts 必须 verbatim from source. 任何 typo 会导致 store/composable 行为不一致。

**Header convention**: Use `Phase 64.1`.

**Trailing newline**: End file with `\n`.

- [ ] **Step 1.3: 改 `useNavUrlUtils.ts`**

顶部加：

```ts
import {
  PRODUCE_TAB_IDS,
  INBOX_TAB_IDS,
  INSIGHT_TAB_IDS,
  CREATOR_WORKSPACE_IDS,
  VALID_NAV,
  REVIEWER_BLOCKED_NAV,
} from './navConstants';
```

**同时删除** `useNavUrlUtils.ts` 中 6 consts definitions (lines 17-44)。

- [ ] **Step 1.4: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/use-nav-url-utils.spec.ts 2>&1 | tail -10
```

Expected: vue-tsc 0 errors; vitest 88 tests pass.

- [ ] **Step 1.5: 验证 useNavStore.js 未改**

```bash
cd /home/ailearn/projects/LingWen
git diff apps/dashboard/src/stores/useNavStore.js | head -5
echo "---should be empty---"
```

Expected: empty diff.

- [ ] **Step 1.6: Commit**

```bash
git add apps/dashboard/src/stores/navConstants.ts \
        apps/dashboard/src/stores/useNavUrlUtils.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(stores): extract navConstants shared module (Phase 64.1)" \
    -m "6 nav constants 抽到 navConstants.ts; useNavUrlUtils.ts 改 import navConstants. useNavStore.js 暂未改（避免临时重复）。"
```

---

## Task 2: 改 `useNavStore.js` import + 验证 + 报告

**Files:**
- Modify: `apps/dashboard/src/stores/useNavStore.js`
- Create: `docs/superpowers/specs/2026-08-20-phase64-final-state.md`

**Why second**: 现在 store 也 import navConstants, 6 consts 完全 single source.

- [ ] **Step 2.1: 改 `useNavStore.js`**

顶部加：

```js
import {
  PRODUCE_TAB_IDS,
  INBOX_TAB_IDS,
  INSIGHT_TAB_IDS,
  CREATOR_WORKSPACE_IDS,
  VALID_NAV,
  REVIEWER_BLOCKED_NAV,
} from './navConstants.js';
```

**同时删除** `useNavStore.js` 中 6 consts definitions (lines 36-63).

- [ ] **Step 2.2: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vue-tsc -p tsconfig.app.json --noEmit 2>&1 | tail -5
pnpm test 2>&1 | tail -10
```

Expected:
- vue-tsc 0 errors (双 config)
- pnpm test 1583 tests pass

- [ ] **Step 2.3: 验证 6 consts 不在 store body**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^const PRODUCE_TAB_IDS|^const INBOX_TAB_IDS|^const INSIGHT_TAB_IDS|^const CREATOR_WORKSPACE_IDS|^const VALID_NAV|^const REVIEWER_BLOCKED_NAV" apps/dashboard/src/stores/useNavStore.js
echo "---should be empty---"
```

Expected: 0 hits.

- [ ] **Step 2.4: 验证 6 consts 仅在 navConstants.ts**

```bash
grep -nE "^export const PRODUCE_TAB_IDS|^export const INBOX_TAB_IDS|^export const INSIGHT_TAB_IDS|^export const CREATOR_WORKSPACE_IDS|^export const VALID_NAV|^export const REVIEWER_BLOCKED_NAV" apps/dashboard/src/stores/navConstants.ts
```

Expected: 6 hits.

- [ ] **Step 2.5: 验证 useNavStore.js 减薄**

```bash
cd apps/dashboard
wc -l src/stores/useNavStore.js
wc -l src/stores/useNavUrlUtils.ts
```

Expected: useNavStore.js 353L → ~330L; useNavUrlUtils.ts 216L → ~200L.

- [ ] **Step 2.6: Commit**

```bash
git add apps/dashboard/src/stores/useNavStore.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(stores): useNavStore consumes navConstants (Phase 64.2)" \
    -m "useNavStore.js 删 6 consts + 改 import navConstants。6 consts 唯一 source of truth。"
```

- [ ] **Step 2.7: 写收官报告**

新建 `docs/superpowers/specs/2026-08-20-phase64-final-state.md`：

```markdown
# Phase 64 — navConstants 收官报告

> **日期**: 2026-08-20
> **范围**: 6 nav constants 抽到 navConstants.ts 共享模块
> **基础**: Phase 63 (useNavUrlUtils composable) follow-up

## 累积指标

| 指标 | 值 |
|------|-----|
| navConstants.ts | 0 → 30L (新建) |
| useNavStore.js | 353 → 330L (-23L) |
| useNavUrlUtils.ts | 216 → 200L (-16L) |
| Total LOC | 569 → 560L (-9L) |
| 6 consts source of truth | 2 → 1 |
| 总测试数 | 1583 (无新增) |
| 架构守卫 | 14 (无新增) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 2 (refactor + refactor) |

## 6 Constants 抽取

| Constant | Type | 单一 source |
|----------|------|------------|
| `PRODUCE_TAB_IDS` | `string[]` | `navConstants.ts:8` |
| `INBOX_TAB_IDS` | `string[]` | `navConstants.ts:9` |
| `INSIGHT_TAB_IDS` | `string[]` | `navConstants.ts:10` |
| `CREATOR_WORKSPACE_IDS` | `string[]` | `navConstants.ts:11` |
| `VALID_NAV` | `string[]` | `navConstants.ts:14` |
| `REVIEWER_BLOCKED_NAV` | `Set<string>` | `navConstants.ts:18` |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1583 tests PASS |
| `grep '^const PRODUCE_TAB_IDS' useNavStore.js` | 0 hits |
| `grep '^const PRODUCE_TAB_IDS' useNavUrlUtils.ts` | 0 hits |
| `grep '^export const PRODUCE_TAB_IDS' navConstants.ts` | 1 hit（validates single source of truth) |

## 2 Commits

| Commit | 描述 |
|--------|------|
| 64.1 | refactor: 建 navConstants.ts + 改 useNavUrlUtils.ts import |
| 64.2 | refactor: 改 useNavStore.js import + 删 6 consts |

## 后续 Phase 65+ 候选

- Doc cleanup pass (trailing newline — 30+ 文件)
- E2E Playwright 集成测试
- Performance 优化
```

- [ ] **Step 2.8: Commit 收官报告**

```bash
git add docs/superpowers/specs/2026-08-20-phase64-final-state.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 64 final state report" \
    -m "2 commits, 6 consts 抽到 navConstants.ts 共享模块. 单一 source of truth 关闭 Phase 63 follow-up."
```

- [ ] **Step 2.9: 显示最终 commits**

```bash
git log --oneline -5
```

Expected: 4 个新 commit (2 task + 1 final-state report + 之前的 spec).

---

## 自检清单

执行前请确认：

- [ ] 工作目录干净（`git status` 无未追踪改动，**除了本 plan 自身的修改**）
- [ ] 在 `LingWen/` 仓库根目录
- [ ] 当前在 master 分支
- [ ] 上一 commit 是 `953782f2`（Phase 64 spec）或更新

执行中遇任何 verify 步骤失败：**立即停止**回退该步骤调查，不要跳过。
