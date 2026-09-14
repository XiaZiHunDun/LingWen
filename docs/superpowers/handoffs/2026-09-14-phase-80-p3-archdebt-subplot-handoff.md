# Phase 80 P3-ARCHDEBT `infra/subplot/` → `packages/lingwen-subplot/` handoff

> **日期**: 2026-09-14
> **Branch**: `phase-80-p3-archdebt-subplot`
> **Version**: v54.12 (Phase 80 NEW)
> **Commits**: 8 atomic (C0-C6) on `phase-80-p3-archdebt-subplot`
> **Spec**: `docs/superpowers/specs/2026-09-14-phase-80-p3-archdebt-subplot-design.md`

## Phase 80 TL;DR

闭环 **ARCHDEBT-CANDIDATES.md Top 5 候选 #2** (`infra/subplot/`, 508 LOC, 4 source files, 10 consumers, NOT-LEAF [1 workspace dep: lingwen-core]) — **ARCHDEBT-REAL cycle 第二例**(Phase 79 LEAF → Phase 80 NOT-LEAF 模式 verification)。

**关键产出**:

| 维度 | 数值 |
|------|------|
| Source files deleted | 4 (`infra/subplot/*.py` — __init__ + lifecycle + queries + registry) |
| Source files added (new pkg) | 4 (`packages/lingwen-subplot/src/lingwen_subplot/*.py`) |
| Test files migrated | 4 (`tests/subplot/*.py` → `packages/lingwen-subplot/tests/*.py`) — rename blame preserved 98-99% |
| Test files in-place rewrite | 3 (test_links.py + test_phase2_integration.py in lingwen-world-model + test_phase35_world_model.py in tests/) |
| Production import sites updated | 3 (1 function-body import in `lingwen-world-model/links.py:41`; 2 intra-subplot absolute imports in `queries.py:18` + `registry.py:32`) |
| New invariant | I081 (`packages/lingwen-subplot/` 是 Plot 模型唯一实包;`infra.subplot.*` 和 `infra/subplot/` 路径非法) |
| Prior-phase guards updated | 3 (`tests/test_phase53d_event_sourcing.py:151-172` + `tests/test_phase18_8_infra_init_simplified.py:6` + `tests/test_phase35_world_model.py:104,280` early-return safe verified) |
| New regression guards | 12 (`tests/test_phase80_p3_archdebt_subplot.py` G1-G12) |
| Functional pytest gates | **94/94 subplot + 25/25 world-model + 17/17 test_phase35 GREEN** |
| Prior-phase guards preserved | **30/30** (Phase 53d 7 + Phase 18_8 5 + Phase 35 17 + 1 bonus) |
| Workspace deps for new package | **1 (NOT-LEAF)**: `lingwen-core` (for `lingwen_core.domain.subplot` types: `Plot`, `PlotStatus`, `PlotType`, `MAX_ACTIVE_SUBPLOTS`) |
| Public symbols | 15 (Plot + PlotType + PlotPurpose + PlotStatus + MAX_ACTIVE_SUBPLOTS + PlotRegistry + 4 exceptions + 4 lifecycle consts + 3 query funcs) |

## 8 atomic commits on branch

```
3742e794 docs(phase-80): spec + 9-pattern audit for P3-ARCHDEBT infra/subplot → packages/lingwen-subplot
9dc59da0 chore(pkg): scaffold packages/lingwen-subplot/ (NOT-LEAF, 1 workspace dep lingwen-core, 5 files, 508 LOC)
9ad1f030 refactor(subplot): migrate 1 production function-body import + 2 intra-subplot absolute imports + 4 docstring narratives
a898f2a0 chore(tests): MIGRATE 4 subplot test files + IN-PLACE rewrite 3 cross-pkg test imports
f6450482 chore(archdebt): FULL DELETE infra/subplot/ + I081 NEW invariant
d88c6bf7 test(phase-80): prior-phase guards fixup
082392c7 test(phase-80): 12 regression guards G1-G12
[pending C6 commit] docs(phase-80): CLAUDE.md v54.12 + CURRENT_STATUS + BACKLOG + handoff sync (this doc)
```

## I079 §A. test files migration plan — closure verification

| Check | Status |
|-------|--------|
| A1 test files inventory | ✅ 7 files listed (4 MIGRATE + 3 IN-PLACE) |
| A2 MIGRATE 路径 | ✅ Single C2b commit, `git mv` pathspec BOTH old + new, blame preserved 98-99% |
| A3 DELETE 路径 | ✅ N/A — no DELETE |
| A4 RETAIN-ORPHAN | ✅ NOT USED — all 4 test files MIGRATE, no orphans |
| A5 Half-migration defense | ✅ C2b single commit pathspec covers BOTH old + new (Phase 56c lesson 1); C3 commit pathspec covers `infra/subplot/` (tests already gone) |

## Validation gates

```
94/94 functional pytest on packages/lingwen-subplot/tests/        ✅
25/25 functional pytest on packages/lingwen-world-model/tests/   ✅ (consumer)
17/17 functional pytest on tests/test_phase35_world_model.py     ✅ (consumer, early-return safe)
12/12 NEW regression guards (G1-G12)                             ✅
7/7 prior-phase Phase 53d guards (after C4 fixup)                ✅
5/5 prior-phase Phase 18_8 guards (after C4 fixup)               ✅
17/17 prior-phase Phase 35 guards (after C2b — early-return safe) ✅
30/30 prior-phase cumulative                                      ✅
ruff clean                                                         ✅
9-pattern audit: 0 infra.subplot functional refs in production    ✅
9-pattern audit: 0 infra.subplot refs in new tests                 ✅
```

## 9-pattern audit results

| # | Pattern | Verdict |
|---|---------|---------|
| 1 | Literal dotted-path imports | ✅ Migrated — 7 sites (4 test files MIGRATE + 3 in-place) rewritten to `lingwen_subplot.X` |
| 2 | Indented/function-body imports | ✅ Migrated — 1 production site (`lingwen-world-model/links.py:41`) |
| 3 | Relative imports (intra-module) | ✅ Auto-fixed — intra-module `.X` imports work as-is |
| 4 | Filesystem path string literals | ✅ Migrated — historical narratives updated in `lingwen-world-model/__init__.py:53` + `lingwen-world-model/links.py:28,30` + `subplot_helpers.py:7,10` |
| 5 | Wildcard `from X import *` | ✅ None found |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ None found |
| 7 | `import X as Y` re-exports | ✅ None found |
| 8 | Doc comments referencing old path | ✅ Migrated — 5 sites: `links.py:28,30,38` + `subplot_helpers.py:7,10` + `test_ripple_registry.py:3` + `__init__.py:53` |
| 9 | Prior-phase guard's hardcoded representative files | ✅ Fixed via C4 — test_phase53d dropped `"subplot"` from `remaining_subdirs` list + added explicit `assert not exists` |

## 2 Lessons (per I079 §C)

### Lesson 1: `__all__` 列表 vs 实际 import 不一致 (pre-existing bug)

**Problem**: `infra/subplot/__init__.py` `__all__` 列了 16 symbols 包括 `VALID_TRANSITIONS`, `CLOSING_MIN_CHAPTERS`, `STAGES`, `STAGE_TYPICAL_RANGES` — 但实际 `__init__.py` 只 import 9 symbols (5 from `lingwen_core.domain.subplot` + 4 from `.registry`),**未 import** the 4 lifecycle constants listed in `__all__`。

```python
__all__ = [
    # ... MAX_ACTIVE_SUBPLOTS, Plot, PlotPurpose, PlotStatus, PlotType  ✓
    # ... PlotRegistry, PlotNotFoundError, DuplicatePlotIdError, SubplotLimitExceeded  ✓
    "VALID_TRANSITIONS",      # ✗ in __all__ but not imported!
    "CLOSING_MIN_CHAPTERS",   # ✗ in __all__ but not imported!
    "STAGES",                 # ✗ in __all__ but not imported!
    "STAGE_TYPICAL_RANGES",   # ✗ in __all__ but not imported!
]
```

**Discovery**: C1 scaffold 后 `from lingwen_subplot import VALID_TRANSITIONS` → `ImportError: cannot import name 'VALID_TRANSITIONS'`。检查 `__init__.py` 才发现 `__all__` vs 实际 import 不一致。

**Solution**:
1. Module-level import: `from lingwen_subplot.lifecycle import VALID_TRANSITIONS, CLOSING_MIN_CHAPTERS, STAGES, STAGE_TYPICAL_RANGES` — works fine
2. **NOT FIXED in this phase** — pre-existing bug, NOT Phase 80 scope. Documented as future cleanup opportunity.

**Future heuristic**: Pre-spec verify of `__all__` vs actual `from .X import` in `__init__.py` for any package being migrated. `__all__` should not list symbols that aren't actually imported.

### Lesson 2: Intra-package absolute imports 是 future cleanup opportunity

**Problem**: `infra/subplot/queries.py:18` and `infra/subplot/registry.py:32` 使用绝对路径 import (e.g., `from infra.subplot.registry import PlotRegistry`) 而非相对路径 (`from .registry import PlotRegistry`)。这是 **pre-existing code smell** — 标准 Python 实践是 relative imports 在同一 package 内。

**Discovery**: 9-pattern audit 找到 `queries.py:18` + `registry.py:32` 两处 intra-package absolute imports。Phase 80 C2a sed 重写为 `from lingwen_subplot.X` (valid absolute imports post-migration, 但仍然是 absolute not relative)。

**Solution**:
1. Phase 80 sed 重写 `infra.subplot` → `lingwen_subplot` (minimal change, post-migration valid)
2. **Future code-quality phase** 应该 normalize 为相对 imports (`from .registry import PlotRegistry`) — 这是 idiomatic Python

**Future heuristic**: P3-ARCHDEBT spec §B (recommended structure) 应该加 "intra-package import normalization" 作为 separate cleanup opportunity, 不混在 relocation commit 里。

## 1 Carryover from Phase 79 (applicable)

### `__pycache__/` 残留 lesson (N.14 v23 重申)

**Problem**: Phase 80 C3 `git rm -r infra/subplot/` 删除 tracked `.py` files,但 gitignored `__pycache__/` 字节码**survived**。Phase 79 v23 lesson 同样适用 — C3 后立刻 `rm -rf infra/subplot/` 清掉 residue。

**Discovery**: Phase 79 v23 lesson 应用到 Phase 80,test_phase53d G11 在 C4 fixup 时加上 `__pycache__` residue comment。

**Solution**: C3 commit message 包含 `+ I081 invariant` 行,C3 后立刻 `rm -rf infra/subplot/`。Future test checking "dir 不存在" should always consider `__pycache__/` residue.

## Carryover closure

✅ **ARCHDEBT-CANDIDATES.md Top 5 候选 #2** (`infra/subplot/`) → CLOSED
🟢 **ARCHDEBT-REAL cycle 模式 verification COMPLETE** — Phase 79 LEAF + Phase 80 NOT-LEAF 都 success

**Next candidates** (post-Phase 80 backlog):
- `infra/di/` (309 LOC) — TRUE LEAF, similar to Phase 37 lingwen-paths
- `infra/util/` (338 LOC) — TRUE LEAF, retry helper
- `infra/config/` (77 LOC) — trivial
- OR non-ARCHDEBT 工作 (Write Workspace / World / Reading Power 增强)

## Cluster cumulative (Phase 53-80)

| Phase | LOC | Type |
|-------|-----|------|
| 53 + 53b | ~600 | dead code cleanup (3 dirs) |
| 53c | 6149 | dead code cleanup (顶层 tools/legacy/) |
| 53d | 992 | dead code cleanup (infra/event_sourcing/) |
| 53e | 61 bytes + 0 bytes | orphan runtime artifacts |
| 78 | 1854 | dead code cleanup (2 dirs) |
| **79** | **848** | **真迁移 LEAF** (story_contracts) |
| **80** | **508** | **真迁移 NOT-LEAF** (subplot) |
| TOTAL | **~18378 LOC dead code + 2 真迁移 packages** | 8 zero-consumer dirs + 2 canonical migrations (LEAF + NOT-LEAF) |

## Phase 80 ready for ff-merge

按 workflow (MEMORY.md §WORKFLOW):
```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-80-p3-archdebt-subplot
git push origin master
```

8 commits ahead of master, working tree clean, all 168+ guards GREEN (94 subplot + 25 world-model + 17 phase35 + 12 NEW + 30 prior-phase).