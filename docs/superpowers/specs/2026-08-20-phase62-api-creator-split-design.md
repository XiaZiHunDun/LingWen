# Phase 62 — `api/creator.js` 拆分设计

> **日期**: 2026-08-20
> **范围**: 把 `api/creator.js` (686L, 114 funcs) 拆为 8 个 sibling submodule + 1 thin facade re-export + 8 个 submodule 独立测试
> **基础**: Phase 60 (facade 模式) + Phase 61 (legacy cleanup) 已完整闭环
> **版本**: master（Phase 61 收官后）

---

## 1. 背景

`apps/dashboard/src/api/creator.js` 历经多 phase 累积，承载 114 个 creator API 调用函数（114 funcs 都是 `request('/creator/...')` 的薄壳），存在以下问题：

- **单文件 686L / 114 funcs**：拖慢 vue-tsc + IDE 跳转
- **8+ 域混合**：agent / volumePlan / volumeTemplate / onboarding / templateApproval / publish / settingsDocs / memory 无法定位
- **0 单元测试**：114 funcs 全部裸跑，HTTP 契约无 assert
- **API 与调用方耦合**：所有 funcs 集中在一处，caller 必须拉整个文件

`api/` 目录下已有 9 个 sibling 模块（budgets/connectivity/core/cvg/decisions/health/studio/workflows/creator），**`creator.js` 是个明显 outlier**——其他 8 个都是单一职责（如 `cvg.js` 只做 Cross-Volume Graph）。

## 2. 目标 & 非目标

### 目标
1. 把 114 funcs 按业务域拆为 8 个 sibling submodule
2. `api/creator.js` 保留为 thin shell re-export（10L 以内），保持向后兼容
3. 每个 submodule 独立测试（5-15 tests/spec）
4. `api/creator.js` ≤ 50L 架构守卫
5. vue-tsc 0 errors + 全测 PASS

### 非目标
- 不重构 `api/index.js` 整体结构
- 不改 `useCreatorSettings.js` 现有 3 子模块
- 不引入新依赖（不用 fetch-mock / msw / nock）
- 不优化 HTTP 调用本身（沿用 `request` from `core.js`）
- 不改 caller 路径（thin facade 保留原 import path）

## 3. 文件结构

### 3.1 终态

```
apps/dashboard/src/api/
├── creator.js               ← 686L → 10L thin shell re-export
├── agent.js                 ← 新建 ~80L（5 funcs）
├── memory.js                ← 新建 ~50L（3 funcs）
├── volumePlan.js            ← 新建 ~120L（7 funcs）
├── volumeTemplate.js        ← 新建 ~240L（15 funcs）
├── onboarding.js            ← 新建 ~280L（19 funcs）
├── templateApproval.js      ← 新建 ~240L（16 funcs）
├── publish.js               ← 新建 ~150L（10 funcs）
└── mergePreset.js           ← 新建 ~480L（39 funcs）
```

合计 8 submodules + 1 facade = 114 funcs 全部迁移。

### 3.2 测试目录

```
apps/dashboard/tests/unit/
├── api-creator-agent.spec.ts              ← 新建 ~80L（5-8 tests）
├── api-creator-memory.spec.ts             ← 新建 ~50L（3-5 tests）
├── api-creator-volume-plan.spec.ts        ← 新建 ~120L（8-12 tests）
├── api-creator-volume-template.spec.ts    ← 新建 ~180L（12-15 tests）
├── api-creator-onboarding.spec.ts         ← 新建 ~180L（12-15 tests）
├── api-creator-template-approval.spec.ts  ← 新建 ~80L（5-8 tests）
├── api-creator-publish.spec.ts            ← 新建 ~120L（8-12 tests）
├── api-creator-settings-docs.spec.ts      ← 新建 ~150L（10-15 tests）
└── guards/architecture-guards.spec.ts     ← 扩展 1 守卫
```

测试总数预估：1343 → 1430~1480（8 submodules × ~10 tests）

## 4. Submodule 职责拆分

按 114 funcs 的业务域切分：

| Submodule | funcs | 包含 |
|-----------|-------|------|
| `agent.js` | 5 | runCreatorAgentPlan, runCreatorAgentPlanStream, runCreatorLogicCheck, updateCreatorCreationMode, fetchCreatorOverview |
| `memory.js` | 3 | fetchCreatorMemoryAssets, saveCreatorMemoryAnnotation, queryCreatorMemory |
| `volumePlan.js` | 7 | fetchCreatorVolumePlan, saveCreatorVolumePlan, previewCreatorVolumePlanDiff, mergeCreatorVolumePlan, splitCreatorVolumePlan, fetchCreatorBatchHistory, exportCreatorBatchHistory |
| `volumeTemplate.js` | 15 | VolumeTemplate CRUD (7) + Factory (4) + Sync + 导出 + Changelog + Version |
| `onboarding.js` | 19 | Onboarding + Digest + Email + Webhook + Notifications + Share + Notes + DeadLetter |
| `templateApproval.js` | 16 | Approvals + Batch + Reject + Transfer + Submit + Chain + Audit + SLA + Overdue + Snapshot Diff/Drift |
| `publish.js` | 10 | Publish + PublishHistory + PublishPlatforms + ExportEpub + ExportDocx + ChapterPreview + ChapterBody + ChapterOutline |
| `mergePreset.js` | 39 | MergePreset CRUD + Factory + Conflicts + Fixes + Graph + Toposort + Import/Export + Preflight + Diff + SettingsDocs + DiffCollabNotes + Wizard + Preferences + Models |

**总计 5+3+7+15+19+16+10+39 = 114 funcs**。最重 `mergePreset.js` 39 funcs（含 settingsDocs / diffCollab / wizard / preferences / models，因为它构成「合并预设 + 设定一致性」完整域），最轻 `memory.js` 3 funcs。

## 5. Submodule 结构

每个 submodule 模板（与 `api/creator.js` 现有风格一致）：

```js
/**
 * <Domain> API
 */

import { request } from './core.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorXxx() {
  return request('/creator/xxx');
}

export async function saveCreatorXxx(body) {
  return request('/creator/xxx', { method: 'POST', body });
}
```

## 6. thin facade 结构

`api/creator.js` 终态：

```js
/**
 * Creator API (thin shell re-export from 8 sibling submodules)
 *
 * Phase 62: 114 funcs 拆为 8 domain submodules。本文件保留为 backward-compat
 * facade。下游 caller 仍可 `import { fetchCreatorXxx } from '.../api/creator.js'`。
 */

export * from './agent.js';
export * from './memory.js';
export * from './volumePlan.js';
export * from './volumeTemplate.js';
export * from './onboarding.js';
export * from './templateApproval.js';
export * from './publish.js';
export * from './settingsDocs.js';
```

约 10L（仅引言 + 8 行 re-export）。

## 7. 迁移策略

8 commits + 1 architecture guard commit = **9 commits**。

### 7.1 每个 commit 内部 4 步（自包含）

1. **新建** `apps/dashboard/src/api/<submodule>.js`，含 N 个 funcs
2. **新建测试** `apps/dashboard/tests/unit/api-creator-<submodule>.spec.ts`，5-15 个 mock fetch tests
3. **改 `api/creator.js`** 删原 N 个 funcs + 改 re-export from submodule
4. **验证** `vue-tsc` + 跑新 spec + 跑全测 → 1 commit

### 7.2 Commit 顺序（按 funcs 数从少到多，逐步热身）

按 funcs 数 升序，diff 风险最小：

| Commit | Submodule | funcs | 难度 |
|--------|-----------|-------|------|
| 62.1 | `memory.js` | 3 | 极低（最简） |
| 62.2 | `agent.js` | 5 | 低 |
| 62.3 | `volumePlan.js` | 7 | 中 |
| 62.4 | `publish.js` | 10 | 中 |
| 62.5 | `volumeTemplate.js` | 15 | 中（CRUD + factory + sync） |
| 62.6 | `templateApproval.js` | 16 | 中（chain + audit + sla） |
| 62.7 | `onboarding.js` | 19 | 高（最多 funcs） |
| 62.8 | `mergePreset.js` | 39 | 高（含 settingsDocs + diffCollab + wizard + preferences + models） |
| 62.9 | `chore(guards)`: api/creator.js ≤ 50L | +1 guard | 低 |

或者可合并 62.1-62.8 为 8 commits 或 4 commits（按 Stage 拆），但 9 commits 与 Phase 60 模式一致，便于 review。

### 7.3 单 commit 内部 diff 模式

每个 commit 内 **api/creator.js** 的 diff 类似：

```diff
- export async function fetchCreatorOverview() {
-   return request('/creator/overview');
- }
- export async function updateCreatorCreationMode(mode) {
-   return request('/creator/overview/mode', {
-     method: 'PUT',
-     body: { mode },
-   });
- }
+ export * from './agent.js';
```

never positive/negative 双 diff（function 定义先从 creator.js 删，新 submodule 加完后再确认无重复声明）。

## 8. 测试策略

### 8.1 沿用现有 mock pattern

`apps/dashboard/src/api/core.js` 导出 `request` 函数。沿用 22 个既有 spec 的 `vi.mock('../../src/api/index.js', ...)` 模式：

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchCreatorAgentPlan } from '../../src/api/agent.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/agent', () => {
  it('runCreatorAgentPlan POSTs to /creator/agent/plan', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await runCreatorAgentPlan({ chapter: 1 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/agent/plan', {
      method: 'POST',
      body: { chapter: 1 },
    });
  });
  // ... 其他 4-7 tests
});
```

### 8.2 每个 submodule 5-15 tests

- **URL path 正确**：每个 func 至少 1 test
- **method 正确**：GET/POST/PUT/DELETE 区分
- **body 序列化**：POST body 透传
- **query string**：带 query 的 func（`?chapter=X`）
- **error propagation**：mock reject → expect throw

### 8.3 沿用既有 helpers

`apps/dashboard/tests/helpers/strict-test-types.js` 已存在；按需使用。

## 9. 架构守卫

`apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` 追加 1 项：

```ts
// Phase 62: api/creator.js must stay a thin shell re-export
it('api/creator.js 保持 ≤ 50 行 (Phase 62)', () => {
  const apiDir = path.resolve(__dirname, '../../../src/api');
  const file = path.join(apiDir, 'creator.js');
  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n').length;
  expect(lines).toBeLessThanOrEqual(50);
});
```

与 Phase 60.6 `useCreatorWriteWorkbench.js ≤ 200L` 守卫同模式。

## 10. 验证清单

| 检查 | 期望 |
|------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | 1343 → ~1430 tests PASS（每 submodule +5-15 tests） |
| `pnpm exec vitest run tests/unit/guards/` | 12 → 13 tests PASS（新增 api/creator.js 守卫） |
| `wc -l apps/dashboard/src/api/creator.js` | ≤ 50L |
| `git log --oneline -10` | 8 个 refactor commits + 1 chore commit = 9 commits |

## 11. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| dynamic import / namespace import 漏 caller | 低 | 拆完 import 报错 | grep `from.*api/creator\|import.*api/creator` 完整扫描 |
| `vi.mock` path 错（应为 `core.js` 非 `index.js`） | 中 | 测试失败 | 8 submodules 测试都 mock `core.js`（与 caller 测试一致） |
| 114 funcs 中 URL 字符串 typo | 低 | HTTP 路径错 | 直接从 `creator.js` 复制 URL 字符串 |
| 单 commit 太大 | 中 | review 困难 | 8 submodules 各自 1 commit，按 funcs 数升序 |
| `api/index.js` 已有 import from `creator.js` | 中 | facade 重新导出 | 验证 `api/index.js` import 仍工作 |

## 12. 后续 Phase 63+ 候选

- `useNavStore.js` (497L) 拆分：25+ URL helper 抽出
- Doc cleanup pass（字段数 51/56/55→59 + trailing newline 全修）
- E2E Playwright 集成测试
- Performance 优化

## 13. 收官报告

实施完成后写 `docs/superpowers/specs/2026-08-20-phase62-final-state.md`：
- 累积指标（行数变化、测试数、commit 数）
- 8 submodules 各自 funcs 数
- 验证结果
- 后续 Phase 63+ 候选
