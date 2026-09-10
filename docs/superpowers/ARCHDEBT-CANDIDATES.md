# ARCHDEBT Candidates — Top 5 下批 P3-ARCHDEBT 候选 (Phase 42+)

> **Phase**: 41+++ mini — `phase-41-plus-plus-infra-residual-audit`
> **承接**: [`infra-residual-audit.md`](./infra-residual-audit.md) 完整模块清单
> **范围**: 5 candidates ranked, 每个含 LOC / consumers / deps / migration 复杂度估计

## 排序逻辑（5 因素）

1. **consumer count** — 越多越优先（highest fan-out = highest cleanup ROI）
2. **workspace deps** — 越少越易迁移（TRUE LEAF > NOT-LEAF 但 high fan-out）
3. **LOC** — ≤500 LOC 友好（mini phase ≤1 day）
4. **migration 复杂度** — 半迁移（已有 re-export shim）= 更易收尾
5. **P3-ARCHDEBT 模式 reuse** — 类似 Phase 40a `studio_registry` 模式（NOT-LEAF but high fan-out）

---

## 🏆 #1 — `infra/project_init.py` (Phase 42 top candidate)

| Metric | Value |
|--------|-------|
| LOC | 453 |
| Consumers | **46** (highest in residual infra) |
| Workspace deps | 2 (`lingwen_paths` + `lingwen_shared`) |
| LEAF | ❌ NOT-LEAF |
| Public symbols | `InitProjectResult` (dataclass) + 11 funcs (`init_minimal_short_project`, `validate_slug`, `default_project_parent`, `_validate_chapter_count`, `_chapter_beats`, `_project_yaml`, `_pillars_md`, `_readme_md`, `_global_outline_md`, `_chapter_outline_md`, `_character_profiles`) |
| Migration complexity | **HIGH** — 类似 P40a `studio_registry` 模式 (NOT-LEAF + 46 consumers + multi-package dep) |

### 为什么候选 #1

- **最高 fan-out**：46 个 consumer 远超其他候选 (next: `studio_batch_runner` 10, `llm_service` 9)
- **成熟模式可复用**：Phase 40a `studio_registry` 是完美先例 — NOT-LEAF 但 multi-package, 50 consumers 迁移用 8 atomic commits (C0 spec+plan / C1 scaffold / C1.5 fixup / C2a intra-infra / C2b bulk / C3 shim / C4 invariant+version / C5 guards+handoff)
- **半业务边界**：`init_minimal_short_project` + `InitProjectResult` + creator-mode-aware validation = 业务语义强（"项目初始化器"），独立成 package 名正言顺
- **测试成熟度**：46 consumer 包含 18+ `tests/infra/test_creator_*.py` — 大量回归覆盖

### Migration 估计

- **Phase name**: `phase-42-p3-archdebt-project-init`
- **Atomic commits**: 7-9 (C0 spec+plan / C1 scaffold / C1.5 fixup / C2a intra-infra / C2b bulk / C3 shim / C4 invariant+version / C5 guards+handoff)
- **Risks**: 多 creator test consumer 需要 bulk migration; `_validate_chapter_count` 私有符号可能漏检 (N.14 lesson 1 第 12 次变体)
- **Invariant**: 新增 #56 — `packages/lingwen-project-init/` 是 project init 唯一实包；`infra.project_init.*` 路径非法
- **Validation gates**: ruff + project_init 全部测试 + 6 baselines preserved + Phase 36-41 guards preserved + regression guards

---

## 🥈 #2 — `infra/llm_service.py` (Phase 42+ candidate)

| Metric | Value |
|--------|-------|
| LOC | 309 |
| Consumers | 9 |
| Workspace deps | 2 (`lingwen_shared` + `lingwen_llm`) |
| LEAF | ❌ NOT-LEAF |
| Public symbols | `LLMService` (class) + `get_llm_service` + `create_task` + re-exports `LLMTask`, `TaskType` |
| Migration complexity | **LOW-MEDIUM** — 半迁移已完成 (v16.5 LLMTask/TaskType 已迁 `lingwen_shared`) |

### 为什么候选 #2

- **半迁移 shim 已存在**：`llm_service.py` 顶部有 `# v16.5 relocation: TaskType + LLMTask moved to lingwen_shared.contracts.python.llm. # Re-export here so tools/, tests/, infra/core/__init__.py star-imports keep working.` — 9 consumer 仍依赖 shim，模式与 Phase 32 shim-cleanup 完美匹配
- **shim cleanup 模式成熟**：Phase 32 已删除 3 个零/低消费者 shim（`infra/subplot/data_structures.py` / `infra/world_model/data_structures.py` / `packages/lingwen-core/src/lingwen_core/agents/master_controller.py`）
- **NOT-LEAF 但简单**：2 dep 都是 stable（`lingwen_shared` 已存在, `lingwen_llm` 已存在）

### Migration 估计

- **Phase name**: `phase-43-p3-archdebt-llm-service`
- **Atomic commits**: 5-6 (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete + shim cleanup / C4 invariant+version / C5 guards+doc-sync)
- **Risks**: tools/ + tests/ + infra/core/__init__.py 的 star-imports 需要逐个验证 (N.14 lesson 1 第 8 次复用)
- **Invariant**: 新增 #57 — `packages/lingwen-llm-service/` 是 LLM service 唯一实包；`infra.llm_service.*` 路径非法

---

## 🥉 #3 — `infra/prose_calibration.py` (Phase 44+ TRUE-LEAF candidate)

| Metric | Value |
|--------|-------|
| LOC | 191 |
| Consumers | 6 |
| Workspace deps | **0** (stdlib yaml + Path only) |
| LEAF | ✅ TRUE LEAF |
| Public symbols | `load_prose_config` + `is_prose_issue` (+ others, TBD on read) |
| Migration complexity | **LOW** — 完美 LEAF, 0 deps, 6 consumers |

### 为什么候选 #3

- **TRUE LEAF 教科书案例**：0 workspace deps, stdlib only (yaml + pathlib), 单职责 ("prose calibration config loader")
- **成熟测试**：`tests/infra/test_prose_calibration.py` 存在
- **P3-ARCHDEBT LEAF pilot 类似**：Phase 39 `logging_config` (3 pub symbols / 7 consumers / 0 cross-package deps) 是教科书模板

### Migration 估计

- **Phase name**: `phase-44-p3-archdebt-prose-calibration`
- **Atomic commits**: 5 (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync)
- **Risks**: 极低 — LEAF + 6 consumer + Path-based config
- **Invariant**: 新增 #58 — `packages/lingwen-prose-calibration/` 是 prose calibration config 唯一实包

---

## #4 — `infra/cache.py` (Phase 45+ TRUE-LEAF micro candidate)

| Metric | Value |
|--------|-------|
| LOC | 91 |
| Consumers | 4 |
| Workspace deps | 0 (stdlib hashlib/json/time/pathlib/dataclasses) |
| LEAF | ✅ TRUE LEAF |
| Public symbols | TBD (read spec) |
| Migration complexity | **LOW** — TRUE LEAF, 4 consumers, 91 LOC |

### 为什么候选 #4

- 最小 LEAF 候选之一 (与 `coverage_gate.py` 78 LOC + `patterns.py` 80 LOC + `result.py` 168 LOC 同档)
- 可与 #5 合并 phase（multi-module mini）

### Migration 估计

- **Phase name**: `phase-45-p3-archdebt-utilities` (合并 cache + coverage_gate + patterns + result)
- **Atomic commits**: 5-6 per module 或合并 1 phase (10-12 atomic commits)
- **Risks**: 极低 — 全 TRUE LEAF, 0 deps
- **Invariant**: 新增 #59 — `packages/lingwen-utilities/` 是通用 utilities 唯一实包

---

## #5 — `infra/filter.py` (Phase 46+ near-LEAF candidate)

| Metric | Value |
|--------|-------|
| LOC | 63 |
| Consumers | 4 |
| Workspace deps | 1 (`lingwen_quality`) |
| LEAF | ⚠️ near-LEAF (1 dep = `lingwen_quality`) |
| Public symbols | TBD |
| Migration complexity | **LOW-MEDIUM** — 1 workspace dep (cross-cutting risk) |

### 为什么候选 #5

- 1 dep 单文件, 单职责 (likely "filter issues by type/severity")
- 候选 #5 是"边界案例"：单 dep 但 LEAF-like，决定是否拆 package 取决于 dep 边界

### Migration 估计

- **Phase name**: `phase-46-p3-archdebt-filter`
- **Atomic commits**: 5
- **Risks**: 中 — `lingwen_quality` 是 cross-cutting package (used by multiple infra modules); 拆 `filter.py` 可能暴露 quality 包边界模糊
- **Invariant**: 新增 #60 — `packages/lingwen-filter/` 是 filter helper 唯一实包 (或合并进 `lingwen_quality` — 待 Phase 46 决策)

---

## 不在下批的候选（已知 / 已知 NOT-LEAF）

| Module | Why not top 5 |
|--------|---------------|
| `studio_batch_runner.py` | 10 consumers, NOT-LEAF, 类似 #2 但半迁移迹象不明确；放 Phase 47+ |
| `studio_batch_templates.py` | 3 consumers, NOT-LEAF; 放 Phase 47+ |
| `studio_batch_streamer.py` | 3 consumers, NOT-LEAF; 放 Phase 47+ |
| `studio_batch_*` (3 个) | 共享 `lingwen_studio_registry` dep — 建议**合并 1 phase** (Phase 47) |
| `full_check_report.py` | 4 consumers, 3 deps (cross-cutting `lingwen_quality` x2) — Phase 48+ |
| `memory_service.py` | 4 consumers, **10 deps** (heavy `lingwen_memory.*`) — Phase 49+ |
| `types.py` `tool.py` `schema.py` `health.py` `permission.py` `llm_cache.py` | 1-2 consumers (低 ROI), LEAF but trivial — Phase 50+ batch |

---

## 推荐执行顺序

| Order | Phase | Module | Est. effort |
|-------|-------|--------|-------------|
| 1 | **Phase 42** | `infra/project_init` (46 consumers) | 1-2 days (high fan-out) |
| 2 | **Phase 43** | `infra/llm_service` (9 consumers, shim cleanup) | 0.5-1 day |
| 3 | **Phase 44** | `infra/prose_calibration` (TRUE LEAF) | 0.5 day |
| 4 | **Phase 45** | `infra/{cache, coverage_gate, patterns, result}` (LEAF batch) | 0.5-1 day |
| 5 | **Phase 46** | `infra/filter` (near-LEAF, boundary check) | 0.5 day |
| 6 | Phase 47 | `infra/studio_batch_*` (3 modules, NOT-LEAF) | 1 day |
| 7 | Phase 48 | `infra/full_check_report` (NOT-LEAF, cross-cutting) | 1 day |
| 8 | Phase 49 | `infra/memory_service` (10 deps, heavy) | 1-2 days |
| 9 | Phase 50+ | `types/tool/schema/health/permission/llm_cache` (low consumer batch) | 1 day |

**Estimated**: 8 phases × 0.5-2 days = ~1-2 weeks, 50+ atomic commits.

---

## Validation strategy (持续)

每个 P3-ARCHDEBT phase 必须验证:
1. ✅ ruff clean on changed Python files
2. ✅ candidate package full test suite
3. ✅ 6 baselines preserved (lingwen-core / lingwen-got / lingwen-world-model / lingwen-creator / studio_api / lingwen-quality)
4. ✅ Prior-phase guards preserved (Phase 36-41)
5. ✅ New regression guards (N.14 lesson 1 第 12 次起 — 每个新 phase 都加 new invariant #N+1)
6. ✅ Old-path audit clean (grep `infra.X.*` → 0 except re-export shim / doc)

---

## Carryover closure

| Phase | Status |
|-------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ Phase 36-40b |
| **P3-ARCHDEBT continued (Phase 42+ top 5)** | 🟡 待启动 |
| **Long tail (Phase 47-50+, 5 more modules)** | 🟡 known backlog |

**Next-actionable**: Phase 42 = `infra/project_init` (highest fan-out, 类似 P40a studio_registry 模式)
