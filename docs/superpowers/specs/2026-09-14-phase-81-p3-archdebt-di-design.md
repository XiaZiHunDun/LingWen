# Phase 81 — P3-ARCHDEBT `infra/di/` → `packages/lingwen-di/`

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

## 1. 背景

闭环 **ARCHDEBT-CANDIDATES.md Top 5 候选 #3** (`infra/di/`, 309 LOC, 2 source files, 2 test consumers, TRUE LEAF) — 第三例 ARCHDEBT-REAL cycle 真迁移 (Phase 79 LEAF story_contracts + Phase 80 NOT-LEAF subplot + Phase 81 TRUE LEAF di)。模式 verification 第三例确认 migration pattern 适用不同 package shape。

**触发**:
- ARCHDEBT-CANDIDATES.md 排名 #3 candidate (`infra/di/`, 309 LOC, TRUE LEAF 0 workspace deps)
- Phase 79 (LEAF) + Phase 80 (NOT-LEAF) 都 success 后, Phase 81 测试 TRUE LEAF 简化路径
- I079 模板 + 9-pattern audit + §A test files migration plan 全套防御机制 ready

**Phase 目标**: 把 `infra/di/` (依赖注入 Layer 系统 + Tag + Runtime + 8 public symbols) 迁移到 `packages/lingwen-di/`, 成为 canonical implementation。`infra.di.*` 路径非法 (I082 NEW invariant)。`infra/di/` 全删。

## 2. 9-pattern 审计结果

| # | Pattern | Verdict | Sites |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports (top-level) | ✅ None | 0 (all imports are function-body) |
| 2 | Indented/function-body imports | ✅ Found | 2 sites in `tests/test_infra_modules.py:456,483` |
| 3 | Relative imports (intra-module) | ✅ Found | 1 site in `__init__.py:11` (`from .layer import ...`) |
| 4 | Filesystem path string literals | ✅ None | 0 |
| 5 | Wildcard `from X import *` | ✅ None | 0 |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ None | 0 |
| 7 | `import X as Y` re-exports | ✅ None | 0 |
| 8 | Doc comments referencing old path | ✅ Found | 2 sites: `tests/test_infra_init_no_deferred_re_exports.py:19,42` (docstring + FORBIDDEN_PATTERNS tuple) |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Found | 2 files: `tests/test_phase53d_event_sourcing.py:152,170` (N.14 v22 — `"di"` in remaining_subdirs list) + `tests/test_phase18_8_infra_init_simplified.py:6,53` (docstring + test_infra_init_no_stale_di) |

**Source LOC tally**:
```
   32 infra/di/__init__.py
  277 infra/di/layer.py
  309 total
```

**Public API** (8 symbols): `Layer`, `Runtime`, `Tag`, `get_runtime`, `make`, `make_with_deps`, `provide`, `reset_runtime`

**Workspace deps**: **0 (TRUE LEAF)** — only stdlib (`logging`, `dataclasses`, `typing`)

**Consumer count** (3 sites total):
- Production: 0 (only test consumers — `infra/di` is NOT used in production code)
- Tests: 1 file MIGRATE + 1 file in-place rewrite:
  - `tests/test_infra_modules.py:456,483` (2 function-body imports) → **MIGRATE** to `packages/lingwen-di/tests/`
  - `tests/test_infra_init_no_deferred_re_exports.py:19,42` (docstring + FORBIDDEN_PATTERNS tuple) → **IN-PLACE** docstring update only (test function `test_infra_init_no_stale_di` already passes since `Tag/Layer/Runtime` not re-exported from `infra`)

## 3. 配套 stale refs (清理清单)

- `tests/test_phase53d_event_sourcing.py:152,170` — drop `"di"` from `remaining_subdirs` list + add `assert not exists` (N.14 v22 lesson)
- `tests/test_phase18_8_infra_init_simplified.py:6` — update docstring (no longer "deferred", now gone)
- `tests/test_infra_init_no_deferred_re_exports.py:19` — update docstring narrative ("moved to packages/lingwen-di/" not "deleted")
- `tests/test_infra_init_no_deferred_re_exports.py:42` — keep FORBIDDEN_PATTERNS tuple as-is (the pattern `from infra.di.layer import` will still not match anything post-migration, so the assertion still passes)

## 4. 计划 (7 atomic commits — simplified)

| # | Subject | Files | +/- | Risk |
|---|---------|-------|-----|------|
| C0 | `docs(phase-81): spec + 9-pattern audit` | 1 file (this spec) | +1 / -0 | none |
| C1 | `chore(pkg): scaffold packages/lingwen-di/` | 3 files (pyproject.toml + 2 modules including __init__.py) + pyproject.toml workspace member | +309 / -0 | low — pure scaffold, TRUE LEAF |
| C2 | `chore(tests): MIGRATE test_infra_modules.py + IN-PLACE docstring fixup` | 1 file MIGRATE + 1 file in-place | +TBD / -TBD | low — pathspec BOTH + simple docstring update |
| C3 | `chore(archdebt): FULL DELETE infra/di/ + I082 invariant` | 2 source files deleted + 1 entry in architecture.yml | -309 / +14 | medium — `infra.di.*` 完全消失 |
| C4 | `test(phase-81): prior-phase guards fixup (test_phase53d + test_phase18_8)` | 2 files | ~10 / ~5 | low — N.14 v22 lesson defense |
| C5 | `test(phase-81): 12 regression guards` | 1 file (tests/test_phase81_p3_archdebt_di.py) | +12 tests / -0 | low — 12 guards G1-G12 |
| C6 | `docs(phase-81): CLAUDE.md v54.13 + CURRENT_STATUS + BACKLOG + handoff sync` | 4 files | doc-only | none |

**Total**: 7 atomic commits on branch `phase-81-p3-archdebt-di` (one fewer than Phase 79/80 since C2a/C2b合并成单 C2 — only 1 test file MIGRATE, no separate production migration needed).

## 5. §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

1 test file referencing `infra.di`:

| File | LOC | pytest path | Plan |
|------|-----|-------------|------|
| tests/test_infra_modules.py | TBD | tests/ | **MIGRATE** → packages/lingwen-di/tests/ |

(Plus 1 in-place docstring fixup: `tests/test_infra_init_no_deferred_re_exports.py` — no MIGRATE, just narrative update)

### A2. MIGRATE 路径

- [x] **目标位置**: `packages/lingwen-di/tests/`
- [x] **迁移步骤**: `git mv tests/test_infra_modules.py packages/lingwen-di/tests/test_infra_modules.py` (single C2 commit, pathspec BOTH old + new for blame preservation)
- [x] **Imports 迁移**: `from infra.di.layer import` → `from lingwen_di.layer import` (sed 全 file)
- [x] **sys.path hack cleanup**: 检查 conftest.py 是否需要 (待验证 — Phase 56b lesson 1 模式)
- [x] **cwd-relative path fixup**: 检查是否用 `Path("tests/...")` (Phase 56b2 lesson 2)
- [x] **Functional gate**: `pytest packages/lingwen-di/tests/ -v` 必须 100% pass

### A3. DELETE 路径

**不适用** — 1 test file MIGRATE, 1 in-place docstring fixup, 无 DELETE。

### A4. RETAIN-ORPHAN 路径

**NOT ALLOWED** — 测试已 MIGRATE 或 IN-PLACE, 无 RETAIN-ORPHAN。

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

- [x] **C2 commit pathspec** 包含 BOTH `tests/test_infra_modules.py` (old) AND `packages/lingwen-di/tests/test_infra_modules.py` (new)
- [x] **C2 commit message**: "MIGRATE test_infra_modules.py from tests/ → packages/lingwen-di/tests/ + import rewrite + in-place docstring fixup"
- [x] **C3 commit pathspec** 包含 `infra/di/` (test 已经在 C2 移到新位置,这里仅删 `infra/` 目录)
- [x] **C3 commit message**: "FULL DELETE infra/di/ + I082 invariant (tests migrated in C2)"
- [x] **验证**: `git show <C2-SHA> --stat` 必须显示 1 test file 在 renames 列表中;`git show <C3-SHA> --stat` 必须显示 infra/di/ 在 deletions 列表中

## 6. 验证 gates

- [x] `ruff check packages/lingwen-di/` clean
- [x] `pytest packages/lingwen-di/tests/ -v` 100% pass
- [x] `pytest tests/test_infra_init_no_deferred_re_exports.py -v` 100% pass (FORBIDDEN_PATTERNS still passes after Phase 81)
- [x] 9-pattern audit clean: `grep -rln "infra\.di" --include="*.py"` 仅命中历史 archive/comments
- [x] 12 NEW guards GREEN (test_phase81_p3_archdebt_di.py)
- [x] 2 prior-phase guards UPDATED: Phase 53d 7 (C4 fixup drop "di" from list) + Phase 18_8 5 (C4 docstring)
- [x] `from infra.di.X import` → ModuleNotFoundError (C3 验证)
- [x] `from lingwen_di.X import` works (C1+C2 验证)

## 7. 风险评估

| Risk | Mitigation |
|------|-----------|
| Workspace deps detection (TRUE LEAF, only stdlib) | C1 pyproject.toml `dependencies = []` |
| test_infra_init_no_stale_di still passes after Phase 81 (Tag/Layer/Runtime not in infra anymore) | Already true — test scans infra/__init__.py FORBIDDEN_PATTERNS, will still pass |
| FORBIDDEN_PATTERNS tuple still contains "infra.di.layer" literal after Phase 81 | KEEP AS-IS — tuple pattern checks that nothing in `infra/__init__.py` re-exports infra.di, which is still true post-migration (infra.di is gone) |
| test_phase53d remaining_subdirs list still has "di" (N.14 v22) | C4 explicit fixup |
| test_phase18_8 docstring narrative mentions "di" | C4 update |

## 8. 不在范围 (defer list)

- ❌ **不**改 workspace deps (`packages/lingwen-di/pyproject.toml` 仅声明 `dependencies = []`,TRUE LEAF)
- ❌ **不**新增 I083-I089 — 本 phase 仅 I082 NEW (1 invariant)
- ❌ **不**touch `infra/di/__pycache__/` — gitignored
- ❌ **不**改 FORBIDDEN_PATTERNS tuple in `tests/test_infra_init_no_deferred_re_exports.py:42` — keeping the "infra.di.layer re-export" check is still semantically meaningful (defense in depth)

## 9. 完工标准

- [x] 7 atomic commits on branch `phase-81-p3-archdebt-di`
- [x] `infra/di/` 完全消失 (git ls-files 验证)
- [x] `packages/lingwen-di/` 含 2 sub-modules + __init__.py + pyproject.toml + tests/
- [x] I082 NEW invariant in `.lingwen/architecture.yml`
- [x] CLAUDE.md v54.12 → v54.13 + invariant table 加 I082 row
- [x] `collaboration/CURRENT_STATUS.md` 更新 ✅ entry + `collaboration/BACKLOG.md` 滚动
- [x] `docs/superpowers/handoffs/2026-09-14-phase-81-p3-archdebt-di-handoff.md`
- [x] Branch ready for ff-merge

## 10. Lessons from prior phases (per I079 §C)

- **Phase 56b (world_db)**: tests/X/ → packages/<pkg>/tests/ + sys.path cleanup
- **Phase 56c (cross_volume)**: pathspec BOTH old + new commit, `chr(47)` regex split trick
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location, docstring-stripped regex
- **Phase 79 (story_contracts)**: (1) `__pycache__/` 残留 (N.14 v23) — apply same `rm -rf` cleanup; (2) Regex anchored checks — apply same strip pattern; (3) Worktree `.venv/bin/python` — same `uv pip install -e` workflow
- **Phase 80 (subplot)**: (1) `__all__` 列表 vs 实际 import 不一致 (pre-existing bug); (2) Intra-package absolute imports 是 future cleanup opportunity
- **N.14 lesson 1 (9-pattern audit matrix)**: Phase 51+ 完整谱系 — Phase 81 audit 已覆盖 9-pattern 全套

## 11. Anti-patterns (per I079 §D)

- ❌ C3 commit **只**写 "+ I082" 而不列 test files
- ❌ 让 `tests/` 留下孤儿文件
- ❌ MIGRATE 测试用 `git rm` 旧路径 + `git add` 新路径 (分开 commit)
- ❌ spec 缺 §A test files migration plan
- ❌ "defer test migration to followup" (Phase 56c lesson 3)