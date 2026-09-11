# Phase 46 P3-ARCHDEBT (filter MERGE) Handoff

> **Date**: 2026-09-11
> **Phase**: 46 — P3-ARCHDEBT item 10/9+1
> **Branch**: `phase-46-p3-archdebt-filter`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **Spec**: [`docs/superpowers/specs/2026-09-11-phase-46-p3-archdebt-filter-design.md`](../specs/2026-09-11-phase-46-p3-archdebt-filter-design.md)
> **ARCHDEBT Rank**: #5 in [ARCHDEBT-CANDIDATES.md](../ARCHDEBT-CANDIDATES.md) (boundary case — MERGE decision)
> **Special**: **MERGE pattern** — no new package, extends existing `lingwen-quality`

## TL;DR

**MERGE decision** (per ARCHDEBT-CANDIDATES.md #5 boundary case): 2 quality-domain modules migrated to EXISTING `packages/lingwen-quality/` package (not new `packages/lingwen-filter/`):

- `infra/filter.py` (63 LOC, FalsePositiveFilter) → `packages/lingwen-quality/src/lingwen_quality/filter.py`
- `tools/problem_classifier.py` (242 LOC, ProblemClassifier) → `packages/lingwen-quality/src/lingwen_quality/problem_classifier.py`

5 consumers migrated (4 wildcard + 1 missed `tests/tools/test_problem_classifier.py`). Both source files DELETED. 1 NEW invariant (I063). Version bump v43.0 → v44.0.

**This is the FIRST P3-ARCHDEBT MERGE pattern** (vs scaffold-new-package in phases 36-45).

## Atomic commits (6 total on `phase-46-p3-archdebt-filter`)

| SHA | Type | Scope | Notes |
|-----|------|-------|-------|
| `2832898f` | `docs(phase-46)` | spec | MERGE decision rationale documented |
| `4aea856e` | `feat(lingwen-quality)` | add 2 sub-modules | filter.py + problem_classifier.py + clean relative imports |
| `15da717f` | `refactor(consumers)` | migrate 5 sites | 4 wildcard + 1 missed test_problem_classifier.py (N.14 lesson 1 #25) |
| `e9eaee59` | `chore(infra,tools)` | delete 2 files + I063 + v44.0 | infra/filter.py + tools/problem_classifier.py DELETED |
| `10e90012` | `fix(test)` | C4.5 fixup | Phase 45 guard updated for filter wildcard migration (N.14 lesson 1 #25) |
| `<C4>` | `test(phase-46)` | 13 guards + handoff + MEMORY | Pending commit (this file) |

## MERGE Decision Rationale (Phase 46 key learning)

ARCHDEBT-CANDIDATES.md #5 flagged this as a **boundary case**:
> 候选 #5 是"边界案例"：单 dep 但 LEAF-like，决定是否拆 package 取决于 dep 边界

### Two options analyzed

**Option A: Split package `packages/lingwen-filter/`** ❌
- 1 workspace dep (`lingwen_quality`)
- 1 tools dep (`tools.problem_classifier` via sys.path hack — fragile)
- New package boundary: lingwen-quality + lingwen-filter + tools
- ARCHDEBT-CANDIDATES.md warning: "1 dep but LEAF-like" → cross-cutting risk

**Option B: Fold into existing `packages/lingwen-quality/`** ✅ CHOSEN
- 0 new workspace deps
- ProblemClassifier also moves into lingwen-quality (eliminates fragile sys.path hack)
- New sub-modules: `lingwen_quality/filter.py` + `lingwen_quality/problem_classifier.py`
- lingwen-quality grows by 305 LOC but stays cohesive (all quality-domain logic)

### Why Option B won

1. **Cohesion**: Both modules are quality-domain logic
2. **Eliminates 2 sys.path hacks**: `infra/filter.py:10-11` + `tools/problem_classifier.py:11-12` both used `PROJECT_ROOT/sys.path.insert(0, PROJECT_ROOT)` to import lingwen_quality — moving into lingwen-quality makes clean internal imports
3. **Avoids cross-cutting risk**: 1-dep package with cross-cutting deps
4. **Existing pattern**: `lingwen_quality` already has `quality.py` (Issue, QualityChecker, etc.)
5. **Side benefit**: eliminates tools/ coupling for ProblemClassifier

## Pre-Spec Audit (N.14 lesson 1 #25 spec drift caught)

### 9-pattern audit results

| # | Pattern | infra.filter | tools.problem_classifier | Total |
|---|---------|--------------|---------------------------|-------|
| 1 | Literal dotted-path imports | 3 | 1 (missed) | **4 (spec said 3)** |
| 2-4, 6-9 | other patterns | 0 | 0 | 0 |
| 5 | Wildcard | 1 | 0 | 1 |

### Real external consumers (5 sites, verified by fresh grep 2026-09-11)

**infra.filter (4 sites)**:
| # | File | Pattern |
|---|------|---------|
| 1 | `infra/core/__init__.py:3` | wildcard → `from lingwen_quality.filter import *` |
| 2 | `tests/test_filter.py:14` | single symbol |
| 3 | `tools/llm_quality/__init__.py:20` | single symbol |
| 4 | `tools/llm_quality/checker.py:14` | single symbol |

**tools.problem_classifier (1 site — CAUGHT pre-commit)**:
| # | File | Pattern |
|---|------|---------|
| 5 | `tests/tools/test_problem_classifier.py:7` | single symbol |

### False-positive filter (1 site excluded)

| File | Line | Reason |
|------|------|--------|
| `tests/test_phase45_lingwen_utilities.py:395` | 395 | STRING LITERAL `"from infra.filter import *"` in docstring check (Phase 45 documentation). NOT a real import. |

### Spec drift (N.14 lesson 1 #25)

Spec listed 4 consumers; actual was **5** (`tests/tools/test_problem_classifier.py` was missed in pre-spec 9-pattern audit). Caught during C2 audit (before commit), fixed in same commit (no separate fixup).

## Architecture (MERGE pattern — no new package)

```
packages/lingwen-quality/                       (existing, extended)
├── pyproject.toml                              (no changes — already covers deps)
├── src/lingwen_quality/
│   ├── __init__.py                             (NO CHANGE — namespace package auto-discovery)
│   ├── consistency/                             (existing)
│   ├── quality/                                (existing)
│   ├── problem_classifier.py                   # NEW (from tools/, 242 LOC)
│   └── filter.py                                # NEW (from infra/, 63 LOC)
└── tests/                                       (existing)
```

### Public surface additions

| Symbol | Module | From |
|--------|--------|------|
| `ProblemClassifier` | `problem_classifier.py` | `tools/problem_classifier.py` |
| `FalsePositiveFilter` | `filter.py` | `infra/filter.py` |

### Workspace deps — no changes

```toml
# packages/lingwen-quality/pyproject.toml (unchanged)
dependencies = [
    "pydantic>=2.7",
    "pyyaml>=6.0",
    "lingwen-core",
    "lingwen-llm",
    "lingwen-storage",
]
```

### Internal imports (after MERGE — sys.path hacks eliminated)

```python
# packages/lingwen-quality/src/lingwen_quality/problem_classifier.py
from lingwen_quality.quality import Issue  # was: sys.path hack + from lingwen_quality.quality import Issue

# packages/lingwen-quality/src/lingwen_quality/filter.py
from lingwen_quality.quality import Issue  # was: sys.path hack + from lingwen_quality.quality import Issue
from lingwen_quality.problem_classifier import ProblemClassifier  # was: sys.path hack + from tools.problem_classifier import ProblemClassifier
```

### Invariant I063

```
I063 | `packages/lingwen-quality/` (extended) is FalsePositiveFilter + ProblemClassifier
       unique canonical home; `infra.filter.*` and `tools.problem_classifier.*`
       paths forbidden (P3-ARCHDEBT 10/9+1 Phase 46 filter MERGE)
```

## Validation gates — all GREEN

| Gate | Status | Notes |
|------|--------|-------|
| **ruff clean** | ✅ | No new findings |
| **13 phase46 guards** | ✅ | 13/13 PASSED first try |
| **Phase 36-45 prior guards** | ✅ | 107/108 PASSED (1 FAIL fixed by C4.5 fixup) |
| **Migrated tests** | ✅ | test_filter.py + test_problem_classifier.py both pass |
| **sys.path hack eliminated** | ✅ | 2 hacks removed (verified via grep) |
| **Production + test audit (2 modules)** | ✅ | 0 hits |
| **Internal imports clean** | ✅ | Both new modules use `from .quality import X` (relative within package) |

**Total**: 13 phase46 + 107 prior-phase + migrated tests = 120+ tests PASSED.

## 4 lessons (Phase 46)

### Lesson 1: P3-ARCHDEBT MERGE pattern (N.14 lesson 1, 26th occurrence — Phase 46 NEW)

First P3-ARCHDEBT MERGE (vs scaffold-new-package). Boundary case per ARCHDEBT-CANDIDATES.md #5.

**Pattern**: When audit shows:
- 2+ related modules with cross-cutting workspace dep
- Same domain logic (quality, security, etc.)
- Boundary decision: split package = 1-dep with cross-cutting risk; merge = no new package + cleaner imports

**Decision tree**:
1. Both modules operate on same domain (Issue → quality) → consider merge
2. Both modules have sys.path hack for each other → MUST merge
3. New package would have only 1 workspace dep → usually merge

### Lesson 2: sys.path hack removal — clean relative imports (Phase 46 NEW)

Both migrated modules had:
```python
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from lingwen_quality.quality import Issue  # already a workspace package!
```

The hack was redundant. After MERGE, both modules use clean `from lingwen_quality.quality import Issue` (no sys.path manipulation).

**Pattern**: When migrating code with sys.path hacks, ALWAYS remove the hack + use proper imports.

### Lesson 3: N.14 lesson 1 #25 — same brittle pattern repeats (Phase 46 C4.5)

Phase 45 test `test_infra_core_init_retains_unmigrated_wildcards` asserted `from infra.filter import *` was still in infra/core/__init__.py. Phase 46 migrated this wildcard → Phase 45 test broke → C4.5 fixup needed.

**Pattern**: "Wildcard remains" assertions in phase guards break when next phase migrates them. Same lesson as Phase 43 (N.14 lesson 1 #22) and Phase 44 (N.14 lesson 1 #23) — recurring pattern across P3-ARCHDEBT phases.

### Lesson 4: N.14 lesson 1 #25 — spec drift caught pre-commit (Phase 46 C2)

Spec listed 4 consumers for `infra.filter`; actual was **5** (`tests/tools/test_problem_classifier.py:7` was missed in pre-spec 9-pattern audit). Caught during C2 anchored-grep audit before commit, fixed in same commit (no separate fixup needed).

**Pattern**: Pre-spec 9-pattern audit MUST include `tools/` and `tests/tools/` directories (not just infra/, apps/, packages/, tests/). The `tools/problem_classifier.py` consumer was in `tests/tools/` not `tests/` directly.

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 9/8+1 (lingwen-utilities batch) | ✅ | Phase 45 |
| **P3-ARCHDEBT 10/9+1 (filter MERGE into lingwen-quality)** | ✅ | **Phase 46 (this phase)** |
| P3-ARCHDEBT remaining (Phase 47+) | 🟡 | studio_batch_* / full_check_report / memory_service / types / etc. |

**Next-actionable after Phase 46**: Phase 47 = `infra/studio_batch_*` (3 modules shared dep on `lingwen_studio_registry`, per ARCHDEBT-CANDIDATES.md "合并 1 phase").

## References

- Pre-spec: [`docs/superpowers/specs/2026-09-11-phase-46-p3-archdebt-filter-design.md`](../specs/2026-09-11-phase-46-p3-archdebt-filter-design.md)
- ARCHDEBT-CANDIDATES.md #5 (boundary case)
- Phase 34 (lingwen-got) — multi-module migration template
- Phase 36 (errors pilot) — first P3-ARCHDEBT (scaffold-new-package)
- Phase 39 (logging_config) — LEAF pattern (N/A for Phase 46 since MERGE)
- Phase 45 (lingwen-utilities batch) — multi-module batch (4 separate packages, NOT merge)
- Phase 38 C3.5 + Phase 44 C3.5 + Phase 45 C4.5 — prior-phase guard fixup precedents

---

> **All claims in this handoff verified by fresh-run** (Phase 41 mini lesson #1):
> 13 phase46 guards + 107 prior-phase guards (after C4.5 fixup) + migrated tests
> = 120+ PASSED, 0 regressions.