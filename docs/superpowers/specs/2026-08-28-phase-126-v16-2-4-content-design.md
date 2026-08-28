# Phase 126 v16.2.4 — Content Subdomain 拆分 + Onboarding T4 闭环 设计方案

> **状态**: ✅ 设计已批准,待 writing-plans
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (母 spec, §2.1 content 子域定义 + §3.7 v16.2.6 content 任务 + §3.8 v16.2.7 cleanup)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§5 content 任务, renumbered to v16.2.4 per 实际执行顺序)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (Plan reorder 说明)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md` (precedent shim pattern)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-3-onboarding-handoff.md` (T4-partial carryover + creator_mode forward-reference)
> **前置**:
> - v16.2.3 onboarding 闭环 (`a82cc4de`) — 9 onboarding files 迁完 + 30 DTOs + 23 wrapper functions
> - v16.2.2 settings 闭环 (`1fb9baed`) — 3 settings files 迁完
> - v16.2.1 volume 闭环 (`5733505b`) — 6 volume files 迁完
> - v16.2.0 shared 闭环 (`5bc35f1b`) — skeleton + shared/{revision,check}.py
> **下一步**: v16.2.5 export + v16.2.6 memory + v16.2.7 cleanup

---

## 0. TL;DR

**v16.2.4 = content subdomain 拆分 + 关键 carryover 闭环**,11 commits / ~25 files / 1.5 天。

**Content 是 Phase 126 v16.2 creator 6-subdomain 拆分的最后一个 sub-phase**,也是最复杂的:
- **8 files** (agent.py 598L + batch_history.py 28L + dashboard.py 228L + logic_check.py 114L + mode.py 108L + models.py 61L + preferences.py 116L + ui_profile.py 327L) → `packages/lingwen-creator/src/lingwen_creator/content/`
- **跨 subdomain 依赖**:onboarding 用 `creator_mode.CREATION_MODE_* + settings_from_project_config` (forward-reference via `infra.creator_mode`)
- **spec violation 修复**:`shared/check.py` 当前依赖 `infra.creator_mode` — 违反 spec §2.4 "shared 不能 import 其他 subdomain"
- **onboarding T4-partial carryover**:5 composable files 需 refactor 掉 21 Creator-prefixed aliases,直接用新 typed wrapper names
- **infra/project_init.py + infra/project_config.py** 仍 import `infra.creator_mode` — T5 同步切到 `lingwen_creator.shared.mode`

**关键决策**:
- **Mode placement**: 抽 `CreatorSettings + settings_from_project_config + CREATION_MODE_*` → `shared/mode.py` (per plan §5),`content/mode.py` 变 shim re-export `shared/mode.py`
- **agent.py 单文件**: 保持 598L 单文件 (precedent: v16.2.3 digest_schedule.py 526L),T2 拆 T2a + T2b 因 DP-06 4 files 上限
- **infra/creator_mode.py**: 变 shim (precedent: v16.2.1..3 全部 shim pattern),v16.2.7 才删
- **infra/project_init.py + infra/project_config.py**: T5 同步切到 `lingwen_creator.shared.mode` import

**11 commits** (T1 + T2a-d + T3-T8):
```
T1:   shared/mode.py + creator_mode shim + shared/check.py + onboarding/onboarding.py (4 files)
T2a:  content/agent.py + agent shim + content/batch_history.py + batch_history shim (4 files)
T2b:  content/dashboard.py + dashboard shim + content/logic_check.py + logic_check shim (4 files)
T2c:  content/mode.py (shim) + mode shim + content/models.py + models shim (4 files)
T2d:  content/preferences.py + preferences shim + content/ui_profile.py + ui_profile shim (4 files)
T3:   DTOs (3 files: creator.py + creator.ts + test_content_dto.py)
T4:   typed wrapper (5 files: content.ts + re-export + index.ts + knip allowlist + URL contract test)
T5:   routes migration (3 files: creator_core.py + project_init.py + project_config.py)
T6:   onboarding T4 refactor (5 files: 4 composables + delete onboarding.js shim)
T7:   cross-subdomain cleanup (1-4 files depending on grep findings,可能 skip)
T8:   handoff (3 files: handoff.md + CLAUDE.md + architecture.yml/migration_log.yml updates)
```

**总计 11 commits**,每 commit ≤5 files (DP-06 严格,所有 commit 都在 3-5 files 之间)。

---

## 1. 背景与动机

### 1.1 v16.2.4 解决的 4 类 carryover

| Carryover 来源 | 描述 | v16.2.4 修复方式 |
|---|---|---|
| **v16.2.3 T1c forward-reference** | `lingwen_creator.onboarding.onboarding` import `infra.creator_mode` + 加 `# noqa: F401  # v16.2.4 will replace` 注释 | T1 把 `infra.creator_mode` 变 shim,onboarding.py 改 import `from lingwen_creator.shared.mode import ...` |
| **shared/check.py spec violation** | `packages/lingwen-creator/src/lingwen_creator/shared/check.py:12` import `infra.creator_mode` (违反 spec §2.4 "shared 不能 import 其他 subdomain") | T1 抽 `CreatorSettings + settings_from_project_config` 到 `shared/mode.py`,改 check.py import 为 `from lingwen_creator.shared.mode import ...` |
| **v16.2.3 T4-partial composables** | 5 composable files (useCreatorOnboarding.js + 3 .ts submodules + index.ts) 仍用 21 Creator-prefixed aliases,shim `api/onboarding.js` 保留作 back-compat | T6 refactor 5 composables 掉 aliases,直接用新 typed wrapper names,删除 `api/onboarding.js` shim |
| **infra/project_X.py** | `infra/project_init.py:10` + `infra/project_config.py:11` 仍 import `infra.creator_mode` | T5 同步切到 `from lingwen_creator.shared.mode import ...` |

### 1.2 Content subdomain 是最大的 sub-phase

| 维度 | 数据 |
|---|---|
| Python files | 8 (vs volume 6, settings 3, onboarding 9 — onboarding 数量多但都 < 600L) |
| 总 LOC | ~1580 (vs volume ~3224, settings ~2277, onboarding ~2468) — onboarding LOC 多因 digest_schedule 526L |
| 最大单文件 | `agent.py` 598L (precedent: v16.2.3 digest_schedule.py 526L 单文件 verbatim copy) |
| Routes | `routes/creator_core.py` 22 endpoints 中 content 部分 (~12 endpoints,除 memory/volume/export 部分) |
| Composables | spec §3.7 列 19 (useCreatorAgent + useCreatorBatchHistory + useCreatorModeGuide + useCreatorPage* + useCreatorPulse + useCreatorProductTools + useCreatorWorkspace + useCreatorWrite* + useCreatorWriteWorkbench) — **实际需要 grep 验证数量** |
| DTOs | ~15 (最大 DTO collection) |

### 1.3 为什么必须 v16.2.4 一起做 onboarding T4 + shared/mode.py 抽取

| 推力 | 后果 |
|---|---|
| **forward-reference 必须关闭** | `infra.creator_mode` 是 onboarding.py 的真实 import,不是测试代码。spec violation 在 production code path |
| **shared/check.py spec violation 暴露给 v16.2.4** | onboarding 不直接 import `shared.check`,但 `shared.check.format_check_mode_banner` 仍依赖 `infra.creator_mode`。如果不修,onboarding forward-reference 关闭后,`shared.check` 仍是 broken state |
| **onboarding T4-partial 是低风险 carryover** | 5 composable files 的 refactor 是机械的 (find/replace 21 aliases),shim 已工作,无行为变化。绑到 v16.2.4 一次性关闭两个 sub-phase 的 carryover |
| **infra/project_X 是 content forward consumer** | `infra/project_init.py` 用 `CreatorSettings` 验证 project config,`infra/project_config.py` 同样。T5 一起切避免 v16.2.7 cleanup 时还要回切 |

---

## 2. 目标架构

### 2.1 Content subdomain 结构

```
packages/lingwen-creator/src/lingwen_creator/
├── shared/
│   ├── mode.py               # v16.2.4 NEW — CreatorSettings + CREATION_MODE_* + settings_from_project_config
│   ├── revision.py           # v16.2.0 (unchanged)
│   └── check.py              # v16.2.0 (UPDATE: import from shared.mode, not infra.creator_mode)
├── onboarding/               # v16.2.3 (UPDATE: onboarding.py import from lingwen_creator.shared.mode)
├── volume/                   # v16.2.1 (unchanged)
├── settings/                 # v16.2.2 (unchanged)
└── content/                  # v16.2.4 NEW
    ├── __init__.py           # star-imports from all 8 submodules
    ├── agent.py              # verbatim from infra/creator_agent.py (598L)
    ├── batch_history.py      # verbatim from infra/creator_batch_history.py (28L)
    ├── dashboard.py          # verbatim from infra/creator_dashboard.py (228L)
    ├── logic_check.py        # verbatim from infra/creator_logic_check.py (114L)
    ├── mode.py               # SHIM — re-export from shared.mode
    ├── models.py             # verbatim from infra/creator_models.py (61L)
    ├── preferences.py        # verbatim from infra/creator_preferences.py (116L)
    └── ui_profile.py         # verbatim from infra/creator_ui_profile.py (327L)
```

**Spec §2.1 v16.2.4 update**: 母 spec 列的 content/ 子模块中:
- `mode.py` 不再 verbatim copy,而是 shim (because mode logic 在 shared/mode.py)
- 其余 7 files verbatim copy from `infra/creator_X.py`

### 2.2 shared/mode.py 内容

```python
# packages/lingwen-creator/src/lingwen_creator/shared/mode.py
"""Creator product line mode + quality profile resolution.

Migrated from infra/creator_mode.py in Phase 126 v16.2.4.
Used by:
  - shared.check.format_check_mode_banner (composition helper)
  - content.preferences (resolve_creator_settings for save)
  - onboarding.onboarding (validate creation_mode in wizard)
  - infra.project_config / project_init (resolve project-level defaults)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CREATION_MODE_COMPANION = "companion"
CREATION_MODE_ADVANCE = "advance"
CREATION_MODE_STUDIO = "studio"

CREATION_MODES = frozenset({CREATION_MODE_COMPANION, CREATION_MODE_ADVANCE, CREATION_MODE_STUDIO})

QUALITY_CREATOR_RELAXED = "creator_relaxed"
QUALITY_STUDIO_FULL = "studio_full"

QUALITY_PROFILES = frozenset({QUALITY_CREATOR_RELAXED, QUALITY_STUDIO_FULL})


@dataclass(frozen=True)
class CreatorSettings:
    creation_mode: str
    quality_profile: str
    fail_severity: str | None
    run_prose_calibration: bool
    run_llm_judge: bool
    run_golden_set: bool
    notify_per_chapter: bool
    advance_volume_summary: bool


def normalize_creation_mode(value: str | None) -> str:
    # ... verbatim ...


def normalize_quality_profile(value: str | None, *, creation_mode: str) -> str:
    # ... verbatim ...


def resolve_creator_settings(
    *,
    creation_mode: str | None = None,
    quality_profile: str | None = None,
) -> CreatorSettings:
    # ... verbatim ...


def settings_from_project_config(config: Any) -> CreatorSettings:
    # ... verbatim ...
```

**Rationale (per spec §2.4 'shared as cross-subdomain utility')**:
- `format_check_mode_banner(ProjectConfig, CreatorSettings)` 在 `shared.check` 中(已有,per v16.2.0)
- onboarding wizard 验证 `CREATION_MODE_*` (forward-reference 已声明)
- content.preferences 用 `resolve_creator_settings` 保存项目设置
- infra/project_X 用 `settings_from_project_config` 解析 YAML config

→ `shared/mode.py` 是 cross-subdomain utility,符合 spec §2.4 "shared 不被其他 subdomain 限制"。

### 2.3 content/mode.py shim

```python
# packages/lingwen-creator/src/lingwen_creator/content/mode.py
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.shared.mode.

Creator mode utilities (CreatorSettings + CREATION_MODE_* + settings_from_project_config)
have been moved to lingwen_creator.shared.mode because they are cross-subdomain
utilities used by:
  - shared.check.format_check_mode_banner
  - onboarding.onboarding (wizard validation)
  - infra.project_config / project_init (YAML resolution)

This shim maintains backwards compat for any code using:
    from lingwen_creator.content.mode import CreatorSettings, ...

Will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.mode import *  # noqa: F403
```

### 2.4 infra/creator_mode.py shim

```python
# infra/creator_mode.py (after v16.2.4 T1)
"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.shared.mode.

Migrated to packages/lingwen-creator/src/lingwen_creator/shared/mode.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_mode import CreatorSettings, settings_from_project_config, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.shared.mode import *  # noqa: F403
```

**Pattern**: 与 v16.2.1..3 全部 shim 一致 (1-line star-import)。

### 2.5 Frontend Layout (新增)

```
apps/dashboard/src/api/
├── onboarding.ts                # v16.2.3 (NEW naming — fetchOnboardingWizard 等)
├── onboarding.js                # v16.2.3 shim with 21 Creator-prefixed aliases (T6 删除)
└── content.ts                   # v16.2.4 NEW (≥10 wrapper functions)

apps/dashboard/src/composables/
└── useCreatorOnboarding/        # v16.2.4 T6 — drop 21 Creator-prefixed aliases,use new typed wrapper names
    ├── index.ts                 # UPDATE: import from @/api/onboarding (new names)
    ├── useOnboardingProgress.ts # UPDATE: 内部调用 fetchOnboardingWizard 等
    ├── useOnboardingNotifications.ts # UPDATE
    └── useWizardSteps.ts        # UPDATE
```

### 2.6 Per-Subdomain 依赖矩阵 (spec §2.4 update)

| Subdomain | 允许 import (v16.2.4) | 禁止 import |
|---|---|---|
| shared | `infra.persistence`, `infra.project_config`, `infra.errors`, **`lingwen_creator.shared.mode` (intra-package)** | 其他 subdomains, `infra.creator_X` |
| memory | (未变) | (未变) |
| settings | (未变) | (未变) |
| export | (未变) | (未变) |
| volume | (未变) | (未变) |
| onboarding | `infra.persistence`, `lingwen_creator.memory`, **`lingwen_creator.shared.mode` (v16.2.4 NEW)** | settings / volume / content / export |
| content | `infra.persistence`, `infra.llm_service`, `lingwen_creator.shared`, **`lingwen_creator.shared.mode` (v16.2.4 NEW)** | settings / volume / onboarding / export |

**关键变更**:
- shared → 允许 intra-package import `lingwen_creator.shared.mode`(shared module 之间的引用,不算 violation)
- onboarding → 增加 `lingwen_creator.shared.mode` 依赖 (close forward-reference to infra.creator_mode)
- content → 增加 `lingwen_creator.shared.mode` 依赖 (content.preferences 用 resolve_creator_settings)
- `content/mode.py` 是 shim re-export from `shared/mode.py`(intra-package import,符合 §12.2 precedent — volume/pulse.py 也 intra-package import volume/plan)

### 2.7 Routes 改造

`apps/studio_api/routes/creator_core.py` 当前 22 endpoints (per spec §3.7)。其中:
- 3 endpoints memory (v16.2.5 Round 2 leaf 待迁)
- ~6 endpoints volume (v16.2.1 已迁,但部分 routes 仍在 creator_core.py — T5 检查)
- 3 endpoints export (v16.2.5 Round 2 leaf 待迁)
- ~10 endpoints content (v16.2.4 待迁)

**T5 scope**:
- 改 ~10 content endpoints 的 lazy imports from `infra.creator_X` → `lingwen_creator.content.X`
- 同步改 `infra/project_init.py:10` + `infra/project_config.py:11` imports

---

## 3. 迁移计划 (T1-T8)

### 3.1 T1: shared/mode.py extraction + creator_mode shim + check.py fix + onboarding forward-ref close (4 files)

**Files:**
- Create: `packages/lingwen-creator/src/lingwen_creator/shared/mode.py` (verbatim from infra/creator_mode.py, 108L)
- Modify: `infra/creator_mode.py` (→ 1-line shim re-exporting from lingwen_creator.shared.mode)
- Modify: `packages/lingwen-creator/src/lingwen_creator/shared/check.py` (12: `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...`)
- Modify: `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` (8: `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...`,移除 `# noqa: F401` forward-reference 注释)

**T1.1**: 写 `test_shared_mode.py` (≥4 tests):
- `CreatorSettings` is dataclass with all 8 fields
- `CREATION_MODE_STUDIO` etc. constants
- `normalize_creation_mode` validation
- `settings_from_project_config` accepts Any (duck-typed ProjectConfig)

**T1.2**: 验证 RED → 创建 `shared/mode.py` (verbatim copy from infra/creator_mode.py)

**T1.3**: 改 `infra/creator_mode.py` → 1-line shim

**T1.4**: 改 `shared/check.py` import → `from lingwen_creator.shared.mode import ...`

**T1.5**: 改 `onboarding/onboarding.py` import → `from lingwen_creator.shared.mode import ...`,删 `# noqa: F401`

**T1.6**: 验证所有 import work (Python 3.13 miniconda — v16.1 lesson uv venv 路径)

**T1.7**: pytest + ruff check + commit

### 3.2 T2: content/ subdomain Python file migration (4 sub-commits)

**T2a**: agent.py + batch_history.py + 2 shims (4 files)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/__init__.py` (empty placeholder)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/agent.py` (verbatim from infra/creator_agent.py, 598L)
- Create: `packages/lingwen-creator/src/lingwen_creator/content/batch_history.py` (verbatim from infra/creator_batch_history.py, 28L)
- Modify: `infra/creator_agent.py` → 1-line shim `from lingwen_creator.content.agent import *  # noqa: F403`
- Modify: `infra/creator_batch_history.py` → 1-line shim

**T2b**: dashboard.py + logic_check.py + 2 shims (4 files)
- Create: `content/dashboard.py` (verbatim from infra/creator_dashboard.py, 228L)
- Create: `content/logic_check.py` (verbatim from infra/creator_logic_check.py, 114L)
- Modify: 2 shim files

**T2c**: mode.py (shim) + models.py + 2 shims (4 files)
- Create: `content/mode.py` (SHIM — `from lingwen_creator.shared.mode import *  # noqa: F403`,per §2.3)
- Create: `content/models.py` (verbatim from infra/creator_models.py, 61L)
- Modify: 2 shim files (`infra/creator_mode.py` already T1, `infra/creator_models.py` now)

**T2d**: preferences.py + ui_profile.py + 2 shims (4 files)
- Create: `content/preferences.py` (verbatim from infra/creator_preferences.py, 116L)
- Create: `content/ui_profile.py` (verbatim from infra/creator_ui_profile.py, 327L)
- Modify: 2 shim files

**T2 common**:
- intra-package imports (per plan §12.2): `from infra.creator_X import ...` → `from lingwen_creator.content.X import ...` (when target 已迁出)
- 保留 `from infra.persistence / infra.llm_service / infra.errors` 等不变
- `content/preferences.py` 需 import `from lingwen_creator.shared.mode import resolve_creator_settings` (T1 已迁)
- `content/dashboard.py` 需 import `from lingwen_creator.shared.mode import settings_from_project_config` (T1 已迁)
- test_content.py (≥5 tests, 覆盖 layout + 8 modules existence + intra-package import)

### 3.3 T3: Content DTOs (~15 DTOs) + TS codegen + tests (3 files)

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (add Content section, ~15 Pydantic models)
- Auto-generated: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts`
- Create: `packages/lingwen-shared/tests/test_content_dto.py` (≥10 tests)

**Content DTO list** (基于 spec §3.7 + routes/creator_core.py content endpoints):
- `CreatorOverviewResponse` (overview payload)
- `CreatorAgentPlanRequest`, `CreatorAgentPlanResponse`
- `CreatorBatchHistoryResponse`, `CreatorBatchHistoryExportRequest`
- `CreatorPreferencesResponse`, `CreatorPreferencesSaveRequest`
- `CreatorModelsResponse`
- `CreatorLogicCheckResponse`
- `CreatorChapterPreview`, `CreatorOutlineSaveRequest`, `CreatorBodySaveRequest`
- `CreatorUiProfileState`, `CreatorUiProfileSaveRequest`
- `CreatorDashboardOverview`, `CreatorDashboardChapterPreview`

(15 DTOs total,per spec §3.7 "≥15 DTO")

**T3.1**: 写 `test_content_dto.py` failing test (RED, ≥10 tests)

**T3.2**: 验证 FAIL

**T3.3**: 创建 15 Pydantic models in `creator.py` (Content section)

**T3.4**: 验证 GREEN

**T3.5**: 跑 `tooling/contracts/generate.py` → TS codegen

**T3.6**: 跑 `tooling/contracts/zod_revalidate.py` → 0 drift

**T3.7**: commit

### 3.4 T4: content typed wrapper + URL contract tests (5 files per DP-06 precedent)

**Files:**
- Create: `apps/dashboard/src/api/content.ts` (≥10 wrapper functions)
- Modify: `packages/dashboard-contracts/src/shared/creator.ts` (re-export list update)
- Modify: `packages/dashboard-contracts/src/shared/index.ts` (re-export `content` per v16.2.1..3 T3 5-file precedent)
- Modify: `apps/dashboard/knip.json` (allowlist add content.ts)
- Create: `apps/dashboard/tests/unit/api/use-content-typed-wrapper.spec.ts` (URL contract tests)

**Content typed wrapper functions** (基于 creator_core.py content endpoints,~10 functions):
- `fetchCreatorOverview`
- `fetchCreatorModels`
- `fetchCreatorPreferences`, `saveCreatorPreferences`
- `fetchCreatorUiProfile`, `saveCreatorUiProfile`
- `fetchCreatorChapterPreview`, `saveCreatorChapterOutline`, `saveCreatorChapterBody`
- `runCreatorAgentPlan`, `fetchCreatorBatchHistory`, `exportCreatorBatchHistory`
- `runCreatorLogicCheck`

**T4.1**: 创建 `content.ts` (no zod — v16.2.1 lesson, zod 在 T5/CI drift,不是 wrapper layer)

**T4.2**: 更新 `dashboard-contracts/src/shared/creator.ts` re-export list (加 15 Content DTOs)

**T4.3**: 更新 `dashboard-contracts/src/shared/index.ts` (export content)

**T4.4**: 更新 knip.json allowlist

**T4.5**: 创建 `use-content-typed-wrapper.spec.ts` (≥10 URL contract tests,regression lock for `/api/` prefix v16.2.1 lesson)

**T4.6**: vue-tsc 0 + knip 0 验证

**T4.7**: commit

### 3.5 T5: routes imports migration + project_init/project_config cleanup (3 files)

**Files:**
- Modify: `apps/studio_api/routes/creator_core.py` (~10 content endpoint lazy imports migrated)
- Modify: `infra/project_init.py` (line 10: `from infra.creator_mode import ...` → `from lingwen_creator.shared.mode import ...`)
- Modify: `infra/project_config.py` (line 11: same migration)

**T5.1**: grep `creator_core.py` for `from infra.creator_` (line by line inspection)

**T5.2**: replace `from infra.creator_X import ...` → `from lingwen_creator.content.X import ...` (~10 sites)

**T5.3**: grep verify 0 `infra.creator_X` remaining in creator_core.py

**T5.4**: modify `infra/project_init.py` import

**T5.5**: modify `infra/project_config.py` import

**T5.6**: pytest + ruff verify

**T5.7**: commit

### 3.6 T6: onboarding T4 composables refactor + delete api/onboarding.js shim (6 files)

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding.js` (refactor 21 Creator-prefixed aliases → new typed wrapper names)
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useWizardSteps.ts`
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingProgress.ts`
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/useOnboardingNotifications.ts`
- Modify: `apps/dashboard/src/composables/useCreatorOnboarding/index.ts`
- Delete: `apps/dashboard/src/api/onboarding.js` (shim obsolete after composables refactor)

**T6.1**: grep composable files for legacy aliases (`fetchCreatorOnboarding*`, `saveCreatorOnboarding*`, etc.)

**T6.2**: per composable file, find/replace aliases → new typed wrapper names (e.g., `fetchCreatorOnboardingWizard` → `fetchOnboardingWizard`)

**T6.3**: update `index.ts` re-exports if needed

**T6.4**: vitest run composable tests (must pass with new imports)

**T6.5**: delete `apps/dashboard/src/api/onboarding.js`

**T6.6**: vue-tsc 0 + vitest 0 验证

**T6.7**: commit

### 3.7 T7: cross-subdomain cleanup (1-4 files)

**Files (TBD by grep):**
- 可能: `packages/lingwen-creator/src/lingwen_creator/{volume,onboarding,settings,shared}/*.py` 有 stale `infra.creator_X` imports
- 可能: `apps/studio_api/routes/{creator_volume,creator_onboarding,creator_settings}.py` 有 stale `infra.creator_*` imports

**T7.1**: grep `infra.creator_` across `packages/lingwen-creator/src/` + `apps/studio_api/routes/`

**T7.2**: per finding, migrate `infra.creator_X` → `lingwen_creator.{subdomain}.X` (per plan §12.2 intra-package rule)

**T7.3**: verify 0 stale imports remaining

**T7.4**: commit (if any changes; otherwise skip)

### 3.8 T8: validation gates + handoff doc (2 files)

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` (10 sections per v16.2.3 template)
- Modify: `CLAUDE.md` (bump v16.2.3 → v16.2.4)
- Modify: `.lingwen/architecture.yml` (creator module path update, content exports add, exports list complete)
- Modify: `.lingwen/migration_log.yml` (v16.2.4 entry add)

**T8.1**: 全套 verification gates (pytest, vitest, vue-tsc, knip, ruff, zod reverse, codegen)

**T8.2**: 写 handoff doc (10 sections: TL;DR + completed tasks + decisions + plan deviations + impact + lessons + carryover + verification + new tooling + commit timeline + closing notes)

**T8.3**: CLAUDE.md bump v16.2.3 → v16.2.4

**T8.4**: .lingwen/architecture.yml update

**T8.5**: .lingwen/migration_log.yml update

**T8.6**: commit + push to origin/master

---

## 4. Verification Gates

### 4.1 Per Sub-phase Gates (T1-T8 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| Backend tests (separated) | `/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_content.py -v` | ≥5 PASSED |
| | `/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_content_dto.py -v` | ≥10 PASSED |
| | `/home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_*.py -q` | baseline + N PASSED |
| Frontend tests | `cd apps/dashboard && pnpm vitest run tests/unit/api/use-content-typed-wrapper.spec.ts` | ≥10 PASSED |
| ruff | `ruff check packages/lingwen-creator/src/lingwen_creator/content/ packages/lingwen-creator/src/lingwen_creator/shared/` | 0 |
| vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 errors |
| knip | `pnpm exec knip` | 0 (allowlist 同步) |
| codegen | `/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py` | ts/creator.ts regenerated |
| zod reverse | `/home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py` | 0 drift |

### 4.2 v16.2.4 Final Gate (T8 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| shim file count | `ls infra/creator_*.py 2>&1 \| wc -l` | 35 (减少 1: creator_mode.py 变 shim — 不算减少,实际 count 不变;减少的是 onboarding forward-reference 的 noqa 注释) |
| | `grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` | 0 |
| | `grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py` | 0 |
| | `grep -cE "infra\.creator_mode" infra/project_init.py infra/project_config.py` | 0 |
| DTO coverage | content DTOs in `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` | 15 (Content section) |
| typed wrapper | `apps/dashboard/src/api/content.ts` | ≥10 functions |
| api/onboarding.js | `ls apps/dashboard/src/api/onboarding.js 2>&1` | not exist (deleted in T6) |
| Handoff doc | `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` | exists |

---

## 5. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| agent.py 598L verbatim copy 触 DP-06 | 中:T2 拆 4 commits vs 1 | 高 | T2a-d sub-commits,每 commit ≤4 files |
| shared/mode.py extraction 误改 internal logic | 高:settings_from_project_config 行为破坏 | 低 | T1 strict verbatim copy (no body changes),只调整 module-level docstring |
| onboarding forward-reference 关闭后行为变化 | 中:onboarding wizard 验证可能 fail | 低 | T1 + onboarding.py import 测试 (pytest test_onboarding.py 24 tests 应仍 pass) |
| composables refactor 触 vitest debt | 中:useOnboardingProgress.ts 测试失败 | 中 | T6 优先 vitest run composable tests 验证,再删 shim |
| infra/project_X migration 引发 settings 反向 regression | 中:project init flow 500 | 低 | T5 + pytest tests/infra/test_project_config.py + test_project_init.py 验证 |
| shared.check.py spec violation fix 误改 format_check_mode_banner | 高:check UI banner 错误 | 低 | T1 strict verbatim copy of mode logic,只改 import path |
| T7 cross-subdomain cleanup 触意外 file | 低 | 中 | T7 grep 限定范围 (packages/lingwen-creator/src/ + apps/studio_api/routes/),不触碰 apps/dashboard/ |
| Content DTO 字段命名与现有 Pydantic 不一致 | 中:zod fail | 中 | T3 test_content_dto.py RED-GREEN,字段 from existing routes/creator_core.py response_model |

---

## 6. Carryover to v16.2.5+

| 任务 | 阶段 | 来源 |
|---|---|---|
| **v16.2.5 export** | 5 files (common, docx, epub, publish, publish_adapters) | per plan §7 (renumbered) |
| **v16.2.6 memory** | 3 files (annotations, assets, query) | per plan §7 (renumbered) |
| **v16.2.7 cleanup** | 36 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality/onboarding) + 22 vitest debt + import-linter DP-01..06 | per plan §9 |
| **api/onboarding.js shim deletion** | ✓ T6 已删 (v16.2.4 carryover closed) |
| **onboarding T4-partial composables** | ✓ T6 已 refactor (v16.2.3 carryover closed) |
| **infra.creator_mode forward-reference** | ✓ T1 closed (onboarding.py 改 import lingwen_creator.shared.mode) |
| **shared/check.py spec violation** | ✓ T1 closed (check.py 改 import lingwen_creator.shared.mode) |
| **infra/project_X migration** | ✓ T5 closed (project_init + project_config 改 import) |
| **Pre-existing vitest debt** | 22 v16.2.1 `useCreatorVolumePlan*.spec.ts` failures + collection errors for `tests/infra` (Phase 125 module-namespace conflict) | v16.2.7 cleanup responsibility |
| **dashboard-contracts/src/shared/creator.ts explicit re-export list** | Each new DTO submodule needs explicit addition here (TS fragility noted in v16.2.3 handoff §5.1 lesson 3) | pattern for v16.2.5+ |
| **import-linter enforcement** | allowed_imports / forbidden_imports (DP-01..06) | v16.4 |
| **StoragePort enforcement** | DP-03 | v16.5 |
| **LLMServicePort enforcement** | DP-04 | v16.4 |
| **yoyo-migrations** | — | v16.5 |
| **workspace members exist gate** | — | v16.5 |

---

## 7. Lessons Applied (from v16.2.0..3)

| Lesson (from handoff) | v16.2.4 应用 |
|---|---|
| v16.2.1: hyphen name + underscore module 严格分离 | `lingwen-creator` (packaging) / `lingwen_creator` (Python module) |
| v16.2.1: DP-06 (≤4 files per commit) | T2 拆 T2a-d (4 commits × 4 files) |
| v16.2.1: T1 verbatim copy + intra-package import adjustment (per §12.2) | T2a-d verbatim copy + intra-package imports from lingwen_creator.{shared.mode, content.X} |
| v16.2.1: shim private name re-exports for test compat | T1 onboarding.py 改 import 时不删 `from lingwen_creator.onboarding.onboarding import *` — 只改 `from infra.creator_mode` → `from lingwen_creator.shared.mode` |
| v16.2.1: typed wrapper 无 zod | T4 content.ts 严格 no zod (zod 在 T5/CI drift,不是 wrapper layer) |
| v16.2.1: `/api/` prefix 不 in code | T4 URL contract regression lock 验证 ≥10 paths |
| v16.2.1: spec-violation carryover discipline | T1 explicit "shared/mode.py placement" decision documents the change |
| v16.2.2: T1a carve-out pattern for cross-task imports | T1 同时改 shared.check.py + onboarding.onboarding.py (4 files) — cross-task dependency 必须同 commit |
| v16.2.2: T3 DP-06 includes index.ts re-export | T4 5 files (content.ts + re-export + index.ts + knip + URL contract test) |
| v16.2.2: shim underscore re-exports added continuously | T1 onboarding.py `# noqa: F401  # v16.2.4 will replace` 注释删掉,改成正常 import |
| v16.2.2: DTO count budgets ~30% extra for nested types | T3 估算 15 DTOs (spec §3.7),实际可能 18-20 with nested helpers |
| v16.2.2: ALWAYS check function-body lazy imports after verbatim copy | T2a-d grep function-body 内部 import (per §12.1 rule 4) |
| v16.2.3: Legacy JS shim with backward-compat aliases pattern | T6 删除 api/onboarding.js shim,composables 改用新 typed wrapper names |
| v16.2.3: Shim count doesn't increase when migrating existing files to shim form | T1 creator_mode.py 变 shim 不增加 count (已存在) |
| v16.2.3: dashboard-contracts re-export chain fragility | T4 同步更新 dashboard-contracts/src/shared/creator.ts re-export list (15 Content DTOs) |
| v16.2.3: Top-level await import in shims unsafe | N/A (T6 直接 delete shim,不写新 shim) |
| v16.2.3: spec §2 import list completeness check before verbatim copy | T2a-d 严格按 spec §3.7 列的 8 files (实际 7 files verbatim + 1 mode.py shim) |
| v15.7.1: ruff `--add-noqa F403` 是 `__init__.py` star-import 标准 | T2a-d content/__init__.py star-imports + T1 infra/creator_mode.py + content/mode.py shim 都用 `# noqa: F403` |
| v15.7.1: `tests/__init__.py` 解决 pytest module-namespace | T2a-d `packages/lingwen-creator/tests/test_content.py` (沿用 v16.2.1 precedent) |
| v15.7.1: vis-network install regression | N/A (content 不依赖 vis-network) |
| v16.0: spec §2.4 依赖矩阵 → import-linter skeleton | v16.2.4 §2.6 更新依赖矩阵 (onboarding + content 加 lingwen_creator.shared.mode) |

---

## 8. Open Decisions

| Decision | Resolution | 影响 |
|---|---|---|
| **shared/mode.py vs content/mode.py** | shared/mode.py (per brainstorming Q1 decision) | 修复 shared/check.py spec violation |
| **agent.py 598L 单文件 vs 拆分** | 单文件 (per brainstorming Q2 decision) | T2 拆 T2a-d |
| **infra/creator_mode.py shim vs delete** | 变 shim (per brainstorming Q3 decision) | 与 v16.2.1..3 shim pattern 一致 |
| **8 vs 4 vs 15 commits** | 11 commits (T1 + T2a-d + T3-T8,per brainstorming Q4 decision) | 与 v16.2.1 (14) + v16.2.2 (20) + v16.2.3 (10) 平均相当 |
| **是否也做 volume T4 carryover** | 否 (本 phase 仅 onboarding T4 + content) | volume T4 carryover 留到 v16.2.7 cleanup |
| **是否在 T7 加 vol/onboarding/settings 的 content forward imports 修复** | 是 (per T7 plan) | cross-subdomain cleanup 顺手做 |
| **Content composables (19 个) 是否在 v16.2.4 全 refactor** | 否 — typed wrapper 创建 (T4) + composables refactor deferred to v16.2.7 (per spec §3.7 19 composables 太多,本 phase 只 close content typed wrapper + onboarding T4) | 减少 v16.2.4 scope,加速闭环 |

---

**下一步**: invoke writing-plans skill 创建 `docs/superpowers/plans/2026-08-28-phase-126-v16-2-4-content-plan.md`。
