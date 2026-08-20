# Phase 63 — `useNavUrlUtils` 拆分设计

> **日期**: 2026-08-20
> **范围**: 从 `apps/dashboard/src/stores/useNavStore.js` (497L) 抽出 17 URL helper functions 为独立 `useNavUrlUtils` composable + 17 dedicated tests + 减薄 store + 1 架构守卫
> **基础**: Phase 60 (facade 模式) + Phase 61 (legacy cleanup) + Phase 62 (sibling submodules) 已完整闭环
> **版本**: master（Phase 62 收官后）

---

## 1. 背景

`apps/dashboard/src/stores/useNavStore.js` 是 497L 单文件 Pinia store，含 17 个 URL 解析/编码/规范化 helpers + 1 store 定义 + 3 个 store-internal helpers（resolveNavTarget / guardReviewerNav / syncNavUrl）。问题：

- **17 helpers 全部 pure functions**（除 `window` 引用），未独立测试
- **0 dedicated tests** — store 行为靠 e2e-smoke 覆盖（25 个测试）
- **3 callers**（App.vue, useDashboardNav.js, router/index.js）从 `./stores/index.js` 引入 store — helpers 与 store 状态深度耦合
- 难以复用：URL 解析逻辑若其他模块需要，只能 import 整个 Pinia store

沿用 Phase 60-62 拆分模式：将 17 helpers 抽到独立 composable，纯函数特性使其更易测试。

## 2. 目标 & 非目标

### 目标
1. 17 URL helpers 抽出为 `useNavUrlUtils` composable
2. 17 dedicated tests（每 helper 至少 1 个 + 边界 cases）
3. `useNavStore.js` 减薄至 ≤ 250L
4. 1 架构守卫确保 store ≤ 250L
5. vue-tsc 0 errors + 全测 PASS

### 非目标
- 不重构 store 内部 helpers（resolveNavTarget / guardReviewerNav / syncNavUrl — 用 store refs 不能直接抽出）
- 不改 Pinia 状态结构
- 不改 3 callers（App.vue, useDashboardNav.js, router/index.js）
- 不引入新依赖

## 3. 文件结构

### 3.1 终态

```
apps/dashboard/src/stores/
├── useNavStore.js                 ← 497L → 200L（删 17 helpers + 改 import composable）
└── useNavUrlUtils.ts              ← 新建 ~250L（17 helper functions as composable）

apps/dashboard/tests/unit/
└── use-nav-url-utils.spec.ts      ← 新建 ~280L（17 tests + 边界 cases）
```

### 3.2 文档

```
docs/superpowers/specs/
├── 2026-08-20-phase63-use-nav-url-utils-design.md   ← 本 spec
└── 2026-08-20-phase63-final-state.md               ← 收官报告
```

## 4. 17 Helpers 详情

按职责分类：

### 4.1 URL 读取 (12)

| Function | 签名 | 用途 |
|----------|------|------|
| `readRawNavFromUrl()` | `() => string \| null` | 从 URL `?nav=` 读 raw nav |
| `readNavFromUrl()` | `() => string` | 读 nav 并 canonicalize |
| `readProduceTab(rawNav)` | `(rawNav: string \| null) => string` | 读 produce tab |
| `readInboxTab(rawNav)` | `(rawNav: string \| null) => string` | 读 inbox tab |
| `readInsightTab(rawNav)` | `(rawNav: string \| null) => string` | 读 insight tab |
| `readCreatorWorkspaceFromUrl()` | `() => string` | 读 creator workspace |
| `readChapterFromUrl()` | `() => number \| null` | 读 ?chapter=N |
| `readDecisionFromUrl()` | `() => string \| null` | 读 ?decision=N |
| `readWizardFromUrl()` | `() => boolean` | 读 ?wizard=1 |
| `readWizardStepFromUrl()` | `() => string` | 读 ?step=N |
| `readWizardDoneFromUrl()` | `() => string[]` | 读 ?done= |
| `readWizardNotesFromUrl()` | `() => Record<string, unknown>` | 读 ?notes= base64 |

### 4.2 URL 编码 (1)

| Function | 签名 | 用途 |
|----------|------|------|
| `encodeWizardNotes(notes)` | `(notes: Record<string, unknown>) => string` | encode notes → base64 JSON |

### 4.3 规范化 (4)

| Function | 签名 | 用途 |
|----------|------|------|
| `canonicalNav(nav)` | `(nav: string) => string` | map legacy nav IDs |
| `normalizeCreatorWorkspace(tab)` | `(tab: string \| null) => string` | normalize creator workspace ids |
| `isReviewerUrl()` | `() => boolean` | 检查 ?review=1 或 /reviewer/ |
| `preserveRoleParams(url)` | `(url: URL) => void` | 保留/删除 ?role= ?review=1 |

## 5. Composable 结构

```ts
/**
 * useNavUrlUtils — URL 解析/编码/规范化 helpers（从 useNavStore.js 拆出）
 *
 * Phase 63: 17 helpers 独立 composable，可独立测试 + 复用。
 * 不依赖 Pinia store 状态，纯函数（除 `window` 引用外）。
 *
 * @returns 对象含 17 helpers
 */
export function useNavUrlUtils() {
  // 17 helpers 全部 verbatim from useNavStore.js
  // 每个 helper 内部：if (typeof window === 'undefined') return default;
  
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

**Composable vs 纯函数模块的取舍**：
- 选 composable 是为 Vue 3 模式一致（与 `useCreatorWriteWorkbench`, `useWorkbenchLayout` 一致）
- 纯函数 module 也可以，但破坏 Phase 60-62 命名约定
- 选 composable 内置 SSR 守卫 — `useNavStore.js` 已有 4 处 `typeof window === 'undefined'` 守卫；composable 内部统一处理

## 6. 3 commits 流程

### 6.1 Commit 1: `feat(stores): extract useNavUrlUtils composable (Phase 63.1)`

- Create `apps/dashboard/src/stores/useNavUrlUtils.ts` ~250L
- Create `apps/dashboard/tests/unit/use-nav-url-utils.spec.ts` ~280L（17 tests）
- **不改** `useNavStore.js`（17 helpers 仍存在，避免重复）
- **Verify**: `pnpm exec vue-tsc --noEmit` 0 errors + 17 tests pass

### 6.2 Commit 2: `refactor(stores): useNavStore consumes useNavUrlUtils (Phase 63.2)`

- Edit `useNavStore.js`:
  - 删 17 helper definitions
  - 加 `import { useNavUrlUtils } from './useNavUrlUtils';`
  - store 内部用 `const utils = useNavUrlUtils();` 一次性引入
  - 替换所有 helper calls 为 `utils.xxx(...)`
- **Verify**: vue-tsc 0 errors + 全部 callers 工作（`pnpm test` 现有 tests pass）

### 6.3 Commit 3: `chore(guards): add useNavStore.js ≤ 250L guard (Phase 63.3)`

- 加 1 架构守卫到 `architecture-guards.spec.ts`
- 创建 `docs/superpowers/specs/2026-08-20-phase63-final-state.md`
- **Verify**: vue-tsc 0 errors + guards 13 → 14 tests pass

## 7. 测试策略

### 7.1 测试文件结构

```ts
/**
 * useNavUrlUtils 独立测试（Phase 63.1）
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNavUrlUtils } from '../../src/stores/useNavUrlUtils';

describe('useNavUrlUtils', () => {
  // 17 tests, 每 helper 1 个 + 边界 cases
});
```

### 7.2 测试模式

- **URL mock**: `vi.stubGlobal('window', { location: { href: 'http://test/?nav=produce' } })` + cleanup
- **SSR 守卫**: 一组 tests 用 `vi.stubGlobal('window', undefined)` 验证返回值合理
- **边界 cases**: 空字符串、null、特殊字符（`?chapter=hello` → null）、大整数（`?chapter=99999999` → 保留）

### 7.3 测试覆盖

| 函数 | Tests |
|------|-------|
| `canonicalNav` | 1 happy + 1 legacy mapping |
| `readRawNavFromUrl` | 1 present + 1 absent + 1 SSR |
| `isReviewerUrl` | 1 in /reviewer/ + 1 ?review=1 + 1 false |
| `readProduceTab` | 1 + 1 fallback |
| `readInboxTab` | 1 + 1 fallback |
| `readInsightTab` | 1 + 1 fallback |
| `readCreatorWorkspaceFromUrl` | 1 + 1 default |
| `normalizeCreatorWorkspace` | 1 + 1 invalid |
| `readNavFromUrl` | 1 + 1 SSR |
| `readChapterFromUrl` | 1 + 1 null + 1 NaN |
| `readDecisionFromUrl` | 1 + 1 null |
| `encodeWizardNotes` | 1 + 1 empty |
| `readWizardNotesFromUrl` | 1 + 1 invalid base64 |
| `readWizardFromUrl` | 1 + 1 false |
| `readWizardStepFromUrl` | 1 + 1 default |
| `readWizardDoneFromUrl` | 1 + 1 empty |
| `preserveRoleParams` | 1 + 1 + 1 |

最小 17 tests + 边界约 8 tests = 25 tests total.

## 8. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1495 → 1520 tests PASS（17 new tests） |
| `pnpm exec vitest run tests/unit/guards/` | 13 → 14 tests PASS |
| `wc -l apps/dashboard/src/stores/useNavStore.js` | ≤ 250L |
| `grep -r 'function canonicalNav\|function readRawNavFromUrl\|...' apps/dashboard/src/stores/useNavStore.js` | 0 hits |
| `git log --oneline -5` | 3 commits (63.1 + 63.2 + 63.3) |

## 9. 架构守卫

`apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` 追加 1 项：

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

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 17 helpers 移出后 useNavStore 内部 refs 失效 | 低 | 编译错 | TypeScript 型检查 + 3 caller 验证 |
| Composable SSR 风险（window undefined） | 中 | 测试 fail | composable 内部统一 `typeof window === 'undefined'` 守卫 |
| Existing tests for nav logic break | 中 | 集成 break | 跑 `tests/unit/` + `tests/e2e-smoke/` 中任何 nav 相关 test |
| encodeWizardNotes 边界 cases（malformed input） | 中 | test fail | 沿用 source 现有容错 |

## 11. 后续 Phase 64+ 候选

- Doc cleanup pass (字段数 51/56/55→59 + trailing newline 全修)
- E2E Playwright 集成测试（追加 8-10 个关键流）
- Performance 优化（bundle / runtime）

## 12. 收官报告

实施完成后写 `docs/superpowers/specs/2026-08-20-phase63-final-state.md`：
- 累积指标（useNavStore.js 减薄、tests、commits）
- 17 helpers 分类详表
- 验证结果
- 架构守卫
- 后续 Phase 64+ 候选
