# Phase 44 P3-ARCHDEBT (prose_calibration) — lingwen-prose-calibration Design Spec

> **Phase**: 44 (P3-ARCHDEBT 8/7+1 — continues from Phase 43's `lingwen-llm-service` closure)
> **Branch**: `phase-44-p3-archdebt-prose-calibration`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md #3 (TRUE LEAF, easiest remaining)
> **Template**: Phase 39 (logging_config) — TRUE LEAF pilot, 5-commit pattern

## Goal

Move `infra/prose_calibration.py` (191 LOC, 8 public symbols, TRUE LEAF 0 workspace deps) into a standalone
canonical package `packages/lingwen-prose-calibration/`, deleting the `infra/` shim and adding
**invariant I058** to forbid reintroduction. Continues the P3-ARCHDEBT pattern established
across Phases 36-43.

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit (N.14 lesson 1, 21st occurrence — wildcard check explicit)

| # | Pattern | Finding | Action |
|---|---------|---------|--------|
| 1 | Literal dotted-path imports `from infra.prose_calibration import X` | 5 sites | Migrate all 5 |
| 2 | Indented/function-body imports | 0 sites | n/a |
| 3 | Relative imports | 0 sites | n/a |
| 4 | Filesystem path literals `infra/prose_calibration.py` | 0 sites | n/a |
| 5 | Wildcard `from infra.prose_calibration import *` | **1 site: `infra/prose/__init__.py:1`** | Migrate wildcard |
| 6 | `monkeypatch.setattr("infra.prose_calibration.X", ...)` | 0 sites | n/a |
| 7 | `import infra.prose_calibration` (plain) | 0 sites | n/a |
| 8 | Doc comments referencing old path | 0 sites | n/a |
| 9 | Prior-phase guard's hardcoded representative files | 0 sites | n/a |

### Real external consumers (6 sites, verified by fresh grep 2026-09-11)

| # | File | Line | Pattern | Migration |
|---|------|------|---------|-----------|
| 1 | `infra/prose/__init__.py` | 1 | wildcard `from infra.prose_calibration import *` | `from lingwen_prose_calibration import *` |
| 2 | `infra/full_check_report.py` | 271 | `from infra.prose_calibration import build_prose_heatmap` | `from lingwen_prose_calibration import build_prose_heatmap` |
| 3 | `infra/prose_judge.py` | 12 | `from infra.prose_calibration import is_prose_issue, load_prose_config` | `from lingwen_prose_calibration import is_prose_issue, load_prose_config` |
| 4 | `infra/prose_snapshot.py` | 10 | `from infra.prose_calibration import build_prose_heatmap, is_prose_issue, load_prose_config` | `from lingwen_prose_calibration import build_prose_heatmap, is_prose_issue, load_prose_config` |
| 5 | `tests/ci/test_llm_golden_primary_ci.py` | 19 | `from infra.prose_calibration import list_primary_revision_slugs` | `from lingwen_prose_calibration import list_primary_revision_slugs` |
| 6 | `tests/infra/test_prose_calibration.py` | 5 | multi-symbol `from infra.prose_calibration import (...)` | `from lingwen_prose_calibration import (...)` |

### False-positive filter (1 site excluded)

| File | Line | Reason |
|------|------|--------|
| `tests/infra/test_prose_calibration_overrides.py` | 7 | Imports from `infra.prose_calibration_overrides` (a SEPARATE module, NOT `infra.prose_calibration`). Different module, different package candidate (Phase 45+). |

### Doc-only mentions (0 sites — no migration noise)

Unlike Phase 43 (8 doc-only mentions preserved), Phase 44 has **zero** doc-only mentions.
This is a clean TRUE-LEAF migration with minimal collateral.

## Architecture

### Package layout (2 sub-modules — TRUE LEAF, no factory.py needed)

```
packages/lingwen-prose-calibration/
├── pyproject.toml                                  # PyYAML>=6.0 (3rd-party, not workspace)
├── src/
│   └── lingwen_prose_calibration/
│       ├── __init__.py                             # public re-exports (8 symbols)
│       └── service.py                              # all logic (191 LOC, 8 funcs + 2 consts)
└── tests/
    └── test_prose_calibration.py                    # 6+ tests moved from tests/infra/
```

### Public surface (8 symbols + 2 private consts)

| Symbol | Kind | Source location |
|--------|------|-----------------|
| `load_prose_config` (cached) | public func | service.py |
| `is_prose_issue` | public func | service.py |
| `build_prose_heatmap` | public func | service.py |
| `evaluate_against_baseline` | public func | service.py |
| `format_calibration_report` | public func | service.py |
| `list_primary_revision_slugs` | public func | service.py |
| `is_primary_revision_slug` | public func | service.py |
| `resolve_llm_post_check` | public func | service.py |
| `_FACTORY_ROOT` (private) | constant | service.py (Path to repo root) |
| `_DEFAULT_CONFIG` (private) | constant | service.py (Path to config yaml) |

### Workspace deps (TRUE LEAF, 0 workspace deps)

```toml
[project]
dependencies = [
    "PyYAML>=6.0",  # 3rd-party only — declared explicitly since package is installable standalone
]
```

`PyYAML` is already declared in root `pyproject.toml` runtime deps (line 44). Declaring
explicitly in the package makes it installable in isolation (good practice per Phase 39 LEAF).

### `_FACTORY_ROOT` migration

Original: `_FACTORY_ROOT = Path(__file__).resolve().parents[1]` — relative to `infra/`, points to repo root.

After relocation to `packages/lingwen-prose-calibration/src/lingwen_prose_calibration/service.py`,
the path resolution changes:
- Old: `infra/prose_calibration.py` → parents[1] = repo root (correct)
- New: `packages/lingwen-prose-calibration/src/lingwen_prose_calibration/service.py` → parents[1] = `src/`, parents[4] = repo root

**Fix**: Update to `Path(__file__).resolve().parents[4]` (4 levels up to repo root from the new location).
This is similar to Phase 40a `factory_root()` fixup (Phase 40a C1.5 commit).

**Verification**: 
```python
# In worktree, after relocation:
>>> from pathlib import Path
>>> Path("/home/ailearn/projects/LingWen/packages/lingwen-prose-calibration/src/lingwen_prose_calibration/service.py").resolve().parents[4]
PosixPath("/home/ailearn/projects/LingWen")  # ✅ repo root
```

### Invariant I058

```
I058 | `packages/lingwen-prose-calibration/` is prose calibration config + heatmap +
       golden baseline gate + format helpers (load_prose_config + is_prose_issue +
       build_prose_heatmap + evaluate_against_baseline + format_calibration_report +
       list_primary_revision_slugs + is_primary_revision_slug + resolve_llm_post_check)
       unique canonical package; `infra.prose_calibration.*` paths forbidden
       (P3-ARCHDEBT 8/7+1 Phase 44)
```

## Atomic commits (5 total per Phase 39 LEAF template)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-44)` | spec | This document |
| **C1** | `feat(packages)` | scaffold `packages/lingwen-prose-calibration/` | 2 sub-modules + pyproject + workspace register |
| **C2** | `refactor(consumers)` | bulk migrate 6 sites | Single commit per Phase 37 lesson |
| **C3** | `chore(infra)` | delete `infra/prose_calibration.py` + I058 + version | v41.0 → v42.0 |
| **C4** | `test(phase-44)` | regression guards + handoff + CLAUDE.md + MEMORY | 10+ guards + topic file |

### C1 details (scaffold)

**Files created**:
- `packages/lingwen-prose-calibration/pyproject.toml` (workspace member + PyYAML dep)
- `packages/lingwen-prose-calibration/src/lingwen_prose_calibration/__init__.py` (re-exports)
- `packages/lingwen-prose-calibration/src/lingwen_prose_calibration/service.py` (191 LOC, all logic)
- `packages/lingwen-prose-calibration/tests/test_prose_calibration.py` (6+ tests moved from tests/infra/)

**Files modified**:
- Root `pyproject.toml` — add `packages/lingwen-prose-calibration` to `[tool.uv.workspace]` members

**`__init__.py` content**:
```python
"""lingwen-prose-calibration — canonical prose calibration package.

Phase 44 P3-ARCHDEBT: relocated from infra/prose_calibration.py (191 LOC).
TRUE LEAF (0 workspace deps; PyYAML>=6.0 3rd-party only).
"""

from lingwen_prose_calibration.service import (
    build_prose_heatmap,
    evaluate_against_baseline,
    format_calibration_report,
    is_primary_revision_slug,
    is_prose_issue,
    list_primary_revision_slugs,
    load_prose_config,
    resolve_llm_post_check,
)

__all__ = [
    "load_prose_config",
    "is_prose_issue",
    "build_prose_heatmap",
    "evaluate_against_baseline",
    "format_calibration_report",
    "list_primary_revision_slugs",
    "is_primary_revision_slug",
    "resolve_llm_post_check",
]
```

### C1.5 fixup note (per Phase 40a C1.5 lesson)

`_FACTORY_ROOT = Path(__file__).resolve().parents[1]` MUST change to `parents[4]` in the
new location. This is a single-line change WITHIN C1 (not a separate fixup commit), since
it's an obvious mechanical update, not a logic defect (unlike Phase 40a factory_root bug).

### C2 details (bulk migrate 6 sites)

**Single bulk commit** (per Phase 37 lesson):

```
refactor(consumers): migrate 6 sites from infra.prose_calibration to lingwen_prose_calibration

Phase 44 P3-ARCHDEBT (lingwen-prose-calibration):

  infra/prose/__init__.py:1            wildcard → from lingwen_prose_calibration import *
  infra/full_check_report.py:271       single symbol
  infra/prose_judge.py:12              multi-symbol
  infra/prose_snapshot.py:10           multi-symbol
  tests/ci/test_llm_golden_primary_ci.py:19
                                      single symbol
  tests/infra/test_prose_calibration.py:5
                                      multi-symbol block
```

### C3 details (delete + invariant)

**Files modified**:
- `infra/prose_calibration.py` — DELETED
- `CLAUDE.md` — version v41.0 → v42.0 + invariant I058 added
- `.lingwen/architecture.yml` — version field updated + invariants list I058 added

### C4 details (guards + handoff + doc-sync)

**Files created**:
- `tests/test_phase44_lingwen_prose_calibration.py` (10 regression guards)
- `docs/superpowers/handoffs/2026-09-11-phase-44-p3-archdebt-prose-calibration-handoff.md`

**Files modified**:
- `CLAUDE.md` — version bump entry + handoff link
- `MEMORY.md` — Phase 44 entry + 4 lessons
- Memory topic file: `phase-44-p3-archdebt-prose-calibration.md`

## Validation gates (Phase 44 acceptance)

1. ✅ ruff clean on changed Python files
2. ✅ `pytest packages/lingwen-prose-calibration/tests/test_prose_calibration.py` passes (6+ moved tests)
3. ✅ `pytest tests/ci/test_llm_golden_primary_ci.py` passes (single-symbol import updated)
4. ✅ `pytest tests/infra/test_prose_calibration_overrides.py` passes (false-positive filter verified)
5. ✅ `pytest infra/prose/` passes (wildcard load works)
6. ✅ `pytest infra/full_check_report.py infra/prose_judge.py infra/prose_snapshot.py` baselines preserved
7. ✅ Phase 36-43 guards preserved (8 prior-phase guard files)
8. ✅ New Phase 44 guards (10 tests)
9. ✅ Production audit: `grep -rn "infra.prose_calibration" infra/ apps/ packages/ tests/` → 0 hits (excluding `__pycache__` + `.claude/worktrees/` + archive)
10. ✅ `_FACTORY_ROOT` resolution verified: `Path(__file__).resolve().parents[4]` = repo root
11. ✅ Module-load behavior preserved: `from lingwen_prose_calibration import load_prose_config` returns same shape dict

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `_FACTORY_ROOT` resolution breaks after relocation | MEDIUM | parents[1] → parents[4] in C1 (Phase 40a C1.5 lesson) |
| `infra/prose/__init__.py` wildcard re-export semantics change | LOW | Same `__all__` (8 symbols) preserved in new package |
| `tests/infra/test_prose_calibration_overrides.py` false-positive filter | LOW | Different module (`prose_calibration_overrides`), not migrated |
| `_DEFAULT_CONFIG` yaml path still resolves | LOW | `parents[4] / "config" / "prose_calibration.yaml"` — verified at repo root |
| `is_prose_issue` / `build_prose_heatmap` signature compatibility | LOW | No signature change in C1 (pure relocation) |
| Pre-existing E741 ruff errors | n/a | Same as Phase 35 baseline |

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ Phase 36-40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ Phase 42 |
| P3-ARCHDEBT 7/6+1 (lingwen-llm-service) | ✅ Phase 43 |
| **P3-ARCHDEBT 8/7+1 (lingwen-prose-calibration)** | 🟡 Phase 44 (this phase) |
| P3-ARCHDEBT 9/8+1 (cache LEAF batch) | 🟡 Phase 45+ |
| P3-ARCHDEBT 10/9+1 (filter near-LEAF) | 🟡 Phase 46+ |

**Next-actionable after Phase 44**: Phase 45 = `infra/cache` (TRUE LEAF, 4 consumers, 91 LOC, 0 deps).

## References

- ARCHDEBT-CANDIDATES.md #3
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 39 (logging_config) — TRUE LEAF template (5-commit pattern, 0 workspace deps, PyYAML-style 3rd-party handling)
- Phase 40a (studio_registry) — C1.5 fixup pattern (path resolution after relocation)
- Phase 42 (project_init) — wildcard-in-`__init__.py` lesson
- Phase 43 (lingwen-llm-service) — bulk 6-site migration pattern

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (6 consumers, 8 public symbols, 191 LOC, 0 workspace deps, 1 wildcard) was verified
> by fresh-run grep on 2026-09-11 BEFORE writing this spec. No stale-count claims.