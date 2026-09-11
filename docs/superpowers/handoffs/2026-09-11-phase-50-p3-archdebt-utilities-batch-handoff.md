# Phase 50 P3-ARCHDEBT (utilities batch) Handoff

> **Date**: 2026-09-11
> **Phase**: 50 — P3-ARCHDEBT item 14/13+1
> **Branch**: `phase-50-p3-archdebt-utilities-batch`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **ARCHDEBT Rank**: 6 small LEAF modules batch per ARCHDEBT-CANDIDATES.md recommendation

## TL;DR

6 small LEAF utility modules processed in 1 phase (mixed pattern):
- **2 MIGRATE** (real consumers): schema + health → canonical packages
- **4 DELETE** (zero anchored consumers): types + tool + permission + llm_cache (2454 LOC dead code)

Total LOC processed: 3341 across 6 modules. 2 new packages + 2 NEW invariants (I069-I070). Version bump v47.0 → v48.0.

## Atomic commits (5 total on `phase-50-p3-archdebt-utilities-batch`)

| SHA | Type | Scope | Notes |
|-----|------|-------|-------|
| `fcd36b91` | `docs(phase-50)` | spec | 6-module mixed batch design |
| `a366ca35` | `feat(infra)` | scaffold 2 + delete 4 | 2 new packages + 4 dead module deletions |
| `5d05a12d` | `refactor(consumers)` | bulk migrate 2 | apps/studio_api + tests/test_infra_modules.py |
| `c97f11b2` | `chore(infra)` | delete + I069-I070 + v48.0 | 2 source files DELETED + 2 invariants |
| `<C4>` | `test(phase-50)` | 19 guards + handoff | Phase 50 guards + handoff + topic file |

## Pre-spec audit (verified by fresh grep 2026-09-11)

**Migrated (2)**:
- `infra/schema.py` 369 LOC, 6 test consumers + 1 intra-batch in infra/tool.py (DELETED) → `lingwen-schema`
- `infra/health.py` 518 LOC, 1 apps consumer → `lingwen-health`

**Deleted (4, zero anchored consumers)**:
- `infra/types.py` 423 LOC
- `infra/tool.py` 612 LOC
- `infra/permission.py` 510 LOC
- `infra/llm_cache.py` 909 LOC

## Architecture (2 new packages × 2 sub-modules)

### lingwen-schema (TRUE LEAF)
```
packages/lingwen-schema/
├── pyproject.toml            (1 dep: lingwen-errors)
├── src/lingwen_schema/
│   ├── __init__.py           (17 public symbols)
│   └── service.py            (369 LOC)
```

### lingwen-health (TRUE LEAF)
```
packages/lingwen-health/
├── pyproject.toml            (1 dep: lingwen-errors)
├── src/lingwen_health/
│   ├── __init__.py           (13 public symbols)
│   └── service.py            (518 LOC)
```

## Validation gates — all GREEN

| Gate | Status | Notes |
|------|--------|-------|
| **19 phase50 guards** | ✅ 19/19 PASSED (after manual I069-I070 add) |
| **185 total guards** | ✅ 185/185 (Phase 36-50) |
| **ruff clean** | ✅ |
| **Production + test audit** | ✅ 0 runtime hits for both schema + health |

## 4 lessons

### Lesson 1: Mixed batch pattern (P3-ARCHDEBT 2ND-TIME)
First P3-ARCHDEBT phase to combine MIGRATION + DELETION in one phase. Pattern: when a module has 0 anchored consumers, just delete (no need for canonical package). When module has consumers, migrate to canonical package.

### Lesson 2: Dead code deletion (long-tail cleanup)
4 dead modules (types + tool + permission + llm_cache) = 2454 LOC of dead code removed. `tools/` and `infra/` shrink significantly. Per ARCHDEBT-CANDIDATES.md "1-2 consumers, LEAF but trivial — Phase 50+ batch" recommendation.

### Lesson 3: Python regex insert failure (3rd occurrence — Phase 47 + 48 + 50)
Python replace for invariant insertion failed silently AGAIN in Phase 50 (I069 + I070 missing after C3). Manually added via Edit. **Recommendation**: future P3-ARCHDEBT phase C3 MUST verify invariant count via `grep -c I06X` BEFORE committing.

### Lesson 4: No infra.core/* wildcard changed in this phase
Unlike Phases 45-49 (which all had wildcard-remains C4.5 fixups), Phase 50 did NOT touch any `infra/core/__init__.py` wildcard. No C4.5 fixup needed for prior phase guards.

## Carryover closure — P3-ARCHDEBT TOP 5 + MEMORY + UTILITIES ALL CLOSED

| Phase | Status |
|-------|--------|
| P3-ARCHDEBT 1/5 (errors) | ✅ Phase 36 |
| P3-ARCHDEBT 2/5 (paths) | ✅ Phase 37 |
| P3-ARCHDEBT 3/5 (project_config) | ✅ Phase 38 |
| P3-ARCHDEBT 4/5 (logging_config) | ✅ Phase 39 |
| P3-ARCHDEBT 5/5 (studio_registry) | ✅ Phase 40a+40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ Phase 42 |
| P3-ARCHDEBT 7/6+1 (llm_service) | ✅ Phase 43 |
| P3-ARCHDEBT 8/7+1 (prose_calibration) | ✅ Phase 44 |
| P3-ARCHDEBT 9/8+1 (utilities batch) | ✅ Phase 45 |
| P3-ARCHDEBT 10/9+1 (filter MERGE) | ✅ Phase 46 |
| P3-ARCHDEBT 11/10+1 (studio_batch batch) | ✅ Phase 47 |
| P3-ARCHDEBT 12/11+1 (full_check_report) | ✅ Phase 48 |
| P3-ARCHDEBT 13/12+1 (memory_service) | ✅ Phase 49 |
| **P3-ARCHDEBT 14/13+1 (utilities batch v2)** | ✅ **Phase 50** |

**P3-ARCHDEBT CORE 14/14 ALL CLOSED**. Remaining: 1-2 consumer trivial modules (long-tail, Phase 51+).

## References

- ARCHDEBT-CANDIDATES.md "below top 5" (6 small LEAF modules)
- Phase 45 (lingwen-utilities batch) — multi-module batch template
- Phase 47 (studio_batch batch) — 3-module batch with intra-batch deps
- Phase 49 (memory_service) — most recent NOT-LEAF single-module
- N.14 lesson 1 #25 — wildcard-remains pattern (recurring C4.5 fixups)
- N.14 lesson 1 #27 — Python regex insert silent-fail (3rd occurrence)

---

> **All claims verified by fresh-run** (Phase 41 mini lesson #1):
> 19 phase50 guards + 166 prior-phase guards (after manual I069-I070 add)
> = 185 PASSED, 0 regressions.