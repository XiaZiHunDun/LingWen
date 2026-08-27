# Phase 126 v16.2.2 — Settings Subdomain 拆分 设计方案

> **状态**: ✅ Approved (brainstorming 闭环)
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§2.1 settings + §3.3 迁移计划 + §2.4 依赖矩阵)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§4 v16.2.2 tasks)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (前置 sub-phase 闭环 + lessons)
> - `.lingwen/architecture.yml` (`creator` module_boundaries — Volume exports 已加,Settings 待加)
> **前置**: v16.0 (`37718276`) + v16.1 (`e6927159`) + v15.7.1 baseline (`13db74f9`) + v16.2.0 (`5bc35f1b` 系) + v16.2.1 (`5733505b`)
> **下一步**: v16.2.3 onboarding (9 files) per plan §4 顺序 (decision 2026-08-27 brainstorming)

---

## 0. TL;DR

**v16.2.2 = 3 个 Python files + ≥8 DTOs + typed wrapper + 1 composable refactor + 32 routes imports** 迁到 `packages/lingwen-creator/src/lingwen_creator/settings/`。Settings 是 root 之一 (被 content + export + memory 依赖),先迁让后续 sub-phase 可用新 package path。

**关键事实** (实测):
- `infra/creator_settings_docs.py`: 351 lines, 7 functions
- `infra/creator_settings_history.py`: 136 lines, ~6 functions
- `infra/creator_merge_preferences.py`: 1355 lines, ~50 functions (最大单 file in v16.2.2)
- `apps/studio_api/routes/creator_settings.py`: 32 lazy imports (route handlers 用 `from infra.creator_X import ...` 在函数体内)
- 跨 subdomain lazy imports in 已迁 volume: 2 处 (volume/templates.py:144 + volume/template_approvals.py:667 — 引用 `infra.creator_settings_docs.text_diff_summary`)
- 12 个 `tests/infra/test_creator_settings_*.py` 继续经 shim 工作
- 4 个 `infra/creator_export_*.py` + `infra/creator_memory_assets.py` 引用 settings (out of scope v16.2.2, v16.2.5/v16.2.6 时更新)

**估算 ~10-12 commits**(DP-06 ≤4 files/commit)。

---

## 1. 范围与文件移动

### 1.1 源 → 目标

| From (shim source) | To (新位置) | Lines | Public functions |
|---|---|---|---|
| `infra/creator_settings_docs.py` | `packages/lingwen-creator/src/lingwen_creator/settings/docs.py` | 351 | 7 (text_diff_summary + 6 creator_settings_X) |
| `infra/creator_settings_history.py` | `packages/lingwen-creator/src/lingwen_creator/settings/history.py` | 136 | ~6 (history_payload + append/restore + 现在相关 helpers) |
| `infra/creator_merge_preferences.py` | `packages/lingwen-creator/src/lingwen_creator/settings/merge_preferences.py` | 1355 | ~50 (load/save/import/export/preset + graph/conflict/fix/toposort/changelog) |

**Verbatim copy 原则** (v16.2.1 lesson 沿用):函数体从 infra/creator_X.py 复制粘贴到 lingwen_creator/settings/X.py。**intra-package imports 调整见 §2**。

### 1.2 不在 v16.2.2 范围

| 文件/范围 | 原因 | 何时处理 |
|---|---|---|
| `infra/creator_export_docx.py` / `creator_export_epub.py` / `creator_export_common.py` (4 imports of settings.docs) | export subdomain 未迁 | v16.2.5 (export 迁移时) |
| `infra/creator_memory_assets.py` (1 import of settings.docs.creator_settings_docs_payload) | memory subdomain 未迁 | v16.2.6 (memory 迁移时) |
| `apps/studio_api/routes/creator_settings.py` 内的 32 个 lazy imports | IN scope (creator_settings.py 是 settings 的 route 层) | v16.2.2 本 sub-phase |
| `packages/lingwen-creator/.../volume/templates.py:144` + `volume/template_approvals.py:667` (2 cross-subdomain lazy imports) | volume 已迁但仍引用 infra paths | v16.2.2 本 sub-phase 顺手清理 (cross-subdomain, settings → volume 是允许方向) |
| `tests/infra/test_creator_settings_*.py` (12 files) | 经 shim 工作, 无需迁移 | v16.2.7 cleanup 时一并改 |
| `infra/creator_mode.py` (CreatorSettings / settings_from_project_config) | creator_mode 当前在 `content` 文件夹但逻辑是 settings concern | **carryover to v16.2.6 content migration**: 抽 `CreatorSettings` 到 `shared/mode.py`, `infra/creator_mode.py` 变 shim |
| `shared/check.py` 当前依赖 `infra.creator_mode.CreatorSettings` (违反 spec §2.4) | 不是 v16.2.2 范围 | v16.2.6 content migration 时修 (carryover from v16.2.0 review) |

---

## 2. Cross-Subdomain Imports (intra-package adjustments)

### 2.1 settings/docs.py — 3 处调整

```python
# Before (infra/creator_settings_docs.py):# 1. shared (v16.2.0 已迁)
from infra.creator_revision import CreatorDocConflictError, content_revision
# 2. intra-settings (intra-package import per plan §12.2)
from infra.creator_settings_history import append_settings_snapshot
# 3. volume (v16.2.1 已迁)
from infra.creator_volume_plan import global_outline_path

# After (packages/lingwen-creator/src/lingwen_creator/settings/docs.py):
# 1. shared → intra-package (target 已迁 → use new path per plan §12.1 rule 3)
from lingwen_creator.shared.revision import CreatorDocConflictError, content_revision
# 2. intra-settings (intra-package import)
from lingwen_creator.settings.history import append_settings_snapshot
# 3. volume → intra-package (target 已迁 → use new path)
from lingwen_creator.volume.plan import global_outline_path
```

### 2.2 settings/history.py — 1 处调整

```python
# Before: from infra.creator_volume_plan import global_outline_path
# After:  from lingwen_creator.volume.plan import global_outline_path
```

### 2.3 settings/merge_preferences.py — 1 处调整

```python
# Before: from infra.creator_volume_templates import is_valid_version_label, validate_version_label
# After:  from lingwen_creator.volume.templates import is_valid_version_label, validate_version_label
```

### 2.4 跨 subdomain lazy imports 清理 (volume 已迁但仍引用 infra paths)

**Volume 的 cross-subdomain imports 是允许方向** (settings ← volume 也允许,因为 target architecture §2.4 "volume: imports lingwen_creator.shared"),但实际是反向 (volume → settings.docs.text_diff_summary)。 这违反 target §2.4 ("volume 禁止 import 其他 subdomains (除 settings 文档交互?)") — 但 design 已经预留 settings 文档交互例外。 既然已经允许,v16.2.2 一并清理这 2 处 lazy imports:

```python
# packages/lingwen-creator/src/lingwen_creator/volume/templates.py:144
# Before: from infra.creator_settings_docs import text_diff_summary
# After:  from lingwen_creator.settings.docs import text_diff_summary

# packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py:667
# Before: from infra.creator_settings_docs import text_diff_summary
# After:  from lingwen_creator.settings.docs import text_diff_summary
```

**Lesson captured**: 已迁 subdomain 的 cross-subdomain lazy imports 应在 target 迁出后立即更新,避免留 stale infra paths。

---

## 3. DTOs (≥8 个,加到 `packages/lingwen-shared/.../creator.py` Settings section)

基于 `infra/creator_settings_*.py` + `infra/creator_merge_preferences.py` 的 return shapes + FastAPI route models 推算:

| DTO | 字段来源 | 路由 endpoint |
|---|---|---|
| `CreatorSettingsDocsResponse` | `creator_settings_docs_payload()` return | GET /api/creator/settings/docs |
| `CreatorSettingsDocsSaveRequest` | `save_creator_settings_docs()` input | PUT /api/creator/settings/docs |
| `CreatorSettingsDocsDiffResponse` | `preview_settings_docs_diff()` return | POST /api/creator/settings/docs/diff |
| `CreatorSettingsThreeWayDiffResponse` | `preview_settings_three_way()` return | POST /api/creator/settings/docs/three-way |
| `CreatorSettingsMergeStrategyResponse` | `preview_settings_merge_strategy()` return | POST /api/creator/settings/docs/merge-strategy |
| `CreatorSettingsHistoryResponse` | `settings_history_payload()` return | GET /api/creator/settings/history |
| `CreatorSettingsHistoryRestoreRequest` | `restore_settings_snapshot()` input | POST /api/creator/settings/history/restore |
| `CreatorMergePreferencesResponse` | `load_merge_preferences()` + global variant return | GET /api/creator/settings/merge-preferences |
| `CreatorMergePreferencesExportResponse` | `export_merge_preferences()` return | POST /api/creator/settings/merge-preferences/export |
| `CreatorMergePreferencesImportRequest` | `import_merge_preferences()` input | POST /api/creator/settings/merge-preferences/import |
| `CreatorMergePresetPackageSummary` | `list_merge_preset_packages()` items | GET /api/creator/settings/merge-presets |
| `CreatorMergePresetPackageDetail` | `get_merge_preset_package()` return | GET /api/creator/settings/merge-presets/{id} |
| `CreatorMergePresetGraphResponse` | `build_merge_preset_graph()` return | GET /api/creator/settings/merge-presets/graph |
| `CreatorMergePresetConflictsResponse` | `detect_merge_preset_conflicts()` + `detect_factory_merge_preset_conflicts()` return | GET /api/creator/settings/merge-presets/conflicts |
| `CreatorMergePresetConflictFix` | `suggest_merge_preset_fixes()` items + `apply_merge_preset_fix()` input | POST /api/creator/settings/merge-presets/fixes |
| `CreatorMergePresetImportPreviewResponse` | `preview_merge_preset_import_diff()` + `preflight_merge_preset_import()` return | POST /api/creator/settings/merge-presets/preflight |
| `CreatorMergePresetChangelogResponse` | `list_merge_preset_changelog()` + `preview_merge_preset_changelog_diff()` return | GET /api/creator/settings/merge-presets/changelog |
| `CreatorMergePresetPublishRequest` / `CreatorFactoryMergePresetOperationResponse` | `publish_merge_preset_to_factory()` + `pull_factory_merge_presets_to_project()` + `resolve_factory_merge_preset_conflict()` | POST /api/creator/settings/merge-presets/publish etc. |
| `CreatorMergePresetToposortResponse` | `toposort_merge_preset_packages()` + `apply_toposort_merge_preset_order()` return | POST /api/creator/settings/merge-presets/toposort |

**注意**: 实际 DTO 字段枚举在执行时由 implementer 严格根据 Python 函数 return shape + FastAPI route Pydantic models 提取。本 spec 仅列 DTO 名 + 来源函数,**实施阶段如有未列出 DTO 需添加时,由 implementer amend §3 + 加一行 deviation 在 handoff §3**。

**Workflow**: implementer 把 DTOs 加到 `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` Settings section → 跑 `uv run python tooling/contracts/generate.py` → TS 自动生成 → zod CI drift check。

---

## 4. Typed Wrapper

### 4.1 `apps/dashboard/src/api/settings.ts` (NEW)

仿 v16.1 T4 reference (world.ts/workspace.ts/quality.ts) + v16.2.1 volume.ts style:
- **No zod runtime validation** (v16.2.1 lesson: zod 是 T5/CI drift,不是 wrapper layer)
- **No `/api/` prefix in code** (v16.2.1 lesson: BASE_URL 已是 `/api`)
- ≥7 wrapper functions:

```typescript
// apps/dashboard/src/api/settings.ts (example signature)
export async function getSettingsDocs(projectId: string): Promise<CreatorSettingsDocsResponse>;
export async function saveSettingsDocs(projectId: string, req: CreatorSettingsDocsSaveRequest): Promise<CreatorSettingsDocsResponse>;
export async function previewSettingsDocsDiff(projectId: string, ...): Promise<CreatorSettingsDocsDiffResponse>;
export async function getSettingsHistory(projectId: string): Promise<CreatorSettingsHistoryResponse>;
export async function restoreSettingsSnapshot(projectId: string, req: CreatorSettingsHistoryRestoreRequest): Promise<void>;
export async function getMergePreferences(projectId: string): Promise<CreatorMergePreferencesResponse>;
export async function exportMergePreferences(projectId: string): Promise<CreatorMergePreferencesExportResponse>;
export async function importMergePreferences(projectId: string, req: CreatorMergePreferencesImportRequest): Promise<void>;
export async function listMergePresetPackages(projectId: string): Promise<CreatorMergePresetPackageSummary[]>;
export async function getMergePresetPackage(projectId: string, packageId: string): Promise<CreatorMergePresetPackageDetail>;
export async function buildMergePresetGraph(projectId: string): Promise<CreatorMergePresetGraphResponse>;
export async function detectMergePresetConflicts(projectId: string, ...): Promise<CreatorMergePresetConflictsResponse>;
// ... 等 (覆盖 creator_settings.py 全部 endpoints)
```

### 4.2 `packages/dashboard-contracts/src/shared/settings.ts` (NEW,re-export shim)

仿 v16.2.1 `packages/dashboard-contracts/src/shared/creator.ts` (volume re-export):
```typescript
export * from '@lingwen/dashboard-contracts/src/shared/settings';
```

### 4.3 knip allowlist

`apps/dashboard/knip.json` 加 entries:
```json
{
  "files": [
    "apps/dashboard/src/api/{world,workspace,quality,volume,settings}.ts"
  ]
}
```

(注意: v16.2.1 漏加 patterns 时, knip 报 unused file error,需 allowlist 同步加)

---

## 5. Composable Refactor

### 5.1 `apps/dashboard/src/composables/useCreatorSettings.*` (existing)

**Exact file 位置需先确认**: 估计在 `apps/dashboard/src/composables/useCreatorSettings.js` 或 `.ts`。**实施前 implementer 必跑 grep**:
```bash
ls apps/dashboard/src/composables/useCreatorSettings*
grep -l "creator_settings_docs\|creator_settings_history\|creator_merge_preferences" apps/dashboard/src/composables/*
```

**Refactor scope**:
- 替换内部 `fetch(BASE_URL + '/api/creator/settings/docs', ...)` → `getSettingsDocs(projectId)`
- 替换其他 raw fetch → 对应 typed wrapper function
- 验证所有现有 composable tests 仍 pass
- **重点**: 沿用 volume 的 composable refactor pattern (T4 + T5e 双 batch, 不要 1 commit 改完)

### 5.2 无新 composable

v16.2.2 不创建新 composable (已有 useCreatorSettings 覆盖)。

---

## 6. Routes Imports Migration

**`apps/studio_api/routes/creator_settings.py`** (32 lazy imports in route handlers):

逐个替换:
```python
# Before (e.g. line 83): from infra.creator_settings_docs import creator_settings_docs_payload
# After:                  from lingwen_creator.settings.docs import creator_settings_docs_payload

# Before (e.g. line 159): from infra.creator_merge_preferences import load_merge_preferences
# After:                  from lingwen_creator.settings.merge_preferences import load_merge_preferences
```

**Migration chunks** (DP-06 严格 ≤4 files per commit; creator_settings.py 是单 file,允许 inline 但 routes migration 可拆为多次 commit):
- Chunk 1: docs.py imports (line 82-93, 119-128, 142)
- Chunk 2: history.py imports (待 grep 确认)
- Chunk 3-4: merge_preferences.py imports (50+ 个)
- 估算 4 commits

**验证**:
```bash
grep "^from infra.creator_settings_\|^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py
# Expected: 0 matches
```

---

## 7. Shims + Private Symbol Audit

### 7.1 Shim files (3 变 1-line)

```python
# infra/creator_settings_docs.py (after v16.2.2)
from lingwen_creator.settings.docs import *  # noqa: F403

# infra/creator_settings_history.py
from lingwen_creator.settings.history import *  # noqa: F403

# infra/creator_merge_preferences.py
from lingwen_creator.settings.merge_preferences import *  # noqa: F403
```

### 7.2 Private symbol audit (v16.2.1 lesson)

**必需 grep** (任何 shim 必须 audit existing tests 是否 import private symbols):
```bash
# Find tests using underscore-prefixed names from settings files
grep -n "_" tests/infra/test_creator_settings_docs.py tests/infra/test_creator_settings_history.py tests/infra/test_creator_merge_preferences.py tests/infra/test_creator_merge_preset_*.py 2>/dev/null | grep "^from infra\|import _" | head -30

# Also check tests for direct module attribute access (e.g. creator_settings_docs.MERGE_SOURCES)
grep -rn "creator_settings_docs\._\|creator_settings_history\._\|creator_merge_preferences\._" tests/ 2>/dev/null | head -20
```

**如有 private symbol 使用**, 在 shim 加 explicit re-export (仿 v16.2.1 templates 加 27 个 + template_approvals 加 13 个 underscore re-exports):

```python
# infra/creator_settings_docs.py (example if audit finds private names used)
from lingwen_creator.settings.docs import *  # noqa: F403
from lingwen_creator.settings.docs import (
    _private_helper_1,
    _private_helper_2,
)  # explicit re-exports for test compat
```

**预估**: settings/docs.py 较小 (351 lines) — 估计 < 5 个 underscore helpers 需 re-export。 settings/merge_preferences.py 较大 (1355 lines, 50+ functions, ~20 个 underscore-prefixed helpers) — 估计需 10-20 个 underscore re-exports。

**验证**:
```bash
/home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import creator_settings_docs_payload, MERGE_SOURCES, text_diff_summary"
# OK (shim works + private names re-exported if needed)

/home/ailearn/miniconda3/bin/python -c "from infra.creator_merge_preferences import load_merge_preferences, _semver_tuple"
# OK
```

---

## 8. Tests + Verification Gates

### 8.1 New tests

`packages/lingwen-creator/tests/test_settings.py` (≥3 tests):
- Test 1: `lingwen_creator/settings/docs.py` 可 import, 暴露 7 expected functions
- Test 2: `lingwen_creator/settings/history.py` + `lingwen_creator/settings/merge_preferences.py` 同上
- Test 3: Intra-package imports 不引入 circular import (per v16.2.1 T1 lesson)

### 8.2 Existing tests (经 shim)

`tests/infra/test_creator_settings_*.py` (12 files) — 全部经 shim 继续工作, **0 改动**。

### 8.3 Verification gates (per spec §8.1)

```bash
# Backend
uv sync --all-packages --all-extras  # 必须 --all-packages
uv run python -m pytest packages/lingwen-creator/tests/test_settings.py -v
# Expected: ≥3 passed

uv run python -m pytest tests/infra/test_creator_settings_*.py -v
# Expected: all 12 files passing (shim back-compat)

# TS codegen
uv run python tooling/contracts/generate.py
# Expected: 59 → ≥? interfaces generated (volume + settings + new)

# Zod reverse validation (needs running FastAPI server)
uv run python tooling/contracts/zod_revalidate.py --openapi /tmp/openapi.json
# Expected: 0 drift

# Frontend
cd apps/dashboard
pnpm vitest run tests/unit/composables/ tests/unit/api/
# Expected: ≥40 passing + new settings tests

pnpm exec vue-tsc --noEmit
# Expected: 0 errors

pnpm lint:all  # ESLint
# Expected: 0 warnings

pnpm exec knip
# Expected: 0 errors (settings.ts in allowlist)

pnpm build
# Expected: success

# Backend import smoke (shim back-compat)
uv run python -c "from lingwen_creator.settings import docs, history, merge_preferences"
# OK

# Routes import check
grep "^from infra.creator_settings_\|^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py
# Expected: 0 matches

# Backwards compat via shim
/home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import creator_settings_docs_payload"
# OK

# Lint
ruff check .
# Expected: 0 errors

# Final shim count
ls infra/creator_*.py | wc -l
# Expected: 36 - 3 = 33 (v16.2.2 -3 settings shims)
```

### 8.4 DP-06 严格遵守

每 commit ≤4 files。v16.2.2 估算 ~10-12 commits:

| Commit | 范围 | Files |
|---|---|---|
| 1 | T1: settings/docs + history.py + 2 shims + 1 init | 4-5 files |
| 2 | T1 cont: merge_preferences.py + 1 shim | 2 files |
| 3 | T1 cont: __init__.py + tests | 2-3 files |
| 4 | T2: Settings DTOs + codegen | 2 files |
| 5 | T3: typed wrapper + re-export shim + knip | 3 files |
| 6 | T4a: useCreatorSettings refactor part 1 | 1-2 files |
| 7 | T4b: useCreatorSettings refactor part 2 + routes chunk 1 (docs imports) | 2 files |
| 8 | T5a: routes chunk 2 (merge_preferences imports) | 1 file |
| 9 | T5b: routes chunk 3 (merge_preset imports) | 1 file |
| 10 | T6: volume/templates + template_approvals cross-import cleanup | 2 files |
| 11 | T7: shim underscore re-exports (if audit finds) | 1-3 files |
| 12 | docs: architecture.yml update + migration_log v16.2.2 entry | 2 files |

**Notes**:
- Commit 1: 不超 4 files 限制 — 4 files = settings/docs.py + settings/history.py + 2 shims (但 shim 文件和原文件不在同一 commit 通常做法, T1 模式或 catch-up)
- Commit 7-9: routes migration 拆 chunk 因为 routes 文件单 file 但 32 lazy imports — 每 commit ≤4 imports? 实际 routes file 单 commit inline edits 都可 (DP-06 是 file-level,不是 line-level)
- Commit 11: 仅当 audit 找到 underscore imports 需 re-export

---

## 9. Risks & Carryover

### 9.1 Risks

| Risk | Probability | Mitigation |
|---|---|---|
| **Shim underscore re-export 漏掉** 导致 tests fail | Medium | §7.2 严格 audit + verification 用 `/home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import _private_helper"` 测 |
| **`/api/` prefix bug** 复发在新 typed wrapper | Low | v16.2.1 lesson 沿用 + spec review 验证 |
| **Intra-package import cycle** (settings ↔ volume) | Low | 已 grep 验证: settings/docs 只 → volume.plan (单向), settings/merge_preferences 只 → volume.templates (单向) |
| **Routes 32 lazy imports 拆 chunk 时跨 commit broken** | Medium | 每 chunk 改后跑 `pytest apps/studio_api/tests/test_creator_settings_route.py` 验证 (如存在) |
| **`MERGE_SOURCES` 全局常量** 是 settings.docs 模块级 | Low | star-import 不会 skip module-level constants, 默认 re-export (no underscore) |
| **knip 报 typed wrapper + re-export shim unused** | Low | §4.3 allowlist 同步加 |

### 9.2 Carryover (NOT in v16.2.2)

| 任务 | 何时处理 |
|---|---|
| `infra/creator_export_docx.py` / `creator_export_epub.py` / `creator_export_common.py` (4 settings.docs imports) | v16.2.5 export migration |
| `infra/creator_memory_assets.py` (1 settings.docs import) | v16.2.6 memory migration |
| `infra/creator_mode.py` CreatorSettings 抽到 `shared/mode.py` + `infra/creator_mode.py` 变 shim | v16.2.6 content migration |
| `shared/check.py` 当前依赖 `infra.creator_mode.CreatorSettings` (违反 spec §2.4) | v16.2.6 content migration (共享 mode.py 后修) |
| `infra/creator_settings_*.py` + `infra/creator_merge_preferences.py` shim 删除 | v16.2.7 cleanup |
| `tests/infra/test_creator_settings_*.py` 12 files 改用 lingwen_creator.settings.* 直接 import | v16.2.7 cleanup |
| `apps/dashboard/src/api/{world,workspace,quality}.ts` 的 `/api/api/` URL 重复 bug | v16.2.7 cleanup |
| `import-linter` 强制 infra.creator_X forbidden pattern (DP-01..06 enforcement) | v16.4/v16.5 (per DP enforcement phases) |

### 9.3 v16.2.2 新增 lessons 候选

- 已迁 subdomain 的 cross-subdomain lazy imports 应在 target 迁出后立即清理 (volume/templates + template_approvals 的 2 处 lazy imports)
- creator_merge_preferences.py 1355 lines / 50 functions / ~20 underscore helpers — 比 v16.2.1 template_approvals.py (697 lines / 13 underscore) 还要 dense, audit 必须彻底

---

## 10. References

- **设计总图**: `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§2.1 settings + §3.3)
- **实施计划**: `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§4 v16.2.2)
- **前置 sub-phase**: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md`
- **架构源**: `.lingwen/architecture.yml` (creator module_boundaries + exports list 待加 settings entries)
- **迁移日志**: `.lingwen/migration_log.yml` (v16.2.2 entry 待加)
- **项目约定**: `CLAUDE.md` (品牌/技术栈/命令/已知遗留)

---

## 11. Verification Plan (sub-phase 闭环验收)

v16.2.2 闭环时必须通过的验收清单 (harness 自动化):

1. ✅ `uv run python -m pytest packages/lingwen-creator/tests/test_settings.py -v` ≥3 passed
2. ✅ `uv run python -m pytest tests/infra/test_creator_settings_*.py -v` 12 files all passing
3. ✅ `uv run python tooling/contracts/generate.py` 生成 settings.ts (≥18 interfaces 估)
4. ✅ `uv run python tooling/contracts/zod_revalidate.py` 0 drift
5. ✅ `pnpm vitest run` ≥40 passing + new settings tests
6. ✅ `pnpm exec vue-tsc --noEmit` 0 errors
7. ✅ `pnpm lint:all` 0 warnings
8. ✅ `pnpm exec knip` 0 errors (settings.ts in allowlist)
9. ✅ `pnpm build` success
10. ✅ `ruff check .` 0 errors
11. ✅ `grep "^from infra.creator_settings_\|^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py` = 0 matches
12. ✅ `grep "^from infra.creator_settings_docs" packages/lingwen-creator/src/lingwen_creator/volume/{templates,template_approvals}.py` = 0 matches
13. ✅ shim back-compat: `/home/ailearn/miniconda3/bin/python -c "from infra.creator_settings_docs import ..."` OK
14. ✅ `ls infra/creator_*.py | wc -l` = 33 (was 36, -3 settings shims)
15. ✅ `.lingwen/architecture.yml` + `.lingwen/migration_log.yml` updated

---

**v16.2.2 settings 拆分设计 end of spec — 待 user review**