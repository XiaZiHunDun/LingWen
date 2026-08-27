# Phase 126 v16.2 — Creator 6-Subdomain 拆分 设计方案

> **状态**: ✅ 设计已批准,待 writing-plans (Phase 126 v16.2)
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-124-target-architecture-design.md` (§6.3 v16.2 范围)
> - `docs/superpowers/handoffs/2026-08-27-phase-124-v16-1-handoff.md` (§6 carryover — v16.2 starter entry)
> - `.lingwen/architecture.yml` (`v16_2_creator_split` 即将登记)
> **前置**:
> - v16.0 闭环 (`37718276`) — uv workspaces + turbo + import-linter skeleton
> - v16.1 闭环 (`e6927159`) — lingwen-shared 包 + 12 DTO + TS codegen + zod CI
> - v15.7.1 baseline cleanup (`13db74f9`)
> **决策**:
> - Q1=A — 6 subdomains = Memory / Onboarding / Volume / Content / Export / Settings
> - Q2=A — Strangler Fig migration,v16.2.1..6 逐 subdomain 迁
> - Q3=A — 顺序 = memory → settings → export → volume → onboarding → content (依赖 bottom-up)
> - Q4=A — Shim re-export pattern (旧 `infra/creator_*.py` 变 1-line re-export shim)
> - Q5=B — Routes 留在 `apps/studio_api/routes/` (thin shim),不搬到 `packages/lingwen-creator/api/`
> - Q6=A — Shared infra (`creator_revision.py` + `creator_check.py`) → `lingwen_creator/shared/`
> - Q7=A — Tests inside package (`packages/lingwen-creator/tests/`)
> - Q8=B — v16.2.1..6 全量加 creator typed wrappers + composable refactor (不全推到 v16.3+)

---

## 0. TL;DR

**v16.2 = 把 36 个 `infra/creator_*.py` 平铺模块按 DDD bounded context 拆为 6 个 subdomains,迁到新 `packages/lingwen-creator/` 包**。同时为 creator 加 typed wrappers (DTO in `lingwen-shared` + TS codegen + `apps/dashboard/src/api/<subdomain>.ts` + 35 composables 切换)。

**6 subdomains**(基于 domain 边界 + 共享 util 分析):

| Subdomain | Files | LOC | 主要职责 |
|---|---|---|---|
| Memory | 3 | 511 | 创作者知识库(RAG: assets/annotations/query) |
| Settings | 3 | 2277 | 配置(pillars/global_outline docs + history + merge preferences) |
| Export | 5 | ~1000 | 内容输出(docx/epub/publish platforms) |
| Volume | 6 | 3224 | 卷规划 + 模板 + 审批 + 分享 |
| Onboarding | 9 | 2468 | 用户引导(wizard + digest + notifications + email/webhook) |
| Content | 10 | 3376 | 核心创作循环(agent + dashboard + batch + models + preferences + revision + ui_profile + check + logic_check) |
| **Shared** | (2 独立) | ~700 | `creator_revision.py` (CreatorDocConflictError) + `creator_check.py` (load/apply_defaults/format_banner) |

**Shared** 独立于 6 subdomains,作为 cross-subdomain utility(由 Content 重度使用)。

**迁移策略 = Strangler Fig**,因 DP-06 enforcement 从 v16.2 起生效("每个 phase 代码改动收敛到自己 context 内 ≤4 文件"):
- v16.2.0 = `packages/lingwen-creator/` skeleton + shared/ 迁移 (4 files)
- v16.2.1 = memory 迁移 (3 files + DTO + typed wrapper + 3 composables)
- v16.2.2 = settings 迁移 (3 files + DTO + typed wrapper + 1 composable)
- v16.2.3 = export 迁移 (5 files + DTO + typed wrapper + 2 composables)
- v16.2.4 = volume 迁移 (6 files + DTO + typed wrapper + 6 composables)
- v16.2.5 = onboarding 迁移 (9 files + DTO + typed wrapper + 4 composables)
- v16.2.6 = content 迁移 (10 files + DTO + typed wrapper + 19 composables)
- v16.2.7 = final gate(import count = 0,所有 118 consumer 走 `lingwen_creator.*`)

**全量 4 周**(每 sub-phase 半天到 1 天)。最后 1 sub-phase (content) 最大,因为 import graph 最深。

---

## 1. 背景与动机

### 1.1 当前 creator 域状态 (evidence-based)

| 维度 | 数据 |
|---|---|
| Python 模块 | 36 个 `infra/creator_*.py`,9220 LOC;最大 `creator_merge_preferences.py` (1355L) + `creator_volume_templates.py` (1022L) |
| Routes | 4 files:`creator_core.py` (22 endpoints) + `creator_onboarding.py` (24) + `creator_volume.py` (24) + `creator_settings.py` (30) = ~100 endpoints |
| Composables | 35 个 `useCreator*.{js,ts}` (useCreatorAgent/Onboarding/Settings/VolumePlan/Write/Page 等) |
| Consumer files | 118 个文件 `from infra.creator_*` import (counted via `grep -rl "from infra.creator"` in `apps/` + `packages/`) |
| Frontend pages | `ProducePage.vue`, `CreatorPage.vue`, `StudioPage.vue`, `OverviewPage.vue` 引用 creator |

**现状问题** (target architecture design §1.2.天花板 #2):
- 36 个 `infra/creator_*.py` 平铺在 `infra/` 根,**没有子包**(历史原因:`infra/creator/` 子目录只有空 `__init__.py`,已在 v16.1 session 前 untracked 删除)
- 改一个 creator feature 通常动 ≥5 文件,分布在 3 个不同目录
- Frontend composables 全部 raw fetch,**没有 typed wrapper**(v16.1 只为 world/workspace/quality 加了 3 个 starter)

### 1.2 v15.x 已经观察的"现状好 seam"

| Seam | 位置 | 价值 |
|---|---|---|
| RoutesContext dataclass 注入 | `apps/studio_api/routes/ctx.py:35-46` | 路由层已与 business logic 解耦,thin shim 化零成本 |
| creator_revision 的 CreatorDocConflictError | `infra/creator_revision.py:1` | 已被 settings_docs + volume_plan 路由 catch,迁移时需保兼容 |
| batch_runner.enrich_batch_history_job | `infra/creator_batch_history.py` + `studio_batch_runner` | 已是 `infra.creator_X` + `infra.studio_*` 的 cross-module 调用样板 |
| 35 个 composables 大多 1 composable ↔ 1 routes namespace | `useCreatorOnboarding` ↔ `routes/creator_onboarding.py` | 已经天然 subdomain 对齐,迁移收益清晰 |

### 1.3 为什么必须现在做(而非推迟到 v16.4+)

| 推力 | 后果 |
|---|---|
| **DP-05 enforcement v16.2** ("新增 feature 必须先建或选 context") | 没有 v16.2,后续 onboarding/volume 新 feature 仍会扩散到 `infra/` 根 |
| **DP-06 enforcement v16.2** ("每个 phase ≤4 文件") | 当前 creator 改 1 feature 必跨 DP-06 上限;不拆无法合规 |
| **typed wrapper carryover from v16.1** | v16.1 T4 note:"composables 仍走 raw fetch — v16.2 creator 拆分时切换" |
| **routes 文件已达 4 个 × 100 endpoints** | creator_volume.py 767 行,creator_settings.py 624 行,creator_onboarding.py 403 行;继续堆必崩 |

---

## 2. 目标架构

### 2.1 6 Subdomains (DDD bounded contexts)

每个 subdomain 是 vertical slice (domain logic + storage access + DTOs + typed wrappers),对外有清晰公共 API。

```
lingwen_creator/
├── __init__.py              # re-export 子 modules
├── shared/                  # 跨 subdomain utils
│   ├── revision.py          # CreatorDocConflictError + content_revision
│   └── check.py             # load_creator_check_context + apply_creator_check_defaults + format_check_mode_banner
├── memory/                  # v16.2.1 (3 files)
│   ├── annotations.py       # upsert_memory_annotation
│   ├── assets.py            # creator_memory_assets_payload
│   └── query.py             # creator_memory_query
├── settings/                # v16.2.2 (3 files)
│   ├── docs.py              # creator_settings_docs_payload + save_creator_settings_docs
│   ├── history.py           # settings_history_payload + restore_settings_snapshot
│   └── merge_preferences.py # load/export/import + preset-packages + conflicts + factory ops
├── export/                  # v16.2.3 (5 files)
│   ├── common.py            # 共用导出 util
│   ├── docx.py              # build_creator_docx_bytes
│   ├── epub.py              # build_creator_epub_bytes
│   ├── publish.py           # submit_creator_publish + list_publish_platforms + history
│   └── publish_adapters.py  # publish adapter impls
├── volume/                  # v16.2.4 (6 files)
│   ├── plan.py              # volume_plan_payload + save_volume_plan + merge/split/diff
│   ├── plan_share.py        # 分享逻辑
│   ├── pulse.py             # creator_volume_pulse
│   ├── summary.py           # write_volume_summary
│   ├── templates.py         # list/save/delete/rename/version/changelog/rollback + factory ops
│   └── template_approvals.py# approval lifecycle (submit/approve/reject/transfer/snapshot diff)
├── onboarding/              # v16.2.5 (9 files)
│   ├── onboarding.py        # wizard payload + progress + dismiss/collapse
│   ├── autodetect.py        # 自动检测进度
│   ├── digest_background.py # 后台 digest task
│   ├── digest_schedule.py   # schedule config + dead-letter + retry + dispatch
│   ├── email.py             # email config
│   ├── notifications.py     # 通知列表 + ack
│   ├── progress.py          # onboarding progress state
│   ├── webhook.py           # webhook config
│   └── diff_collab.py       # diff collab notes (从 onboarding 主 wizard 独立)
└── content/                 # v16.2.6 (10 files)
    ├── agent.py             # run_creator_agent_plan + iter_creator_agent_plan_stream
    ├── batch_history.py     # enrich_batch_history_job
    ├── check.py             # (留 content? 见 §2.4 决策)
    ├── dashboard.py         # creator_overview + chapter preview + save outline/body
    ├── logic_check.py       # run_creator_logic_check
    ├── mode.py              # creation mode switch
    ├── models.py            # list_creator_models_payload
    ├── preferences.py       # creator_preferences_payload + load/save
    ├── revision.py          # (留 content? 见 §2.4 决策)
    └── ui_profile.py        # UI profile state
```

### 2.2 Package Layout (uv workspace member)

```
packages/lingwen-creator/
├── pyproject.toml                    # uv workspace member (hyphen name, v16.0 lesson)
├── src/
│   └── lingwen_creator/              # underscore module (v16.0 lesson)
│       ├── __init__.py               # re-export from .memory / .settings / etc.
│       ├── shared/
│       ├── memory/
│       ├── settings/
│       ├── export/
│       ├── volume/
│       ├── onboarding/
│       └── content/
├── contracts/                        # Pydantic DTOs (per sub-phase, incremental)
│   ├── python/
│   │   ├── __init__.py
│   │   ├── memory.py                 # v16.2.1+
│   │   ├── settings.py               # v16.2.2+
│   │   ├── export.py                 # v16.2.3+
│   │   ├── volume.py                 # v16.2.4+
│   │   ├── onboarding.py             # v16.2.5+
│   │   └── content.py                # v16.2.6+
│   └── ts/                           # auto-generated by tooling/contracts/generate.py
│       ├── shared.ts
│       ├── memory.ts
│       ├── settings.ts
│       ├── export.ts
│       ├── volume.ts
│       ├── onboarding.ts
│       └── content.ts
└── tests/
    ├── test_lingwen_creator_layout.py  # v16.2.0 (5 tests, 仿 v16.1 T1)
    ├── test_shared_revision.py         # v16.2.0
    ├── test_shared_check.py            # v16.2.0
    ├── test_memory.py                  # v16.2.1+
    ├── test_settings.py                # v16.2.2+
    ├── test_export.py                  # v16.2.3+
    ├── test_volume.py                  # v16.2.4+
    ├── test_onboarding.py              # v16.2.5+
    └── test_content.py                 # v16.2.6+
```

### 2.3 Frontend Layout

```
apps/dashboard/src/
├── api/
│   ├── world.ts                # v16.1 (existing)
│   ├── workspace.ts            # v16.1 (existing)
│   ├── quality.ts              # v16.1 (existing)
│   ├── memory.ts               # v16.2.1 (NEW)
│   ├── settings.ts             # v16.2.2 (NEW)
│   ├── export.ts               # v16.2.3 (NEW)
│   ├── volume.ts               # v16.2.4 (NEW)
│   ├── onboarding.ts           # v16.2.5 (NEW)
│   └── content.ts              # v16.2.6 (NEW)
└── composables/
    ├── useCreatorMemory.{js,ts}              # v16.2.1 (refactor)
    ├── useCreatorSettings.{js,ts}            # v16.2.2
    ├── useCreatorExportDocx.{js,ts}          # v16.2.3
    ├── useCreatorExportEpub.{js,ts}          # v16.2.3
    ├── useCreatorPublish.{js,ts}             # v16.2.3
    ├── useCreatorVolumePlan.{js,ts}          # v16.2.4
    ├── useCreatorVolumePlanDiff.{js,ts}      # v16.2.4
    ├── useCreatorVolumePlanTemplates.{js,ts} # v16.2.4
    ├── useCreatorOnboarding.{js,ts}          # v16.2.5
    ├── useCreatorOnboardingDigest.{js,ts}    # v16.2.5
    ├── useCreatorAgent.{js,ts}               # v16.2.6
    ├── useCreatorBatchHistory.{js,ts}        # v16.2.6
    ├── useCreatorModeGuide.{js,ts}           # v16.2.6
    └── useCreatorWrite*.{js,ts}              # v16.2.6 (Write, WriteWorkbench, etc.)
```

### 2.4 Per-Subdomain 依赖矩阵

| Subdomain | 允许 import | 禁止 import |
|---|---|---|
| shared | `infra.persistence`, `infra.project_config`, `infra.errors` | 其他 subdomains, `infra.creator_X` |
| memory | `infra.persistence`, `lingwen_creator.shared` | 其他 subdomains, `infra.creator_X` |
| settings | `infra.persistence`, `lingwen_creator.shared` | 其他 subdomains, `infra.creator_X` |
| export | `infra.persistence`, `lingwen_creator.shared`, `infra.project_config` | 其他 subdomains (除 settings 共享 template_approvals? 见下) |
| volume | `infra.persistence`, `infra.paths`, `infra.project_config`, `lingwen_creator.shared` | 其他 subdomains (除 settings 文档交互?) |
| onboarding | `infra.persistence`, `lingwen_creator.memory` (cross-ref annotation) | settings / volume / content(避免循环依赖) |
| content | `infra.persistence`, `infra.llm_service`, `lingwen_creator.shared`, `lingwen_creator.memory` | settings / volume / onboarding / export |

**注意**:`creator_check.py` 和 `creator_revision.py` 已被规划在 `shared/`。具体 decision:

- `shared.revision.CreatorDocConflictError` — 由 settings/docs + volume/plan + volume/templates 抛 → 路由层 catch → HTTPException(409)。放在 `shared/` 是 cross-subdomain utility。
- `shared.check` — `format_check_mode_banner(ProjectConfig, CreatorSettings)` 是 composition helper,实际只被 content/agent 用。**Decision**:放 `shared/` (per Q6=A),即便目前主要消费方是 content。这是为 future-proof(其他 subdomain 加 check banner 时不需要 import content)。

---

## 3. 迁移计划 (Strangler Fig)

### 3.1 v16.2.0 — Skeleton + shared migration

| 任务 | 文件 |
|---|---|
| 1. 加 `packages/lingwen-creator/` 到 root `pyproject.toml` `[tool.uv.workspace]` | `pyproject.toml` |
| 2. 建 `packages/lingwen-creator/pyproject.toml` (hatchling + underscore module) | `packages/lingwen-creator/pyproject.toml` |
| 3. 建 `packages/lingwen-creator/src/lingwen_creator/__init__.py` + `shared/__init__.py` + `shared/{revision,check}.py` | `packages/lingwen-creator/src/lingwen_creator/__init__.py`, `shared/__init__.py`, `shared/revision.py`, `shared/check.py` |
| 4. 移 `infra/creator_revision.py` + `infra/creator_check.py` 内容到 `shared/` | `infra/creator_revision.py` → 1-line shim `from lingwen_creator.shared.revision import * # noqa: F403`;`infra/creator_check.py` 同 |
| 5. 加 `test_lingwen_creator_layout.py` (5 tests, 仿 v16.1 T1) | `packages/lingwen-creator/tests/test_lingwen_creator_layout.py` |
| 6. 加 `test_shared_revision.py` + `test_shared_check.py` (各 ≥2 tests) | `packages/lingwen-creator/tests/test_shared_{revision,check}.py` |

**验证门**:uv sync OK + pytest 3758+10 = ≥3768 + ruff 0 + knip 0 + vue-tsc 0。

### 3.2 v16.2.1 — Memory subdomain

| 任务 | 文件 |
|---|---|
| 1. 加 `lingwen_creator/memory/` 包 | `packages/lingwen-creator/src/lingwen_creator/memory/{__init__,annotations,assets,query}.py` |
| 2. 移文件:`infra/creator_memory_annotations.py` → `memory/annotations.py`(改内部 import 用 `lingwen_creator.shared` 而非 `infra.creator_revision`) |  |
| 3. 移 `infra/creator_memory_assets.py` → `memory/assets.py` |  |
| 4. 移 `infra/creator_memory_query.py` → `memory/query.py` |  |
| 5. 3 个旧 `infra/creator_memory_*.py` 变 shim (1-line re-export) |  |
| 6. 加 DTO `packages/lingwen-shared/src/lingwen_shared/contracts/python/memory.py`(≥5 DTO:MemoryAsset, MemoryAnnotation, MemoryQueryRequest/Response, MemoryAssetsResponse) | `packages/lingwen-shared/src/lingwen_shared/contracts/python/memory.py` |
| 7. 跑 `uv run python tooling/contracts/generate.py` 生成 TS |  |
| 8. 加 typed wrapper `apps/dashboard/src/api/memory.ts`(≥3 function: getMemoryAssets, upsertMemoryAnnotation, queryMemory) |  |
| 9. 加 frontend re-export shim `packages/dashboard-contracts/src/shared/memory.ts` |  |
| 10. Refactor `useCreatorMemory.*` composables 用 typed wrapper | `apps/dashboard/src/composables/useCreatorMemory*` |
| 11. 更新 `apps/studio_api/routes/creator_core.py` 的 3 个 memory routes 改 import (`from infra.creator_memory_X` → `from lingwen_creator.memory.X`) | `apps/studio_api/routes/creator_core.py` |
| 12. knip.json allowlist 加 memory.ts + lingwen_creator.memory |  |
| 13. `packages/lingwen-creator/tests/test_memory.py` (≥3 tests) |  |

**验证门**:同上 + 新增 Memory DTO 的 zod CI 不 drift。

### 3.3 v16.2.2 — Settings subdomain

类似 v16.2.1,3 Python files + DTO (CreatorSettingsDocsResponse/SaveRequest, CreatorSettingsHistoryEntry, MergePreferenceEntry, MergePresetPackage 等 ≥8 DTO) + typed wrapper + 1 composable (`useCreatorSettings`) + routes 改 import (`creator_settings.py` 30 endpoints)。

### 3.4 v16.2.3 — Export subdomain

5 files + DTO (CreatorDocxExportRequest, CreatorEpubExportRequest, CreatorPublishRequest/Entry/Platform/History, ≥6 DTO) + typed wrapper + 3 composables (`useCreatorExportDocx`, `useCreatorExportEpub`, `useCreatorPublish`) + routes 改 import (`creator_core.py` 中的 export/publish routes)。

### 3.5 v16.2.4 — Volume subdomain

6 files + DTO (CreatorVolumePlanEntry/Response/SaveRequest/MergeRequest/SplitRequest, CreatorVolumeTemplateInfo, ≥10 DTO — 最大 domain) + typed wrapper + 6 composables (`useCreatorVolumePlan`, `useCreatorVolumePlanDiff`, `useCreatorVolumePlanMergeSplit`, `useCreatorVolumePlanTemplates`, `useCreatorVolumePulse`, `useCreatorVolumeSummary`) + routes 改 import (`creator_volume.py` 24 endpoints + `creator_core.py` 的 volume-plan/diff + volume-summary/generate)。

### 3.6 v16.2.5 — Onboarding subdomain

9 files + DTO (CreatorOnboardingResponse/Progress, CreatorOnboardingNotification, CreatorOnboardingDigestScheduleConfig, CreatorOnboardingWebhookConfig, CreatorOnboardingEmailConfig, CreatorDiffCollabNotes, ≥10 DTO) + typed wrapper + 4 composables (`useCreatorOnboarding`, `useCreatorOnboardingDigest`, `useCreatorOnboardingNotifications`, `useCreatorOnboardingProgress`) + routes 改 import (`creator_onboarding.py` 24 endpoints)。

### 3.7 v16.2.6 — Content subdomain

10 files (最大) + DTO (CreatorOverviewResponse, CreatorAgentPlanRequest/Response, CreatorBatchHistoryResponse/Export, CreatorMemoryQueryRequest/Response, CreatorPreferencesResponse/SaveRequest, CreatorModelsResponse, CreatorLogicCheckResponse, CreatorChapterPreview/OutlineSaveRequest/BodySaveRequest, ≥15 DTO) + typed wrapper + 19 composables (`useCreatorAgent`, `useCreatorBatchHistory`, `useCreatorModeGuide`, `useCreatorPage*`, `useCreatorPulse`, `useCreatorProductTools`, `useCreatorWorkspace`, `useCreatorWrite*`, `useCreatorWriteWorkbench`, `useCreatorSettings` (preferences 部分), 等) + routes 改 import (`creator_core.py` 22 endpoints 中除 memory/export/volume 部分,余下全 content)。

### 3.8 v16.2.7 — Final gate

| 任务 | 命令 |
|---|---|
| 1. 验证 `from infra.creator_*` 在 `apps/` + `packages/` 中除 shim 文件外为 0 | `grep -rl "from infra\.creator_" --include="*.py" apps/ packages/ \| grep -v "infra/creator_.*\.py"` |
| 2. 验证 shim 文件仍然 re-export 全部原 symbols | 跑现有 integration tests,确认 0 regression |
| 3. 删除 36 个 shim 文件 (`infra/creator_*.py`),改 routes composables import | 36 个 shim 删除 + 1 commit |
| 4. 更新 `.lingwen/architecture.yml`:`creator` module 移到 `packages/lingwen-creator/` | `module_boundaries.creator.path: packages/lingwen-creator/` |
| 5. 更新 `infra/__init__.py` 注释(如果有 creator 相关) |  |
| 6. knip 全清(allowlist 仍需要,但确保 typed wrappers 都在引用) |  |

**v16.2 final gate**(必过):
- `pytest tests/ packages/lingwen-creator/tests/ -q` ≥3768 tests,0 regression
- `pnpm vitest run --reporter=dot` ≥1731 + 35 composables 切换测试 = ≥1766,0 regression
- `ruff check .` 0
- `pnpm exec vue-tsc --noEmit` 0
- `pnpm exec knip` 0
- `uv run python tooling/contracts/generate.py` 生成 7 ts files (shared + 6 subdomains)
- `uv run python tooling/contracts/zod_revalidate.py` 0 drift

---

## 4. Backwards Compatibility (Shim Re-export Pattern)

### 4.1 Shim Pattern

每个迁移后,旧 `infra/creator_*.py` 变成 1-line shim:

```python
# infra/creator_memory_assets.py (after v16.2.1)
from lingwen_creator.memory.assets import *  # noqa: F403
```

**原因**:
- 118 个 consumer 文件继续 work,**0 consumer 改动**
- 允许 incremental migration(consumer 可以择机切换到 `from lingwen_creator.memory.assets import ...`,非强制)
- v16.2.7 最终一次性清理 shim

### 4.2 已知 Trade-off

| Pro | Con |
|---|---|
| 0 consumer file 改动 | `infra/` 残留 36 个 shim 文件(直到 v16.2.7) |
| 与 v15.x baseline pattern 一致 (`from infra.creator_X import *` 仍在 work) | Star-import (F403) 需要 noqa;knip 会警告未使用 symbol |
| TDD-driven 增量迁移 | 测试需要 fixture-aware,确保 `import infra.creator_X` 与 `import lingwen_creator.X` 返回相同 module |

### 4.3 与 v16.0 Lesson 沿用

- v16.0 lesson "infra/__init__.py 已是 thin shell,不再 import 子模块" — 36 个 shim 文件存在 `infra/` 根,但 `infra/__init__.py` 不会 import 它们(consumer 自己 `from infra.creator_X import ...`)
- v16.0 lesson "hyphen name + underscore module 严格分离" — `lingwen-creator` (packaging) / `lingwen_creator` (Python module)
- v16.0 lesson "uv sync 不验证 member 目录存在" — `test_lingwen_creator_layout.py` 显式 5 tests gate

---

## 5. Data Flow (Memory Subdomain 示例)

### 5.1 Request path (无变化,v16.2 是 module 搬家,不动 IO)

```
Browser → Vue component (CreatorPage.vue)
  → composable useCreatorMemory.js
    → apps/dashboard/src/api/memory.ts (typed wrapper, zod validate)
      → HTTP GET /api/creator/memory-assets
        → apps/studio_api/routes/creator_core.py:creator_memory_assets_get
          → lingwen_creator.memory.assets:creator_memory_assets_payload(project)
            → infra.persistence (read .state/creator_memory.json)
 → Pydantic CreatorMemoryAssetsResponse → JSON → zod validate → typed ref
```

### 5.2 Backward-compat during transition

```
infra.creator_memory_assets.py (shim)
  → from lingwen_creator.memory.assets import *
 → → 旧 caller (e.g., scripts/cli) 不变,继续 work
```

### 5.3 Storage

- 全部保留现有 IO 路径(`.state/*.json` 文件 + SQLite v16.1+ 扩展点)
- **v16.2 不动 storage layer**(DP-03 enforcement 在 v16.5)
- Subdomain 内模块直接 import `infra.persistence` (当前 path),v16.5 时换 `StoragePort`

---

## 6. Error Handling

| 错误类型 | 现有处理 | v16.2 行为 |
|---|---|---|
| `ValidationError` | `infra.errors.ValidationError` | **不动** (in `infra/errors.py`,已是 thin shell) |
| `CreatorDocConflictError` | `infra.creator_revision.CreatorDocConflictError` | 重导出到 `lingwen_creator.shared.revision.CreatorDocConflictError`,旧 import path 仍 work via shim |
| `ValueError` | 路由 raise HTTPException(400) | **不动** |
| `HTTPException(404/409)` | 路由层直接 raise | **不动** |

**v16.2 不动错误基类** — 那是 v16.4 LLMServicePort enforcement 的范围。

---

## 7. Testing Strategy

| 测试类型 | 位置 | 触发时机 | 数量(预计) |
|---|---|---|---|
| Layout tests | `packages/lingwen-creator/tests/test_lingwen_creator_layout.py` | v16.2.0 | 5 |
| Shared unit tests | `test_shared_revision.py` + `test_shared_check.py` | v16.2.0 | 4 (2 each) |
| Subdomain unit tests | `test_<subdomain>.py` | 每个 sub-phase (≥3 per subdomain) | 18 (3 × 6) |
| Integration tests | `tests/apps/studio_api/test_creator_routes.py` (existing) | 现有(验证 route handler 调 lingwen_creator.* work) | 不变 |
| Frontend unit tests | `useCreator*.spec.{js,ts}` (existing + 新) | composable 切换时加 | ≥35 (1 per composable) |
| knip check | `apps/dashboard/knip.json` allowlist | 每个 sub-phase 同步 | 不变 |

**TDD 模式**(沿用 v16.0/v16.1):
- Subdomain 迁第一个 file: RED (test failure) → GREEN (move + import) → REFACTOR (typed wrapper + composable)
- 每个 sub-phase ≥3 commits (move file + add DTO/codegen + typed wrapper/composable)

**Lessons applied from v15.x**:
- v15.7.1: pytest test fixtures must NOT depend on global state — 每个 subdomain test 用 `tmp_path` fixture
- v18.0 计划: vitest + globalThis stubs for auto-import functions
- v17.6 (proposed): `@/` alias for composable imports(不要 `../../../../` 相对路径)

---

## 8. Verification Gates

### 8.1 Per Sub-phase Gates (7 gates 每次必过)

| Gate | 命令 | 期望 |
|---|---|---|
| uv sync | `uv sync` | 0 errors |
| Backend tests | `pytest tests/ packages/lingwen-creator/tests/ -q` | baseline + ≥N per sub-phase |
| Frontend tests | `pnpm vitest run --reporter=dot` | 1731 + ≥N per sub-phase |
| ruff | `ruff check .` | 0 |
| vue-tsc | `pnpm exec vue-tsc --noEmit` | 0 |
| knip | `pnpm exec knip` | 0 (allowlist 跟 typed wrappers 同步) |
| codegen | `uv run python tooling/contracts/generate.py` | ts/<subdomain>.ts 生成 |
| zod reverse | `uv run python tooling/contracts/zod_revalidate.py` | 0 drift |

### 8.2 v16.2 Final Gate (v16.2.7 必过)

| Gate | 命令 | 期望 |
|---|---|---|
| import count | `grep -rl "from infra\.creator_" --include="*.py" apps/ packages/ \| grep -v "infra/creator_.*\.py" \| wc -l` | 0 |
| shim file count | `ls infra/creator_*.py \| wc -l` | 36 (过渡期,v16.2.7 最后清理) |
| DTO + typed wrapper coverage | `ls packages/dashboard-contracts/src/shared/*.ts \| wc -l` | ≥9 (3 existing + 6 new) |
| migration_log entry | `.lingwen/migration_log.yml` has v16.2.0..v16.2.7 entries | ✓ |

---

## 9. Lessons Applied (from v16.0/v16.1)

| Lesson (from handoff) | v16.2 应用 |
|---|---|
| v16.0: hyphen name + underscore module | `lingwen-creator` (packaging) / `lingwen_creator` (Python module) |
| v16.0: uv sync 不验证 member 存在 | `test_lingwen_creator_layout.py` (5 tests,仿 v16.1 T1) |
| v16.0: empty `[tool.ruff]` override root | `packages/lingwen-creator/pyproject.toml` 不加 ruff section,继承 root |
| v16.1: hand-rolled JSON Schema → TS converter (avoid pydantic-to-typescript version drift) | 沿用 `tooling/contracts/generate.py`,不切回 library |
| v16.1: `ChapterDTO.id optional` TDD-driven 修正 vs spec 冲突 | 每个 DTO 写 test first (`test_<subdomain>_dto.py`),TDD discipline 优先于 plan spec |
| v16.1: knip allowlist 加 typed wrapper 时同步 | 每个 sub-phase 加 typed wrapper 时立即更新 `apps/dashboard/knip.json` |
| v16.1: CI `setup-uv` cache 必加 | 沿用 v16.1 T6 fix,CI cache 已有 |
| v16.1: `sleep N` → readiness poll | v16.2 不涉及新 CI job,沿用 v16.1 zod-revalidate job |
| v15.7.1: ruff `--add-noqa F403` 是处理 `__init__.py` star-import 的标准 | shim 文件用 `# noqa: F403` |
| v15.7.1: `tests/__init__.py` 是 pytest module-namespace 冲突的根治 | `packages/lingwen-creator/tests/__init__.py` + `tests/{subdomain}/__init__.py` (如需要) |
| v18.0 (proposed): `@/` alias for composable imports | composable import `api/<subdomain>.ts` 用 `@/api/<subdomain>` 别名 |
| v15.x: 每个 phase ≤4 files (DP-06) | Strangler Fig + sub-phase 拆分,每 phase ≤4 files |

---

## 10. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Star-import shim 被 knip 误报为 unused | 中:knip CI fail | 高 | 每个 typed wrapper 立即加 knip allowlist;shim 文件 allowlist "module re-export" |
| 118 consumer 文件 import path 在 v16.2.7 一次性切换时出现回归 | 高:routes 500 | 中 | v16.2.1..6 期间 shim 仍 work;v16.2.7 切换前跑 full integration tests |
| Content (10 files) 一次性切 composables 引发大量 changes | 中:PR review 困难 | 高 | v16.2.6 拆为 2-3 sub-commits (agent + dashboard + check/revision),每个 ≤4 files |
| Routes 改 import 时漏掉某个 endpoint | 中:某 route 500 | 中 | 每个 sub-phase routes 改 import 后立即 grep verify (`grep -n "from infra.creator_" routes/creator_*.py`) |
| DTO 字段命名与现有 Pydantic 不一致 | 中:前端 zod fail | 中 | TDD-driven DTO 测试 + zod reverse validation CI(已存在) |
| shared.revision 跨 subdomain 引用未来引发循环依赖 | 低 | 低 | import-linter 骨架(v16.0 已建)在 v16.4 enforcement 时启用;v16.2 只声明 allowed imports |
| v16.2 与 v16.3 (world + workspace) 并行时 workspace import lingwen_creator 引发冲突 | 低 | 极低 | workspace 当前不依赖 creator;v16.3 启动时再次 verify |
| 35 个 composables 切换在 6 个 sub-phase 内分布不均 | 低:PR 不均衡 | 中 | plan 阶段明确每 sub-phase composable 数量(v16.2.1=3, v16.2.5=4, v16.2.6=19) |

---

## 11. Carryover (deferred to v16.3+ / v16.4+)

| 任务 | 阶段 |
|---|---|
| import-linter enforcement(allowed_imports / forbidden_imports §2.4) | v16.4 |
| pydantic-to-typescript 库真实集成(替换 hand-rolled converter) | v16.4 可选 |
| StoragePort enforcement(DP-03) | v16.5 |
| yoyo-migrations | v16.5 |
| workspace members exist gate(v16.0 lesson) | v16.5 |
| **world + workspace 拆分 + application service 层提取** | v16.3 (与 v16.2 并行) |
| **LLMServicePort enforcement** | v16.4 |
| Shadcn/Tailwind composable UI refactor(独立 task) | v16.3+ (非本 spec 范围) |

---

## 12. Open Decisions (待 v16.2.6 之前再次确认)

| Decision | Option | 影响 |
|---|---|---|
| 是否保留 `creator_check.py` 在 `shared/` 或 `content/` | 当前决定:shared (per Q6=A) | 主要消费方是 content/agent;若 onboarding 加 check banner 则 shared 更合理 |
| `infra/creator/` 子目录(v16.1 已删空 `__init__.py`)是否需要在 v16.2.7 重建 | 当前决定:不重建,目录可保留为空 | clean removal |
| `creator_volume_pulse.py` 是否独立 subdomain 或归 volume/ | 当前决定:volume/plan_pulse.py (volume 子模块) | pulse 是 volume 的子概念 |

---

**下一步**: invoke writing-plans skill 创建 `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md`。