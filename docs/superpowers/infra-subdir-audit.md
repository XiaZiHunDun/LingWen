# infra/ 子目录级审计 (Phase 52 audit)

> **Branch**: `phase-52-subdir-audit` (audit-only; **不真迁移**)
> **承接**: Phase 41+++ mini (顶层 .py 5 候选) + Phase 51 (prose 簇收尾, 顶层 4 → 1)
> **新战场**: 21 个 infra/ 子目录, 21349 LOC / 134 文件

## 1. 子目录 LOC 排序

| LOC | files | 子目录 | 备注 |
|-----|-------|--------|------|
| 7485 | 35 | `infra/tools/` | 含 legacy/ 4976 LOC (66%) |
| 4493 | 23 | `infra/cross_volume/` | 业务子系统, NOT-LEAF, 多包消费 |
| 1578 | 18 | `infra/persistence/` | 数据持久化, NOT-LEAF |
| 1291 | 13 | `infra/world_db/` | Phase 117 World DB 已有独立路由 → **可能冗余** |
| 1006 | 7 | `infra/reading_power/` | 单包消费? |
| 992 | 3 | `infra/event_sourcing/` | 事件溯源 |
| 848 | 7 | `infra/story_contracts/` | 契约 |
| 751 | 7 | `infra/llm_benchmarks/` | 基准测试 |
| 508 | 4 | `infra/subplot/` | 副图 |
| 439 | 2 | `infra/poc/` | POC |
| 338 | 2 | `infra/util/` | 工具 |
| 309 | 2 | `infra/di/` | DI 层 |
| 77 | 2 | `infra/config/` | 配置 |
| 8 | 1 | `infra/core/` | 已空 (Phase 39 logging_config 残留) |
| 1 | 1 | `infra/studio/` | 已空 (Phase 40 studio_registry 残留) |

**总 21349 LOC**, top 3 占 **13556 / 63%**。

## 2. Top 3 分类 (本审计核心发现)

### 2.1 `infra/tools/` — 混合 1 子包 (BIG WIN)

**结构**:
| 子目录 | LOC | 消费者状态 |
|--------|-----|-----------|
| `legacy/` | **4976** | **零消费** (28 文件) |
| `workflow/` | 1012 | 真消费 (lingwen-pipeline/block_proceed + 5+ tests) |
| `consistency/` | 742 | 真消费 (lingwen-pipeline/run_checker + tests) |
| 顶层 5 个 .py | <500 | 杂项脚本 |

**结论**: **legacy/ 是完整死代码区**, 标记"逐步迁移中"实际上已经迁完。删除 4976 LOC 是**单 commit 高 ROI 动作**。

**风险评估**: LOW
- 名称带"legacy" + 路径用 `legacy/` 子目录名 = 软 deprecation 暗示
- 0 runtime import (grep 验证)
- 唯一可能的风险: 测试代码引用这些 checker 的 **字符串字面量** (mock 路径) — 需 grep `check_character_activity\|check_segment_relevance\|check_battle_density|...`

### 2.2 `infra/cross_volume/` — 业务子系统 (高复杂)

**4493 LOC**, 15 模块, 反向依赖 lingwen-got/lingwen-llm (workspace deps 2)

**消费点**:
- `apps/studio_api/app.py` 6 处 import (核心路由)
- `packages/lingwen-cli/commands/cascade.py` + ripple_*.py + backfill.py (5+ CLI 命令)
- `packages/lingwen-core/agents/workflow_runner.py` (lazy import)
- `packages/lingwen-core/agents/internal/__init__.py` 注释提及

**结构**:
- `storage.py` 1353 LOC — 最大块, RippleStorage + ConflictError
- `reference_graph.py` 441 — 4-dim graph (character/foreshadow/setting/plot_point)
- `e2e_seed.py` 446 — 测试 fixtures
- `scanner_calibration.py` 295 — LLM scanner 校准
- `llm_scanner.py` 284 — 4-dim serial scanner
- `edge_inferrer.py` 258 — 8-rel-type edge inferrer

**迁移复杂度评估**: **HIGH**
- 工作量 ~ 1 周
- 类似 P40a studio_registry 模式: NOT-LEAF + workspace deps 2 + 多包消费
- 但 storage.py 1353 LOC 单独可拆子包 (5 子模块)
- **建议拆 2 包**: `lingwen-cross-volume` (graph + scanner + edge_inferrer) + `lingwen-ripple-storage` (storage.py + 相关辅助)
- Phase 52-53 候选

### 2.3 `infra/persistence/` — 持久化层 (中复杂)

**1578 LOC**, 10 模块, 反向依赖 lingwen-storage (workspace deps 1)

**消费点**: 80 处 (apps/studio_api + 全栈)
- `apps/studio_api/app.py` 4 处 (ripple 注册 + 启动)
- 多个 walkthrough scripts

**关键模块**:
- `connection.py` 79 + `paths.py` 11 + `sqlite_config.py` 79 — SQLite 基础设施
- `schemas.py` 246 — 各 SQLite 表 DDL
- `registry.py` 79 — 单例注册表 (ripple/cost_tracker/cross_volume 等)
- `write_chapter.py` 98 — Phase 115 章节写端点
- `write_workspace_api.py` 31 — Phase 115 router
- `sqlite_storage_adapter.py` 20 — lingwen-storage 适配
- `bootstrap.py` 33 — register_all()

**迁移复杂度评估**: MEDIUM
- 类似 P45 utilities batch: 多个子模块 + 单例注册表模式
- 拆 1 包 `lingwen-persistence` 即可 (10 模块全 <500 LOC, 单子模块最重 schemas.py 246)
- Phase 54 候选

### 2.4 `infra/world_db/` — **可能冗余** (Phase 53 高概率 dead code)

1291 LOC / 13 文件。Phase 117 之后 world DB 已迁到独立 SQLite + FastAPI router (apps/studio_api/routes/world.py + infra/world_db/)。

**疑点**:
- `infra/world_db/` 的 SQLite 可能仍是老 schema
- `apps/studio_api/routes/world.py` 的 SQLite 可能已替换
- 需要 grep 实际查询流向才能判断

**建议**: Phase 53 先做**单点验证** — 跑一遍 world DB 的 query, 看老 infra/world_db/ 是否还在被读写。

## 3. 其他目录 (低优先级)

| 子目录 | LOC | 备注 |
|--------|-----|------|
| `event_sourcing/` | 992 | 3 文件 = 平均 330 LOC, NOT-LEAF 风险 |
| `story_contracts/` | 848 | 7 文件, 业务契约层 |
| `llm_benchmarks/` | 751 | 基准测试, 可能是 dev-only |
| `reading_power/` | 1006 | 7 文件, 阅读力分析 |
| `subplot/` | 508 | 4 文件, 副图 (副剧情子图) |
| `poc/` | 439 | 2 文件, POC 验证代码 — **可能全 dead** |
| `util/` | 338 | 2 文件 |
| `di/` | 309 | 2 文件, DI 层 |
| `config/` | 77 | 2 文件 |
| `core/` | 8 | 1 文件, 已空 (Phase 39 残留) |
| `studio/` | 1 | 1 文件, 已空 (Phase 40 残留) |

**低优先级建议**:
- `infra/core/` (8 LOC) + `infra/studio/` (1 LOC) — 立即删 (Phase 39/40 残留)
- `infra/poc/` (439 LOC) — 需审计后判断 (POC 通常是 dev-only, 容易成孤儿)

## 4. 战略建议

**Phase 52** (本审计 phase): 输出本文档 + ARCHDEBT-SUBDIR-CANDIDATES.md 排序表

**Phase 53** (高 ROI, 1-2 commit):
- 删 `infra/tools/legacy/` (4976 LOC, 28 文件)
- 删 `infra/core/` + `infra/studio/` 残留 (9 LOC)
- 审计 `infra/poc/` 是否真 dead
- **预期**: 删 ~5500 LOC dead code, 4-6 atomic commits, 1 天

**Phase 54** (业务迁移, 1 周):
- `infra/persistence/` → `packages/lingwen-persistence/` (10 模块, 1 包)
- 类似 P45 utilities batch 模式

**Phase 55** (业务迁移, 1 周):
- `infra/cross_volume/` → 拆 2 包 (`lingwen-cross-volume` + `lingwen-ripple-storage`)
- 类似 P40a studio_registry 模式 (NOT-LEAF + workspace deps)

**Phase 56** (审计 + 可能删):
- `infra/world_db/` 是否被 Phase 117 替代
- 整合 cross_volume + persistence 的 leftover

## 5. 立即可执行 (本期 Phase 53 预告)

如果用户同意, Phase 53 (单文件删除类, 0 migration risk):
1. 删 `infra/tools/legacy/` 全部 (28 文件, 4976 LOC)
2. 删 `infra/core/` + `infra/studio/` 残留 (2 文件, 9 LOC)
3. 删 `infra/poc/` (审计后, 可能 439 LOC)
4. 加 invariant I074 (legacy/consistency 子目录不存在)

**总预期删除 ~5500 LOC, 跨 30+ 文件, 1-2 commit, 半天工作量。**
