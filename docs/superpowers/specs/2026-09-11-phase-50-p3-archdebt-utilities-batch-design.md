# Phase 50 P3-ARCHDEBT (utilities batch) — 6-module mixed Design Spec

> **Phase**: 50 (P3-ARCHDEBT 14/13+1 — continues from Phase 49's `lingwen-memory-service` closure)
> **Branch**: `phase-50-p3-archdebt-utilities-batch`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md "below top 5" (6 small LEAF modules batch recommendation)
> **Template**: Phase 45 (lingwen-utilities BATCH) — multi-module batch, 5-6 commit pattern
> **Special**: **Mixed pattern** — 4 zero-consumer modules DELETED + 2 real-consumer modules MIGRATED

## Goal

Process 6 small LEAF utility modules in 1 phase per ARCHDEBT-CANDIDATES.md batch recommendation:
- **2 MIGRATE** (real consumers): `infra/schema.py` → `packages/lingwen-schema/`; `infra/health.py` → `packages/lingwen-health/`
- **4 DELETE** (zero anchored consumers): `infra/types.py` + `infra/tool.py` + `infra/permission.py` + `infra/llm_cache.py`

Add 2 new invariants (I069-I070). Version bump v47.0 → v48.0.

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### Per-module reality check

| # | Module | LOC | Anchored ^from consumers | Decision |
|---|--------|-----|--------------------------|----------|
| 1 | `infra/schema.py` | 369 | 6 (tests/test_infra_modules.py) + 4 (intra-batch in infra/tool.py) | **MIGRATE** → `lingwen-schema` |
| 2 | `infra/health.py` | 518 | 1 (apps/studio_api/routes/health.py) | **MIGRATE** → `lingwen-health` |
| 3 | `infra/types.py` | 423 | 0 anchored | **DELETE** (zero-consumer, no package) |
| 4 | `infra/tool.py` | 612 | 0 anchored (only intra-batch from infra/schema) | **DELETE** (zero-consumer, no package) |
| 5 | `infra/permission.py` | 510 | 0 anchored | **DELETE** (zero-consumer, no package) |
| 6 | `infra/llm_cache.py` | 909 | 0 anchored | **DELETE** (zero-consumer, no package) |

**Total LOC**: 3341 across 6 modules (2 migrated + 4 deleted)
**Total anchored consumers**: 7 (6 schema + 1 health)
**Total new packages**: 2 (lingwen-schema + lingwen-health)
**Total deleted modules**: 4 (types + tool + permission + llm_cache)

### False-positive filter (test docstring references — preserved per spec)

- `tests/test_infra_modules.py:382/393/405/416/423` STRING LITERAL refs in docstring (Phase 45 pattern)
- `tests/test_infra_modules.py:441` STRING LITERAL ref to `infra.result` (unrelated)

### Workspace deps (per module)

| Module | Workspace deps | 3rd-party deps |
|--------|----------------|-----------------|
| `schema` | `lingwen-errors` | none (stdlib) |
| `health` | `lingwen-errors` | none (stdlib) |

## Architecture (2 new packages × 2 sub-modules each)

### 1. `packages/lingwen-schema/`

```
packages/lingwen-schema/
├── pyproject.toml              (1 dep: lingwen-errors)
├── src/lingwen_schema/
│   ├── __init__.py             (re-exports public symbols)
│   └── service.py              (369 LOC, from infra/schema.py)
└── tests/test_schema.py        # NEW (or test from existing tests/test_infra_modules.py)
```

### 2. `packages/lingwen-health/`

```
packages/lingwen-health/
├── pyproject.toml              (1 dep: lingwen-errors)
├── src/lingwen_health/
│   ├── __init__.py             (re-exports public symbols)
│   └── service.py              (518 LOC, from infra/health.py)
```

## Atomic commits (5+1 = 6 total — mixed batch pattern)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-50)` | spec | This document |
| **C1** | `feat(infra)` | scaffold 2 pkgs + delete 4 dead | 4 new files + 4 deletions + workspace register + tool.uv.sources |
| **C2** | `refactor(consumers)` | bulk migrate 2 sites | apps/studio_api/routes/health.py + tests/test_infra_modules.py (6 imports) |
| **C3** | `chore(infra)` | delete 2 files + I069-I070 + v48.0 | infra/schema.py + infra/health.py DELETED + 2 invariants + version |
| **C4** | `test(phase-50)` | guards + handoff | Phase 50 guards + handoff + topic file |
| **(C4.5)** | `fix(test)` | optional | If prior guards break (N.14 lesson 1 #25 — no infra.core/* wildcards changed, so unlikely) |

### C1 details (scaffold 2 + delete 4 in one commit)

**Files created** (8):
- `packages/lingwen-schema/pyproject.toml`
- `packages/lingwen-schema/src/lingwen_schema/__init__.py`
- `packages/lingwen-schema/src/lingwen_schema/service.py` (via git mv)
- `packages/lingwen-health/pyproject.toml`
- `packages/lingwen-health/src/lingwen_health/__init__.py`
- `packages/lingwen-health/src/lingwen_health/service.py` (via git mv)

**Files deleted** (4):
- `infra/types.py` (423 LOC, 0 consumers)
- `infra/tool.py` (612 LOC, 0 consumers)
- `infra/permission.py` (510 LOC, 0 consumers)
- `infra/llm_cache.py` (909 LOC, 0 consumers)

**Files modified** (1):
- Root `pyproject.toml` — add 2 workspace members + 2 tool.uv.sources entries

### C2 details (bulk migrate 2 sites)

```
refactor(consumers): migrate 2 real consumer sites

  apps/studio_api/routes/health.py:20    1 anchored import (infra.health → lingwen_health)
  tests/test_infra_modules.py            6 anchored imports (infra.schema → lingwen_schema)
```

### C3 details (delete 2 + 2 invariants + v48.0)

**Files deleted** (2):
- `infra/schema.py` (369 LOC, after C2 consumer migration)
- `infra/health.py` (518 LOC, after C2 consumer migration)

**Files modified** (2):
- `CLAUDE.md` — version v47.0 → v48.0 + I069 + I070
- `.lingwen/architecture.yml` — version + 2 invariants

## Validation gates (Phase 50 acceptance)

1. ✅ ruff clean on changed Python files
2. ✅ 2 packages importable
3. ✅ 2 consumer files migrated
4. ✅ Phase 36-49 prior guards preserved
5. ✅ New Phase 50 guards
6. ✅ Production audit: `grep -rn "infra\.(schema|health|types|tool|permission|llm_cache)\b" infra/ apps/ packages/ tests/ tools/` → 0 runtime hits
7. ✅ Test audit: same grep in tests/ → 0 hits
8. ✅ `__all__` exact counts
9. ✅ Workspace deps correct (each package: 1 dep lingwen-errors)
10. ✅ 2 invariants I069-I070 in arch.yml + CLAUDE.md
11. ✅ tool.uv.sources updated

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 4 DELETED modules have hidden consumers (monkeypatch, string-literal patches) | MEDIUM | Pre-spec audit verified 0 anchored imports; C4 audit covers unanchored |
| 6 test_infra_modules.py schema imports use various names | LOW | All use same prefix `from infra.schema import` → single sed |
| `infra/core/__init__.py` wildcards unaffected | LOW | No wildcard from these 6 modules (Phase 45 + 48 already migrated all infra.core/* wildcards) |
| Phase 36-49 guards regress | LOW | No `from infra.X import *` wildcards migrated → no C4.5 expected |

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 13/12+1 (memory_service) | ✅ | Phase 49 |
| **P3-ARCHDEBT 14/13+1 (6-module utilities batch)** | 🟡 | Phase 50 (this phase) |
| P3-ARCHDEBT remaining | 🟡 | studio_batch_*, full_check_report (already done) / nothing major |

**P3-ARCHDEBT TOP 5 ARCHDEBT-CANDIDATES ALL CLOSED** (project_init, llm_service, prose_calibration, filter, full_check_report, memory_service, utilities batch). After Phase 50, only the original ARCHDEBT-CANDIDATES.md "long-tail" modules remain (1-2 consumer trivial modules — Phase 51+).

## References

- ARCHDEBT-CANDIDATES.md "below top 5" (6 small LEAF modules)
- Phase 45 (lingwen-utilities batch) — multi-module batch template
- Phase 47 (studio_batch batch) — multi-module batch with intra-batch deps
- Phase 49 (memory_service) — most recent NOT-LEAF single-module

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (3341 LOC, 7 anchored consumers, 2 packages + 4 deletions, 2 invariants)
> was verified by fresh-run grep on 2026-09-11 BEFORE writing this spec.
> No stale-count claims.