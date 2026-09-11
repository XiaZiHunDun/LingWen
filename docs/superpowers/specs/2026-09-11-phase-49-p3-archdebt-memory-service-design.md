# Phase 49 P3-ARCHDEBT (memory_service) — lingwen-memory-service Design Spec

> **Phase**: 49 (P3-ARCHDEBT 13/12+1 — continues from Phase 48's `full_check_report` closure)
> **Branch**: `phase-49-p3-archdebt-memory-service`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md "memory_service" (heavy 10 deps candidate)
> **Template**: Phase 44 (lingwen-prose-calibration) — single-module NOT-LEAF pattern, 5-commit pattern

## Goal

Move `infra/memory_service.py` (307 LOC, NOT-LEAF with 9 workspace deps) into standalone canonical package `packages/lingwen-memory-service/`. Delete the `infra/` source and add **invariant I068**. Continue P3-ARCHDEBT pattern.

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit

| # | Pattern | Sites |
|---|---------|-------|
| 1 | Literal dotted-path imports `from infra.memory_service import X` | 3 |
| 2 | Indented/function-body imports | 0 |
| 3 | Relative imports | 0 |
| 4 | Filesystem path literals | 0 |
| 5 | **Wildcard** `from infra.memory_service import *` | **1** |
| 6 | `monkeypatch.setattr` + `with patch(...)` | 0 |
| 7 | Plain `import infra.memory_service` | 0 |
| 8 | Doc comments referencing old path | 0 |
| 9 | Prior-phase guard's hardcoded representative | 0 |

### Real external consumers (4 sites, verified by fresh grep 2026-09-11)

| # | File | Pattern | Migration |
|---|------|---------|-----------|
| 1 | `infra/core/__init__.py:6` | wildcard | `from lingwen_memory_service import *` |
| 2 | `packages/lingwen-creator/src/lingwen_creator/content/agent.py:78` | indented single symbol | `from lingwen_memory_service import get_memory_gateway` |
| 3 | `packages/lingwen-creator/src/lingwen_creator/memory/assets.py:32` | indented single symbol | `from lingwen_memory_service import get_memory_gateway` |
| 4 | `packages/lingwen-creator/src/lingwen_creator/memory/query.py:119` | indented single symbol | `from lingwen_memory_service import get_memory_gateway` |

### False-positive filter (1 self-import + 2 string literals)

| File | Reason |
|------|--------|
| `infra/memory_service.py:7` | self-import (`from infra.memory_service import get_memory_gateway`) — preserve Phase 42 lesson (skip self) |
| `tests/test_phase45_lingwen_utilities.py:400` | STRING LITERAL in docstring (Phase 45 documentation) |
| `tests/test_phase46_lingwen_filter.py:313` | STRING LITERAL in docstring (Phase 46 documentation) |

### Spec drift (N.14 lesson 1 #25)

ARCHDEBT-CANDIDATES.md said "4 consumers". Actual = **4 real consumers** ✅. Matches spec.

## Architecture —

### Package layout (2 sub-modules — single-module NOT-LEAF pattern per Phase 44)

```
packages/lingwen-memory-service/
├── pyproject.toml                             # 9 workspace deps (NOT-LEAF, heavy)
├── src/lingwen_memory_service/
│   ├── __init__.py                            # re-exports 4 public symbols
│   └── service.py                             # 307 LOC, all logic
```

Note: No test MOVE — `packages/lingwen-creator/tests/test_memory.py` is unrelated (tests `lingwen_creator.memory` package).

### Public surface (4 public symbols + 1 class + 3 private funcs)

| Symbol | Kind |
|--------|------|
| `NoOpMemoryGateway` | class |
| `get_memory_gateway` | public func |
| `is_memory_gateway_available` | public func |
| `get_initialization_error` | public func |
| (private: `_load_default_config`, `_check_qdrant_availability`, `_create_memory_gateway`) | not re-exported |

### Workspace deps — NOT-LEAF (9 workspace deps — heavy!)

```toml
dependencies = [
    "lingwen-logging-config",                  # Phase 39 (logger)
    "lingwen-memory",                    # # gateway + state + vector submodules (8 imports)
]
```

Note: `lingwen_memory` package provides 8 submodules (config + embeddings + gateway + state + vector). Declaring `lingwen-memory` covers all 8 submodule imports.

### Invariant I068

```
I068 | `packages/lingwen-memory-service/` is NoOpMemoryGateway + get_memory_gateway +
       is_memory_gateway_available + get_initialization_error unique canonical package;
       `infra.memory_service.*` paths forbidden (P3-ARCHDEBT 13/12+1 Phase 49)
```

## Atomic commits (5+1 = 6 total — single-module NOT-LEAF pattern)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-49)` | spec | This document |
| **C1** | `feat(packages)` | scaffold | 2 sub-modules + pyproject + workspace + tool.uv.sources |
| **C2** | `refactor(consumers)` | bulk migrate 4 sites | 1 wildcard + 3 indented |
| **C3** | `chore(infra)` | delete + I068 + v47.0 | infra/memory_service.py DELETED + invariant + version |
| **C4** | `test(phase-49)` | guards + handoff | Phase 49 guards + handoff + topic file |
| **(C4.5)** | `fix(test)` | optional | If Phase 45/46 wildcard-remains guards break |

### C1 details

**Files created** (3):
- `packages/lingwen-memory-service/pyproject.toml`
- `packages/lingwen-memory-service/src/lingwen_memory_service/__init__.py`
- `packages/lingwen-memory-service/src/lingwen_memory_service/service.py` (via git mv)

**Files modified** (1):
- Root `pyproject.toml` — add workspace member + tool.uv.sources entry

### C2 details (single bulk commit)

```
refactor(consumers): migrate 4 sites from infra.memory_service to lingwen_memory_service

Phase 49 P3-ARCHDEBT:

  infra/core/__init__.py:6                  wildcard → from lingwen_memory_service import *
  packages/lingwen-creator/src/lingwen_creator/
    content/agent.py:78                    indented single symbol (get_memory_gateway)
  packages/lingwen-creator/src/lingwen_creator/
    memory/assets.py:32                    indented single symbol
  packages/lingwen-creator/src/lingwen_creator/
    memory/query.py:119                     indented single symbol

Self-import in infra/memory_service.py:7 preserved (Phase 42 lesson).
```

## Validation gates (Phase 49 acceptance)

1. ✅ ruff clean on changed Python files
2. ✅ 4 consumer files migrated (1 wildcard + 3 indented)
3. ✅ Phase 36-48 guards preserved (13 prior-phase guard files)
4. ✅ New Phase 49 guards (10+ tests)
5. ✅ Production audit: `grep -rn "infra\.memory_service\b" infra/ apps/ packages/ tests/ tools/` → 0 runtime hits
6. ✅ Test audit: same grep in tests/ → 0 hits
7. ✅ `__all__` exact count (4 public symbols)
8. ✅ Workspace deps correct (2 deps: lingwen-logging-config + lingwen-memory)
9. ✅ I068 in `.lingwen/architecture.yml` + `CLAUDE.md`
10. ✅ tool.uv.sources updated

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 9 workspace deps heavy | MEDIUM | `lingwen-memory` package covers 8 submodule imports via single dep declaration |
| Self-import in `infra/memory_service.py:7` triggers audit | LOW | Pre-spec audit identified self-import, excluded from migration |
| Phase 45/46 "wildcards remain" guards break (N.14 lesson 1 #25) | HIGH | Plan C4.5 fixup commit for prior-phase guards |
| Memory-heavy package causes long uv sync | LOW | uv sync already includes lingwen-memory (Phase 45 + 47 deps) |

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 12/11+1 (full_check_report) | ✅ | Phase 48 |
| **P3-ARCHDEBT 13/12+1 (memory_service)** | 🟡 | Phase 49 (this phase) |
| P3-ARCHDEBT remaining (Phase 50+) | 🟡 | types / filter (Phase 46 MERGE cleanup) |

**Next-actionable after Phase 49**: Phase 50 = `infra/types` (1-2 consumers, LEAF but trivial — Phase 50+ batch candidate).

## References

- ARCHDEBT-CANDIDATES.md "memory_service" (4 consumers, 10 deps)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 40a (studio_registry) — first NOT-LEAF with multiple workspace deps
- Phase 44 (lingwen-prose-calibration) — single-module NOT-LEAF template
- Phase 48 (full_check_report) — most recent NOT-LEAF single-module
- N.14 lesson 1 #25 — wildcard-remains pattern (recurring C4.5 fixups in P3-ARCHDEBT)

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (307 LOC, 4 public symbols, 9 workspace deps, 4 real consumers + 1 self-import + 2 string-literal false-positives)
> was verified by fresh-run grep on 2026-09-11 BEFORE writing this spec.
> No stale-count claims.