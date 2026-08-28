# Phase 126 v16.2.6 — Memory Subdomain 拆分 设计方案

> **状态**: 设计已定,进入 plan
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (母 spec)
> - `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-5-export-handoff.md` (前置 sub-phase 闭环 + 3 new lessons)
> **前置**: v16.2.5 export 闭环 (`7b7c7c18`)
> **下一步**: v16.2.7 cleanup (44 shims + typed wrapper `/api/` fix + import-linter + 22 vitest debt + 19 content composables)

---

## 0. TL;DR

**v16.2.6 = memory subdomain 拆分,Round 2 leaf 最后一个,也是 creator 6-subdomain 拆分的最后一个 sub-phase。**

3 files (430 LOC) → `packages/lingwen-creator/src/lingwen_creator/memory/`:

| infra 文件 | 行数 | 新路径 |
|---|---|---|
| `infra/creator_memory_annotations.py` | 100 | `memory/annotations.py` |
| `infra/creator_memory_assets.py` | 182 | `memory/assets.py` |
| `infra/creator_memory_query.py` | 148 | `memory/query.py` |

**Round 2 leaf,依赖模式最简单**:
- 所有跨子域依赖都已迁完 (content + settings),无 forward-reference
- 无 shared extraction、无 spec violation
- 3 endpoints / 7 DTOs / 3 typed wrapper funcs / 1 composable

---

## 1. 现状

### 1.1 依赖图

```
memory/annotations.py   → (stdlib only: json / datetime / pathlib / typing)
memory/assets.py        → content.dashboard (creator_overview)
                          settings.docs (creator_settings_docs_payload)
                          infra.studio_registry (StudioProject)        [保留 infra]
                          infra.memory_service (get_memory_gateway)    [保留 infra, 函数体 lazy]
                          memory.annotations (apply/load, 函数体 lazy)
                          content.preferences (load_creator_preferences, 函数体 lazy)
memory/query.py         → memory.assets (creator_memory_assets_payload)
                          content.preferences (load_creator_preferences)
                          infra.studio_registry (StudioProject)        [保留 infra]
                          infra.memory_service (get_memory_gateway)    [保留 infra, 函数体 lazy]
```

`infra.studio_registry` / `infra.memory_service` 不是 creator 子域,保持 infra import 不变 (与 v16.2.5 export/publish_adapters 一致)。

### 1.2 消费者

| 层 | 位置 | 数量 |
|---|---|---|
| Routes | `apps/studio_api/routes/creator_core.py:231/244/269` | 3 lazy imports |
| DTOs | `apps/studio_api/models/creator_settings.py:85-153` | 7 类 |
| Frontend API | `apps/dashboard/src/api/memory.js` (Phase 62 拆分) | 3 funcs |
| Composable | `src/composables/useCreatorProductTools/useProductMemory.ts` | 3 调用点 (via `api/index.js` barrel) |
| Barrel | `src/api/index.js:145-147` + `src/api/creator.js:8` | re-export |
| 后端测试 | `tests/infra/test_creator_memory_{annotations,query}.py` + `tests/dashboard/test_creator_endpoints.py` (3 tests) | back-compat via shim |

### 1.3 Endpoints

| Method | Path | DTO in → out |
|---|---|---|
| GET | `/api/creator/memory-assets` | — → `CreatorMemoryAssetsResponse` |
| PUT | `/api/creator/memory-assets/{asset_id}/annotation` | `CreatorMemoryAnnotationRequest` → `CreatorMemoryAnnotationResponse` |
| POST | `/api/creator/memory/query` | `CreatorMemoryQueryRequest` → `CreatorMemoryQueryResponse` |

---

## 2. 目标架构

### 2.1 Python package

```
packages/lingwen-creator/src/lingwen_creator/memory/
├── __init__.py        # 3 star-imports
├── annotations.py     # verbatim copy
├── assets.py          # verbatim copy + intra-package import 调整
└── query.py           # verbatim copy + intra-package import 调整
```

3 个 infra 文件变 1-line shim (v16.2.5 docstring pattern,`# noqa: F403`)。

### 2.2 Intra-package import 调整 (per v16.2.4 §5.1 lesson 1)

verbatim copy 后必须改的 import (module-level **和** 函数体 lazy import,per v16.2.2 §5.1 lesson 7):

| 文件 | 旧 | 新 |
|---|---|---|
| `assets.py:8` | `from infra.creator_dashboard import creator_overview` | `from lingwen_creator.content.dashboard import creator_overview` |
| `assets.py:9` | `from infra.creator_settings_docs import creator_settings_docs_payload` | `from lingwen_creator.settings.docs import creator_settings_docs_payload` |
| `assets.py:170` | `from infra.creator_memory_annotations import ...` | `from lingwen_creator.memory.annotations import ...` |
| `assets.py:171` | `from infra.creator_preferences import load_creator_preferences` | `from lingwen_creator.content.preferences import load_creator_preferences` |
| `query.py:7` | `from infra.creator_memory_assets import creator_memory_assets_payload` | `from lingwen_creator.memory.assets import creator_memory_assets_payload` |
| `query.py:8` | `from infra.creator_preferences import load_creator_preferences` | `from lingwen_creator.content.preferences import load_creator_preferences` |

保持不变:`infra.studio_registry` / `infra.memory_service`。

### 2.3 DTOs (7 个,全部 top-level,无 nested helper)

移到 `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` Memory section:

`CreatorMemoryAssetItem` / `CreatorMemoryAnnotationRequest` / `CreatorMemoryAnnotationResponse` / `CreatorMemoryAssetsResponse` / `CreatorMemoryQueryRequest` / `CreatorMemoryQueryResult` / `CreatorMemoryQueryResponse`

`apps/studio_api/models/creator_settings.py` 保留原定义 (与 v16.2.1..5 一致:contracts 是 source-of-truth,studio_api models 在 v16.2.7 cleanup 统一收敛)。

TS 通过 `tooling/contracts/generate.py` 自动生成。

### 2.4 Typed wrapper

`apps/dashboard/src/api/memory.ts` — 3 funcs,**NO zod**,**NO `/api/` prefix** (v16.2.1 §5.1 lessons 4-5):

```ts
fetchCreatorMemoryAssets(): Promise<CreatorMemoryAssetsResponse>
saveCreatorMemoryAnnotation(assetId: string, body: CreatorMemoryAnnotationRequest): Promise<CreatorMemoryAnnotationResponse>
queryCreatorMemory(body: CreatorMemoryQueryRequest): Promise<CreatorMemoryQueryResponse>
```

签名与 `api/memory.js` 完全一致 → composable 调用点零改动 (只改 import 来源)。
`packages/dashboard-contracts/src/shared/memory.ts` re-export + `creator.ts` +7 types + knip allowlist。

若使用 `import.meta.env`,必须加 `/// <reference types="vite/client" />` (v16.2.5 §5.1 lesson 1)。

### 2.5 前端删除

- `apps/dashboard/src/api/memory.js` → 删除 (typed wrapper 完全替代)
- `src/api/creator.js:8` `export * from './memory.js'` → 删除
- `src/api/index.js:145-147` → 改为从 `./memory.ts` re-export
- 删除前 `grep -r "api/memory" apps/dashboard/tests/` 找 orphan tests (v16.2.4 §5.1 lesson 5)

---

## 3. 验证门

| 门 | 命令 | 期望 |
|---|---|---|
| creator pkg | `python -m pytest packages/lingwen-creator/tests/ -q` | 71 → ~78 passing |
| shared pkg | `python -m pytest packages/lingwen-shared/tests/ -q` | 75 → ~82 passing |
| infra | `python -m pytest tests/infra/ -q` | 359 passing (unchanged, shim back-compat) |
| frontend | `pnpm vitest run` | ≥1774 passing,22 pre-existing volume-plan debt 不变 |
| types | `pnpm exec vue-tsc --noEmit` | 0 errors |
| lint | `ruff check .` | 0 |
| dead code | `pnpm exec knip` | 0 errors |
| codegen | `python tooling/contracts/generate.py` | creator.ts 增长,无 drift |

---

## 4. 风险

| 风险 | 缓解 |
|---|---|
| `assets.py:170` 函数体 lazy import 漏改 → 走 shim 形成 cycle | spec §2.2 明确列出所有 6 处 (module-level + 函数体);T1 后 `grep -n "infra.creator_" memory/*.py` 必须只剩 studio_registry/memory_service |
| composable 直接 import typed wrapper 后 `vi.mock('api/index.js')` 失效 | T7 split vi.mock per module (v16.2.5 §5.1 lesson 3) |
| `api/memory.js` 删除留下 orphan test | 删除前 grep tests/ (v16.2.4 §5.1 lesson 5) |
| DTO 名冲突 (contracts 已有 87+ interfaces) | T2 前 grep `CreatorMemory` in contracts/creator.py |

---

## 5. 非目标

- 44 shims 删除 → v16.2.7
- world/workspace/quality/onboarding typed wrapper `/api/` prefix fix → v16.2.7
- 22 pre-existing vitest debt → v16.2.7
- import-linter DP-01..06 enforcement → v16.4/v16.5
- `apps/studio_api/models/creator_settings.py` DTO 去重 → v16.2.7
