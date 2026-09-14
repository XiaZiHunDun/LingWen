# Phase 80 — P3-ARCHDEBT `infra/subplot/` → `packages/lingwen-subplot/`

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

## 1. 背景

闭环 **ARCHDEBT-CANDIDATES.md Top 5 候选 #2** (`infra/subplot/`, 508 LOC, 10 consumers, NOT-LEAF) — 第二例 ARCHDEBT-REAL cycle 真迁移 (Phase 79 是第一例)。Phase 79 验证 ARCHDEBT-REAL cycle 模式可行后,Phase 80 启动 NOT-LEAF package 真迁移。

**触发**:
- ARCHDEBT-CANDIDATES.md 排名 #2 candidate (`infra/subplot/`, 508 LOC, NOT-LEAF 1 workspace dep lingwen-core)
- Phase 79 ARCHDEBT-REAL 第一例(LEAF package)成功后, Phase 80 启动 NOT-LEAF 真迁移
- I079 模板 + 9-pattern audit + §A test files migration plan 全套防御机制 ready

**Phase 目标**: 把 `infra/subplot/` (Plot/PlotType/PlotPurpose/PlotStatus + MAX_ACTIVE_SUBPLOTS + PlotRegistry + 6 状态转换 + 7 阶段模型 + 3 queries) 迁移到 `packages/lingwen-subplot/`, 成为 canonical implementation。`infra.subplot.*` 路径非法 (I081 NEW invariant)。`infra/subplot/` 全删。

## 2. 9-pattern 审计结果

| # | Pattern | Verdict | Sites |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports (top-level) | ✅ Found | 7 sites: `tests/subplot/*.py` (4 files, ~8 imports) + `tests/test_phase35_world_model.py` (1 docstring narrative) |
| 2 | Indented/function-body imports | ✅ Found | 1 site: `packages/lingwen-world-model/src/lingwen_world_model/links.py:41` |
| 3 | Relative imports (intra-module) | ✅ Found | 1 site in `__init__.py` (`from .registry import ...`) — auto-fixed when moved |
| 4 | Filesystem path string literals | ✅ Found | 5 sites: `packages/lingwen-world-model/src/lingwen_world_model/subplot_helpers.py:7` (docstring narrative) + `packages/lingwen-world-model/tests/test_ripple_registry.py:3` (docstring narrative) + `tests/test_phase35_world_model.py:4,104,106,158,165,167,185,186,280` (assertions about helpers.py — early-return safe) |
| 5 | Wildcard `from X import *` | ✅ Clean | 0 sites |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ Clean | 0 sites |
| 7 | `import X as Y` re-exports | ✅ Clean | 0 sites |
| 8 | Doc comments referencing old path | ✅ Found | 5 sites: `subplot_helpers.py:7` + `test_ripple_registry.py:3` + `lingwen-core/domain/subplot.py:3` (Phase 19 narrative) + `test_phase35_world_model.py:4` + `test_phase35_world_model.py:104` |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Found | 2 files: `tests/test_phase53d_event_sourcing.py:172` (N.14 v22 trigger — `"subplot"` in remaining_subdirs) + `tests/test_phase18_8_infra_init_simplified.py:6` (docstring narrative) |

**Source LOC tally**:
```
   51 infra/subplot/__init__.py
  133 infra/subplot/lifecycle.py
   95 infra/subplot/queries.py
  229 infra/subplot/registry.py
  508 total
```

**Public API** (15 symbols per `__init__.py`): `MAX_ACTIVE_SUBPLOTS`, `Plot`, `PlotPurpose`, `PlotStatus`, `PlotType`, `PlotRegistry`, `PlotNotFoundError`, `DuplicatePlotIdError`, `SubplotLimitExceeded`, `VALID_TRANSITIONS`, `CLOSING_MIN_CHAPTERS`, `STAGES`, `STAGE_TYPICAL_RANGES`, `can_open_new_subplot`, `suggest_subplot_to_close`, `detect_constraint_saturation`

**Workspace deps** (**NOT-LEAF**, 1 direct):
- `lingwen-core` — for `lingwen_core.domain.subplot` types (`MAX_ACTIVE_SUBPLOTS`, `Plot`, `PlotStatus`, `PlotType`, etc.)

**Intra-subplot absolute imports (pre-existing code smell)**: 
- `infra/subplot/queries.py:18` — `from infra.subplot.registry import PlotRegistry` (should be `from .registry`)
- `infra/subplot/registry.py:32` — `from infra.subplot.lifecycle import ...` (should be `from .lifecycle`)
- After migration, must be rewritten (`infra.subplot` doesn't exist). **Strategy**: pure sed `infra.subplot` → `lingwen_subplot` (becomes `from lingwen_subplot.registry import ...`) — works post-migration, future cleanup opportunity to relative imports.

**Consumer count** (10 total):
- Production (1 cross-package): `packages/lingwen-world-model/src/lingwen_world_model/links.py:41` (function-body import)
- Tests (7 files):
  - `tests/subplot/test_lifecycle.py`
  - `tests/subplot/test_queries.py`
  - `tests/subplot/test_subplot_integration.py`
  - `tests/subplot/test_subplot_registry.py`
  - `tests/test_phase35_world_model.py` (early-return safe pattern — file moves to `packages/lingwen-subplot/tests/`, path checks safely return)
  - `packages/lingwen-world-model/tests/test_links.py`
  - `packages/lingwen-world-model/tests/test_phase2_integration.py`
- Intra-subplot (already covered by package structure): `queries.py` + `registry.py`

## 3. 配套 stale refs (清理清单)

- `tests/test_phase53d_event_sourcing.py:172` — drop `"subplot"` from `remaining_subdirs` list + add `assert not exists` (N.14 v22 lesson)
- `tests/test_phase18_8_infra_init_simplified.py:6` — update docstring (no longer "deferred", now gone)
- `packages/lingwen-world-model/src/lingwen_world_model/subplot_helpers.py:7` — update docstring narrative ("moved to packages/lingwen-subplot/" not infra/subplot/helpers.py)
- `packages/lingwen-world-model/tests/test_ripple_registry.py:3` — update docstring narrative
- `packages/lingwen-core/src/lingwen_core/domain/subplot.py:3` — Phase 19 narrative (historical — leave as is or update to reflect Phase 80)
- `tests/test_phase35_world_model.py:4` — docstring (update Phase 79 + Phase 80 narrative)

## 4. 计划 (8 atomic commits)

| # | Subject | Files | +/- | Risk |
|---|---------|-------|-----|------|
| C0 | `docs(phase-80): spec + 9-pattern audit` | 1 file (this spec) | +1 / -0 | none |
| C1 | `chore(pkg): scaffold packages/lingwen-subplot/` | 5 files (pyproject.toml + 4 modules including __init__.py) + pyproject.toml workspace member | +508 / -0 | low — pure scaffold, NOT-LEAF (deps=[lingwen-core]) |
| C2a | `refactor(subplot): migrate production + intra-subplot absolute imports + docstrings` | 3 files (links.py:41 + queries.py:18 + registry.py:32 + 5 docstring narratives) | ~10 / -10 | low — sed rewrite |
| C2b | `chore(tests): MIGRATE 4 subplot test files + verify 3 lingwen-world-model test files` | 4 test files at new location + 3 cross-pkg test imports | +~850 / -~850 | low — pathspec BOTH per I079 §A5 |
| C3 | `chore(archdebt): FULL DELETE infra/subplot/ + I081 invariant` | 4 source files deleted + 1 entry in architecture.yml | -508 / +14 | medium — `infra.subplot.*` 完全消失 |
| C4 | `test(phase-80): prior-phase guards fixup (test_phase53d + test_phase18_8 + test_phase35)` | 3 files | ~10 / ~5 | low — N.14 v22 lesson defense |
| C5 | `test(phase-80): 12 regression guards` | 1 file (tests/test_phase80_p3_archdebt_subplot.py) | +12 tests / -0 | low — 12 guards G1-G12 |
| C6 | `docs(phase-80): CLAUDE.md v54.12 + CURRENT_STATUS + BACKLOG + handoff sync` | 4 files | doc-only | none |

**Total**: 8 atomic commits on branch `phase-80-p3-archdebt-subplot`。

## 5. §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

7 test files referencing `infra.subplot`:

| File | LOC | pytest path | Plan |
|------|-----|-------------|------|
| tests/subplot/test_lifecycle.py | TBD | tests/subplot/ | **MIGRATE** → packages/lingwen-subplot/tests/ |
| tests/subplot/test_queries.py | TBD | tests/subplot/ | **MIGRATE** → packages/lingwen-subplot/tests/ |
| tests/subplot/test_subplot_integration.py | TBD | tests/subplot/ | **MIGRATE** → packages/lingwen-subplot/tests/ |
| tests/subplot/test_subplot_registry.py | TBD | tests/subplot/ | **MIGRATE** → packages/lingwen-subplot/tests/ |
| packages/lingwen-world-model/tests/test_links.py | TBD | lingwen-world-model/tests/ | **IN-PLACE** rewrite imports (no MIGRATE) |
| packages/lingwen-world-model/tests/test_phase2_integration.py | TBD | lingwen-world-model/tests/ | **IN-PLACE** rewrite imports (no MIGRATE) |
| tests/test_phase35_world_model.py | TBD | tests/ | **IN-PLACE** rewrite imports + docstring + ensure early-return pattern (already has `if not p.exists(): return` per Phase 78 lesson 2 v22 sibling) |

### A2. MIGRATE 路径

- [x] **目标位置**: `packages/lingwen-subplot/tests/`
- [x] **迁移步骤**: `git mv` per-file (single C2b commit, pathspec BOTH old + new for blame preservation)
- [x] **Imports 迁移**: `from infra.subplot.X import` → `from lingwen_subplot.X import` (sed 全 file, 机械替换)
- [x] **sys.path hack cleanup**: 检查 4 文件是否需要 conftest.py (待验证 — Phase 56b lesson 1 模式)
- [x] **cwd-relative path fixup**: 检查 4 文件是否用 `Path("tests/...")` (Phase 56b2 lesson 2)
- [x] **Functional gate**: `pytest packages/lingwen-subplot/tests/ -v` 必须 100% pass

### A3. DELETE 路径

**不适用** — 7 test files 全部保留 (4 MIGRATE + 3 IN-PLACE),无 DELETE。

### A4. RETAIN-ORPHAN 路径

**NOT ALLOWED** — 所有 test files 已规划去向 (MIGRATE 或 IN-PLACE),无 RETAIN-ORPHAN。

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

- [x] **C2b commit pathspec** 包含 BOTH `tests/subplot/*.py` (old) AND `packages/lingwen-subplot/tests/*.py` (new)
- [x] **C2b commit message**: "MIGRATE 4 test files from tests/subplot/ → packages/lingwen-subplot/tests/ + import rewrite"
- [x] **C3 commit pathspec** 包含 `infra/subplot/` (tests 已经在 C2b 移到新位置,这里仅删 `infra/` 目录)
- [x] **C3 commit message**: "FULL DELETE infra/subplot/ + I081 invariant (tests migrated in C2b)"
- [x] **验证**: `git show <C2b-SHA> --stat` 必须显示 4 test files 在 renames 列表中;`git show <C3-SHA> --stat` 必须显示 infra/subplot/ 在 deletions 列表中

## 6. 验证 gates

- [x] `ruff check packages/lingwen-subplot/` clean
- [x] `pytest packages/lingwen-subplot/tests/ -v` 100% pass
- [x] `pytest packages/lingwen-world-model/tests/ -v` 100% pass (consumer)
- [x] 9-pattern audit clean: `grep -rln "infra\.subplot" --include="*.py"` 仅命中历史 archive/comments
- [x] 12 NEW guards GREEN (test_phase80_p3_archdebt_subplot.py)
- [x] 3 prior-phase guards PRESERVED/UPDATED: Phase 53d 7 (C4 fixup drop "subplot" from list) + Phase 18_8 5 (C4 docstring) + Phase 35 10 (C4 verify early-return still works)
- [x] `from infra.subplot.X import` → ModuleNotFoundError (C3 验证)
- [x] `from lingwen_subplot.X import` works (C1+C2b 验证)
- [x] `from lingwen_subplot.X import` from `packages/lingwen-world-model/` works (NOT-LEAF dep resolution)

## 7. 风险评估

| Risk | Mitigation |
|------|-----------|
| NOT-LEAF dep resolution (lingwen-subplot depends on lingwen-core) | Phase 80 C1 pyproject.toml `dependencies = ["lingwen-core"]`; uv workspace auto-resolves; verify with `uv pip install -e` from worktree |
| Intra-subplot absolute imports break (queries.py:18 + registry.py:32 use `from infra.subplot.X`) | C2a sed rewrite `infra.subplot` → `lingwen_subplot` (becomes valid absolute import post-migration). Future cleanup to relative imports possible |
| Prior-phase guard test_phase53d breaks (N.14 v22 trigger) | C4 explicit fixup: drop `"subplot"` from remaining_subdirs + add `assert not exists` + add `__pycache__/` residue lesson comment (Phase 79 v23 lesson) |
| test_phase35_world_model.py:280 checks `tests/subplot/test_subplot_integration.py` for stale imports | ALREADY SAFE — test has `if not p.exists(): return` early-return pattern (Phase 78 lesson 2 v22 sibling). After C2b moves file, path doesn't exist, test safely returns. Verify in C4. |
| test_phase35_world_model.py line 161 `"infra/subplot/" in str(p)` could trigger false-positive if any infra/subplot/ file remains | ALREADY HANDLED — test scans for `.py` files in `infra/`, after C3 FULL DELETE no `.py` files remain. Verify in C4. |
| Multiple docstring narrative updates (5 sites) | C2a + C4 bundle into manageable edits (1 production sed + 1 docstring fixup batch) |
| Workspace member declaration order (Phase 34 lesson) | C1 adds workspace member in pyproject.toml BEFORE first import attempt |
| Worktree `.venv/bin/python` (Phase 79 lesson 3) | Use `uv pip install -e packages/lingwen-subplot/` from worktree + `.venv/bin/python` for tests |

## 8. 不在范围 (defer list)

- ❌ **不**改 intra-subplot absolute imports → relative imports cleanup — defer to future code-quality phase (current state works post-migration, sed rewrite preserves semantics)
- ❌ **不**改 workspace deps (`packages/lingwen-subplot/pyproject.toml` 声明 `dependencies = ["lingwen-core"]`,NOT-LEAF)
- ❌ **不**新增 I082-I089 — 本 phase 仅 I081 NEW (1 invariant)
- ❌ **不**touch `infra/subplot/__pycache__/` — gitignored
- ❌ **不**migrate `packages/lingwen-world-model/tests/test_*.py` — IN-PLACE rewrite only (test files stay in lingwen-world-model, only imports change)

## 9. 完工标准

- [x] 8 atomic commits on branch `phase-80-p3-archdebt-subplot`
- [x] `infra/subplot/` 完全消失 (git ls-files 验证)
- [x] `packages/lingwen-subplot/` 含 4 sub-modules + __init__.py + pyproject.toml + tests/ (4 files + __init__.py)
- [x] I081 NEW invariant in `.lingwen/architecture.yml`
- [x] CLAUDE.md v54.11 → v54.12 + invariant table 加 I081 row
- [x] `collaboration/CURRENT_STATUS.md` 更新 ✅ entry + `collaboration/BACKLOG.md` 滚动
- [x] `docs/superpowers/handoffs/2026-09-14-phase-80-p3-archdebt-subplot-handoff.md`
- [x] Branch ready for ff-merge

## 10. Lessons from prior phases (per I079 §C)

- **Phase 56b (world_db)**: tests/X/ → packages/<pkg>/tests/ + sys.path cleanup
- **Phase 56c (cross_volume)**: pathspec BOTH old + new commit, `chr(47)` regex split trick
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location, docstring-stripped regex
- **Phase 79 (story_contracts)**: (1) `__pycache__/` 残留 (N.14 v23) — apply same `rm -rf` cleanup; (2) Regex anchored checks — apply same strip pattern; (3) Worktree `.venv/bin/python` — same `uv pip install -e` workflow
- **N.14 lesson 1 (9-pattern audit matrix)**: Phase 51+ 完整谱系 — Phase 80 audit 已覆盖 9-pattern 全套

## 11. Anti-patterns (per I079 §D)

- ❌ C3 commit **只**写 "+ I081" 而不列 test files
- ❌ 让 `tests/subplot/` 留下孤儿文件
- ❌ MIGRATE 测试用 `git rm` 旧路径 + `git add` 新路径 (分开 commit)
- ❌ spec 缺 §A test files migration plan
- ❌ "defer test migration to followup" (Phase 56c lesson 3)
- ❌ **NOT-LEAF** workspace dep declaration 漏 (`dependencies = []` for NOT-LEAF package 会让 import 失败)