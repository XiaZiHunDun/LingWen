# Phase 62 — `api/creator.js` 拆分实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `apps/dashboard/src/api/creator.js` (686L, 114 funcs) 拆为 8 个 sibling submodule + thin facade re-export + 8 个 submodule 独立测试 + 1 architecture guard；9 commits；vue-tsc 0 errors；pnpm test 1343 → ~1430 tests PASS。

**Architecture:** 沿用 Phase 60 facade 模式 + Phase 61 守卫模式。`api/creator.js` 终态为 10L thin shell re-export 8 个 sibling submodule（与 `api/budgets.js`/`api/cvg.js` 等 sibling 同级）。每个 submodule 沿用 `import { request } from './core.js'` 现有 HTTP 模式。测试沿用 `vi.mock('../../src/api/core.js', ...)` 已有 pattern（22 个既有用例）。

**Tech Stack:** Vue 3 + TypeScript + Vitest + vi.mock。零新依赖。

**Spec:** `docs/superpowers/specs/2026-08-20-phase62-api-creator-split-design.md`

---

## 文件结构（终态）

```
apps/dashboard/src/api/
├── creator.js               ← 686L → 10L thin shell re-export
├── agent.js                 ← 新建（5 funcs）
├── memory.js                ← 新建（3 funcs）
├── volumePlan.js            ← 新建（7 funcs）
├── volumeTemplate.js        ← 新建（15 funcs）
├── onboarding.js            ← 新建（19 funcs）
├── templateApproval.js      ← 新建（16 funcs）
├── publish.js               ← 新建（10 funcs）
└── mergePreset.js           ← 新建（39 funcs）

apps/dashboard/tests/unit/
├── api-creator-agent.spec.ts
├── api-creator-memory.spec.ts
├── api-creator-volume-plan.spec.ts
├── api-creator-volume-template.spec.ts
├── api-creator-onboarding.spec.ts
├── api-creator-template-approval.spec.ts
├── api-creator-publish.spec.ts
├── api-creator-merge-preset.spec.ts
└── guards/architecture-guards.spec.ts   ← 扩展 1 守卫
```

---

## 通用模板：每个 submodule 4 步模式

每个 task 内部一致 4 步：

1. **新建** `apps/dashboard/src/api/<submodule>.js` 含 N 个 funcs（复制 URL 字符串 from `creator.js`）
2. **新建** `apps/dashboard/tests/unit/api-creator-<submodule>.spec.ts`，N 个 mock fetch tests
3. **改 `api/creator.js`** 删原 N 个 funcs + 加 `export * from './<submodule>.js';`
4. **验证** + **commit**

**Submodule 文件模板**（与 `api/creator.js` 现有风格一致）：

```js
/**
 * <Domain> API
 *
 * Phase 62: 从 api/creator.js 拆出。
 */

import { request } from './core.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorXxx() {
  return request('/creator/xxx');
}

// ... 其他 funcs
```

**测试模板**（沿用 `tests/unit/use-creator-volume-plan.spec.ts` 模式）：

```ts
/**
 * api/<submodule> 独立测试（Phase 62.<N>）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorXxx,
  saveCreatorXxx,
  // ... import 全部 funcs
} from '../../src/api/<submodule>.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/<submodule>', () => {
  it('fetchCreatorXxx GETs /creator/xxx', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await fetchCreatorXxx();
    expect(mocks.request).toHaveBeenCalledWith('/creator/xxx');
  });

  it('saveCreatorXxx POSTs to /creator/xxx', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorXxx({ data: 1 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/xxx', {
      method: 'POST',
      body: { data: 1 },
    });
  });

  // ... 每个 func 1 个 test
});
```

**Facade 修改模板**：

```diff
- export async function fetchCreatorXxx() {
-   return request('/creator/xxx');
- }
- export async function saveCreatorXxx(body) {
-   return request('/creator/xxx', { method: 'POST', body });
- }
+ export * from './<submodule>.js';
```

---

## Task 1: 拆 `api/memory.js`（3 funcs，极简热身）

**Files:**
- Create: `apps/dashboard/src/api/memory.js`
- Create: `apps/dashboard/tests/unit/api-creator-memory.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (3):
- `fetchCreatorMemoryAssets`
- `saveCreatorMemoryAnnotation(assetId, body)`
- `queryCreatorMemory(body)`

- [ ] **Step 1.1: 读取 `creator.js` 中 3 个 funcs 的 URL 字符串**

```bash
cd apps/dashboard/src/api
grep -A3 "^export async function \(fetchCreatorMemoryAssets\|saveCreatorMemoryAnnotation\|queryCreatorMemory\)" creator.js
```

记录 3 个 funcs 的 URL + method + body。

- [ ] **Step 1.2: 创建 `apps/dashboard/src/api/memory.js`**

```js
/**
 * Memory API
 *
 * Phase 62 Task 1: 从 api/creator.js 拆出。
 */

import { request } from './core.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorMemoryAssets() {
  return request('/creator/memory/assets');
}

export async function saveCreatorMemoryAnnotation(assetId, body) {
  return request(`/creator/memory/assets/${assetId}/annotate`, {
    method: 'POST',
    body,
  });
}

export async function queryCreatorMemory(body) {
  return request('/creator/memory/query', {
    method: 'POST',
    body,
  });
}
```

- [ ] **Step 1.3: 创建 `apps/dashboard/tests/unit/api-creator-memory.spec.ts`**

```ts
/**
 * api/memory 独立测试（Phase 62.1）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation,
  queryCreatorMemory,
} from '../../src/api/memory.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/memory', () => {
  it('fetchCreatorMemoryAssets GETs /creator/memory/assets', async () => {
    mocks.request.mockResolvedValueOnce({ assets: [] });
    await fetchCreatorMemoryAssets();
    expect(mocks.request).toHaveBeenCalledWith('/creator/memory/assets');
  });

  it('saveCreatorMemoryAnnotation POSTs with assetId', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorMemoryAnnotation('asset-1', { note: 'hello' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/memory/assets/asset-1/annotate', {
      method: 'POST',
      body: { note: 'hello' },
    });
  });

  it('queryCreatorMemory POSTs query body', async () => {
    mocks.request.mockResolvedValueOnce({ results: [] });
    await queryCreatorMemory({ query: 'foo' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/memory/query', {
      method: 'POST',
      body: { query: 'foo' },
    });
  });
});
```

- [ ] **Step 1.4: 改 `api/creator.js` 删原 3 funcs + 加 re-export**

```bash
# Remove the 3 function definitions
# Add at top of file: export * from './memory.js';
```

- [ ] **Step 1.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-memory.spec.ts 2>&1 | tail -10
```

Expected: vue-tsc 0 errors; vitest 3 tests pass.

- [ ] **Step 1.6: Commit**

```bash
git add apps/dashboard/src/api/memory.js \
        apps/dashboard/src/api/creator.js \
        apps/dashboard/tests/unit/api-creator-memory.spec.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract memory submodule (Phase 62.1)" \
    -m "3 funcs: fetchCreatorMemoryAssets, saveCreatorMemoryAnnotation, queryCreatorMemory → api/memory.js; api/creator.js 改 re-export；新建 3 个 spec tests。"
```

---

## Task 2: 拆 `api/agent.js`（5 funcs）

**Files:**
- Create: `apps/dashboard/src/api/agent.js`
- Create: `apps/dashboard/tests/unit/api-creator-agent.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (5):
- `fetchCreatorOverview`
- `updateCreatorCreationMode(mode)`
- `runCreatorLogicCheck({ chapter } = {})`
- `runCreatorAgentPlan(body)`
- `runCreatorAgentPlanStream(body, onEvent)`

- [ ] **Step 2.1: 读 URL**

```bash
grep -A6 "^export async function \(fetchCreatorOverview\|updateCreatorCreationMode\|runCreatorLogicCheck\|runCreatorAgentPlan\|runCreatorAgentPlanStream\)" apps/dashboard/src/api/creator.js
```

- [ ] **Step 2.2: 创建 `api/agent.js`**

5 funcs 模板（沿用 Task 1 pattern）：

```js
/**
 * Agent API
 *
 * Phase 62 Task 2: 从 api/creator.js 拆出。
 */

import { request } from './core.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

export async function fetchCreatorOverview() {
  return request('/creator/overview');
}

export async function updateCreatorCreationMode(mode) {
  return request('/creator/overview/mode', {
    method: 'PUT',
    body: { mode },
  });
}

export async function runCreatorLogicCheck({ chapter } = {}) {
  const query = chapter != null ? `?chapter=${chapter}` : '';
  return request(`/creator/logic-check${query}`, { method: 'POST' });
}

export async function runCreatorAgentPlan(body) {
  return request('/creator/agent/plan', {
    method: 'POST',
    body,
  });
}

export async function runCreatorAgentPlanStream(body, onEvent) {
  return request('/creator/agent/plan/stream', {
    method: 'POST',
    body,
    onEvent,
  });
}
```

**注意**：`runCreatorAgentPlanStream` 实际 URL + onEvent 透传以 `creator.js` 原代码为准。

- [ ] **Step 2.3: 创建 `api-creator-agent.spec.ts`**

5 tests: fetchCreatorOverview, updateCreatorCreationMode (PUT), runCreatorLogicCheck (with/without chapter query), runCreatorAgentPlan (POST body), runCreatorAgentPlanStream (POST + onEvent callback)。

- [ ] **Step 2.4: 改 `api/creator.js` 删 5 funcs + 加 re-export**

- [ ] **Step 2.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-agent.spec.ts 2>&1 | tail -10
```

Expected: 5 tests pass.

- [ ] **Step 2.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract agent submodule (Phase 62.2)" \
    -m "5 funcs: fetchCreatorOverview, updateCreatorCreationMode, runCreatorLogicCheck, runCreatorAgentPlan, runCreatorAgentPlanStream → api/agent.js。"
```

---

## Task 3: 拆 `api/volumePlan.js`（7 funcs）

**Files:**
- Create: `apps/dashboard/src/api/volumePlan.js`
- Create: `apps/dashboard/tests/unit/api-creator-volume-plan.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (7):
- `fetchCreatorVolumePlan`
- `saveCreatorVolumePlan(volumes, expectedRevision)`
- `previewCreatorVolumePlanDiff(volumes)`
- `mergeCreatorVolumePlan(body)`
- `splitCreatorVolumePlan(body)`
- `fetchCreatorBatchHistory`
- `exportCreatorBatchHistory`

- [ ] **Step 3.1: 读 URL**

```bash
grep -A4 "^export async function \(fetchCreatorVolumePlan\|saveCreatorVolumePlan\|previewCreatorVolumePlanDiff\|mergeCreatorVolumePlan\|splitCreatorVolumePlan\|fetchCreatorBatchHistory\|exportCreatorBatchHistory\)" apps/dashboard/src/api/creator.js
```

- [ ] **Step 3.2: 创建 `api/volumePlan.js`**

7 funcs 模板，沿用 Task 1 pattern（`saveCreatorVolumePlan` 接受 volumes + expectedRevision，传 `body: { volumes, expected_revision: expectedRevision }` — 实际以 creator.js 原代码为准）。

- [ ] **Step 3.3: 创建 `api-creator-volume-plan.spec.ts`**

7 tests，覆盖每个 func 的 URL + method + body 形状。

- [ ] **Step 3.4: 改 `api/creator.js`**

- [ ] **Step 3.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-volume-plan.spec.ts 2>&1 | tail -10
```

Expected: 7 tests pass.

- [ ] **Step 3.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract volumePlan submodule (Phase 62.3)" \
    -m "7 funcs: volumePlan CRUD + diff/merge/split + batchHistory → api/volumePlan.js。"
```

---

## Task 4: 拆 `api/publish.js`（10 funcs）

**Files:**
- Create: `apps/dashboard/src/api/publish.js`
- Create: `apps/dashboard/tests/unit/api-creator-publish.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (10):
- `fetchCreatorChapterPreview(chapterNum, { full = false } = {})`
- `saveCreatorChapterBody`
- `saveCreatorChapterOutline`
- `submitCreatorPublish(body)`
- `fetchCreatorPublishHistory(limit = 10)`
- `fetchCreatorPublishPlatforms`
- `exportCreatorEpub(body)`
- `exportCreatorDocx(body)`
- `generateCreatorVolumeSummary`（建议归 publish 或 volumePlan，由 implementer 决定）

- [ ] **Step 4.1: 读 URL**

- [ ] **Step 4.2: 创建 `api/publish.js`**

10 funcs 模板。

- [ ] **Step 4.3: 创建 `api-creator-publish.spec.ts`**

10 tests（含 `fetchCreatorChapterPreview` 的 `?full=X` query 参数测试）。

- [ ] **Step 4.4: 改 `api/creator.js`**

- [ ] **Step 4.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-publish.spec.ts 2>&1 | tail -10
```

Expected: 10 tests pass.

- [ ] **Step 4.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract publish submodule (Phase 62.4)" \
    -m "10 funcs: publish + publishHistory + publishPlatforms + exportEpub + exportDocx + chapterPreview + chapterBody + chapterOutline → api/publish.js。"
```

---

## Task 5: 拆 `api/volumeTemplate.js`（15 funcs）

**Files:**
- Create: `apps/dashboard/src/api/volumeTemplate.js`
- Create: `apps/dashboard/tests/unit/api-creator-volume-template.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (15):
- `fetchCreatorVolumeTemplates`
- `saveCreatorVolumeTemplate(body)`
- `deleteCreatorVolumeTemplate(templateId)`
- `renameCreatorVolumeTemplate(templateId, body)`
- `setCreatorVolumeTemplateVersion(templateId, body)`
- `fetchCreatorVolumeTemplateChangelog(templateId)`
- `rollbackCreatorVolumeTemplate(templateId, body)`
- `importCreatorVolumeTemplates(body)`
- `exportCreatorVolumeTemplates`
- `fetchCreatorVolumeTemplateSyncSources`
- `syncCreatorVolumeTemplates(body)`
- `fetchCreatorFactoryVolumeTemplates`
- `publishCreatorVolumeTemplateToFactory(body)`
- `pullCreatorFactoryVolumeTemplates(body)`
- `deleteCreatorFactoryVolumeTemplate(templateId)`

- [ ] **Step 5.1: 读 URL**

- [ ] **Step 5.2: 创建 `api/volumeTemplate.js`**

15 funcs 模板（URL + method + body 全部按 creator.js 原代码）。

- [ ] **Step 5.3: 创建 `api-creator-volume-template.spec.ts`**

15 tests，重点覆盖 path param（templateId 在 URL 中插值）+ factory endpoint domain。

- [ ] **Step 5.4: 改 `api/creator.js`**

- [ ] **Step 5.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-volume-template.spec.ts 2>&1 | tail -10
```

Expected: 15 tests pass.

- [ ] **Step 5.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract volumeTemplate submodule (Phase 62.5)" \
    -m "15 funcs: volumeTemplate CRUD + factory + sync + publish + changelog + version → api/volumeTemplate.js。"
```

---

## Task 6: 拆 `api/templateApproval.js`（16 funcs）

**Files:**
- Create: `apps/dashboard/src/api/templateApproval.js`
- Create: `apps/dashboard/tests/unit/api-creator-template-approval.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (16):
- `fetchCreatorTemplateApprovals(params = {})`
- `approveCreatorTemplateApproval(approvalId, body = {})`
- `batchApproveCreatorTemplateApprovals`
- `batchRejectCreatorTemplateApprovals`
- `rejectCreatorTemplateApproval`
- `transferCreatorTemplateApproval`
- `submitCreatorTemplateVersionApproval(templateId, body)`
- `fetchCreatorTemplateApprovalHistory(limit = 20)`
- `fetchCreatorTemplateApprovalAudit`
- `fetchCreatorTemplateApprovalSlaConfig`
- `saveCreatorTemplateApprovalSlaConfig`
- `fetchCreatorTemplateApprovalChainConfig`
- `saveCreatorTemplateApprovalChainConfig`
- `fetchCreatorTemplateApprovalOverdue`
- `fetchCreatorTemplateApprovalSnapshotDiff`
- `fetchCreatorTemplateApprovalSnapshotDrift`

- [ ] **Step 6.1: 读 URL**

- [ ] **Step 6.2: 创建 `api/templateApproval.js`**

16 funcs（含 `params` query string 处理）。

- [ ] **Step 6.3: 创建 `api-creator-template-approval.spec.ts`**

16 tests，重点：
- `fetchCreatorTemplateApprovals` 的 `params` → query string 序列化
- `approveCreatorTemplateApproval` 的 approvalId 路径插值
- `batchApprove` / `batchReject` 的 body shape

- [ ] **Step 6.4: 改 `api/creator.js`**

- [ ] **Step 6.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-template-approval.spec.ts 2>&1 | tail -10
```

Expected: 16 tests pass.

- [ ] **Step 6.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract templateApproval submodule (Phase 62.6)" \
    -m "16 funcs: approvals + batch + reject + transfer + submit + chain + audit + sla + overdue + snapshot diff/drift → api/templateApproval.js。"
```

---

## Task 7: 拆 `api/onboarding.js`（19 funcs）

**Files:**
- Create: `apps/dashboard/src/api/onboarding.js`
- Create: `apps/dashboard/tests/unit/api-creator-onboarding.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (19):
- `fetchCreatorOnboarding`
- `saveCreatorOnboardingProgress`
- `applyCreatorOnboardingShare`
- `saveCreatorOnboardingNotes`
- `fetchCreatorOnboardingNotifications(handle)`
- `ackCreatorOnboardingNotifications(body)`
- `fetchCreatorOnboardingWebhook`
- `saveCreatorOnboardingWebhook(body)`
- `fetchCreatorOnboardingEmail`
- `saveCreatorOnboardingEmail(body)`
- `fetchCreatorOnboardingNotificationDigest(handle)`
- `fetchCreatorOnboardingDigestSchedule`
- `saveCreatorOnboardingDigestSchedule(body)`
- `dispatchCreatorOnboardingDigest(force = false)`
- `fetchCreatorOnboardingDigestRetryQueue`
- `fetchCreatorOnboardingDigestStats`
- `processCreatorOnboardingDigestRetries`
- `fetchCreatorOnboardingDigestDeadLetter`
- `replayCreatorOnboardingDigestDeadLetter(body)`

- [ ] **Step 7.1: 读 URL**

- [ ] **Step 7.2: 创建 `api/onboarding.js`**

19 funcs 模板（含 `handle` 路径插值 + `force` query 参数）。

- [ ] **Step 7.3: 创建 `api-creator-onboarding.spec.ts`**

19 tests。

- [ ] **Step 7.4: 改 `api/creator.js`**

- [ ] **Step 7.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-onboarding.spec.ts 2>&1 | tail -10
```

Expected: 19 tests pass.

- [ ] **Step 7.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract onboarding submodule (Phase 62.7)" \
    -m "19 funcs: onboarding + digest + email + webhook + notifications + share + notes + deadLetter → api/onboarding.js。"
```

---

## Task 8: 拆 `api/mergePreset.js`（39 funcs，最重，含 settingsDocs/diffCollab/wizard/preferences/models）

**Files:**
- Create: `apps/dashboard/src/api/mergePreset.js`
- Create: `apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`

**Funcs to migrate** (39):
- **MergePreset 主域** (25): fetchCreatorMergePreferences, exportCreatorMergePreferences, importCreatorMergePreferences, fetchCreatorGlobalMergePreferences, fetchCreatorMergePresetPackages, exportCreatorMergePresetPackages, importCreatorMergePresetPackages, fetchCreatorFactoryMergePresetPackages, deleteCreatorFactoryMergePresetPackage, pullCreatorFactoryMergePresetPackages, publishCreatorMergePresetToFactory, preflightCreatorFactoryMergePresetPull, fetchCreatorFactoryMergePresetConflicts, resolveCreatorFactoryMergePresetConflict, preflightCreatorMergePresetImport, previewCreatorMergePresetImportDiff, fetchCreatorMergePresetChangelog, fetchCreatorMergePresetChangelogDiff, fetchCreatorMergePresetConflicts, fetchCreatorMergePresetConflictFixes, applyCreatorMergePresetConflictFix, applyAllCreatorMergePresetConflictFixes, fetchCreatorMergePresetGraph, fetchCreatorMergePresetToposort, applyCreatorMergePresetToposort
- **SettingsDocs** (7): fetchCreatorSettingsDocs, saveCreatorSettingsDocs(body), previewCreatorSettingsDocs, previewCreatorSettingsThreeWay, previewCreatorSettingsMerge, fetchCreatorSettingsHistory, restoreCreatorSettingsSnapshot
- **DiffCollab** (2): fetchCreatorDiffCollabNotes, saveCreatorDiffCollabNotes
- **Wizard** (2): dismissCreatorWizardPanel, saveCreatorWizardPanelCollapsed
- **Preferences** (3): fetchCreatorPreferences, saveCreatorPreferencesApi, fetchCreatorModels

- [ ] **Step 8.1: 读 URL**

```bash
grep -A4 "^export async function" apps/dashboard/src/api/creator.js | grep -B1 -A3 "MergePreset\|SettingsDocs\|DiffCollab\|WizardPanel\|Preferences\|Models" | head -200
```

如不便用 grep，可逐个读取 39 funcs 的完整 URL。

- [ ] **Step 8.2: 创建 `api/mergePreset.js`**

39 funcs 模板。**submodule 内部可按子域加 section 注释**（MergePreset / SettingsDocs / DiffCollab / Wizard / Preferences）便于阅读。

```js
/**
 * MergePreset + Settings + Wizard + Preferences API
 *
 * Phase 62 Task 8: 从 api/creator.js 拆出 39 funcs（合并预设 + 设定一致性完整域）。
 *
 * 子域：
 * - MergePreset (25): CRUD + Factory + Conflicts + Fixes + Graph + Toposort
 * - SettingsDocs (7): 文档编辑 + 3-way diff + 保存
 * - DiffCollab (2): 协作备注
 * - Wizard (2): 引导面板
 * - Preferences (3): 偏好 + 模型
 */

import { request } from './core.js';

const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

// --- MergePreset ---
export async function fetchCreatorMergePreferences() {
  return request('/creator/merge-presets/preferences');
}

// ... 25 funcs

// --- SettingsDocs ---
export async function fetchCreatorSettingsDocs() {
  return request('/creator/settings/docs');
}

// ... 7 funcs

// ...等等
```

- [ ] **Step 8.3: 创建 `api-creator-merge-preset.spec.ts`**

39 tests。可按子域分 5 个 `describe` block（MergePreset / SettingsDocs / DiffCollab / Wizard / Preferences）便于阅读。

- [ ] **Step 8.4: 改 `api/creator.js` 删 39 funcs + 加 re-export**

- [ ] **Step 8.5: 验证**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vitest run tests/unit/api-creator-merge-preset.spec.ts 2>&1 | tail -10
```

Expected: 39 tests pass.

- [ ] **Step 8.6: Commit**

```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): extract mergePreset submodule (Phase 62.8)" \
    -m "39 funcs: mergePreset + settingsDocs + diffCollab + wizard + preferences + models → api/mergePreset.js。"
```

---

## Task 9: 架构守卫 + 终验

**Files:**
- Modify: `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts`
- Modify: `apps/dashboard/src/api/creator.js`（删除原 114 funcs 全部，保留 thin shell）

- [ ] **Step 9.1: 确认 `api/creator.js` 终态**

```bash
wc -l apps/dashboard/src/api/creator.js
cat apps/dashboard/src/api/creator.js
```

Expected: ~10L，含 8 行 `export * from './Xxx.js';` + 注释。

如果仍有 funcs 残留（Task 8 漏迁），fix-up 删完后 commit。

- [ ] **Step 9.2: 添加 1 项架构守卫**

文件 `apps/dashboard/tests/unit/guards/architecture-guards.spec.ts` 在 Phase 61 守卫后追加：

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

- [ ] **Step 9.3: 验证终态**

```bash
cd apps/dashboard
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5
pnpm exec vue-tsc -p tsconfig.app.json --noEmit 2>&1 | tail -5
pnpm test 2>&1 | tail -10
pnpm exec vitest run tests/unit/guards/ 2>&1 | tail -10
grep -rn "fetchCreator\|saveCreator\|updateCreator\|approveCreator\|rejectCreator\|runCreator\|mergeCreator\|splitCreator\|publishCreator\|pullCreator\|ackCreator\|rollbackCreator\|syncCreator\|previewCreator\|setCreator\|dispatchCreator\|exportCreator\|submitCreator\|processCreator\|applyCreator\|deleteCreator\|renameCreator\|generateCreator\|dismissCreator\|restoreCreator\|batchCreator\|resolveCreator\|replayCreator\|transferCreator\|importCreator\|preflightCreator\|queryCreator" apps/dashboard/src/api/creator.js 2>/dev/null
```

Expected：
- vue-tsc 0 errors（双 config）
- pnpm test：原 1343 + 新 8 submodules tests ≈ 1350 tests PASS
- vitest run guards：12 → 13 tests PASS
- grep 最后命令：0 hits（creator.js 已是 thin shell）

- [ ] **Step 9.4: 验证 8 submodules 存在**

```bash
ls -la apps/dashboard/src/api/{agent,memory,volumePlan,volumeTemplate,onboarding,templateApproval,publish,mergePreset}.js
```

Expected: 8 files 都存在。

- [ ] **Step 9.5: Commit 守卫**

```bash
git add apps/dashboard/src/api/creator.js \
        apps/dashboard/tests/unit/guards/architecture-guards.spec.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "chore(guards): add api/creator.js thin shell guard (Phase 62.9)" \
    -m "api/creator.js 留守为 10L thin shell re-export 8 submodules。新增 1 架构守卫确保 creator.js ≤ 50L、8 submodules 存在。"
```

- [ ] **Step 9.6: 写收官报告**

新建 `docs/superpowers/specs/2026-08-20-phase62-final-state.md`，模板：

```markdown
# Phase 62 — api/creator.js 拆分收官报告

> **日期**: 2026-08-20
> **范围**: api/creator.js (686L, 114 funcs) → 8 sibling submodules + thin facade
> **基础**: Phase 60 (facade 模式) + Phase 61 (legacy cleanup)

## 累积指标

| 指标 | 值 |
|------|-----|
| api/creator.js 行数 | 686 → 10 (-98.5%) |
| 8 submodules 行数 | 0 → ~1640 (新增) |
| Total LOC | 686 → ~1650 (+960) |
| Submodule funcs | 0 + 114 = 114 |
| Submodule 测试 | 0 + 90+ = 90+ tests |
| 总测试数 | 1343 → ~1430 |
| 架构守卫 | 11 → 12 (+1) |
| vue-tsc 错误 | 0 (both configs) |
| Commits | 9 (8 refactor + 1 chore) |

## 8 Submodules 拆分

| Submodule | funcs | tests | LOC |
|-----------|-------|-------|-----|
| memory.js | 3 | 3 | ~50 |
| agent.js | 5 | 5 | ~80 |
| volumePlan.js | 7 | 7 | ~120 |
| publish.js | 10 | 10 | ~150 |
| volumeTemplate.js | 15 | 15 | ~240 |
| templateApproval.js | 16 | 16 | ~240 |
| onboarding.js | 19 | 19 | ~280 |
| mergePreset.js | 39 | 39 | ~480 |
| **合计** | **114** | **114** | **~1640** |

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `pnpm exec vue-tsc --noEmit` | 0 errors |
| `pnpm exec vue-tsc -p tsconfig.app.json` | 0 errors |
| `pnpm test` | ~1430 tests PASS |
| `pnpm exec vitest run tests/unit/guards/` | 13 tests PASS |
| `wc -l apps/dashboard/src/api/creator.js` | ≤ 50L |
| `grep -r fetchCreatorXxx apps/dashboard/src/api/creator.js` | 0 hits |

## 架构守卫（新增 1 项）

- `api/creator.js 保持 ≤ 50 行 (Phase 62)`：确保 creator.js 永远是 thin shell

## 后续 Phase 63+ 候选

- `useNavStore.js` (497L) 拆分
- Doc cleanup pass（字段数 51/56/55→59 + trailing newline 全修）
- E2E Playwright 集成测试
- Performance 优化
```

- [ ] **Step 9.7: 推送**

```bash
git log --oneline -10
```

Expected: 9 个新 commit 显示。Phase 60 模式直接 commit 到 master，不开 PR。

---

## 自检清单

执行前请确认：

- [ ] 工作目录干净（`git status` 无未追踪改动，**除了本 plan 自身的修改**）
- [ ] 在 `LingWen/` 仓库根目录
- [ ] 当前在 master 分支
- [ ] 上一 commit 是 `ba558858`（Phase 62 spec）或更新

执行中遇任何 verify 步骤失败：**立即停止**回退该步骤调查，不要跳过。
