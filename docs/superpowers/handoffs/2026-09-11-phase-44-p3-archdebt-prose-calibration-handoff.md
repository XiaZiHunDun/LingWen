# Phase 44 P3-ARCHDEBT (lingwen-prose-calibration) Handoff

> **Date**: 2026-09-11
> **Phase**: 44 — P3-ARCHDEBT item 8/7+1
> **Branch**: `phase-44-p3-archdebt-prose-calibration`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **Spec**: [`docs/superpowers/specs/2026-09-11-phase-44-p3-archdebt-prose-calibration-design.md`](../specs/2026-09-11-phase-44-p3-archdebt-prose-calibration-design.md)
> **ARCHDEBT Rank**: #3 in [ARCHDEBT-CANDIDATES.md](../ARCHDEBT-CANDIDATES.md)

## TL;DR

`infra/prose_calibration.py` (191 LOC, 8 public symbols + 2 private consts, TRUE LEAF 0 workspace deps) → `packages/lingwen-prose-calibration/` (2 sub-modules: service.py + __init__.py). 6 consumers migrated in single atomic C2 commit. `_FACTORY_ROOT` path resolution fixup in C1 (parents[1] → parents[4]). 1 NEW invariant (I058). Version bump v41.0 → v42.0.

## Atomic commits (6 total on `phase-44-p3-archdebt-prose-calibration`)

| SHA | Type | Scope | Notes |
|-----|------|-------|-------|
| `3adc6448` | `docs(phase-44)` | spec | Pre-spec 9-pattern audit verified 6 consumers + 0 doc-only mentions |
| `6f6122cd` | `feat(packages)` | scaffold | 2 sub-modules + pyproject + workspace register + _FACTORY_ROOT fixup + test MOVE |
| `faf9749f` | `refactor(consumers)` | bulk 6 sites | Single atomic commit per Phase 37 lesson |
| `bf71035c` | `chore(infra)` | delete + I058 + v42.0 | infra/prose_calibration.py DELETED (FULL DELETE) |
| `b529388d` | `fix(test)` | C3.5 fixup | Phase 43 guard forward-compatible version check (N.14 lesson 1 #22) |
| `<C4>` | `test(phase-44)` | 13 guards + handoff + MEMORY | Pending commit (this file) |

## Pre-spec audit (Phase 42 lesson #1 reinforcement — wildcard-in-`__init__.py`)

### 9-pattern audit results

| # | Pattern | Sites found |
|---|---------|-------------|
| 1 | Literal dotted-path imports `from infra.prose_calibration import X` | 5 |
| 2 | Indented/function-body imports | 0 |
| 3 | Relative imports | 0 |
| 4 | Filesystem path literals | 0 |
| 5 | Wildcard `from infra.prose_calibration import *` | **1** (`infra/prose/__init__.py:1`) |
| 6 | `monkeypatch.setattr("infra.prose_calibration.X", ...)` | 0 |
| 7 | Plain `import infra.prose_calibration` (side-effect) | 0 |
| 8 | Doc comments referencing old path | 0 |
| 9 | Prior-phase guard's hardcoded representative | 0 |

### Real external consumers (6 sites, verified by fresh grep 2026-09-11)

| # | File | Pattern | Migration |
|---|------|---------|-----------|
| 1 | `infra/prose/__init__.py:1` | wildcard | `from lingwen_prose_calibration import *` |
| 2 | `infra/full_check_report.py:271` | single symbol | `from lingwen_prose_calibration import build_prose_heatmap` |
| 3 | `infra/prose_judge.py:12` | multi-symbol | `from lingwen_prose_calibration import is_prose_issue, load_prose_config` |
| 4 | `infra/prose_snapshot.py:10` | multi-symbol | `from lingwen_prose_calibration import build_prose_heatmap, is_prose_issue, load_prose_config` |
| 5 | `tests/ci/test_llm_golden_primary_ci.py:19` | single symbol | `from lingwen_prose_calibration import list_primary_revision_slugs` |
| 6 | `tests/infra/test_prose_calibration.py:5` | multi-symbol block | **MOVE** → `packages/lingwen-prose-calibration/tests/test_prose_calibration.py` (C1) |

### False-positive filter (1 site excluded)

| File | Line | Reason |
|------|------|--------|
| `tests/infra/test_prose_calibration_overrides.py` | 7 | Imports from `infra.prose_calibration_overrides` (DIFFERENT module, separate P3-ARCHDEBT candidate for Phase 45+) |

### Doc-only mentions (0 sites — clean TRUE-LEAF migration)

Unlike Phase 43 (8 doc-only mentions), Phase 44 has **zero** doc-only mentions. No collateral preservation needed.

## Architecture (canonical layout — TRUE LEAF)

```
packages/lingwen-prose-calibration/
├── pyproject.toml                                    # PyYAML>=6.0 (3rd-party only, 0 workspace deps)
├── src/
│   └── lingwen_prose_calibration/
│       ├── __init__.py    # 8 public symbols re-export
│       └── service.py     # 191 LOC, all logic
└── tests/
    └── test_prose_calibration.py    # 9 tests moved from tests/infra/
```

### Public surface (8 symbols, EXACTLY 8 — verified by `len(__all__) == 8`)

- `load_prose_config` (cached config loader)
- `is_prose_issue` (issue type matcher)
- `build_prose_heatmap` (Studio dashboard heatmap)
- `evaluate_against_baseline` (golden baseline gate)
- `format_calibration_report` (CLI report formatter)
- `list_primary_revision_slugs` (七样章主修书 selector)
- `is_primary_revision_slug` (single slug check)
- `resolve_llm_post_check` (LLM golden post-check policy resolver)

Plus 2 private consts: `_FACTORY_ROOT` (repo root Path), `_DEFAULT_CONFIG` (config yaml Path).

### TRUE LEAF — 0 workspace deps

```toml
dependencies = ["PyYAML>=6.0"]  # 3rd-party only
```

`PyYAML` is also declared in root `pyproject.toml` runtime deps. Declaring explicitly makes the package installable in isolation (Phase 39 LEAF template pattern).

### `_FACTORY_ROOT` path resolution fixup (Phase 40a C1.5 lesson)

Old: `Path(__file__).resolve().parents[1]` (from `infra/prose_calibration.py`) → repo root.
New: `Path(__file__).resolve().parents[4]` (from `packages/lingwen-prose-calibration/src/lingwen_prose_calibration/service.py`) → repo root.

Verified by `test_factory_root_resolves_to_repo_root` guard.

## Validation gates — all GREEN

| Gate | Status | Notes |
|------|--------|-------|
| **ruff clean** | ✅ | No new findings (pre-existing E741 baseline unchanged) |
| **lingwen_prose_calibration importable** | ✅ | `from lingwen_prose_calibration import load_prose_config` works |
| **`__all__ == 8 symbols EXACTLY** | ✅ | Phase 42 lesson #4 enforced |
| **`_FACTORY_ROOT == PROJECT_ROOT** | ✅ | Phase 40a C1.5 fixup verified |
| **test_prose_calibration.py (9 tests moved)** | ✅ | 9/9 PASSED |
| **Phase 44 guards (13 tests)** | ✅ | 13/13 PASSED |
| **Phase 36-43 prior guards (62 tests)** | ✅ | 62/62 PASSED (after C3.5 fixup) |
| **Production audit (no `infra.prose_calibration` runtime imports)** | ✅ | 0 hits |
| **Test audit (no `infra.prose_calibration` runtime imports)** | ✅ | 0 hits |
| **Module-load behavior preserved** | ✅ | `load_prose_config()` returns same shape dict |

**Total**: 84 tests passing across 4 test suites (Phase 36-43 guards + Phase 44 guards + migrated test_prose_calibration.py).

## 4 lessons (Phase 44)

### Lesson 1: TRUE LEAF — no factory.py needed (N.14 lesson 1, 21st occurrence)

Phase 44 is a TRUE LEAF (0 workspace deps; only stdlib + PyYAML). Unlike Phase 43 (NOT-LEAF with factory.py + module-load DP-02 contract), Phase 44 only needs 2 sub-modules: `service.py` (all logic) + `__init__.py` (re-exports).

**Pattern**: TRUE LEAF migrations → 2 sub-modules; NOT-LEAF migrations → 3+ sub-modules (add factory.py for module-load side effects).

### Lesson 2: brittle version assertion in P3-ARCHDEBT phase guards (N.14 lesson 1 #22)

Phase 43's `test_invariant_in_claude_md` asserted strict `assert "v41.0" in content`. After Phase 44 bumped version to v42.0 (replacing v41.0 in header), this strict check broke — requiring a C3.5 fixup commit.

**Pattern**: P3-ARCHDEBT phase guards should use regex-based version checks `>= vN.0` to allow version drift across future phases. Per Phase 38 C3.5 precedent, this requires a separate fixup commit between C3 (delete + invariant) and C4 (guards + handoff).

### Lesson 3: false-positive filter for prose_calibration_overrides (Phase 44 NEW)

The grep audit found 7 files mentioning `prose_calibration`, but 1 of those (`tests/infra/test_prose_calibration_overrides.py`) imports from `infra.prose_calibration_overrides` (DIFFERENT module). The `\b` word-boundary in grep regex correctly excludes this false positive:

```
^[[:space:]]*(from infra\.prose_calibration\b|import infra\.prose_calibration\b)\b
                                                       ^^ ensures `_overrides` excluded
```

Without `\b`, the audit would have flagged `prose_calibration_overrides` as a hit and required migration that doesn't apply.

### Lesson 4: workspace deps handling for 3rd-party packages (Phase 39 template reused)

Phase 44 uses PyYAML which is already in root `pyproject.toml` runtime deps. Declaring `PyYAML>=6.0` explicitly in the package pyproject makes it installable in isolation (no transitive reliance on root). This is Phase 39 logging_config pattern — even for stdlib-only packages, explicit declaration is best practice.

For pure stdlib LEAF (like Phase 39), deps would be `dependencies = []`. For 3rd-party LEAF (like Phase 44), deps include the 3rd-party packages explicitly.

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ | Phase 36-40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ | Phase 42 |
| P3-ARCHDEBT 7/6+1 (lingwen-llm-service) | ✅ | Phase 43 |
| **P3-ARCHDEBT 8/7+1 (lingwen-prose-calibration)** | ✅ | **Phase 44 (this phase)** |
| P3-ARCHDEBT 9/8+1 (cache LEAF batch) | 🟡 | Phase 45+ |
| P3-ARCHDEBT 10/9+1 (filter near-LEAF) | 🟡 | Phase 46+ |

## References

- Pre-spec: [`docs/superpowers/specs/2026-09-11-phase-44-p3-archdebt-prose-calibration-design.md`](../specs/2026-09-11-phase-44-p3-archdebt-prose-calibration-design.md)
- ARCHDEBT-CANDIDATES.md #3 (this phase ranked #3)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 38 (project_config) — C3.5 fixup precedent (N.14 lesson 1 #9)
- Phase 39 (logging_config) — TRUE LEAF template (5-commit pattern, 0 workspace deps, explicit PyYAML-style 3rd-party handling)
- Phase 40a (studio_registry) — C1.5 fixup pattern (path resolution after relocation)
- Phase 42 (project_init) — wildcard-in-`__init__.py` lesson + `__all__` count spec drift prevention
- Phase 43 (lingwen-llm-service) — bulk 6-site migration pattern + DP-02 contract preservation (N/A for Phase 44 since no DP-02 equivalent)

---

> **All claims in this handoff verified by fresh-run** (Phase 41 mini lesson #1):
> 13 phase44 guards + 9 migrated tests + 62 prior-phase guards (after C3.5 fixup)
> = 84 PASSED, 0 regressions.