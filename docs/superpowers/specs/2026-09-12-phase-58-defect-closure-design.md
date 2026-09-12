# Phase 58 P3-ARCHDEBT 缺陷闭环 — Design

> **目标**: 修复 24 个 pre-existing pytest 失败 + 1 个生产级 silent bug
> **触发**: Phase 57 ff-merge 后，跑 `pytest apps/studio_api/tests/` 发现 24 failed / 58 passed
> **版本**: v53.0 → v53.1
> **日期**: 2026-09-12

## 1. 背景

Phase 57 P3-ARCHDEBT 闭环后，跑 backend test baseline 验证 ff-merge 安全，结果发现 `apps/studio_api/tests/` 有 24 failed。展开调查后，发现这是 Phase 56 P3-ARCHDEBT 漏迁的连锁缺陷：

1. **production bug (silent)**: `packages/lingwen-world-db/src/lingwen_world_db/queries/*.py` (6 files) + `agent_extractors.py` + `markdown_roundtrip.py` (3 sites) 内部仍用 `infra.world_db.*` 旧路径，**整个 package import 时 ModuleNotFoundError**。任何调用 `/api/world/characters` 等 endpoint 的 runtime 都会爆。
2. **test bug**: `apps/studio_api/tests/test_world_route.py` (5 imports) 用 `infra.world_db.*` 旧路径
3. **package export bug**: `lingwen_studio_batch_streamer/__init__.py` 没有 re-export `KNOWN_EVENT_TYPES`，但 `apps/studio_api/routes/studio.py` 5 处 import
4. **orphan test directory**: `tests/infra/world_db/` (5 files) 全部 import broken，pytest collect 失败

## 2. 24 个失败分类

| 类别 | 文件 | 失败数 | Root cause | 修复方式 |
|------|------|--------|------------|----------|
| A. Batch streamer export | `test_studio_batch_events_route.py` + `test_studio_batch_templates_route.py` | 18 | `KNOWN_EVENT_TYPES` 未在 `__init__.py` re-export | C1: 加 1 行 export |
| B. World route test imports | `test_world_route.py` (4 tests) | 4 | 测试用 `infra.world_db.*` 旧路径 | C2: 5 行 sed |
| C. World route behavior | `test_world_route.py::test_import_and_export_roundtrip` | 1 | `markdown_roundtrip.py:322,337,352` 生产代码 import broken | C3: 修复 3 处生产 import |
| D. Test infra import chain | `markdown_roundtrip.py:322,337,352` cascade 触发 C 失败 | (合并到 C) | 隐含 chain | C3 |
| **Total** | | **24** | | |

## 3. 额外发现（不在 24 内，但顺手处理）

| 项 | 文件 | 类型 | 处理 |
|----|------|------|------|
| E. Orphan test dir | `tests/infra/world_db/` (5 files) | 5 ERROR pytest collect | C4: 全量删除（test 内容已并入 `packages/lingwen-world-db/tests/`... 注：当前包内**无**tests，orphan tests 是历史 copy；删后无回归）|
| F. `infra` 不存在 | `apps/studio_api/tests/test_world_route.py:41` 等 5 处 | 同 B | C2 |
| G. Batch route static import | `apps/studio_api/routes/studio.py:404` 顶部 `KNOWN_EVENT_TYPES` | 顶部 import 同样需要 (not in 24 but in 18) | C1 |

> **Not in scope（独立 follow-up）**:
> - `tests/infra/world_db/` 内容是否需迁回 `packages/lingwen-world-db/tests/`（与 24 defects 无关；orphan 删掉即可）

## 4. 计划

| Commit | SHA | Subject | Files | +/- |
|--------|-----|---------|-------|-----|
| C0 | TBD | spec + plan handoff | 1 | +150 |
| C1 | TBD | `fix(streamer): re-export KNOWN_EVENT_TYPES` | 2 | +2/-0 |
| C2 | TBD | `fix(tests): migrate test_world_route.py to lingwen_world_db` | 1 | +5/-5 |
| C3 | TBD | `fix(world-db): migrate 8 production imports infra→lingwen` | 8 | +8/-8 |
| C4 | TBD | `chore(tests): delete orphan tests/infra/world_db/` | 5 | +0/-5 |
| C5 | TBD | regression guards + handoff | 2 | +400 |

**Net**: 24/24 test failures fixed, 1 production bug fixed, 5 orphan test files deleted, 6+ regression guards added.

## 5. 验证 gates

| Gate | 命令 | 期望 |
|------|------|------|
| G1 | `pytest apps/studio_api/tests/ -q` | 82 passed / 0 failed |
| G2 | `pytest tests/ -q --ignore=tests/infra/world_db` (master baseline 336 + 11 skip) | ≥ 336 passed |
| G3 | new regression guards | 6+ new tests pass |
| G4 | `python -c "from lingwen_world_db.queries.characters import create_character"` | 0 exit |
| G5 | `python -c "from lingwen_world_db.agent_extractors import LLMExtractor"` | 0 exit |
| G6 | `ruff check packages/lingwen-world-db/ apps/studio_api/` | clean |

## 6. 风险

- **低**: Production code migration 是路径替换（`infra.world_db.queries._helpers` → `lingwen_world_db.queries._helpers`），无逻辑变更
- **低**: `KNOWN_EVENT_TYPES` 已存在 service.py，re-export 无新逻辑
- **中**: 删 `tests/infra/world_db/` 5 文件 — 已确认其内容无任何 `packages/lingwen-world-db/tests/` 副本，纯 orphan
- **零**: 不动任何架构 / invariant / I001 等

## 7. 不在范围（deliberate non-goal）

- `tests/infra/world_db/` → `packages/lingwen-world-db/tests/` 迁移（orphan deletion 即可，full migration 是单独 phase）
- Phase 56 I076 invariant 升级（当前 I077 已声明 lingwen-reading-power canonical；I076 同样适用 lingwen-world-db）
- 新增 production 端到端 test
