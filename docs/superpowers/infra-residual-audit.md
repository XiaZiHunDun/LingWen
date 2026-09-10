# infra/ 残留模块审查 (2026-09-10)

> **Phase**: 41+++ mini — `phase-41-plus-plus-infra-residual-audit`
> **作者**: Claude + user 推荐
> **范围**: 仅文档化（审计 + 候选识别），不真迁移
> **承接**: P3-ARCHDEBT 5/5b 已闭环 (Phase 36-40 + 40b)

## TL;DR

P3-ARCHDEBT 5 项（errors / paths / project_config / logging_config / studio_registry）已全部闭环。`infra/` 仍剩 **24 个顶层 .py + 25 个子目录** (~18K LOC, 141 .py)。本审查完成两件事：

1. **完整模块清单**（本文件）+ 按"是否值得迁 packages/"分类
2. **Top 5 下批候选** → [`ARCHDEBT-CANDIDATES.md`](./ARCHDEBT-CANDIDATES.md)

**核心结论**：`infra/` 不应再"批量迁移"。剩余 ~15K LOC 主要是 cross-cutting 子系统（`cross_volume/` `tools/` `persistence/` `world_db/`），各自已有完整业务语义，不适合拆成 LEAF package。最优路径是**继续 P3-ARCHDEBT 模式，按 consumer count 排优先级，单 module 单独 mini phase**。

---

## 1. 顶层 .py 完整清单（24 个）

| Module | LOC | Consumers | Workspace deps | 分类 |
|--------|-----|-----------|----------------|------|
| `llm_cache.py` | 909 | 1 | `lingwen_errors` | 🟡 大型但低 fan-out |
| `prose_judge.py` | 734 | 3 | 0 | 🟡 大型 TRUE-LEAF |
| `studio_batch_runner.py` | 676 | 10 | `lingwen_studio_registry` | ⚠️ NOT-LEAF 候选 #2 |
| `tool.py` | 612 | 1 | `lingwen_errors` | 🟡 LEAF 低消费者 |
| `health.py` | 518 | 1 | `lingwen_errors` | 🟡 LEAF 低消费者 |
| `permission.py` | 510 | 1 | `lingwen_errors` | 🟡 LEAF 低消费者 |
| `project_init.py` | 453 | **46** | `lingwen_paths` + `lingwen_shared` | ⚠️ **候选 #1 (highest fan-out)** |
| `types.py` | 423 | 1 | `lingwen_errors` | 🟡 LEAF 低消费者 |
| `schema.py` | 369 | 2 | `lingwen_errors` | 🟡 LEAF 低消费者 |
| `llm_service.py` | 309 | 9 | `lingwen_shared` + `lingwen_llm` | ⚠️ **候选 #2 (半迁移)** |
| `memory_service.py` | 307 | 4 | 10×`lingwen_memory.*` | ❌ NOT-LEAF (重 cross-cutting) |
| `full_check_report.py` | 287 | 4 | `lingwen_paths` + 2×`lingwen_quality` | ⚠️ NOT-LEAF |
| `studio_batch_templates.py` | 234 | 3 | `lingwen_studio_registry` | ⚠️ NOT-LEAF |
| `prose_snapshot.py` | 195 | 3 | 0 | 🟡 TRUE-LEAF |
| `prose_calibration.py` | 191 | 6 | 0 | ✅ **候选 #3 (TRUE LEAF)** |
| `prose_calibration_overrides.py` | 174 | 3 | 0 | 🟡 TRUE-LEAF |
| `result.py` | 168 | 2 | 0 | ✅ TRUE-LEAF |
| `studio_batch_streamer.py` | 131 | 3 | (?) | ⚠️ NOT-LEAF |
| `cache.py` | 91 | 4 | 0 | ✅ **候选 #4 (TRUE LEAF)** |
| `project_characters.py` | 89 | 3 | `lingwen_paths` | ⚠️ NOT-LEAF (1 dep) |
| `patterns.py` | 80 | 3 | 0 | ✅ TRUE-LEAF |
| `coverage_gate.py` | 78 | 3 | 0 | ✅ TRUE-LEAF |
| `filter.py` | 63 | 4 | `lingwen_quality` | ⚠️ **候选 #5 (near-LEAF)** |
| `__init__.py` | 25 | - | `lingwen_errors` | (wildcard — 已知 P3-ARCHDEBT 范围外) |

**Total**: 24 个顶层模块 / 7,825 LOC / 130 consumer-import points

## 2. 子目录完整清单（17 个非空）

| Dir | py 数 | LOC | 分类 |
|-----|-------|-----|------|
| `tools/` | 35 | 7,485 | ❌ CLI 集合 (dev-only, 不迁) |
| `cross_volume/` | 23 | 4,496 | ❌ 大型子系统 (跨卷引擎, **不迁**) |
| `persistence/` | 18 | 1,578 | ❌ cross-cutting 多 concern |
| `world_db/` | 13 | 1,291 | ❌ Phase 117 新模块 (已有 router layer) |
| `reading_power/` | 7 | 1,006 | ❌ 引擎子系统 |
| `event_sourcing/` | 3 | 992 | ❌ 引擎子系统 |
| `story_contracts/` | 7 | 848 | ❌ 业务子系统 |
| `llm_benchmarks/` | 7 | 751 | ❌ 基准测试 (dev-only) |
| `subplot/` | 4 | 508 | ❌ 已迁 `lingwen-world-model` 子模块 — 残留 PHASE-COMPAT 痕迹？ |
| `poc/` | 2 | 439 | ❌ POC (无 production consumer) |
| `util/` | 2 | 338 | ⚠️ 待审查 |
| `di/` | 2 | 309 | ❌ DI 框架 (cross-cutting) |
| `config/` | 2 | 77 | ⚠️ 待审查 |
| `core/` | 1 | 8 | ⚠️ wildcard re-export (`__init__.py`) |
| `prose/` | 1 | 4 | ⚠️ wildcard re-export |
| `project/` | 1 | 4 | ⚠️ wildcard re-export |
| `studio/` | 1 | 1 | ⚠️ wildcard re-export |

**Total**: 17 子目录 / 131 .py / ~20K LOC

> **Note**: 上述"❌ 不迁"模块均 ≥300 LOC 且 cross-cutting，不适合 LEAF package 模式。`tools/` 是 dev-only CLI（35 py / 7.5K LOC），本质是 scripts 集合，应保持现状或拆 worktree-isolated 工具集。

## 3. 分类总结

### 🅰️ TRUE LEAF candidates（0 workspace deps, 仅 stdlib）

- `result.py` (168 LOC, 2 consumers)
- `cache.py` (91 LOC, 4 consumers)
- `coverage_gate.py` (78 LOC, 3 consumers)
- `patterns.py` (80 LOC, 3 consumers)
- `prose_calibration.py` (191 LOC, 6 consumers)
- `prose_calibration_overrides.py` (174 LOC, 3 consumers)
- `prose_snapshot.py` (195 LOC, 3 consumers)
- `prose_judge.py` (734 LOC, 3 consumers) — 唯一大型 TRUE-LEAF

### 🅱️ NEAR-LEAF candidates（1 workspace dep）

- `tool.py` (612 LOC, 1 consumer) — `lingwen_errors` (P36)
- `types.py` (423 LOC, 1 consumer) — `lingwen_errors`
- `schema.py` (369 LOC, 2 consumers) — `lingwen_errors`
- `health.py` (518 LOC, 1 consumer) — `lingwen_errors`
- `permission.py` (510 LOC, 1 consumer) — `lingwen_errors`
- `llm_cache.py` (909 LOC, 1 consumer) — `lingwen_errors`
- `filter.py` (63 LOC, 4 consumers) — `lingwen_quality`
- `project_characters.py` (89 LOC, 3 consumers) — `lingwen_paths`

### 🅲️ NOT-LEAF candidates（≥2 workspace deps — Phase 42+ candidates）

- `project_init.py` (453 LOC, **46** consumers) — `lingwen_paths` + `lingwen_shared` — **最高 fan-out**
- `llm_service.py` (309 LOC, 9 consumers) — `lingwen_shared` + `lingwen_llm` — **半迁移 (v16.5 LLMTask/TaskType 已迁)**
- `studio_batch_runner.py` (676 LOC, 10 consumers) — `lingwen_studio_registry`
- `studio_batch_templates.py` (234 LOC, 3 consumers) — `lingwen_studio_registry`
- `studio_batch_streamer.py` (131 LOC, 3 consumers) — likely `lingwen_studio_registry`
- `full_check_report.py` (287 LOC, 4 consumers) — `lingwen_paths` + 2×`lingwen_quality`
- `memory_service.py` (307 LOC, 4 consumers) — 10×`lingwen_memory.*`

### 🅳️ 引擎子系统（≥500 LOC + cross-cutting — 不迁）

- `tools/` (7,485 LOC), `cross_volume/` (4,496), `persistence/` (1,578), `world_db/` (1,291), `reading_power/` (1,006), `event_sourcing/` (992), `story_contracts/` (848), `llm_benchmarks/` (751), `subplot/` (508), `di/` (309)

---

## 4. 迁移策略建议

**`infra/` 不应"批量迁移"**（Phase 32 shim-cleanup 教训：批量迁移极易漏检 relative/function-body imports）。

**P3-ARCHDEBT 模式继续**：每个 candidate = 1 个 mini phase，每个 phase = 5-7 atomic commits（spec+plan / scaffold / migrate / delete / invariant+version / guards+doc-sync）。Phase 36-40b 已建立成熟流程。

**优先级排序**（5 因素：consumer count / LOC / workspace deps / shared usage / `studio_registry` 类似案例）：

详见 [`ARCHDEBT-CANDIDATES.md`](./ARCHDEBT-CANDIDATES.md) — Top 5 详细分析。

---

## 5. 已知遗留 / 不在范围

- `infra/cli/` `infra/creator/` `infra/hooks/` `infra/novel-factory/` — 创作者层 + 历史布局，未在本审查 grep 范围
- `infra/__init__.py` wildcard — Phase 36-40 已逐个删除对应 P3-ARCHDEBT 包的 wildcard；剩余模块（health/permission/types/schema/tool/llm_cache 等）的 wildcard 行为需后续审查
- `infra/subplot/` — Phase 35 已迁 `lingwen-world-model`（subplot helpers 已 package-locality），残留目录需确认是否仍是 PHASE-COMPAT shim

## 6. Carryover closure status

| Phase | Status |
|-------|--------|
| P2-ARCHDEBT (got/world_model) | ✅ Phase 33-35 |
| P3-ARCHDEBT errors | ✅ Phase 36 |
| P3-ARCHDEBT paths | ✅ Phase 37 |
| P3-ARCHDEBT project_config | ✅ Phase 38 |
| P3-ARCHDEBT logging_config | ✅ Phase 39 |
| P3-ARCHDEBT studio_registry | ✅ Phase 40 + 40b |
| **P3-ARCHDEBT continued (Phase 42+)** | 🟡 待启动 — see [`ARCHDEBT-CANDIDATES.md`](./ARCHDEBT-CANDIDATES.md) |

**Next-actionable**: Phase 42 candidate = `infra/project_init` (46 consumer fan-out, 类似 P40a `studio_registry` 模式)
