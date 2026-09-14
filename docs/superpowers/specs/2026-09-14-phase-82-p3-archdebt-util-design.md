# Phase 82 — P3-ARCHDEBT `infra/util/` → `packages/lingwen-util/`

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

## 1. 背景

闭环 **ARCHDEBT-CANDIDATES.md Top 5 候选 #4** (`infra/util/`, 338 LOC, retry helper, NOT-LEAF) — 第四例 ARCHDEBT-REAL cycle 真迁移。Phase 79 LEAF + Phase 80 NOT-LEAF + Phase 81 TRUE LEAF 都 success 后, Phase 82 验证 NOT-LEAF retry helper pattern。

**Note**: 实际上 `infra/util/retry.py` 从 `lingwen_errors` import (NOT stdlib),所以 Phase 82 是 NOT-LEAF (1 workspace dep: `lingwen-errors`),不是 TRUE LEAF。这是 Phase 80 (NOT-LEAF subplot) 的简化版本(只有 1 intra-infra + 1 meta-test consumer)。

**触发**:
- ARCHDEBT-CANDIDATES.md 排名 #4 candidate (`infra/util/`, 338 LOC, retry helper)
- Phase 79-81 cluster 完成(LEAF + NOT-LEAF + TRUE LEAF)后, Phase 82 测试 NOT-LEAF retry helper 模式
- I079 模板 + 9-pattern audit + §A test files migration plan 全套防御机制 ready

**Phase 目标**: 把 `infra/util/` (RetryConfig + retry + retry_async + with_retry + is_transient_error + backoff_delay, 6 public symbols) 迁移到 `packages/lingwen-util/`, 成为 canonical implementation。`infra.util.*` 路径非法 (I083 NEW invariant)。`infra/util/` 全删。

## 2. 9-pattern 审计结果

| # | Pattern | Verdict | Sites |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports (top-level) | ✅ Found | 1 site: `infra/__init__.py:15` (intra-infra re-export) |
| 2 | Indented/function-body imports | ✅ None | 0 sites |
| 3 | Relative imports (intra-module) | ✅ Found | 1 site in `infra/util/__init__.py` (`from infra.util.retry import ...` — actually absolute, not relative; pre-existing) |
| 4 | Filesystem path string literals | ✅ None | 0 |
| 5 | Wildcard `from X import *` | ✅ None | 0 |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ None | 0 |
| 7 | `import X as Y` re-exports | ✅ None | 0 |
| 8 | Doc comments referencing old path | ✅ Found | 1 site: `infra/__init__.py:3` docstring (`config / util / errors`) |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Found | 2 files: `tests/test_phase53d_event_sourcing.py:152,172` (N.14 v22 — `"util"` in remaining_subdirs) + `tests/test_phase18_8_infra_init_simplified.py:6` (docstring) |

**Source LOC tally**:
```
   30 infra/util/__init__.py
  308 infra/util/retry.py
  338 total
```

**Public API** (6 symbols): `RetryConfig`, `retry`, `retry_async`, `with_retry`, `is_transient_error`, `backoff_delay`

**Workspace deps** (**NOT-LEAF**, 1 direct):
- `lingwen-errors` — for error classes (`AuthenticationError`, `BaseError`, `FatalError`, `NetworkError`, `RateLimitError`, `RetryableError`, `ServiceUnavailableError`, `TimeoutError`, `is_instance`)

**Consumer count** (2 sites):
- Production (intra-infra): `infra/__init__.py:15` (re-export from infra top level)
- Test (meta-test allowlist): `tests/test_phase18_10_stale_imports.py:18` (allowlist entry)
- **No test files to MIGRATE** — Phase 82 has no direct test consumers

## 3. 配套 stale refs (清理清单)

- `infra/__init__.py:15` — `from infra.util import` → `from lingwen_util import` (in-place rewrite)
- `infra/__init__.py:3` docstring — `(config / util / errors)` → `(config / errors)` (util is gone)
- `tests/test_phase18_10_stale_imports.py:18` — remove `"infra.util"` from ALLOWED_COMPAT_IMPORTS frozenset (it's gone now)
- `tests/test_phase53d_event_sourcing.py:152,172` — drop `"util"` from `remaining_subdirs` list + add `assert not exists` (N.14 v22 lesson)
- `tests/test_phase18_8_infra_init_simplified.py:6` — update docstring (no longer "deferred", now gone)

## 4. 计划 (7 atomic commits — simplified)

| # | Subject | Files | +/- | Risk |
|---|---------|-------|-----|------|
| C0 | `docs(phase-82): spec + 9-pattern audit` | 1 file (this spec) | +1 / -0 | none |
| C1 | `chore(pkg): scaffold packages/lingwen-util/` | 3 files (pyproject.toml NOT-LEAF + 2 modules) + pyproject.toml workspace member | +338 / -0 | low — pure scaffold, NOT-LEAF (deps=[lingwen-errors]) |
| C2 | `refactor(util): migrate 1 intra-infra + 1 meta-test consumer (in-place, no MIGRATE)` | 2 files (infra/__init__.py + test_phase18_10_stale_imports.py) | ~3 / ~3 | low — simple sed |
| C3 | `chore(archdebt): FULL DELETE infra/util/ + I083 invariant` | 2 source files deleted + 1 entry in architecture.yml | -338 / +14 | medium — `infra.util.*` 完全消失 |
| C4 | `test(phase-82): prior-phase guards fixup (test_phase53d + test_phase18_8)` | 2 files | ~10 / ~5 | low — N.14 v22 lesson defense |
| C5 | `test(phase-82): 12 regression guards` | 1 file (tests/test_phase82_p3_archdebt_util.py) | +12 tests / -0 | low — 12 guards G1-G12 |
| C6 | `docs(phase-82): CLAUDE.md v54.14 + CURRENT_STATUS + BACKLOG + handoff sync` | 4 files | doc-only | none |

**Total**: 7 atomic commits on branch `phase-82-p3-archdebt-util` (simplified — no separate C2a/C2b since no production + no MIGRATE test files).

## 5. §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

**No test files to MIGRATE** — Phase 82 has no direct test consumers (only intra-infra + meta-test allowlist).

### A2. MIGRATE 路径

**不适用** — 0 test files MIGRATE。

### A3. DELETE 路径

**不适用** — 0 test files DELETE。

### A4. RETAIN-ORPHAN 路径

**NOT ALLOWED** — 无 test files to begin with。

### A5. Half-migration defense (Phase 56b/56c/57b third occurrence)

**不适用** — 0 test files MIGRATE,所以无 half-migration risk。

## 6. 验证 gates

- [x] `ruff check packages/lingwen-util/` clean
- [x] `pytest packages/lingwen-util/` (no tests) — verify package imports OK
- [x] `pytest tests/test_phase18_8_infra_init_simplified.py -v` 100% pass
- [x] `pytest tests/test_phase18_10_stale_imports.py -v` 100% pass (allowlist updated)
- [x] `pytest tests/test_phase53d_event_sourcing.py -v` 100% pass
- [x] 9-pattern audit clean: `grep -rln "infra\.util" --include="*.py"` 仅命中历史 archive
- [x] 12 NEW guards GREEN (test_phase82_p3_archdebt_util.py)
- [x] 2 prior-phase guards UPDATED: Phase 53d (C4 fixup drop "util" from list) + Phase 18_8 (C4 docstring)
- [x] `from infra.util.X import` → ModuleNotFoundError (C3 验证)
- [x] `from lingwen_util.X import` works (C1+C2 验证)
- [x] `from lingwen_util.X import` from `packages/lingwen-util/` (NOT-LEAF dep resolution lingwen-errors)

## 7. 风险评估

| Risk | Mitigation |
|------|-----------|
| NOT-LEAF dep resolution (lingwen-util depends on lingwen-errors) | Phase 82 C1 pyproject.toml `dependencies = ["lingwen-errors"]`; uv workspace auto-resolves |
| test_phase18_10_stale_imports.py tests infra/util as compat import — false positive after Phase 82 | C2 explicit allowlist update (remove "infra.util") |
| test_phase53d remaining_subdirs list still has "util" (N.14 v22) | C4 explicit fixup |
| Infra-level re-export `infra/__init__.py:15` from infra.util breaks after Phase 82 | C2 in-place rewrite `from infra.util` → `from lingwen_util` |
| Infra-level docstring narrative `infra/__init__.py:3` mentions util | C2 in-place rewrite |

## 8. 不在范围 (defer list)

- ❌ **不**改 workspace deps (`packages/lingwen-util/pyproject.toml` 声明 `dependencies = ["lingwen-errors"]`,NOT-LEAF)
- ❌ **不**新增 I084-I089 — 本 phase 仅 I083 NEW (1 invariant)
- ❌ **不**touch `infra/util/__pycache__/` — gitignored
- ❌ **不**migrate test files — Phase 82 has 0 test consumers to MIGRATE

## 9. 完工标准

- [x] 7 atomic commits on branch `phase-82-p3-archdebt-util`
- [x] `infra/util/` 完全消失 (git ls-files 验证)
- [x] `packages/lingwen-util/` 含 2 sub-modules + __init__.py + pyproject.toml
- [x] I083 NEW invariant in `.lingwen/architecture.yml`
- [x] CLAUDE.md v54.13 → v54.14 + invariant table 加 I083 row
- [x] `collaboration/CURRENT_STATUS.md` 更新 ✅ entry + `collaboration/BACKLOG.md` 滚动
- [x] `docs/superpowers/handoffs/2026-09-14-phase-82-p3-archdebt-util-handoff.md`
- [x] Branch ready for ff-merge

## 10. Lessons from prior phases (per I079 §C)

- **Phase 56b (world_db)**: tests/X/ → packages/<pkg>/tests/ + sys.path cleanup
- **Phase 56c (cross_volume)**: pathspec BOTH old + new commit, `chr(47)` regex split trick
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location, docstring-stripped regex
- **Phase 79 (story_contracts)**: (1) `__pycache__/` 残留 (N.14 v23); (2) Regex anchored checks; (3) Worktree `.venv/bin/python`
- **Phase 80 (subplot)**: (1) `__all__` vs actual import; (2) Intra-package absolute imports
- **Phase 81 (di)**: Pre-existing failures carry over
- **N.14 lesson 1 (9-pattern audit matrix)**: Phase 51+ 完整谱系 — Phase 82 audit 已覆盖 9-pattern 全套

## 11. Anti-patterns (per I079 §D)

- ❌ C3 commit **只**写 "+ I083" 而不列 test files
- ❌ 漏 fixup meta-test allowlist (`test_phase18_10_stale_imports.py`)
- ❌ 漏 fixup prior-phase guards (test_phase53d + test_phase18_8)
- ❌ spec 缺 §A test files migration plan
- ❌ **NOT-LEAF** workspace dep declaration 漏 (`dependencies = []` for NOT-LEAF package 会让 import 失败)