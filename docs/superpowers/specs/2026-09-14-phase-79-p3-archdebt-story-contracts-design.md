# Phase 79 — P3-ARCHDEBT `infra/story_contracts/` → `packages/lingwen-story-contracts/`

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

## 1. 背景

闭环 **Phase 41+++ ARCHDEBT-CANDIDATES.md** 排名 #1 candidate (`infra/story_contracts/`, 848 LOC, 8 consumers, 3 subdirs) — multi-week P3-ARCHDEBT 真迁移。Phase 78 闭环后,infra/ 顶层只剩 6 active subdirs,本 phase 启动 ARCHDEBT 真迁移 → `packages/*` 系列。

**触发**:
- ARCHDEBT-CANDIDATES.md Top 5 候选 #1 (Phase 41+++ 闭环:ranked by NOT-LEAF + high fan-out,不是 leaf 但是高 ROI)
- Phase 56-78 P3-ARCHDEBT cycle 固化 (~17022 LOC 死代码清理后),真迁移 candidate 上台
- I079 模板 + 9-pattern audit + §A test files migration plan 全套防御机制 ready

**Phase 目标**: 把 `infra/story_contracts/` (story contracts + genre routing + anti-pattern constraints + injection) 迁移到 `packages/lingwen-story-contracts/`,成为 canonical implementation。`infra.story_contracts.*` 路径非法 (I080 NEW invariant)。`infra/story_contracts/` 全删。

## 2. 9-pattern 审计结果

| # | Pattern | Verdict | Sites |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports (top-level) | ✅ Found | 7 sites: `tests/story_contracts/*.py` 5 files (6 imports) |
| 2 | Indented/function-body imports | ✅ Found | 2 sites: `packages/lingwen-cli/.../story_contract.py:37` + `packages/lingwen-core/.../context_helpers.py:40` |
| 3 | Relative imports (intra-module) | ✅ Found | 11 sites in `infra/story_contracts/{__init__,engine,injector,persister}.py` (intra-package,自动修复 when moved) |
| 4 | Filesystem path string literals | ✅ Clean | 0 sites |
| 5 | Wildcard `from X import *` | ✅ Clean | 0 sites |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ Clean | 0 sites |
| 7 | `import X as Y` re-exports | ✅ Clean | 0 sites |
| 8 | Doc comments referencing old path | ✅ Found | 4 sites: `packages/lingwen-core/.../context_helpers.py:2,7,25` + `context_builder.py:66` (narrative only — fix in C2a) |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Found | 2 files: `tests/test_phase53d_event_sourcing.py:152,169` + `tests/test_phase18_8_infra_init_simplified.py:6` (N.14 v22 lesson — fix in C4) |

**Source LOC tally**:
```
   21 infra/story_contracts/__init__.py
   59 infra/story_contracts/anti_patterns.py
  178 infra/story_contracts/engine.py
  122 infra/story_contracts/injector.py
   58 infra/story_contracts/paths.py
  247 infra/story_contracts/persister.py
  163 infra/story_contracts/router.py
  848 total
```

**Public API** (10 symbols): `StoryContractEngine`, `StoryContractPaths`, `GenreRouter`, `RouteResult`, `AntiPattern`, `AntiPatternAggregator`, `ContractPayload`, `ContractPersister`, `StoryContractInjector`, `inject_story_contract`

**Workspace deps**: **ZERO** (TRUE LEAF) — infra/story_contracts source 仅依赖 stdlib (`dataclasses`, `datetime`, `pathlib`, `json`, `re`, `typing`) + intra-module。

**Test files LOC**:
```
   76 tests/story_contracts/test_anti_patterns.py
  217 tests/story_contracts/test_engine.py
   61 tests/story_contracts/test_paths.py
  155 tests/story_contracts/test_persister.py
  421 tests/story_contracts/test_router.py
  930 total
```

## 3. 配套 stale refs (清理清单)

- `tests/test_phase53d_event_sourcing.py:152` (docstring) + `:169` (literal in list) — N.14 v22 fixup
- `tests/test_phase18_8_infra_init_simplified.py:6` (docstring listing deleted modules)
- `packages/lingwen-core/.../context_helpers.py:2,7,25` (docstring narrative about `infra.story_contracts` lazy stub)
- `packages/lingwen-core/.../context_builder.py:66` (Phase 17.0 narrative about deferred infra.story_contracts)

## 4. 计划 (8 atomic commits)

| # | Subject | Files | +/- | Risk |
|---|---------|-------|-----|------|
| C0 | `docs(phase-79): spec + 9-pattern audit` | 1 file (this spec) | +1 / -0 | none |
| C1 | `chore(pkg): scaffold packages/lingwen-story-contracts/` | 8 files (pyproject.toml + 6 modules + __init__.py) | +848 / -0 | low — pure scaffold, no consumers |
| C2a | `refactor(story-contracts): migrate 2 production function-body imports` | 2 files (story_contract.py:37 + context_helpers.py:40 + docstring fixups) | ~5 / -5 | low — pattern from Phase 37-40 |
| C2b | `chore(tests): move 5 test files to packages/lingwen-story-contracts/tests/` | 5 files (BOTH `tests/story_contracts/*.py` source + `packages/lingwen-story-contracts/tests/*.py` destination) | +930 / -930 | low — pathspec BOTH per I079 §A5 |
| C3 | `chore(archdebt): FULL DELETE infra/story_contracts/ + tests/story_contracts/ + I080 invariant` | 12 files deleted + 1 entry in architecture.yml | -848 / +14 | medium — `infra.story_contracts.*` canonical module 完全消失 (类似 Phase 40b) |
| C4 | `test(phase-79): prior-phase guards fixup (test_phase53d + test_phase18_8)` | 2 files | ~10 / ~5 | low — N.14 v22 lesson defense |
| C5 | `test(phase-79): 12 regression guards` | 1 file (tests/test_phase79_p3_archdebt_story_contracts.py) | +12 tests / -0 | low — 12 guards G1-G12 |
| C6 | `docs(phase-79): CLAUDE.md v54.11 + CURRENT_STATUS + BACKLOG + handoff sync` | 4 files | doc-only | none |

**Total**: 8 atomic commits on branch `phase-79-p3-archdebt-story-contracts`。

## 5. §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

5 test files in `tests/story_contracts/`, **all** 测试 `infra.story_contracts.*`:

| File | LOC | pytest path | Plan |
|------|-----|-------------|------|
| test_anti_patterns.py | 76 | tests/story_contracts/ | **MIGRATE** → packages/lingwen-story-contracts/tests/ |
| test_engine.py | 217 | tests/story_contracts/ | **MIGRATE** → packages/lingwen-story-contracts/tests/ |
| test_paths.py | 61 | tests/story_contracts/ | **MIGRATE** → packages/lingwen-story-contracts/tests/ |
| test_persister.py | 155 | tests/story_contracts/ | **MIGRATE** → packages/lingwen-story-contracts/tests/ |
| test_router.py | 421 | tests/story_contracts/ | **MIGRATE** → packages/lingwen-story-contracts/tests/ |

grep verification: `grep -rln "infra\.story_contracts" tests/story_contracts/`

### A2. MIGRATE 路径

- [x] **目标位置**: `packages/lingwen-story-contracts/tests/`
- [x] **迁移步骤**: `git mv` per-file (single C2b commit, pathspec BOTH old + new for blame preservation — Phase 56c lesson 1)
- [x] **Imports 迁移**: `from infra.story_contracts.X import` → `from lingwen_story_contracts.X import` (sed 全 file,机械替换)
- [x] **sys.path hack cleanup**: 检查 `tests/story_contracts/__init__.py` (0 bytes) + tests/ 是否有 conftest.py with sys.path.insert (待验证)
- [x] **cwd-relative path fixup**: 检查 5 文件是否用 `Path("tests/...")` (Phase 56b2 lesson 2)
- [x] **Functional gate**: `pytest packages/lingwen-story-contracts/tests/ -v` 必须 100% pass (目标 ~50 tests,取决于现有 collection 数)

### A3. DELETE 路径

**不适用** — 5 test files 全部 MIGRATE,无 DELETE。

### A4. RETAIN-ORPHAN 路径

**NOT ALLOWED** — 所有 5 test files MIGRATE,无 RETAIN-ORPHAN。

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

- [x] **C2b commit pathspec** 包含 BOTH `tests/story_contracts/*.py` (old) AND `packages/lingwen-story-contracts/tests/*.py` (new) — single commit blame preservation
- [x] **C2b commit message**: "MIGRATE 5 test files from tests/story_contracts/ → packages/lingwen-story-contracts/tests/ + import rewrite"
- [x] **C3 commit pathspec** 包含 BOTH `infra/story_contracts/` AND `tests/story_contracts/` (后者已经在 C2b 移到新位置,这里仅删 `infra/` 目录)
- [x] **C3 commit message**: "FULL DELETE infra/story_contracts/ + tests/story_contracts/ (moved to packages/lingwen-story-contracts/ in C2b) + I080 invariant"
- [x] **验证**: `git show <C2b-SHA> --stat` 必须显示 5 test files 在 renames 列表中;`git show <C3-SHA> --stat` 必须显示 infra/story_contracts/ 在 deletions 列表中

## 6. 验证 gates

- [x] `ruff check packages/lingwen-story-contracts/` clean
- [x] `pytest packages/lingwen-story-contracts/tests/ -v` 100% pass (target ~50 tests)
- [x] `pytest packages/lingwen-cli/tests/ -v` 100% pass (consumer)
- [x] `pytest packages/lingwen-core/tests/ -v` 100% pass (consumer)
- [x] 9-pattern audit clean: `grep -rln "infra\.story_contracts" --include="*.py" --include="*.ts"` 仅命中历史 archive/comments
- [x] 12 NEW guards GREEN (test_phase79_p3_archdebt_story_contracts.py)
- [x] 7 prior-phase guards PRESERVED: Phase 53d 7 + Phase 60 6 + Phase 77 12 (C4 fixup 更新 Phase 53d + Phase 18_8 docstring)
- [x] `from infra.story_contracts.X import` → ModuleNotFoundError (C3 验证)
- [x] `from lingwen_story_contracts.X import` works (C1+C2b 验证)

## 7. 风险评估

| Risk | Mitigation |
|------|-----------|
| Function-body import miss (Pattern 2) | Pre-spec grep verified: 仅 2 sites (story_contract.py:37 + context_helpers.py:40) — Phase 37-40 pattern 复用 |
| Prior-phase guard breaks (Pattern 9, N.14 v22) | C4 显式 fixup test_phase53d:152,169 + test_phase18_8:6 — Phase 78 lesson 复用 |
| Half-migration recurrence (Phase 56b/56c/57b) | C2b pathspec BOTH + I079 §A5 single commit — 4 commits 防御 |
| Docstring narrative stale (Pattern 8) | C2a 改 context_helpers.py docstring 3 处 + context_builder.py:66 narrative |
| Workspace deps 检测漏检 | Pre-spec grep 验证 source 仅依赖 stdlib + intra-module — TRUE LEAF |
| Test functional gate fails post-migration | C2b 单一 import rewrite (`infra.story_contracts.X` → `lingwen_story_contracts.X`),无 logic 改动 — 风险低 |

## 8. 不在范围 (defer list)

- ❌ **不**改 `infra/story_contracts/` 内 logic / refactor — 纯 relocate
- ❌ **不**改 workspace deps (`packages/lingwen-story-contracts/pyproject.toml` 仅声明 `dependencies = []`,TRUE LEAF)
- ❌ **不**新增 I081-I089 — 本 phase 仅 I080 NEW (1 invariant)
- ❌ **不**re-run Phase 53e orphan runtime artifacts 审计 — Phase 78 已 closed 8 zero-consumer dirs,本次针对 active subdir
- ❌ **不**touch `infra/story_contracts/__pycache__/` — gitignored

## 9. 完工标准

- [x] 8 atomic commits on branch `phase-79-p3-archdebt-story-contracts`
- [x] `infra/story_contracts/` + `tests/story_contracts/` 完全消失 (git ls-files 验证)
- [x] `packages/lingwen-story-contracts/` 含 6 sub-modules + __init__.py + pyproject.toml + tests/ (5 files + conftest.py optional)
- [x] I080 NEW invariant in `.lingwen/architecture.yml`
- [x] CLAUDE.md v54.10 → v54.11 + invariant table 加 I080 row
- [x] `collaboration/CURRENT_STATUS.md` 更新 ✅ entry + `collaboration/BACKLOG.md` 滚动
- [x] `docs/superpowers/handoffs/2026-09-14-phase-79-p3-archdebt-story-contracts-handoff.md` (carryover closure)
- [x] Branch ready for ff-merge

## 10. Lessons from prior phases (per I079 §C)

- **Phase 56b (world_db)**: tests/X/ → packages/<pkg>/tests/ + sys.path cleanup
- **Phase 56c (cross_volume)**: pathspec BOTH old + new commit, `chr(47)` regex split trick
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location, docstring-stripped regex
- **Phase 78 (llm_benchmarks + poc)**: prior-phase guard N.14 v22 lesson — test_phase53d hardcoded `"story_contracts"` in list,本 phase C4 显式 fixup
- **N.14 lesson 1 (9-pattern audit matrix, 22nd time — Phase 76)**: 9-pattern 全套,本 spec §2 完整覆盖

## 11. Anti-patterns (per I079 §D)

- ❌ C3 commit **只**写 "+ I080" 而不列 test files
- ❌ 让 `tests/story_contracts/` 留下孤儿文件 (Phase 56c lesson 3)
- ❌ MIGRATE 测试用 `git rm` 旧路径 + `git add` 新路径 (分开 commit, blame 丢失 — Phase 56c lesson 1)
- ❌ spec 缺 §A test files migration plan (本 template 强制)
- ❌ "defer test migration to followup" (Phase 56c lesson 3: "defer = never")