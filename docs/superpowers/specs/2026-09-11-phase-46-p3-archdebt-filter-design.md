# Phase 46 P3-ARCHDEBT (filter merge) — lingwen-quality extension Design Spec

> **Phase**: 46 (P3-ARCHDEBT 10/9+1 — continues from Phase 45's `lingwen-utilities` batch closure)
> **Branch**: `phase-46-p3-archdebt-filter`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md #5 (boundary case — near-LEAF)
> **Template**: Phase 34 (lingwen-got) — multi-module migration that moves related code together
> **Special**: **MERGE decision** — `infra.filter` + `tools.problem_classifier` → `packages/lingwen-quality/`

## Goal

**MERGE** two related quality-domain modules into the existing canonical `packages/lingwen-quality/` package:

- `infra/filter.py` (63 LOC, FalsePositiveFilter) → `packages/lingwen-quality/src/lingwen_quality/filter.py`
- `tools/problem_classifier.py` (242 LOC, ProblemClassifier) → `packages/lingwen-quality/src/lingwen_quality/problem_classifier.py`

Delete both source files and add **invariant I063** documenting the merge.

## Background — MERGE Decision Rationale

ARCHDEBT-CANDIDATES.md #5 explicitly flagged this as a boundary case:
> 候选 #5 是"边界案例"：单 dep 但 LEAF-like，决定是否拆 package 取决于 dep 边界

### Two options considered

**Option A: Split package `packages/lingwen-filter/`**
- 1 workspace dep (`lingwen_quality`)
- 1 tools dep (`tools.problem_classifier` via sys.path hack — fragile)
- New package boundary: lingwen-quality + lingwen-filter + tools

**Option B: Fold into existing `packages/lingwen-quality/`** ✅ CHOSEN
- 0 new workspace deps
- ProblemClassifier also moves into lingwen-quality (eliminates fragile sys.path hack)
- New sub-modules: `lingwen_quality/filter.py` + `lingwen_quality/problem_classifier.py`
- lingwen-quality grows by 305 LOC but stays cohesive (all quality-domain logic)

### Why Option B wins

1. **Cohesion**: Both modules are quality-domain logic (filter false positives from quality checks)
2. **Eliminates fragile sys.path hack**: `tools/problem_classifier.py` lines 11-12 use `sys.path.insert(0, PROJECT_ROOT)` to import `lingwen_quality` — moving into lingwen-quality makes it a clean internal import
3. **Avoids cross-cutting risk**: ARCHDEBT-CANDIDATES.md warning "1 dep but LEAF-like" → split creates 1-dep package with cross-cutting risk
4. **Existing pattern**: `lingwen_quality` already contains `quality.py` (Issue, QualityChecker, etc.) — filter is a natural extension
5. **Eliminates tools/ coupling**: Both filter and problem_classifier move OUT of tools/ — cleanup side effect

### Side benefit: removes 2 sys.path hacks

- `infra/filter.py:10-11` — `PROJECT_ROOT = Path(__file__).parent.parent; sys.path.insert(0, str(PROJECT_ROOT))`
- `tools/problem_classifier.py:11-12` — same pattern

Both become unnecessary after migration (clean module imports within package).

## Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit (per module)

| # | Pattern | infra/filter | tools/problem_classifier | Total |
|---|---------|--------------|---------------------------|-------|
| 1 | Literal dotted-path imports `from infra.filter` | 3 | 0 | 3 |
| 2 | Indented/function-body imports | 0 | 0 | 0 |
| 3 | Relative imports | 0 | 0 | 0 |
| 4 | Filesystem path literals | 0 | 0 | 0 |
| 5 | **Wildcard** `from infra.filter import *` | **1** | 0 | **1** |
| 6 | `monkeypatch.setattr("infra.filter.X", ...)` | 0 | 0 | 0 |
| 7 | Plain `import infra.filter` | 0 | 0 | 0 |
| 8 | Doc comments referencing old path | 0 | 0 | 0 |
| 9 | Prior-phase guard's hardcoded representative | 0 | 0 | 0 |

### Real external consumers (4 sites, verified by fresh grep 2026-09-11)

| # | File | Module | Pattern | Migration |
|---|------|--------|---------|-----------|
| 1 | `infra/core/__init__.py:3` | infra.filter | wildcard | `from lingwen_quality import *` (re-exported FalsePositiveFilter + ProblemClassifier) |
| 2 | `tests/test_filter.py:14` | infra.filter | single symbol | `from lingwen_quality import FalsePositiveFilter` |
| 3 | `tools/llm_quality/__init__.py:20` | infra.filter | single symbol | `from lingwen_quality import FalsePositiveFilter` |
| 4 | `tools/llm_quality/checker.py:14` | infra.filter | single symbol | `from lingwen_quality import FalsePositiveFilter` |

### False-positive filter (1 site excluded)

| File | Line | Reason |
|------|------|--------|
| `tests/test_phase45_lingwen_utilities.py:395` | 395 | STRING LITERAL `"from infra.filter import *"` in docstring — not an actual import. Confirms Phase 45 left wildcard in infra/core/__init__.py (documented expected). |

### tools/problem_classifier consumers

`tools/problem_classifier.py` has NO external consumers except `infra/filter.py` (line 15). After Phase 46, ProblemClassifier is only used by FalsePositiveFilter — moves with it.

## Architecture

### 2 new sub-modules in existing `packages/lingwen-quality/`

```
packages/lingwen-quality/                    (existing package, extended)
├── pyproject.toml                           (no dep changes — already has quality deps)
├── src/lingwen_quality/
│   ├── __init__.py                          # +ProblemClassifier, +FalsePositiveFilter re-exports
│   ├── quality.py                           # existing — Issue, QualityChecker, etc.
│   ├── problem_classifier.py                # NEW (from tools/problem_classifier.py, 242 LOC)
│   └── filter.py                             # NEW (from infra/filter.py, 63 LOC)
└── tests/                                    # (no new tests; existing coverage sufficient)
```

### Public surface additions

| Symbol | Kind | Module | From |
|--------|------|--------|------|
| `ProblemClassifier` | class | `problem_classifier.py` | `tools/problem_classifier.py` |
| `FalsePositiveFilter` | class | `filter.py` | `infra/filter.py` |

### Workspace deps — no changes

```toml
# packages/lingwen-quality/pyproject.toml (unchanged)
dependencies = [...]  # existing deps already cover required packages
```

### Internal imports (after migration)

```python
# packages/lingwen-quality/src/lingwen_quality/problem_classifier.py
from .quality import Issue  # was: from lingwen_quality.quality import Issue + sys.path hack

# packages/lingwen-quality/src/lingwen_quality/filter.py
from .quality import Issue  # was: from lingwen_quality.quality import Issue + sys.path hack
from .problem_classifier import ProblemClassifier  # was: from tools.problem_classifier import ProblemClassifier + sys.path hack
```

### `__init__.py` additions

```python
# packages/lingwen-quality/src/lingwen_quality/__init__.py
from lingwen_quality.filter import FalsePositiveFilter
from lingwen_quality.problem_classifier import ProblemClassifier
# ... existing exports (Issue, QualityChecker, etc.)
```

### Invariant I063

```
I063 | `packages/lingwen-quality/` (extended) is FalsePositiveFilter + ProblemClassifier
       unique canonical home; `infra.filter.*` and `tools.problem_classifier.*`
       paths forbidden (P3-ARCHDEBT 10/9+1 Phase 46 filter merge)
```

## Atomic commits (5 total — MERGE pattern)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-46)` | spec | This document (with MERGE decision) |
| **C1** | `feat(lingwen-quality)` | add 2 sub-modules | problem_classifier.py + filter.py + __init__.py re-exports |
| **C2** | `refactor(consumers)` | migrate 4 sites | Single commit per Phase 37 lesson |
| **C3** | `chore(infra,tools)` | delete 2 files + I063 + v44.0 | infra/filter.py + tools/problem_classifier.py DELETED |
| **C4** | `test(phase-46)` | guards + handoff + CLAUDE.md + MEMORY | Phase 46 guards + topic file |

### C1 details (scaffold — ADDITION to existing package)

**Files created** (3 total):
- `packages/lingwen-quality/src/lingwen_quality/problem_classifier.py` (242 LOC, from tools/)
- `packages/lingwen-quality/src/lingwen_quality/filter.py` (63 LOC, from infra/)
- (none — `__init__.py` MODIFIED, not created)

**Files modified**:
- `packages/lingwen-quality/src/lingwen_quality/__init__.py` — add 2 re-exports

### C2 details (bulk migrate 4 sites — single commit)

```
refactor(consumers): migrate 4 sites from infra.filter to lingwen_quality

Phase 46 P3-ARCHDEBT (filter merge into lingwen-quality):

  infra/core/__init__.py:3                    wildcard → from lingwen_quality import *
  tests/test_filter.py:14                     single symbol
  tools/llm_quality/__init__.py:20            single symbol (FalsePositiveFilter)
  tools/llm_quality/checker.py:14             single symbol (FalsePositiveFilter)

tools/problem_classifier.py had only 1 external consumer (infra/filter.py)
which is also being migrated; ProblemClassifier is now internal to lingwen-quality.
```

### C3 details (delete 2 files + invariant)

**Files modified**:
- `infra/filter.py` — DELETED
- `tools/problem_classifier.py` — DELETED
- `CLAUDE.md` — version v43.0 → v44.0 + invariant I063 added
- `.lingwen/architecture.yml` — version field updated + invariants list I063 added

### C4 details (guards + handoff + doc-sync)

**Files created**:
- `tests/test_phase46_lingwen_filter.py` (10+ regression guards)
- `docs/superpowers/handoffs/2026-09-11-phase-46-p3-archdebt-filter-handoff.md`

**Files modified**:
- `CLAUDE.md` — version bump entry + handoff link
- `MEMORY.md` — Phase 46 entry + 4 lessons
- Memory topic file: `phase-46-p3-archdebt-filter.md`

## Validation gates (Phase 46 acceptance)

1. ✅ ruff clean on changed Python files (problem_classifier.py + filter.py + 4 consumer sites)
2. ✅ `pytest tests/test_filter.py` passes (import updated to lingwen_quality)
3. ✅ `pytest tools/llm_quality/` passes (2 imports updated)
4. ✅ Phase 36-45 guards preserved (10 prior-phase guard files)
5. ✅ New Phase 46 guards (10+ tests)
6. ✅ Production audit: `grep -rn "infra\.filter\b\|tools\.problem_classifier\b" infra/ apps/ packages/ tests/ tools/` → 0 hits
7. ✅ Test audit: same grep in tests/ → 0 hits
8. ✅ Internal imports verified: `lingwen_quality.problem_classifier` uses `from .quality import Issue` (no sys.path hack)
9. ✅ Internal imports verified: `lingwen_quality.filter` uses `from .quality import Issue` + `from .problem_classifier import ProblemClassifier` (no sys.path hack)
10. ✅ I063 invariant in `.lingwen/architecture.yml` + `CLAUDE.md`

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Merge decision creates larger lingwen-quality package | LOW | Quality-domain cohesion justifies it; existing package already 305+ LOC |
| `tools/problem_classifier.py` deletion breaks hidden consumers | LOW | Pre-spec audit verified only 1 consumer (infra/filter.py) — both migrate together |
| sys.path hack removal breaks something | LOW | Hack was redundant (workspace package already importable) |
| `__init__.py` wildcard re-exports conflict with existing names | LOW | ProblemClassifier + FalsePositiveFilter names don't conflict |
| Workspace `tools/` directory becomes unused (still has other .py files like cli.py, checker.py) | n/a | `tools/` directory persists; only `tools/problem_classifier.py` moves |

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 9/8+1 (lingwen-utilities batch) | ✅ Phase 45 |
| **P3-ARCHDEBT 10/9+1 (filter MERGE into lingwen-quality)** | 🟡 Phase 46 (this phase) |
| P3-ARCHDEBT remaining | Phase 47+ (studio_batch_*, full_check_report, memory_service, types, etc.) |

**Next-actionable after Phase 46**: Phase 47 = `infra/studio_batch_*` (3 modules shared dep on lingwen_studio_registry, per ARCHDEBT-CANDIDATES.md "合并 1 phase").

## References

- ARCHDEBT-CANDIDATES.md #5 (boundary case decision)
- Phase 34 (lingwen-got) — multi-module migration template (similar pattern)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 39 (logging_config) — LEAF pattern (N/A for Phase 46 since NOT-LEAF due to merge)
- Phase 44 (lingwen-prose-calibration) — single-module LEAF (different shape)
- Phase 45 (lingwen-utilities batch) — multi-module batch (4 LEAF modules, NOT merge)

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (4 real consumers, 305 LOC total, 2 sys.path hacks eliminated, MERGE decision
> rationale) was verified by fresh-run grep on 2026-09-11 BEFORE writing this spec.
> No stale-count claims.