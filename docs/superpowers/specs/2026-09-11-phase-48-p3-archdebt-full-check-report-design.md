# Phase 48 P3-ARCHDEBT (full_check_report) — lingwen-full-check-report Design Spec

> **Phase**: 48 (P3-ARCHDEBT 12/11+1 — continues from Phase 47's `studio_batch` batch closure)
> **Branch**: `phase-48-p3-archdebt-full-check-report`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md "full_check_report" (cross-cutting candidate)
> **Template**: Phase 44 (lingwen-prose-calibration) — single-module LEAF-ish template, 5-commit pattern

## Goal

Move `infra/full_check_report.py` (287 LOC, 13 public symbols, NOT-LEAF 3 workspace deps) into standalone canonical package `packages/lingwen-full-check-report/`. Delete the `infra/` source and add **invariant I067**. Continue P3-ARCHDEBT pattern.

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit

| # | Pattern | Sites |
|---|---------|-------|
| 1 | Literal dotted-path imports `from infra.full_check_report import X` | 3 |
| 2 | Indented/function-body imports | 0 |
| 3 | Relative imports | 0 |
| 4 | Filesystem path literals | 0 |
| 5 | **Wildcard** `from infra.full_check_report import *` | **1** |
| 6 | `monkeypatch.setattr` + `with patch("infra.X.Y", ...)` | 0 |
| 7 | Plain `import infra.X` | 0 |
| 8 | Doc comments referencing old path | 0 |
| 9 | Prior-phase guard's hardcoded representative | 0 |

### Real external consumers (4 sites, verified by fresh grep 2026-09-11)

| # | File | Pattern | Migration |
|---|------|---------|-----------|
| 1 | `infra/core/__init__.py:4` | wildcard | `from lingwen_full_check_report import *` |
| 2 | `infra/prose_judge.py` | single symbol (intra-infra) | `from lingwen_full_check_report import <symbol>` |
| 3 | `packages/lingwen-studio-registry/src/lingwen_studio_registry/reports.py` | single symbol (cross-package, NEWLY added in Phase 47) | `from lingwen_full_check_report import <symbol>` |
| 4 | `tests/infra/test_full_check_report.py` | single symbol | `from lingwen_full_check_report import <symbol>` |

### False-positive filter (2 string-literal sites in test docstrings — N.14 lesson 1 #25)

| File | Line | Reason |
|------|------|--------|
| `tests/test_phase45_lingwen_utilities.py:395` | docstring `"from infra.full_check_report import *"` | Phase 45 documentation string. NOT a real import. |
| `tests/test_phase46_lingwen_filter.py:282` | docstring `"from infra.full_check_report import *"` | Phase 46 documentation string. NOT a real import. |

### Spec drift (N.14 lesson 1 #25)

ARCHDEBT-CANDIDATES.md said "4 consumers". Actual real consumers = 4 (matches spec ✅). The 2 false-positives (Phase 45 + 46 test files) are STRING LITERALS in docstrings, NOT real imports.

### Architecture

#### Package layout (2 sub-modules — single-module pattern per Phase 44)

```
packages/lingwen-full-check-report/
├── pyproject.toml                            # 3 workspace deps (NOT-LEAF)
├── src/lingwen_full_check_report/
│   ├── __init__.py                           # re-exports 13 public symbols
│   └── service.py                            # 287 LOC, all logic
└── tests/test_full_check_report.py            # MOVED from tests/infra/
```

#### Public surface (13 public symbols)

| Symbol | Kind |
|--------|------|
| `report_path_for` | func |
| `collect_prose_vitality_scores` | func |
| `collect_full_check_issues` | func |
| `format_report_markdown` | func |
| `generate_report` | func |
| `parse_report_markdown` | func |
| `load_report_summary` | func |
| (private funcs: `_char_count`, `_severity_counts`, `_extract_generated_at`) | not re-exported |
| (private consts: `_TOTAL_RE`, `_CHAPTER_RE`, `_VITALITY_RE`, `_ISSUE_RE`) | not re-exported |

#### Workspace deps — NOT-LEAF (3 deps)

```toml
dependencies = [
    "lingwen-paths",                                          # ProjectPaths (Phase 37)
    "lingwen-quality",                                         # ConsistencyEngine + Issue (Phase 36)
]
```

Note: `lingwen_quality.consistency.engine.consistency_engine` + `lingwen_quality.consistency.engine.data_structures` are submodules of `lingwen-quality`. Declaring `lingwen-quality` as workspace dep covers both.

#### `_FACTORY_ROOT` migration

N/A — `infra/full_check_report.py` has NO `_FACTORY_ROOT` or `_DEFAULT_*` constants. Module-load behavior is preserved as-is.

### Invariant I067

```
I067 | `packages/lingwen-full-check-report/` is full-check report generation + parsing
       (report_path_for + collect_prose_vitality_scores + collect_full_check_issues +
       format_report_markdown + generate_report + parse_report_markdown +
       load_report_summary) unique canonical package;
       `infra.full_check_report.*` paths forbidden (P3-ARCHDEBT 12/11+1 Phase 48)
```

## Atomic commits (5 total per Phase 44 LEAF template)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-48)` | spec | This document |
| **C1** | `feat(packages)` | scaffold | 2 sub-modules + pyproject + workspace register + tool.uv.sources + test MOVE |
| **C2** | `refactor(consumers)` | bulk 4 sites | Single commit per Phase 37 lesson |
| **C3** | `chore(infra)` | delete + I067 + v46.0 | infra/full_check_report.py DELETED + invariant + version bump |
| **C4** | `test(phase-48)` | guards + handoff | Phase 48 guards + handoff doc + topic file |

### C1 details

**Files created** (3):
- `packages/lingwen-full-check-report/pyproject.toml` (NOT-LEAF, 2 deps)
- `packages/lingwen-full-check-report/src/lingwen_full_check_report/__init__.py` (re-exports)
- `packages/lingwen-full-check-report/src/lingwen_full_check_report/service.py` (287 LOC)

**Files moved** (1):
- `tests/infra/test_full_check_report.py` → `packages/lingwen-full-check-report/tests/test_full_check_report.py`

**Files modified** (1):
- Root `pyproject.toml` — add `packages/lingwen-full-check-report` to workspace + `[tool.uv.sources]`

### C2 details (single bulk commit)

```
refactor(consumers): migrate 4 sites from infra.full_check_report to lingwen_full_check_report

Phase 48 P3-ARCHDEBT:

  infra/core/__init__.py:4                  wildcard → from lingwen_full_check_report import *
  infra/prose_judge.py                       single symbol (intra-infra)
  packages/lingwen-studio-registry/
    src/lingwen_studio_registry/reports.py  single symbol (cross-package, Phase 47 NEW)
  tests/infra/test_full_check_report.py      single symbol (moved in C1)
```

Test file MOVE (in C1, not C2):
  tests/infra/test_full_check_report.py → packages/lingwen-full-check-report/tests/test_full_check_report.py

infra/core/__init__.py retains 2 wildcards for NOT-YET-MIGRATED modules:
  infra.filter (Phase 46 MERGED but wildcard remains in infra/core/__init__.py?)
  infra.memory_service (Phase 49+)
```

## Validation gates (Phase 48 acceptance)

1. ✅ ruff clean on changed Python files
2. ✅ 4 consumer files migrated
3. ✅ Phase 36-47 guards preserved (12 prior-phase guard files)
4. ✅ New Phase 48 guards (10+ tests)
5. ✅ Production audit: `grep -rn "infra\.full_check_report\b" infra/ apps/ packages/ tests/ tools/` → 0 hits
6. ✅ Test audit: same grep in tests/ → 0 hits
7. ✅ `__all__` exact count (13 public symbols)
8. ✅ I067 in `.ling + architecture.yml` + `CLAUDE.md`

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 2 string-literal docstring refs in Phase 45/46 tests flagged as violations | LOW | `\b` boundary in grep + exclude docstring lines |
| Wildcard state in `infra/core/__init__.py` after Phase 46 | MEDIUM | Phase 46 MERGE preserves `infra.filter` wildcard (per Phase 46 lessons) — verify state before C3 |
| `lingwen-quality` workspace dep covered `lingwen_quality.consistency.engine.*` | LOW | Pre-spec verified — both submodules exist in `lingwen-quality` |

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 11/10+1 (studio_batch batch) | ✅ | Phase 47 |
| **P3-ARCHDEBT 12/11+1 (full_check_report)** | 🟡 | Phase 48 (this phase) |
| P3-ARCHDEBT remaining (Phase 49+) | 🟡 | memory_service / types / filter (post-Phase 46 MERGE cleanup) |

**Next-actionable after Phase 48**: Phase 49 = `infra/memory_service` (4 consumers, 10 deps heavy — likely NOT-LEAF with 3+ workspace deps).

## References

- ARCHDEBT-CANDIDATES.md "full_check_report" (4 consumers, 3 deps)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 37 (paths) — C3.5 fixup precedent
- Phase 44 (lingwen-prose-calibration) — single-module LEAF template
- Phase 47 (studio_batch batch) — provides `lingwen_studio_registry.reports` cross-package consumer

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (287 LOC, 13 public symbols, 4 real consumers + 2 false-positives, NOT-LEAF 3 deps)
> was verified by fresh-run grep on 2026-09-11 BEFORE writing this spec.
> No stale-count claims.