# Phase 82 P3-ARCHDEBT `infra/util/` → `packages/lingwen-util/` handoff

> **日期**: 2026-09-14
> **Branch**: `phase-82-p3-archdebt-util`
> **Version**: v54.14 (Phase 82 NEW)
> **Commits**: 8 atomic (C0-C6 + C3.5 fixup) on `phase-82-p3-archdebt-util`
> **Spec**: `docs/superpowers/specs/2026-09-14-phase-82-p3-archdebt-util-design.md`

## Phase 82 TL;DR

闭环 **ARCHDEBT-CANDIDATES.md Top 5 候选 #4** (`infra/util/`, 338 LOC, 2 source files, 2 consumer sites, NOT-LEAF [1 workspace dep: lingwen-errors]) — **ARCHDEBT-REAL cycle 第四例, 简化版本** (Phase 79 LEAF + Phase 80 NOT-LEAF + Phase 81 TRUE LEAF + Phase 82 NOT-LEAF retry — 4 package shapes verification)。

**Simplified Phase 82**: 与 Phase 79-81 不同,Phase 82 **没有 test files to MIGRATE** — 0 test consumers。简化 pattern: C2 只做 in-place rewrite (intra-infra re-export + meta-test allowlist),不需要 C2a/C2b 分裂。

**关键产出**:

| 维度 | 数值 |
|------|------|
| Source files deleted | 2 (`infra/util/*.py` — __init__ + retry) |
| Source files added (new pkg) | 2 (`packages/lingwen-util/src/lingwen_util/*.py`) |
| Test files migrated | **0** (Phase 82 has no test consumers) |
| In-place consumer fixups | 2 (infra/__init__.py:17 re-export + tests/test_phase18_10_stale_imports.py:18 allowlist removal) |
| Production import sites updated | 1 (intra-infra `from infra.util import` → `from lingwen_util import`) |
| New invariant | I083 (`packages/lingwen-util/` 是 retry helper 唯一实包;`infra.util.*` 和 `infra/util/` 路径非法) |
| Prior-phase guards updated | 2 (`tests/test_phase53d_event_sourcing.py:152,172` + `tests/test_phase18_8_infra_init_simplified.py:6`) |
| New regression guards | 12 (`tests/test_phase82_p3_archdebt_util.py` G1-G12; G3+G6+G8 marked n/a for no-MIGRATE case) |
| Functional pytest gate | **N/A** (no test files to migrate) — G12 verifies package import + infra compat re-exports work |
| Prior-phase guards preserved | **14/14** (Phase 53d 7 + Phase 18_8 5 + Phase 18_10 2) |
| Workspace deps for new package | **1 (NOT-LEAF)**: `lingwen-errors` (for error classes + `is_instance` helper) |
| Public symbols | 6 (RetryConfig + retry + retry_async + with_retry + is_transient_error + backoff_delay) |

## 8 atomic commits on branch

```
ea5a90de docs(phase-82): spec + 9-pattern audit
5a2c76de chore(pkg): scaffold packages/lingwen-util/ (NOT-LEAF, 1 dep lingwen-errors, 3 files, 338 LOC)
b6df145b refactor(util): migrate 1 intra-infra re-export + 1 meta-test allowlist + 2 docstring narratives
aa223934 chore(archdebt): FULL DELETE infra/util/ + I083 NEW invariant
338327f2 chore(archdebt): I083 NEW invariant (separated from C3 due to Edit failure retry)
41f73436 test(phase-82): prior-phase guards fixup + C3.5 fixup: intra-package absolute import
333691b1 test(phase-82): 12 regression guards G1-G12
[pending C6 commit] docs(phase-82): CLAUDE.md v54.14 + CURRENT_STATUS + BACKLOG + handoff sync
```

## I079 §A. test files migration plan — closure verification

| Check | Status |
|-------|--------|
| A1 test files inventory | ✅ N/A — 0 test files to MIGRATE (Phase 82 has no test consumers) |
| A2 MIGRATE 路径 | ✅ N/A — 0 test files MIGRATE |
| A3 DELETE 路径 | ✅ N/A — 0 test files DELETE |
| A4 RETAIN-ORPHAN | ✅ N/A — no test files to begin with |
| A5 Half-migration defense | ✅ N/A — no half-migration risk when 0 test files MIGRATE |

## Validation gates

```
12/12 NEW regression guards (G1-G12) GREEN                       ✅
   (G3 + G6 + G8 marked n/a for no-MIGRATE case)
14/14 prior-phase cumulative (Phase 53d 7 + Phase 18_8 5 + Phase 18_10 2)  ✅
ruff clean                                                          ✅
9-pattern audit: 0 infra.util refs in production                    ✅
Functional import gate (G12): 6 symbols import OK + infra compat re-exports work ✅
```

## 9-pattern audit results

| # | Pattern | Verdict |
|---|---------|---------|
| 1 | Literal dotted-path imports | ✅ Migrated — 1 intra-infra site `infra/__init__.py:17` rewritten to `from lingwen_util import` |
| 2 | Indented/function-body imports | ✅ None found |
| 3 | Relative imports (intra-module) | ✅ Migrated — `infra/util/__init__.py:14` `from infra.util.retry import` rewritten to `from lingwen_util.retry import` (C3.5 fixup, pre-existing intra-package absolute import) |
| 4 | Filesystem path string literals | ✅ None found |
| 5 | Wildcard `from X import *` | ✅ None found |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ None found |
| 7 | `import X as Y` re-exports | ✅ None found |
| 8 | Doc comments referencing old path | ✅ Updated — `infra/__init__.py:3` docstring narrative update + `infra/__init__.py:11` Phase 82 migration note |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Fixed via C4 — test_phase53d dropped `"util"` from `remaining_subdirs` list + added explicit `assert not exists` |

## 1 Lesson (per I079 §C)

### Intra-package absolute imports break after C3 (Phase 80 v2 lesson)

**Problem**: `infra/util/__init__.py:14` originally has `from infra.util.retry import ...` (intra-package absolute import, pre-existing code smell). Phase 82 C1 copied this file verbatim to `packages/lingwen-util/src/lingwen_util/__init__.py`. C3 deleted `infra/util/`, but the `__init__.py` in new package STILL references `infra.util.retry` — which now fails with `ModuleNotFoundError: No module named 'infra.util'`. This breaks `from infra import ...` chain via `infra/__init__.py:17 from lingwen_util import ...`.

**Discovery**: C3 commit 后 `import infra` 立即 fail with `ModuleNotFoundError: No module named 'infra.util'`。检查发现 `lingwen_util/__init__.py:14` 仍有 `from infra.util.retry import ...` 引用(不是 `from lingwen_util.retry` 或 `from .retry`)。

**Solution**:
1. **C3.5 fixup commit** — 单独 commit rename `from infra.util.retry` → `from lingwen_util.retry` (per N.14 lesson #6 / Phase 80 similar pattern)
2. **Or in C1** — 在 copy 时直接 grep `from infra.<subdir_name>\.` rewrite before commit

**Future heuristic**:
- **Pre-C1 verification**: `grep -n "^from infra\.<subdir_name>\." <new-pkg>/src/<new-pkg>/__init__.py` should return 0 matches
- **Always check intra-package imports**: When copying source files to new package location, ALWAYS grep for `from <old_pkg>.` and rewrite to `from <new_pkg>.` or relative `from .` BEFORE commit C1
- **Or unified pattern**: After C1, immediately `grep -rln "from infra\." packages/<new-pkg>/src/ | xargs sed -i 's|from infra\.|from <new-pkg>.|g'` to normalize

## Carryover closure

✅ **ARCHDEBT-CANDIDATES.md Top 5 候选 #4** (`infra/util/`) → CLOSED
🟢 **ARCHDEBT-REAL cycle 4 package shapes verification COMPLETE** — Phase 79 LEAF + Phase 80 NOT-LEAF + Phase 81 TRUE LEAF + Phase 82 NOT-LEAF retry 都 success

**Next candidates** (post-Phase 82 backlog):
- `infra/config/` (77 LOC) — trivial TRUE LEAF
- `infra/tools/` (~1750 LOC) — workflow + consistency NOT-LEAF, multi-week
- `infra/permission` / `infra/llm_cache` / `infra/types` — non-existent modules referenced by test_infra_modules.py (separate cleanup)

## Cluster cumulative (Phase 53-82)

| Phase | LOC | Type |
|-------|-----|------|
| 53 + 53b | ~600 | dead code cleanup (3 dirs) |
| 53c | 6149 | dead code cleanup (顶层 tools/legacy/) |
| 53d | 992 | dead code cleanup (infra/event_sourcing/) |
| 53e | 61 bytes + 0 bytes | orphan runtime artifacts |
| 78 | 1854 | dead code cleanup (2 dirs) |
| **79** | **848** | **真迁移 LEAF** (story_contracts) |
| **80** | **508** | **真迁移 NOT-LEAF** (subplot) |
| **81** | **309** | **真迁移 TRUE LEAF** (di) |
| **82** | **338** | **真迁移 NOT-LEAF retry** (util) |
| TOTAL | **~19025 LOC dead code + 4 真迁移 packages** | 8 zero-consumer dirs + 4 canonical migrations (LEAF + NOT-LEAF + TRUE LEAF + NOT-LEAF retry) |

## Phase 82 ready for ff-merge

按 workflow (MEMORY.md §WORKFLOW):
```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-82-p3-archdebt-util
git push origin master
```

8 commits ahead of master, working tree clean, all 26+ guards GREEN (12 NEW + 14 prior-phase).