# Phase 35 — World Model Package 设计稿

> **状态**: v1 (设计稿)
> **日期**: 2026-09-08
> **作者**: LingWen solo maintainer
> **关联 phase**: v34 LINGWEN-GOT 闭环后,P2-ARCHDEBT 收官项
> **关联 plan**: `docs/superpowers/plans/2026-09-08-phase-35-world-model-package.md`

---

## 1. 背景与动机

### 1.1 P2-ARCHDEBT 收官

| Phase | 处理对象 | 状态 |
|-------|----------|------|
| Phase 32 (v32.0) | PHASE-COMPAT shim × 3 (infra/subplot/data_structures + infra/world_model/data_structures + master_controller) | ✅ |
| Phase 34 (v33.0) | `infra.got.*` (9 modules, 1788 lines) → `packages/lingwen-got/` | ✅ |
| **Phase 35** (v34.0) | `infra.world_model.*` (10 modules, 2282 lines) → `packages/lingwen-world-model/` | ⏳ 本文 |

### 1.2 carryover 描述 vs 实际

CLAUDE.md / BACKLOG.md 描述为「split (canonical re-exports vs behavior services, 5 consumer 迁移)」。实际:
- 16 external consumer files (1 POC + 3 cross-test + 12 in-package tests)
- cross-package import 复杂: `infra/world_model/__init__.py:53` 引用 `infra.subplot.helpers`
- 「split」=「move + re-export」而非 file-split:Phase 32 已部分完成 canonical-only re-export (lingwen_core.domain import + re-export),剩 behavior services + subplot helpers

### 1.3 为什么是 package,不是 module

- 2282 lines / 10 files / 37 public symbols ≥ lingwen-got (1788 lines / 9 files / 32 symbols)
- Phase 34 已建立「P2-ARCHDEBT → packages/」pattern,本 phase 复用 + 闭环 P2-ARCHDEBT 全部
- I001 不变量延展: `infra/{paths, project_config, logging_config, errors, studio_registry}` → packages/ (Phase 36+, P3-ARCHDEBT)

---

## 2. 范围

### 2.1 In-Scope

| 类别 | 数量 |
|------|------|
| Source files 迁移 (infra/world_model/*.py) | 10 files / 2282 lines |
| Cross-package source files 迁移 (infra/subplot/helpers.py) | 1 file / 52 lines |
| Public symbols (`__all__`) | 37 symbols |
| External consumer migration (POC + cross-test) | 4 files |
| In-package tests 跟随迁移 | 12 files / 201 tests |
| 全套 guards + invariant + doc sync | 1 new invariant (#50) |

### 2.2 Out-of-Scope (P3-ARCHDEBT)

- `infra/{paths, project_config, logging_config, errors, studio_registry}` → packages/ (Phase 36+)
- `infra/subplot/__init__.py` 剩余内容 (canonical re-exports of PlotStatus, etc.) 不动
- `infra/{creator, ai_service, master_controller, consistency, agent_system, cross_volume, ...}` PHASE-COMPAT shims 全部不动 (MEMORY.md 「不要对 PHASE-COMPAT shim 做小范围迁移」)

---

## 3. 目标架构

### 3.1 Package 布局 (mirrors lingwen-got)

```
packages/lingwen-world-model/
├── pyproject.toml                         # name=lingwen-world-model, deps=[lingwen-core]
├── README.md
├── src/lingwen_world_model/
│   ├── __init__.py                        # 37 __all__ symbols (canonical re-exports + behavior services)
│   ├── engine.py                          # RippleEngine (6 methods)
│   ├── character_snapshot.py
│   ├── foreshadow_snapshot.py
│   ├── key_point_graph.py                 # Contradiction + ContradictionKind + KeyPointGraph (N² 检测)
│   ├── lifecycle.py                       # 7 symbols (constants + can_transition + is_terminal)
│   ├── links.py                           # LinkAction + link_subplot_to_ripple + apply_ripple_resolution
│   ├── queries.py                         # 3 helpers (detect/predict/suggest)
│   ├── registry.py                        # RippleRegistry + 3 exceptions
│   ├── snapshot_diff.py                   # SnapshotChange + ChangeKind + EntityKind + 4 helpers
│   ├── snapshot_store.py                  # SnapshotStore + 2 exceptions
│   └── subplot_helpers.py                 # ← NEW from infra/subplot/helpers.py (3 functions)
└── tests/                                 # 12 test files (from tests/world_model/) + __init__.py
```

### 3.2 Pyproject.toml 设计

```toml
[project]
name = "lingwen-world-model"
version = "0.1.0"
description = "LingWen · World Model (Ripple + Subplot + Snapshot engine)"
requires-python = ">=3.12"
dependencies = [
    "lingwen-core",  # transitive dep via lingwen_core.domain.{chapter, common, ripple, subplot}
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_world_model"]
include = ["src/lingwen_world_model/**/*.py"]
```

### 3.3 不变量 #50 (NEW)

```yaml
- id: I050
  rule: "packages/lingwen-world-model/ 是 World Model (Ripple + Subplot + Snapshot) 引擎的唯一实包; infra.world_model.* 路径非法 (Phase 35+)"
  severity: error
  scope: "all new world model code; enforcement via tests/test_phase35_world_model.py::test_infra_world_model_deleted + test_infra_subplot_helpers_deleted + grep -rln 'infra\\.world_model\\b' --include='*.py' . → 0 行"
```

---

## 4. 迁移映射

### 4.1 Source file 迁移 (11 files)

| 源 | 目标 |
|----|------|
| `infra/world_model/__init__.py` | `packages/lingwen-world-model/src/lingwen_world_model/__init__.py` |
| `infra/world_model/engine.py` | `.../engine.py` |
| `infra/world_model/character_snapshot.py` | `.../character_snapshot.py` |
| `infra/world_model/foreshadow_snapshot.py` | `.../foreshadow_snapshot.py` |
| `infra/world_model/key_point_graph.py` | `.../key_point_graph.py` |
| `infra/world_model/lifecycle.py` | `.../lifecycle.py` |
| `infra/world_model/links.py` | `.../links.py` |
| `infra/world_model/queries.py` | `.../queries.py` |
| `infra/world_model/registry.py` | `.../registry.py` |
| `infra/world_model/snapshot_diff.py` | `.../snapshot_diff.py` |
| `infra/world_model/snapshot_store.py` | `.../snapshot_store.py` |
| `infra/subplot/helpers.py` | `.../subplot_helpers.py` (filename rename:helpers → subplot_helpers) |

### 4.2 Intra-package import 修复 (C2 内完成,8 sites)

| 文件 | 旧 import | 新 import |
|------|----------|----------|
| `engine.py:23` | `from infra.world_model.lifecycle import (...)` | `from lingwen_world_model.lifecycle import (...)` |
| `engine.py:30` | lazy `from infra.world_model.queries import detect_unresolved_ripples` | `from lingwen_world_model.queries import ...` |
| `links.py:35` | lazy `from infra.world_model.registry import RippleRegistry` | `from lingwen_world_model.registry import ...` |
| `registry.py:26` | `from infra.world_model.lifecycle import MAX_OPEN_RIPPLOTS` | `from lingwen_world_model.lifecycle import ...` |
| `queries.py:22` | `from infra.world_model.lifecycle import (...)` | `from lingwen_world_model.lifecycle import (...)` |
| `character_snapshot.py:6` | lazy `from infra.world_model.character_snapshot import (...)` | `from lingwen_world_model.character_snapshot import (...)` |
| `foreshadow_snapshot.py:7` | lazy `from infra.world_model.foreshadow_snapshot import (...)` | `from lingwen_world_model.foreshadow_snapshot import (...)` |
| `__init__.py:53` | `from infra.subplot.helpers import (add_subplot, get_active_subplots, subplots_count)` | `from lingwen_world_model.subplot_helpers import (...)` |

### 4.3 External consumer migration (4 files)

| 文件 | 旧 import | 新 import | 备注 |
|------|----------|----------|------|
| `infra/poc/run_volume_1.py:44` | `from infra.world_model import (...)` | `from lingwen_world_model import (...)` | 1 import site |
| `tests/subplot/test_subplot_integration.py:27` | `from infra.subplot.helpers import (...)` | `from lingwen_world_model.subplot_helpers import (...)` | 1 import site |
| `tests/consistency/checkers/test_pacing_ripple_integration.py:30` | `from infra.world_model.registry import RippleRegistry` | `from lingwen_world_model.registry import RippleRegistry` | 1 import site |
| `tests/consistency/checkers/test_foreshadow_ripple_alignment.py:28-29` | `from infra.world_model.{lifecycle,registry} import (...)` | `from lingwen_world_model.{lifecycle,registry} import (...)` | 2 import sites |

### 4.4 In-package tests 跟随迁移 (12 files, C3)

| 源 | 目标 |
|----|------|
| `tests/world_model/test_character_snapshot.py` | `packages/lingwen-world-model/tests/test_character_snapshot.py` |
| `tests/world_model/test_integration.py` | `.../test_integration.py` |
| `tests/world_model/test_key_point_graph.py` | `.../test_key_point_graph.py` |
| `tests/world_model/test_links.py` | `.../test_links.py` |
| `tests/world_model/test_phase2_integration.py` | `.../test_phase2_integration.py` |
| `tests/world_model/test_ripple_engine.py` | `.../test_ripple_engine.py` |
| `tests/world_model/test_ripple_integration.py` | `.../test_ripple_integration.py` |
| `tests/world_model/test_ripple_lifecycle.py` | `.../test_ripple_lifecycle.py` |
| `tests/world_model/test_ripple_queries.py` | `.../test_ripple_queries.py` |
| `tests/world_model/test_ripple_registry.py` | `.../test_ripple_registry.py` |
| `tests/world_model/test_snapshot_diff.py` | `.../test_snapshot_diff.py` |
| `tests/world_model/test_snapshot_store.py` | `.../test_snapshot_store.py` |
| `tests/world_model/test_world_snapshot.py` | `.../test_world_snapshot.py` |

**注意**: Phase 32 lessons applied — 13 files (我之前算 12,实际 13;包含 `test_world_snapshot.py`)。所有 13 files 都使用 `from infra.world_model.X` 形式,迁移时 sed 替换为 `from lingwen_world_model.X`。

### 4.5 Filesystem-path string literal audit (preC7)

Phase 34 lesson #4 (4th occurrence): 文件系统路径 string literals (`infra/world_model` 在 `Path(...)` 或 string-built path) 不被 import grep 抓到。需要审计:

```bash
grep -rn '"infra/world_model' --include="*.py" .
grep -rn '"infra/subplot/helpers' --include="*.py" .
grep -rn "infra/world_model" --include="*.md" .
```

已知高风险 site:`infra/poc/run_volume_1.py:312` (string literal `source="infra.world_model.WorldSnapshot"`)。该 site 在 C5 同步迁移。

---

## 5. 风险 + 缓解

| 风险 | 缓解 |
|------|------|
| `infra/subplot/helpers.py` 是 infra/subplot 唯一非-shim 行为服务,Phase 35 一并迁出后 infra/subplot/__init__.py 形变 | 验证 `infra/subplot/__init__.py` 不再引用 helpers.py;若仍引用,加 deprecation re-export 或一并清理 |
| `infra/world_model/__init__.py` cross-package 引 `infra.subplot.helpers` → 引 `lingwen_world_model.subplot_helpers` 后,需确认无循环依赖 | lingwen-world-model 不依赖 infra,依赖 lingwen-core (already);反向 infra/subplot 不依赖 lingwen-world-model |
| 13 in-package tests 迁移后 pytest conftest 可能 namespace 冲突 (Phase 34 lesson) | 新 package 用 `tests/` 目录 + pytest rootdir=`packages/lingwen-world-model` (mirror lingwen-got) |
| `infra/poc/run_volume_1.py:312` string literal `source="infra.world_model.WorldSnapshot"` 在 C5 一起改;漏改将造成 stale reference | C5 commit 内含 grep 验证 |
| ruff 引入新 errors (新 __init__.py 比原 file 长) | pre-commit ruff check + ruff --fix (Phase 34 lesson) |
| worktree venv env-sync | `--offline` flag + worktree `.venv/bin/python` (MEMORY.md N.14) |
| .db 文件误 add (Phase 34 C3 lesson) | `git add <explicit paths>` 而非 `git add dir/` |
| uv sync 在 workspace member 注册前运行 → import 失败 (Phase 34 lesson) | C1 先改 root pyproject.toml workspace members,再 uv sync |

---

## 6. Validation gates (Phase 34 pattern)

| Gate | 内容 | Target |
|------|------|--------|
| G1 | ruff check on new/modified files | clean |
| G2 | `tests/test_phase35_world_model.py` regression guards | 9+/9+ GREEN |
| G3 | `packages/lingwen-world-model/tests/` | 201/201 PASS (baseline) |
| G4 | `packages/lingwen-core/tests/` | 68/68 PASS (baseline 不变) |
| G5 | `packages/lingwen-got/tests/` | 208/208 PASS (invariant 保护) |
| G6 | `tests/world_model/` (old path) | 0 files (deleted) |
| G7 | `infra/subplot/helpers.py` | 0 files (deleted) |
| G8 | `apps/studio_api/tests/` | 82/82 PASS (invariant 保护) |
| G9 | `tests/consistency/checkers/` (2 ripple 文件) | 22/22 PASS (migrated) |
| G10 | `tests/subplot/test_subplot_integration.py` | 11/11 PASS (migrated) |
| G11 | Audit grep `infra.world_model\b` → 0 行 + `infra/world_model/` dir 不存在 | 0 hits |
| G12 | workspace member 已注册 + `uv run python -c "import lingwen_world_model"` | 0 errors |

---

## 7. Rollback plan

Phase 35 ff-merge to master 后若发现严重问题:
1. `git checkout master`
2. `git revert -m 1 <merge-commit>` (no merge commit for ff-merge, 直接 revert phase branch HEAD)
3. 具体: `git revert <c8-commit-sha>` (回退到 Phase 34)
4. ruff + pytest 重跑 → 应回到 v33.0 baseline

worktree 内: 直接 `git worktree remove .worktrees/phase-35-world-model-package --force`。

---

## 8. 不变更记录

- #I001 (infra/ 禁 import apps/) — 不变
- #I049 (packages/lingwen-got/ 是 GoT 唯一实包) — 不变
- #I050 NEW (packages/lingwen-world-model/ 是 World Model 唯一实包) — 本 phase 新增

---

## 9. 关联文档

- Phase 32 (v32.0) handoff: `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md` (sister phase)
- Phase 34 (v33.0) handoff: `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md` (sister phase — pattern 来源)
- Phase 35 plan: `docs/superpowers/plans/2026-09-08-phase-35-world-model-package.md`
- architecture.yml: `.lingwen/architecture.yml` (不变量 truth source)
