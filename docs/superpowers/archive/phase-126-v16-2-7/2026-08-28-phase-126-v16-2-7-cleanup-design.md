# Phase 126 v16.2.7 — Cleanup 设计方案

> **状态**: 设计已定,进入 plan
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (母 spec §3.8 final gate)
> - `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-6-memory-handoff.md` (carryover list §7)
> **前置**: v16.2.6 memory 闭环 (`5d53a8af`)
> **下一步**: v16.3 (import-linter enforcement,DP-01..06)

---

## 0. TL;DR

**v16.2.7 = Phase 126 final cleanup,creator 6-subdomain 拆分收尾。**

| Task | 范围 | 文件数 | 风险 |
|---|---|---|---|
| **T1** typed wrapper `/api/` prefix fix | 4 wrappers × 2-3 calls | 4 files + URL contract tests | 低 |
| **T2** onboarding diff-collab-notes 404 fix | 1 endpoint path | 2 files + URL contract test | 低 |
| **T3** 22 vitest debt fix | useCreatorVolumePlan* | 3-4 files | 中 (tests skip vs refactor) |
| **T4** shim deletion (12 commits) | 36 infra/creator_*.py → 0 | ~140 consumer files | 高 (118 import 切) |
| **T5** creator_settings.py DTO dedup | 27 local DTO → re-export | 1 file + 8 callers | 中 (back-compat 必须保持) |
| **T6** 19 content composables refactor | composables barrel → typed wrapper | 11-19 files | 中 (test mock 拆分) |
| **T7** 4 unwired Content DTOs decision | CreatorDashboard* / CreatorUiProfile* | 0-4 files (delete 或 wire) | 低 |

**不在 v16.2.7 范围**(carryover 到 v16.3 / v16.4 / v16.5):
- import-linter DP-01..06 enforcement (v16.3 候选)
- 22 vitest debt 中无法 scope 的部分(如需 redesign,推到独立 phase)

---

## 1. T1: typed wrapper `/api/` prefix fix

### 1.1 现状

`apps/dashboard/src/api/core.js:10`:`const BASE_URL = import.meta.env.VITE_API_BASE || '/api';`

`core.js:217 export async function request(path, opts = {})` → `${BASE_URL}${path}` → 已 prepend `/api/`。

**错误模式**:`request('/api/world/characters')` → fetch `/api/api/world/characters` → 404。

### 1.2 受影响文件

| 文件 | 错误 path | 正确 path |
|---|---|---|
| `apps/dashboard/src/api/world.ts` (2 calls) | `/api/world/characters`, `/api/world/characters/${id}`, `/api/world/factions`, `/api/world/lore`, `/api/world/timeline` (5 total) | `world/...` |
| `apps/dashboard/src/api/workspace.ts` (3 calls) | `/api/write/${chapterId}`, `/api/write/${chapterId}/conflict` (3 total) | `write/...` |
| `apps/dashboard/src/api/quality.ts` (3 calls) | `/api/studio/quality`, `/api/studio/prose-judge`, `/api/studio/prose-diff` (3 total) | `studio/quality`, `studio/prose-judge`, `studio/prose-diff` |

注: `onboarding.ts` 已用 `/creator/onboarding/*` (无 `/api/` prefix),正确,**无需改**。

### 1.3 设计

- 单一 commit,4 个 wrapper file + 4 个 URL contract test file
- 测试断言每个 call 的 `path` argument 是 relative (以 endpoint 名开头,非 `/api/`)
- `request()` 调用方所有 endpoint path 不变 (只是少 `/api/` 前缀)
- 沿用 v16.2.1 §5.1 lesson 4:typed wrapper 不带 `/api/` prefix

---

## 2. T2: onboarding diff-collab-notes 404 fix

### 2.1 现状

**Backend** (`apps/studio_api/routes/creator_onboarding.py:116`):
```python
@router.get("/api/creator/diff-collab-notes", ...)  # 注意:挂在 creator 路由下
```

**Typed wrapper** (`apps/dashboard/src/api/onboarding.ts:103, 110`):
```typescript
const data = await request('/creator/onboarding/diff-collab-notes');  // 错误!
```

→ fetch URL = `/api/creator/onboarding/diff-collab-notes` → 404 (real endpoint is `/api/creator/diff-collab-notes`)

### 2.2 修复

typed wrapper path 改为 `/creator/diff-collab-notes`,与 router mount 匹配。

### 2.3 设计

- 单 commit,1 个 wrapper file 改 + 1 个 URL contract test
- 验证两个方向 (GET + PUT) 都返回正确 path

---

## 3. T3: 22 vitest debt (useCreatorVolumePlan*)

### 3.1 现状

`pnpm vitest run` 失败 22 tests,4 个 file:

```
FAIL tests/unit/use-creator-volume-plan-diff.spec.ts     (4 tests)
FAIL tests/unit/use-creator-volume-plan-merge-split.spec.ts (3 tests)
FAIL tests/unit/use-creator-volume-plan.spec.ts          (12 tests)
FAIL tests/unit/use-volume-plan-diff.spec.ts             (3 tests)
```

### 3.2 根因

v16.2.1 时 refactor `useCreatorVolumePlan{,Diff,MergeSplit}.js` 但**没完成** — 测试 expect 新 typed wrapper 行为,实际代码仍走 barrel `api/creator.js` (旧路径)。

### 3.3 设计 — 二选一

**Option A (推荐)**:跑 spec-aligned TDD
- 重读每个测试失败点 → 确认期望行为 → 改 composable 实现对齐 typed wrapper
- 失败 pattern 显示 composable 没 track 正确的 state (refreshVolumePlanDiffPreview, saveVolumePlan, applyVolumeMerge 等)
- 预计:4 files × 1 commit = 1 commit
- **风险**:可能发现 v16.2.1 漏掉的 bug,需要 v16.2.7 后续 fix

**Option B**:测试 align 当前 behavior
- 改测试 expect 当前 composable 实际行为
- 不修代码,只 snapshot
- **风险**:留下 known-broken tests,后续 phase 需要回过头修

**Option C**:skip 22 tests
- 加 `it.skip()` 标注 "v16.2.7a deferred",加 TODO comment
- **风险**:coverage 下降,不符合 `.lingwen/constraints.yml`

**决定**:走 Option A。每个失败测试先看根因,小修 composable 对齐 typed wrapper 调用。

---

## 4. T4: shim deletion (12 commits per parent spec §3.8)

### 4.1 现状

`ls infra/creator_*.py | wc -l` = 36。每个 shim 当前都是 `from lingwen_creator.X import *` 1-line re-export。

**Consumer reference count** (按使用次数排序,用于选择 deletion 顺序):

| Shim | Refs | Subdomain |
|---|---|---|
| `creator_ui_profile` | 38 | content |
| `creator_merge_preferences` | 20 | settings |
| `creator_volume_templates` | 16 | volume |
| `creator_volume_plan` | 13 | volume |
| `creator_onboarding_digest_schedule` | 10 | onboarding |
| `creator_template_approvals` | 7 | volume |
| `creator_dashboard` | 7 | content |
| `creator_onboarding_progress` | 6 | onboarding |
| `creator_revision` | 4 | (orphan,only used by routes) |
| ... | ... | ... |
| `creator_export_common` | 0 | (orphan) |
| `creator_memory_assets` | 0 | (orphan) |

### 4.2 12 commits per parent spec §3.8

| Commit | 范围 | Files | 操作 |
|---|---|---|---|
| 1 | memory shim ×3 | 3 | rm + consumer import migration |
| 2 | settings shim ×3 | 3 | rm + consumer import migration |
| 3-4 | export shim ×5 (split 4+1) | 5 | rm + consumer import migration |
| 5-6 | volume shim ×6 (split 4+2) | 6 | rm + consumer import migration |
| 7-8 | onboarding shim ×8 (split 4+4) | 8 | rm + consumer import migration |
| 9-12 | content shim ×10 (split 2+4+2+2) | 10 | rm + consumer import migration |

### 4.3 Order rationale

- **Leaf-first**:memory (subdomain 内 0 依赖) → settings (1 依赖 content) → export (依赖 content) → volume (依赖 content + onboarding) → onboarding (依赖 volume) → content (root)
- **Reverse-dependency**:每个 commit 先确保所有上游 shim 仍可 import (作为 fallback)
- **DP-06 ≤4 files per commit**

### 4.4 Consumer import migration pattern

```python
# 旧
from infra.creator_memory_annotations import annotate_memory_asset
# 新
from lingwen_creator.memory.annotations import annotate_memory_asset
```

per v16.2.1 §12.2 intra-package import 规则:
- `from lingwen_creator.X.Y import Z` 优先 (canonical)
- `from lingwen_creator.X import Y as _Y; Z = _Y.Z` 不推荐 (test compat 场景)

---

## 5. T5: creator_settings.py DTO dedup

### 5.1 现状

`apps/studio_api/models/creator_settings.py` 定义 27 个 Pydantic class,**其中 21 个在 `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` 已有同一定义**。

具体清单:

| Local (creator_settings.py) | Shared (creator.py) | 已重复 |
|---|---|---|
| CreatorChapterPreviewResponse | ✓ (line 1833 CreatorDashboardChapterPreview 类似) | 待 verify |
| CreatorChapterBodySaveRequest | ✗ | 没重复 |
| CreatorChapterOutlineSaveRequest | ✗ | 没重复 |
| CreatorVolumeSummaryGenerateRequest | ✓ | 重复 |
| CreatorVolumeSummaryGenerateResponse | ✓ | 重复 |
| CreatorTaskModelsPreferences | ✗ | 没重复 |
| CreatorInterventionRules | ✗ | 没重复 |
| CreatorModelOption | ✗ | 没重复 |
| CreatorModelsResponse | ✓ | 重复 |
| CreatorPreferencesResponse | ✓ | 重复 |
| CreatorPreferencesSaveRequest | ✓ | 重复 |
| CreatorMemoryAssetItem | ✓ | 重复 |
| CreatorMemoryAnnotationRequest | ✓ | 重复 |
| CreatorMemoryAnnotationResponse | ✓ | 重复 |
| CreatorMemoryAssetsResponse | ✓ | 重复 |
| CreatorEpubExportRequest | ✓ | 重复 |
| CreatorDocxExportRequest | ✓ | 重复 |
| CreatorMemoryQueryRequest | ✓ | 重复 |
| CreatorMemoryQueryResult | ✓ | 重复 |
| CreatorMemoryQueryResponse | ✓ | 重复 |
| CreatorPublishRequest | ✓ | 重复 |
| CreatorPublishEntry | ✓ | 重复 |
| CreatorPublishPlatformCapabilities | ✓ | 重复 |
| CreatorPublishPlatform | ✓ | 重复 |
| CreatorPublishPlatformsResponse | ✓ | 重复 |
| CreatorPublishHistoryResponse | ✓ | 重复 |

**预计**:21 个重复可换成 re-export。**6 个独有**(ChapterBodySaveRequest, ChapterOutlineSaveRequest, TaskModelsPreferences, InterventionRules, ModelOption, CreatorChapterPreviewResponse) 留在 local (或移到 shared)。

### 5.2 设计

**Option A (推荐)**:shim re-export
```python
# apps/studio_api/models/creator_settings.py
from lingwen_shared.contracts.python.creator import (
    CreatorVolumeSummaryGenerateRequest, CreatorVolumeSummaryGenerateResponse,
    CreatorModelsResponse, CreatorPreferencesResponse, CreatorPreferencesSaveRequest,
    CreatorMemoryAssetItem, CreatorMemoryAnnotationRequest, CreatorMemoryAnnotationResponse,
    CreatorMemoryAssetsResponse, CreatorEpubExportRequest, CreatorDocxExportRequest,
    CreatorMemoryQueryRequest, CreatorMemoryQueryResult, CreatorMemoryQueryResponse,
    CreatorPublishRequest, CreatorPublishEntry, CreatorPublishPlatformCapabilities,
    CreatorPublishPlatform, CreatorPublishPlatformsResponse, CreatorPublishHistoryResponse,
)
# 6 local-only DTOs 保持本地
class CreatorChapterPreviewResponse(BaseModel): ...
class CreatorChapterBodySaveRequest(BaseModel): ...
# ...
```

**Option B**:全部移到 shared
- 6 local DTO 也移 + 加 codegen 测试
- 更彻底,但增加 scope

**决定**:Option A。最小 scope,back-compat 0 改动,后续可推 Option B。

### 5.3 Migration pattern

- 单 commit,1 file 改 (`creator_settings.py` 变 re-export) + 1 file 改 (`apps/studio_api/models/__init__.py` import 列表可能简化)
- 测试:无新增 (current behavior 完全保留)
- 验证:`grep -E "class Creator" apps/studio_api/models/creator_settings.py` 应只有 6 个 class (而非 27)

---

## 6. T6: 19 content composables refactor

### 6.1 现状

parent spec §3.7 列出 19 个 content composables,v16.2.4 T6 只完成 onboarding 部分 (5 个),剩余 14 个待迁移。

实际盘点 (从 grep):

```
useCreatorAgent (3 files: .js + /useAgentTask.ts + ...?)
useCreatorBatchHistory (.js + /useBatchList.ts + /useBatchRestore.ts)
useCreatorModeGuide.js
useCreatorPage (.js + / subdir)
useCreatorPageHeader.js
useCreatorPageProviders.js
useCreatorPageRefresh.js
useCreatorProductTools (.js + / 5+ files)
useCreatorPulse.js
useCreatorWorkspace.js
useCreatorWrite (.js + / 1 file)
useCreatorWriteWorkbench (.js + / 1 file)
useCreatorAdvanceBatch.js
useCreatorSettings (preferences 部分)
```

### 6.2 设计

按 parent spec §3.7 范围:
- `useCreatorAgent` + `useCreatorDashboard` + `useCreatorLogicCheck` + `useCreatorPreferences` + `useCreatorUiProfile` 是主目标
- 其余 14 个 composable 是辅助 (Page-related, Write-related, Settings sub-functions)

**建议**:分 2-3 commits:
- **T6a**:5 主 composables (Agent, Dashboard, LogicCheck, Preferences, UiProfile) → 5-10 files
- **T6b**:14 辅助 composables → 8-12 files
- **T6c**:清理 `api/creator.js` 残余 aliases → 1 commit

每个 composable 内:`from '@/api/creator'` → 改 `@/api/content` 或 `@/api/settings` (per 各子域 typed wrapper)。

### 6.3 Test mock 拆分

per v16.2.5 §5.1 lesson 3:shim mock 不 propagate,每个 composable test 必须 mock typed wrapper module 本身 (非 barrel)。

---

## 7. T7: 4 unwired Content DTOs decision

### 7.1 现状

`packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` 定义了 4 个 DTO 但**没有 endpoint 引用**:

- `CreatorDashboardOverview` (line 1820)
- `CreatorDashboardChapterPreview` (line 1833)
- `CreatorUiProfileState` (line 1796)
- `CreatorUiProfileSaveRequest` (line 1808)

### 7.2 二选一

**Option A**:补 endpoint
- `GET /api/creator/dashboard/overview` → `CreatorDashboardOverview`
- `GET /api/creator/dashboard/chapter/{n}/preview` → `CreatorDashboardChapterPreview`
- `GET /api/creator/ui-profile` → `CreatorUiProfileState`
- `PUT /api/creator/ui-profile` → `CreatorUiProfileSaveRequest` → `CreatorUiProfileState`

**Option B**:删除 DTO
- 4 DTO 从 contracts/python/creator.py 移除
- TS codegen 同步移除
- 无前端 change (没有 caller)

**决定**:**Option B (删除)**。理由:
- 4 DTO 是 v16.2.4 content migration 时**前瞻性**写的,但 endpoint 没 wire (无 spec 要求)
- 留着增加 contracts 表面积,后续 endpoint 落地时再补
- YAGNI 原则

---

## 8. 风险与缓解

| 风险 | 影响 | 概率 | 缓解 |
|---|---|---|---|
| T4 shim deletion 引发 118 file import path 错误 | 高:routes 500 | 中 | 每个 commit 后 grep verify (`grep -rn "from infra.creator_X" apps/ tests/ \| grep -v "infra/creator_*.py"`) |
| T3 vitest debt 修后发现 v16.2.1 漏的真正 bug | 中:routes 行为错误 | 中 | T3 单开 commit 不合其他,bug 单独 follow-up |
| T6 composable refactor 触发 mock 拆分链 | 中:20+ test file 改动 | 高 | 沿用 v16.2.5 §5.1 lesson 3:shim mock 不 propagate |
| T5 DTO dedup 漏某个 caller | 低:type error | 低 | typed wrapper 已有 typed assertion,run mypy + pyright 后置 |
| T1 /api/ fix 修 world.ts 后 useWorldDb.js 的 raw fetch 仍 OK | 0 | 0 | world.ts 是新 typed wrapper,composables 仍 raw fetch,无 overlap |

---

## 9. Final gate (per parent spec §8.2)

```
grep -rl "from infra\.creator_" --include="*.py" apps/ packages/ \
  | grep -v "infra/creator_.*\.py" | wc -l  →  0

ls infra/creator_*.py | wc -l  →  0 (after T4)

ls packages/dashboard-contracts/src/shared/*.ts | wc -l  →  ≥9

uv run python tooling/contracts/zod_revalidate.py  →  0 drift
```

---

## 10. Carryover

T1-T7 全部完成后,v16.3 候选:
- import-linter DP-01..06 enforcement (T3 from parent spec §3.8 final gate)
- Content composables 还没切的剩余 (T6b/c 范围内推)
- `creator_ui_profile` 是 38 refs 最高的 shim,删完后必须有完整 integration test 覆盖

---

## 11. Plan 结构

`docs/superpowers/plans/2026-08-28-phase-126-v16-2-7-cleanup-plan.md` 详列每 task 的:
- commit 序列
- 文件清单
- 测试 expectation
- 验证命令
