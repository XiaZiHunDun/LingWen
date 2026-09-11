# Phase 45 P3-ARCHDEBT (utilities batch) — 4 LEAF modules Design Spec

> **Phase**: 45 (P3-ARCHDEBT 9/8+1 — continues from Phase 44's `lingwen-prose-calibration` closure)
> **Branch**: `phase-45-p3-archdebt-utilities`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md #4 (batch recommendation: cache + coverage_gate + patterns + result)
> **Template**: Phase 39 (logging_config) + Phase 44 (prose_calibration) — TRUE LEAF batch, 5-commit pattern

## Goal

Move 4 small TRUE-LEAF utility modules (`infra/cache.py` + `infra/coverage_gate.py` + `infra/patterns.py` + `infra/result.py` = 417 LOC total) into 4 standalone canonical packages (`packages/lingwen-cache/` + `packages/lingwen-coverage-gate/` + `packages/lingwen-patterns/` + `packages/lingwen-result/`), deleting the `infra/` sources and adding **invariants I059-I062**. Continues the P3-ARCHDEBT pattern established across Phases 36-44.

This is the FIRST multi-module P3-ARCHDEBT batch phase (vs single-module per phase 36-44).

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit (N.14 lesson 1, 23rd occurrence — wildcard check explicit)

| # | Pattern | cache | coverage_gate | patterns | result | Total |
|---|---------|-------|---------------|----------|--------|-------|
| 1 | Literal dotted-path imports | 3 | 2 | 2 | 1 | 8 |
| 2 | Indented/function-body imports | 0 | 0 | 0 | 0 | 0 |
| 3 | Relative imports | 0 | 0 | 0 | 0 | 0 |
| 4 | Filesystem path literals | 0 | 0 | 0 | 0 | 0 |
| 5 | **Wildcard** `from infra.X import *` | **1** | **1** | **1** | **1** | **4** |
| 6 | `monkeypatch.setattr("infra.X.Y", ...)` | 0 | 0 | 0 | 0 | 0 |
| 7 | Plain `import infra.X` (side-effect) | 0 | 0 | 0 | 0 | 0 |
| 8 | Doc comments referencing old path | 0 | 0 | 0 | 0 | 0 |
| 9 | Prior-phase guard's hardcoded representative | 0 | 0 | 0 | 0 | 0 |

### Real external consumers (12 sites, verified by fresh grep 2026-09-11)

| # | File | Module | Pattern | Migration |
|---|------|--------|---------|-----------|
| 1 | `infra/core/__init__.py:1` | cache | wildcard | `from lingwen_cache import *` |
| 2 | `tests/test_cache.py:5` | cache | single symbol (`CheckerCache`) | `from lingwen_cache import CheckerCache` |
| 3 | `tools/llm_quality/__init__.py:19` | cache | single symbol | `from lingwen_cache import CheckerCache` |
| 4 | `tools/llm_quality/checker.py:13` | cache | single symbol | `from lingwen_cache import CheckerCache` |
| 5 | `infra/core/__init__.py:2` | coverage_gate | wildcard | `from lingwen_coverage_gate import *` |
| 6 | `tests/ci/test_coverage_modules_ci.py:48` | coverage_gate | single symbol | `from lingwen_coverage_gate import evaluate_module_gate` |
| 7 | `tests/infra/test_coverage_gate.py:7` | coverage_gate | multi-symbol | `from lingwen_coverage_gate import (...)` |
| 8 | `infra/core/__init__.py:7` | patterns | wildcard | `from lingwen_patterns import *` |
| 9 | `packages/lingwen-quality/src/lingwen_quality/consistency/checkers/sentence_diversity_checker.py:21` | patterns | single symbol | `from lingwen_patterns import PatternRegistry` |
| 10 | `tests/test_patterns.py:5` | patterns | single symbol | `from lingwen_patterns import PatternRegistry` |
| 11 | `infra/core/__init__.py:8` | result | wildcard | `from lingwen_result import *` |
| 12 | `tests/test_infra_modules.py:382/393/405/416/423` | result | multi-import (5 sites in 1 file) | `from lingwen_result import ...` |

### Infra/core/__init__.py after Phase 45

After Phase 45 migration, `infra/core/__init__.py` will still contain wildcards for **NOT-YET-MIGRATED** modules:
- `infra.filter` (Phase 46+)
- `infra.full_check_report` (Phase 48+)
- `infra.memory_service` (Phase 49+)

The 4 Phase 45 wildcards will be REPLACED in-place (not deleted wholesale) — per Phase 38 + 42 lessons on per-module wildcard handling.

### Doc-only mentions (0 sites — clean TRUE-LEAF migration, no collateral preservation needed)

## Architecture — 4 packages × 2 sub-modules

```
packages/
├── lingwen-cache/             # 91 LOC
│   ├── pyproject.toml
│   ├── src/lingwen_cache/
│   │   ├── __init__.py        # re-exports: CacheEntry + CheckerCache
│   │   └── service.py         # all logic (91 LOC)
│   └── tests/test_cache.py    # MOVED from tests/test_cache.py
│
├── lingwen-coverage-gate/     # 78 LOC
│   ├── pyproject.toml         # PyYAML>=6.0 (3rd-party)
│   ├── src/lingwen_coverage_gate/
│   │   ├── __init__.py        # re-exports: 4 funcs
│   │   └── service.py         # all logic + _FACTORY_ROOT fixup
│   └── tests/test_coverage_gate.py  # MOVED from tests/infra/
│
├── lingwen-patterns/          # 80 LOC
│   ├── pyproject.toml
│   ├── src/lingwen_patterns/
│   │   ├── __init__.py        # re-exports: PatternRegistry + Pattern
│   │   └── service.py         # all logic
│   └── tests/test_patterns.py # MOVED from tests/test_patterns.py
│
└── lingwen-result/            # 168 LOC
    ├── pyproject.toml
    ├── src/lingwen_result/
    │   ├── __init__.py        # re-exports: Ok + Err + Result + 5 funcs
    │   └── service.py         # all logic
    └── tests/test_infra_modules.py  # NOT MOVED (multi-module test, just imports updated)
```

### Public surface (per package)

| Package | Public symbols | Count |
|---------|----------------|-------|
| `lingwen_cache` | `CacheEntry` (dataclass), `CheckerCache` (class) | 2 |
| `lingwen_coverage_gate` | `load_coverage_policy`, `module_percent`, `evaluate_module_gate`, `format_module_gate_report` | 4 |
| `lingwen_patterns` | `PatternRegistry` (class singleton), `Pattern` (type alias) | 2 |
| `lingwen_result` | `Ok` (class), `Err` (class), `Result` (type alias), `ok`, `err`, `wrap`, `from_optional`, `combine`, `either` | 9 |
| **Total** | | **17** |

### Workspace deps — all 4 packages TRUE LEAF

```toml
# packages/lingwen-cache/pyproject.toml
dependencies = []  # TRUE LEAF — stdlib only (hashlib/json/time/dataclasses/pathlib)

# packages/lingwen-coverage-gate/pyproject.toml
dependencies = ["PyYAML>=6.0"]  # 3rd-party only (Phase 39 + Phase 44 pattern)

# packages/lingwen-patterns/pyproject.toml
dependencies = []  # TRUE LEAF — stdlib only (re/typing)

# packages/lingwen-result/pyproject.toml
dependencies = []  # TRUE LEAF — stdlib only (typing)
```

### `_FACTORY_ROOT` path resolution (coverage_gate only)

Only `lingwen_coverage_gate.service` needs path resolution fixup (uses `_FACTORY_ROOT` like Phase 44 prose_calibration).

- Old: `Path(__file__).resolve().parents[1]` (from `infra/coverage_gate.py`) → repo root
- New: `Path(__file__).resolve().parents[4]` (from `packages/lingwen-coverage-gate/src/lingwen_coverage_gate/service.py`) → repo root

`cache`, `patterns`, `result` modules have no `_FACTORY_ROOT` — pure logic, no path resolution needed.

### Invariants I059-I062

```
I059 | `packages/lingwen-cache/` is CheckerCache + CacheEntry (dataclass) unique canonical package;
       `infra.cache.*` paths forbidden (P3-ARCHDEBT 9/8+1 Phase 45 cache)

I060 | `packages/lingwen-coverage-gate/` is coverage module gate helpers
       (load_coverage_policy + module_percent + evaluate_module_gate + format_module_gate_report)
       unique canonical package; `infra.coverage_gate.*` paths forbidden (P3-ARCHDEBT 9/8+1 Phase 45 coverage_gate)

I061 | `packages/lingwen-patterns/` is PatternRegistry (singleton) + Pattern type alias
       unique canonical package; `infra.patterns.*` paths forbidden (P3-ARCHDEBT 9/8+1 Phase 45 patterns)

I062 | `packages/lingwen-result/` is Result type (Ok/Err union) + 5 helper functions
       (ok + err + wrap + from_optional + combine + either) unique canonical package;
       `infra.result.*` paths forbidden (P3-ARCHDEBT 9/8+1 Phase 45 result)
```

## Atomic commits (5 total — batch pattern)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-45)` | spec | This document (covers 4 modules) |
| **C1** | `feat(packages)` | scaffold 4 packages | 4× pyproject + 4× __init__.py + 4× service.py + 4× workspace register + 3× test MOVE |
| **C2** | `refactor(consumers)` | bulk 12 sites | Single commit per Phase 37 lesson (12 sites = safe) |
| **C3** | `chore(infra)` | delete 4 files + I059-I062 + v43.0 | 4 files DELETED + 4 invariants + version bump |
| **C4** | `test(phase-45)` | 20+ guards + handoff + MEMORY | Guards cover all 4 packages + handoff doc + topic file |

### C1 details (scaffold — 4 packages in single commit)

**Files created** (16 total):
- 4× `pyproject.toml` (one per package)
- 4× `__init__.py` (one per package)
- 4× `service.py` (one per package)
- 3× test file MOVES (cache + coverage_gate + patterns) — result test NOT moved (multi-module test file)

**Files modified**:
- Root `pyproject.toml` — add 4 new workspace members BEFORE uv sync (per Phase 34 lesson)

### C2 details (bulk migrate 12 sites — single commit per Phase 37 lesson)

```
refactor(consumers): migrate 12 sites from infra.{cache,coverage_gate,patterns,result} to lingwen_*

Phase 45 P3-ARCHDEBT (4-module batch):

  cache (4 sites):
    infra/core/__init__.py:1                  wildcard → from lingwen_cache import *
    tests/test_cache.py:5                     single symbol (CheckerCache)
    tools/llm_quality/__init__.py:19          single symbol (CheckerCache)
    tools/llm_quality/checker.py:13           single symbol (CheckerCache)

  coverage_gate (3 sites):
    infra/core/__init__.py:2                  wildcard → from lingwen_coverage_gate import *
    tests/ci/test_coverage_modules_ci.py:48   single symbol (evaluate_module_gate)
    tests/infra/test_coverage_gate.py:7       multi-symbol

  patterns (3 sites):
    infra/core/__init__.py:7                  wildcard → from lingwen_patterns import *
    packages/lingwen-quality/src/lingwen_quality/...
      consistency/checkers/sentence_diversity_checker.py:21
                                            single symbol (PatternRegistry)
    tests/test_patterns.py:5                 single symbol (PatternRegistry)

  result (2 sites — wildcard + 1 test file with 5 imports):
    infra/core/__init__.py:8                  wildcard → from lingwen_result import *
    tests/test_infra_modules.py:382/393/405/416/423
                                            multi-import (5 sites in 1 file)

Test file MOVEs (in C1, not C2):
  tests/test_cache.py           → packages/lingwen-cache/tests/test_cache.py
  tests/infra/test_coverage_gate.py → packages/lingwen-coverage-gate/tests/test_coverage_gate.py
  tests/test_patterns.py        → packages/lingwen-patterns/tests/test_patterns.py

tests/test_infra_modules.py NOT moved (multi-module test, just imports updated in-place).
```

### C3 details (delete 4 files + 4 invariants)

**Files modified**:
- `infra/cache.py` — DELETED
- `infra/coverage_gate.py` — DELETED
- `infra/patterns.py` — DELETED
- `infra/result.py` — DELETED
- `CLAUDE.md` — version v42.0 → v43.0 + invariants I059-I062 added to table
- `.lingwen/architecture.yml` — version field updated + invariants list I059-I062 added

### C4 details (guards + handoff + doc-sync)

**Files created**:
- `tests/test_phase45_lingwen_utilities.py` (20 regression guards covering 4 packages)
- `docs/superpowers/handoffs/2026-09-11-phase-45-p3-archdebt-utilities-handoff.md`

**Files modified**:
- `CLAUDE.md` — version bump entry + handoff link
- `MEMORY.md` — Phase 45 entry + 4 lessons
- Memory topic file: `phase-45-p3-archdebt-utilities.md`

## Validation gates (Phase 45 acceptance)

1. ✅ ruff clean on all 4 changed Python packages
2. ✅ `pytest packages/lingwen-cache/tests/` passes (moved tests)
3. ✅ `pytest packages/lingwen-coverage-gate/tests/` passes (moved tests)
4. ✅ `pytest packages/lingwen-patterns/tests/` passes (moved tests)
5. ✅ `pytest packages/lingwen-result/tests/` — N/A (no moved test; `tests/test_infra_modules.py` covers result tests via in-place import update)
6. ✅ `pytest tests/test_infra_modules.py` passes (result + 5 imports updated)
7. ✅ `pytest tools/llm_quality/` passes (cache imports updated)
8. ✅ Phase 36-44 guards preserved (9 prior-phase guard files)
9. ✅ New Phase 45 guards (20 tests)
10. ✅ Production audit: `grep -rn "infra\.(cache|coverage_gate|patterns|result)\b" infra/ apps/ packages/ tests/ tools/` → 0 hits
11. ✅ Test audit: `grep -rn "infra\.(cache|coverage_gate|patterns|result)\b" tests/` → 0 hits
12. ✅ `_FACTORY_ROOT` resolution verified for `lingwen_coverage_gate` (parents[4])
13. ✅ 4 NEW invariants I059-I062 in `.lingwen/architecture.yml`
14. ✅ 4 NEW invariants I059-I062 in `CLAUDE.md` 架构不变量 table
15. ✅ Module-load behavior preserved: `from lingwen_X import Y` works for all 4 packages

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Multi-module batch coordination errors | MEDIUM | C1 scaffold in single commit ensures atomic package creation |
| 12-site bulk migration misses a site | LOW | Pre-spec 9-pattern audit verified all 12 sites; C2 commit message lists each |
| `_FACTORY_ROOT` breaks for coverage_gate only | LOW | parents[1] → parents[4] in C1 (same pattern as Phase 44 prose_calibration) |
| `infra/core/__init__.py` over-cleared (lost unrelated wildcards) | LOW | Only 4 lines migrated; remaining 3 wildcards (filter, full_check_report, memory_service) untouched |
| Test file MOVE + import update atomicity | LOW | C1 does MOVE + import update; C2 only updates non-moved tests |
| `tests/test_infra_modules.py` result imports (5 sites in 1 file) | LOW | Bulk sed in C2 with `\1` backreference (Phase 37 lesson) |
| Pre-existing E741 ruff errors | n/a | Same as Phase 35 baseline |
| Version assertion in Phase 36-44 guards breaks (N.14 lesson 1 #22) | LOW | Phase 43 already fixed (C3.5); Phase 44 forward-compat; Phase 45 same pattern |

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ Phase 36-40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ Phase 42 |
| P3-ARCHDEBT 7/6+1 (lingwen-llm-service) | ✅ Phase 43 |
| P3-ARCHDEBT 8/7+1 (lingwen-prose-calibration) | ✅ Phase 44 |
| **P3-ARCHDEBT 9/8+1 (lingwen-utilities batch: cache+coverage_gate+patterns+result)** | 🟡 Phase 45 (this phase) |
| P3-ARCHDEBT 10/9+1 (filter near-LEAF) | 🟡 Phase 46+ |

**Next-actionable after Phase 45**: Phase 46 = `infra/filter` (1 workspace dep lingwen-quality, 4 consumers, 63 LOC — boundary check whether to split package).

## References

- ARCHDEBT-CANDIDATES.md #4 (this phase — batch recommendation)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 38 (project_config) — C3.5 fixup precedent
- Phase 39 (logging_config) — TRUE LEAF template (5-commit pattern)
- Phase 40a (studio_registry) — C1.5 fixup pattern (path resolution after relocation)
- Phase 42 (project_init) — wildcard-in-`__init__.py` lesson + `__all__` count spec drift
- Phase 43 (lingwen-llm-service) — bulk 6-site migration + DP-02 contract (N/A for Phase 45)
- Phase 44 (lingwen-prose-calibration) — TRUE LEAF single-module template (this phase EXTENDS to multi-module)

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (12 consumers, 4 modules, 4 wildcards, 0 doc-only mentions, 17 total public symbols)
> was verified by fresh-run grep on 2026-09-11 BEFORE writing this spec. No stale-count claims.