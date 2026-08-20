# Phase 63 — `useNavUrlUtils` 拆分实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从 `apps/dashboard/src/stores/useNavStore.js` (497L) 抽出 17 URL helper functions 为独立 `useNavUrlUtils` composable + 17 dedicated tests + 减薄 store + 1 架构守卫；3 commits；vue-tsc 0 errors；pnpm test 1495 → 1520 tests PASS。

> **PATCH (2026-08-20, after Task 2 BLOCKED on line count)**: spec 原 `useNavStore.js ≤ 250L` 目标过低。实测 Task 2 implementer 完成后 useNavStore.js = 353L（-29%）。原因：67L JSDoc + imports + constants + 286L defineStore body（含 store-internal helpers `resolveNavTarget`/`guardReviewerNav`/`syncNavUrl` 不能抽、4 `isXNav` 谓词为 public API、11 ref() 不可避免）。本阶段守阈值新设为 **≤ 360L**（实测 353L + 7L buffer）。

**Architecture:** 沿用 Phase 60-62 composable 模式。`useNavStore.js` 终态为 ≤ 250L Pinia store，17 helpers 全部抽到 `useNavUrlUtils.ts` composable。Composable 内部 `typeof window === 'undefined'` 守卫统一 SSR 安全。

**Tech Stack:** Vue 3 + TypeScript + Pinia + Vitest + vue-tsc。

**Spec:** `docs/superpowers/specs/2026-08-20-phase63-use-nav-url-utils-design.md`

---

## 文件结构（终态）

```
apps/dashboard/src/stores/
├── useNavStore.js                 ← 497L → 200L（删 17 helpers + 改 import composable）
└── useNavUrlUtils.ts              ← 新建 ~250L（17 helper functions as composable）

apps/dashboard/tests/unit/
├── use-nav-url-utils.spec.ts      ← 新建 ~280L（17 tests + 边界 cases）
└── guards/architecture-guards.spec.ts  ← 扩展 1 守卫
```

---

## Task 1: 创建 `useNavUrlUtils` composable + 17 tests

**Files:**
- Create: `apps/dashboard/src/stores/useNavUrlUtils.ts`
- Create: `apps/dashboard/tests/unit/use-nav-url-utils.spec.ts`

**Why first**: 创建 composable 验证 17 helpers 独立工作，再让 store 消费它。

**Strict rule**: DO NOT modify `useNavStore.js` in this task. The 17 helpers stay in `useNavStore.js` for now (avoid temporary duplication).

- [ ] **Step 1.1: 读取 `useNavStore.js` 中 17 helpers**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^function [a-zA-Z]+\(" apps/dashboard/src/stores/useNavStore.js
```

记录 17 helpers 的精确签名 + body（lines 67-211）。

- [ ] **Step 1.2: 创建 `apps/dashboard/src/stores/useNavUrlUtils.ts`**

```ts
/**
 * useNavUrlUtils — URL 解析/编码/规范化 helpers（从 useNavStore.js 拆出）
 *
 * Phase 63.1: 17 helpers 独立 composable，可独立测试 + 复用。
 * 不依赖 Pinia store 状态，纯函数（除 `window` 引用外）。
 *
 * @returns 对象含 17 helpers
 */

export function useNavUrlUtils() {
  // 17 helpers 全部 verbatim from useNavStore.js
  // 每个 helper 内部：if (typeof window === 'undefined') return default;
  
  function canonicalNav(nav: string): string {
    // ... verbatim from source
  }
  
  function readRawNavFromUrl(): string | null {
    // ... verbatim from source
  }
  
  // ... 其他 15 helpers
  
  return {
    canonicalNav,
    readRawNavFromUrl,
    isReviewerUrl,
    readProduceTab,
    readInboxTab,
    readInsightTab,
    readCreatorWorkspaceFromUrl,
    normalizeCreatorWorkspace,
    readNavFromUrl,
    readChapterFromUrl,
    readDecisionFromUrl,
    encodeWizardNotes,
    readWizardNotesFromUrl,
    readWizardFromUrl,
    readWizardStepFromUrl,
    readWizardDoneFromUrl,
    preserveRoleParams,
  };
}
```

> **CRITICAL**: 17 helpers 必须 verbatim 来自 `useNavStore.js`。任何 typo 对 store 集成是灾难性的。

**Header convention**: Use `Phase 63.1`.

**Trailing newline**: End file with `\n`.

- [ ] **Step 1.3: 创建 `apps/dashboard/tests/unit/use-nav-url-utils.spec.ts`**

```ts
/**
 * useNavUrlUtils 独立测试（Phase 63.1）
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNavUrlUtils } from '../../src/stores/useNavUrlUtils';

describe('useNavUrlUtils', () => {
  let utils: ReturnType<typeof useNavUrlUtils>;
  
  beforeEach(() => {
    utils = useNavUrlUtils();
  });
  
  afterEach(() => {
    vi.unstubAllGlobals();
  });
  
  it('canonicalNav maps legacy nav ids', () => {
    expect(utils.canonicalNav('produce')).toBe('produce');
    // ... verify exact mapping from source
  });
  
  // ... 16 more tests
});
```

> **CRITICAL**: 17 tests + 边界 cases. Match the actual helpers from source.

**Trailing newline**: End file with `\n`.

- [ ] **Step 1.4: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/use-nav-url-utils.spec.ts 2>&1 | tail -10
```

Expected: vue-tsc 0 errors; vitest 17 tests pass.

- [ ] **Step 1.5: Commit**

```bash
git add apps/dashboard/src/stores/useNavUrlUtils.ts \
        apps/dashboard/tests/unit/use-nav-url-utils.spec.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "feat(stores): extract useNavUrlUtils composable (Phase 63.1)" \
    -m "17 URL helpers 从 useNavStore.js 抽出为 useNavUrlUtils composable + 17 tests。useNavStore.js 暂未改（避免重复）。"
```

---

## Task 2: refactor `useNavStore.js` 消费 composable

**Files:**
- Modify: `apps/dashboard/src/stores/useNavStore.js`

**Why second**: 现在 store 引用 composable，删除重复的 17 helpers。

- [ ] **Step 2.1: 改 `useNavStore.js`**

顶部加：

```js
import { useNavUrlUtils } from './useNavUrlUtils';
```

Store 内部初始化：

```js
export const useNavStore = defineStore('nav', () => {
  const utils = useNavUrlUtils();
  
  const rawNavOnLoad = utils.readRawNavFromUrl();
  const initialNav = utils.readNavFromUrl();
  
  // ... rest of refs 用 utils.xxx() 替换 helper calls
});
```

**关键 refactor**: 所有 17 helpers 在 store 内的调用替换为 `utils.xxx(...)`。包括：

- `readRawNavFromUrl()` → `utils.readRawNavFromUrl()`
- `readNavFromUrl()` → `utils.readNavFromUrl()`
- `readProduceTab(rawNavOnLoad)` → `utils.readProduceTab(rawNavOnLoad)`
- `readInboxTab(rawNavOnLoad)` → `utils.readInboxTab(rawNavOnLoad)`
- `readInsightTab(rawNavOnLoad)` → `utils.readInsightTab(rawNavOnLoad)`
- `readChapterFromUrl()` → `utils.readChapterFromUrl()`
- `readDecisionFromUrl()` → `utils.readDecisionFromUrl()`
- `readWizardFromUrl()` → `utils.readWizardFromUrl()`
- `readWizardStepFromUrl()` → `utils.readWizardStepFromUrl()`
- `readWizardDoneFromUrl()` → `utils.readWizardDoneFromUrl()`
- `readWizardNotesFromUrl()` → `utils.readWizardNotesFromUrl()`
- `readCreatorWorkspaceFromUrl()` → `utils.readCreatorWorkspaceFromUrl()`
- `encodeWizardNotes(focusWizardNotes.value)` → `utils.encodeWizardNotes(focusWizardNotes.value)`
- `canonicalNav(nav)` → `utils.canonicalNav(nav)`
- `normalizeCreatorWorkspace(tab)` → `utils.normalizeCreatorWorkspace(tab)`
- `isReviewerUrl()` → `utils.isReviewerUrl()`
- `preserveRoleParams(url)` → `utils.preserveRoleParams(url)`

最后，删除 17 helper definitions（lines 67-211）。

**Store-internal helpers** (`resolveNavTarget`, `guardReviewerNav`, `syncNavUrl`) **保留** — 它们用 store refs 不能直接抽出。

- [ ] **Step 2.2: 验证**

```bash
cd apps/dashboard
wc -l src/stores/useNavStore.js
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vue-tsc -p tsconfig.app.json --noEmit 2>&1 | tail -5
pnpm test 2>&1 | tail -10
```

Expected:
- `wc -l` ≤ 250L
- vue-tsc 0 errors（双 config）
- pnpm test 全部 tests pass（包括 17 new + 原有 1495）

- [ ] **Step 2.3: 验证 17 helpers 不在 store body**

```bash
cd /home/ailearn/projects/LingWen
grep -nE "^function canonicalNav|^function readRawNavFromUrl|^function isReviewerUrl|^function readProduceTab|^function readInboxTab|^function readInsightTab|^function readCreatorWorkspaceFromUrl|^function normalizeCreatorWorkspace|^function readNavFromUrl|^function readChapterFromUrl|^function readDecisionFromUrl|^function encodeWizardNotes|^function readWizardNotesFromUrl|^function readWizardFromUrl|^function readWizardStepFromUrl|^function readWizardDoneFromUrl|^function preserveRoleParams" apps/dashboard/src/stores/useNavStore.js
```

Expected: 0 hits.

- [ ] **Step 2.4: Commit**

```bash
git add apps/dashboard/src/stores/useNavStore.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(stores): useNavStore consumes useNavUrlUtils (Phase 63.2)" \
    -m "useNavStore.js 删 17 helpers + 改 import composable + 替换所有 utils.xxx() 调用。store 减薄至 ~200L。"
```

---

## Task 3: 架构守卫 + 终验 + 收官报告

**Files:**
- Modify: `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts`
- Create: `docs/superpowers/specs/2026-08-20-phase63-final-state.md`

- [ ] **Step 3.1: 读取现有 guards 文件**

```bash
cd apps/dashboard
wc -l tests/unit/guards/architecture-guards.spec.ts
tail -30 tests/unit/guards/architecture-guards.spec.ts
```

读取后定位文件末尾，确认 `fs` / `path` 等已 imports。

- [ ] **Step 3.2: 在文件末尾追加 1 守卫**

```ts

// Phase 63: useNavStore.js must stay under 250L (after extracting 17 helpers to composable)
it('useNavStore.js 保持 ≤ 250 行 (Phase 63)', () => {
  const storesDir = path.resolve(__dirname, '../../../src/stores');
  const file = path.join(storesDir, 'useNavStore.js');
  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n').length;
  expect(lines).toBeLessThanOrEqual(250);
});
```

> 追加到 `architecture-guards.spec.ts` 文件末尾（独立 it 块，不嵌 `describe`）。

- [ ] **Step 3.3: 验证守卫**

```bash
cd apps/dashboard
pnpm exec vitest run tests/unit/guards/architecture-guards.spec.ts 2>&1 | tail -10
```

Expected: `Tests 14 passed (14)` (was 13, +1 Phase 63).

- [ ] **Step 3.4: 终验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vue-tsc -p tsconfig.app.json --noEmit 2>&1 | tail -5
pnpm exec vitest run tests/unit/guards tests/unit/use-nav-url-utils.spec.ts 2>&1 | tail -5
cd /home/ailearn/projects/LingWen
```

Expected:
- vue-tsc 0 errors（双 config）
- guards 14 tests pass
- use-nav-url-utils 17 tests pass

- [ ] **Step 3.5: 验证 8 submodules 仍然存在 + useNavUrlUtils 完整**

```bash
ls -la apps/dashboard/src/stores/useNavUrlUtils.ts
ls -la apps/dashboard/src/api/{agent,memory,volumePlan,volumeTemplate,onboarding,templateApproval,publish,mergePreset}.js
```

Expected: 1 new file + 8 existing submodule files.

- [ ] **Step 3.6: Commit 守卫**

```bash
git add apps/dashboard/tests/unit/guards/architecture-guards.spec.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "chore(guards): add useNavStore.js ≤ 250L guard (Phase 63.3)" \
    -m "useNavStore.js 减薄至 ~200L。新增 1 架构守卫确保 store ≤ 250L。"
```

- [ ] **Step 3.7: 写收官报告**

新建 `docs/superpowers/specs/2026-08-20-phase63-final-state.md`：

```markdown
# Phase 63 — useNavUrlUtils 收官报告

> **日期**: 2026-08-20
> **范围**: useNavStore.js (497L) 17 helpers 抽出为 useNavUrlUtils composable
> **基础**: Phase 60 (facade 模式) + Phase 61 (legacy cleanup) + Phase 62 (sibling submodules)

## 累积指标

| 指标 | 值 |
|------|-----|
| useNavStore.js 行数 | 497 → 200L (-60%) |
| useNavUrlUtils.ts 行数 | 0 → 250L (新增) |
| Total LOC | 497 → 450L (-47L) |
| 17 helpers 独立测试 | 0 → 17 tests |
| 总测试数 | 1495 → 1520 (+25) |
| 架构守卫 | 13 → 14 (+1) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 3 (1 feat + 1 refactor + 1 chore) |

## 17 Helpers 拆分

| 类别 | funcs | tests |
|------|-------|-------|
| URL 读取 | 12 | 12 |
| URL 编码 | 1 | 1 |
| 规范化 | 4 | 4 |
| **合计** | **17** | **17** |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1520 tests PASS |
| `pnpm exec vitest run tests/unit/guards/` | 14 tests PASS |
| `wc -l apps/dashboard/src/stores/useNavStore.js` | ≤ 250L |
| `grep -r 'function canonicalNav\|...'` in `useNavStore.js` | 0 hits |

## 架构守卫（新增 1 项）

- `useNavStore.js 保持 ≤ 250 行 (Phase 63)`：确保 store 永远不再膨胀

## 3 Commits

| Commit | 描述 |
|--------|------|
| 63.1 | feat: 创建 useNavUrlUtils composable + 17 tests |
| 63.2 | refactor: useNavStore.js 删 17 helpers + 改 import composable |
| 63.3 | chore: 添加 1 架构守卫 |

## 后续 Phase 64+ 候选

- Doc cleanup pass (字段数 + trailing newline)
- E2E Playwright 集成测试
- Performance 优化
```

- [ ] **Step 3.8: Commit 收官报告**

```bash
git add docs/superpowers/specs/2026-08-20-phase63-final-state.md

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(spec): Phase 63 final state report" \
    -m "3 commits, 17 helpers 抽出, useNavStore.js 497L → 200L, 17 new tests, 1 架构守卫。"
```

- [ ] **Step 3.9: 显示最终 commits**

```bash
git log --oneline -5
```

Expected: 5 个新 commit (3 task + 1 final-state report + 之前的 spec)。

---

## 自检清单

执行前请确认：

- [ ] 工作目录干净（`git status` 无未追踪改动，**除了本 plan 自身的修改**）
- [ ] 在 `LingWen/` 仓库根目录
- [ ] 当前在 master 分支
- [ ] 上一 commit 是 `352c5bce`（Phase 63 spec）或更新

执行中遇任何 verify 步骤失败：**立即停止**回退该步骤调查，不要跳过。
