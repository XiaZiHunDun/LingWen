# Phase 126 v16.5 #N.8 — Cleanup + Backend Pydantic Re-export Handoff

> **Status:** closed, 5 commits on `phase-126-v16-5-n8` branch
> **Previous:** v16.5 #N.7 (DTO Pydantic codegen + SSE stream typing, `59356faf`)
> **Next:** v16.5 #N.9+ (workflow.py re-export after split decision; CVG adapter wire-up; async port conformance; 39 cast cleanup)

## 0. TL;DR

Closed two carryover items from v16.5 #N.7 handoff §6 + extended the cleanup:
- **T1**: 5 re-export shim paths fixed (2-dot → 3-dot). Surfaces 21 latent test type bugs (masked by broken module resolution). Single atomic commit also adds `as unknown as Xxx[]` casts to 5 spec files.
- **T2**: useAgentTask T5.4 type tightening — drop one `as unknown as` cast via `CreatorAgentPlanRequest & Record<string, unknown>` intersection.
- **T3**: CVG presentation adapter scaffolding (NEW `apps/studio_api/cvg_adapter.py` + 5 tests). Establishes boundary between storage shape (`protocols.py`) and presentation shape (`lingwen_shared.contracts.python.cvg`).
- **T4**: Backend Pydantic re-export for 2 of 4 candidate models. `health.py` (12 models) + `decision.py` (4 models) converted to thin re-export shims.

## 1. Files Created/Modified

### New backend files (2)
- `apps/studio_api/cvg_adapter.py` — 176 lines. `ripple_storage_to_presentation`, `ripple_detail_storage_to_presentation`, `cascade_node_storage_to_presentation`, `cascade_edge_storage_to_presentation`, `cascade_storage_to_presentation`. Returns lingwen-shared presentation shape. Domain mapping decisions documented in module docstring; wiring into routes deferred to v16.5 #N.9+.
- `apps/studio_api/tests/test_cvg_adapter.py` — 5 cases.

### Modified shim files (5)
- `packages/dashboard-contracts/src/shared/{cvg,decisions,health,studio,workflows}.ts` — import paths 2-dot → 3-dot (`'../../lingwen-shared/...'` → `'../../../lingwen-shared/...'`).

### Modified test files (5) — fixture casts surfaced by path fix
- `apps/dashboard/tests/unit/use-decision-store.spec.ts` — 9 fixture casts + import added.
- `apps/dashboard/tests/unit/use-overview-store.spec.ts` — 5 fixture casts + import.
- `apps/dashboard/tests/unit/use-workflow-list-store.spec.ts` — 2 fixture casts + import.
- `apps/dashboard/tests/unit/decisions-page.spec.ts` — 2 fixture casts + import.
- `apps/dashboard/tests/unit/creator-write-workbench.spec.ts` — SSE event cast + return cast + imports.

### Modified frontend files (1)
- `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` — `buildPlanRequestBody` return type tightened from `Record<string, unknown>` to `CreatorAgentPlanRequest & Record<string, unknown>`; removed 1 `as unknown as` cast at call site; the SSE-side cast remains with JSDoc reason.

### Modified backend files (2) — re-export shims
- `apps/studio_api/models/health.py` — 12 manual Pydantic models replaced with re-export from `lingwen_shared.contracts.python.health`. Net -39/+48 lines.
- `apps/studio_api/models/decision.py` — 4 manual Pydantic models replaced with re-export from `lingwen_shared.contracts.python.decisions`. Net -39/+24 lines.

## 2. Migration Pattern

```python
# Backend models → thin re-export shims (apps/studio_api/models/X.py)
"""
Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.8: Backend models are now thin re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/X.py``.
"""
from lingwen_shared.contracts.python.X import (
    ModelA, ModelB, ...
)

__all__ = ["ModelA", "ModelB", ...]
```

Verified field-by-field equivalence before each conversion. `HealthResponse`: 10 fields, types + defaults match. `DecisionResponse`: 13 fields, `extra='ignore'` preserved.

## 3. Drift Notes

### Vue-tsc module resolution bug exposed by 2-dot → 3-dot fix
The 5 re-export shims used 2-dot relative paths to `packages/lingwen-shared/src/lingwen_shared/contracts/ts/X.ts`. Realpath check confirmed 3-dot is correct. Pre-existing on master.

Application of the fix surfaced **21 latent TypeScript errors** in 5 spec files that were **masked** by the broken module resolution. Tests passed at runtime via vitest (which uses more lenient esbuild) but failed vue-tsc compile.

Resolution: single atomic commit covering both path fix + test fixture casts (each `as unknown as Xxx[]` cast documents a partial-shape mock fixture that intentionally doesn't satisfy the canonical DTO).

### handleStreamEvent cast remains
The `useAgentTask.ts:344-345` SSE-side `as unknown as (event: unknown) => void` cast persists because `handleStreamEvent` has a loose signature `{type?, message?, label?, text?, source?}` that pre-dates the v16.5 #N.7 SSE envelope's discriminated union. Tightening it requires:
- Drop the `evt.type === 'status'` branch (status not in envelope)
- Drop the `evt.source` field handling (not in any union member)

This is genuine code logic change, deferred to v16.5 #N.9+.

### CVG storage vs presentation drift unresolved
The CVG API surface still serves the **storage shape** (`source_chapter/target_chapter`) via `apps/studio_api/helpers/cvg.py::_ripple_list_items`. The lingwen-shared presentation shape (`chapter_id/source_volume/impact_volumes`) is the canonical source-of-truth but not yet wired into routes. v16.5 #N.8 establishes `cvg_adapter.py` as the canonical boundary; route migration requires validating dashboard consumer expectations on the new field semantics.

### workflow.py re-export deferred
`apps/studio_api/models/workflow.py` has 2 non-workflow DTOs (`BudgetSetRequest`, `BudgetTierSetRequest`) not in `lingwen_shared.contracts.python.workflows`. Splitting the file (workflow re-export + budget local) is a structural decision deferred to v16.5 #N.9.

## 4. Verification Matrix

| Gate | Before (v16.5 #N.7) | After (v16.5 #N.8) |
|------|---------------------|---------------------|
| `vue-tsc` errors in apps/dashboard | 5 (TS2307 module errors) | **0** |
| `vue-tsc` test type errors in 5 spec files | (masked) | **0** (explicit casts added) |
| `vitest` | 1733 + 1 skipped | **1733 + 1 skipped** (no regression) |
| `apps/studio_api/tests/test_cvg_adapter.py` | (N/A) | **5 NEW passed** |
| `pytest packages/lingwen-shared` | 113 passed | **113 passed** (no regression) |
| `pytest apps/studio_api/tests/ + tests/infra/` | ~400 passed | **396 passed + 5 skipped + 1 pre-existing fail** (LLM provider loading bug, unrelated to this phase) |
| `ruff` | 0 errors | **0 errors** |
| Backend `import sqlite3` count in 18 model files | (unchanged) | **unchanged** (no infra migration in this phase) |
| `apps/dashboard/src/api/*.ts` `Promise<unknown>` count | 0 | **0** (no change) |
| `apps/studio_api/models/health.py` lines | 48 lines (12 manual models) | **48 lines (12 re-exports)** — net architecture change, code size preserved |
| `apps/studio_api/models/decision.py` lines | 39 lines (4 manual models) | **24 lines (4 re-exports)** |
| Backend Pydantic re-export coverage | 0 / 18 model files | **2 / 18 (health + decision)** |

## 5. Lessons Learned

1. **TS2307 masks downstream type errors** — Broken module resolution (`'../../X'` resolving to wrong directory) makes TS treat module imports as `any`/empty, hiding downstream shape mismatches. Fixing the path surfaces 21 latent errors. Counter-measure: `pnpm exec vue-tsc --noEmit 2>&1 | grep -E "error TS"` should be in any pre-commit gate that touches shim files.

2. **`Promise<unknown>` is not only an API-layer smell** — The same masking effect applies to function signatures: if a parameter's type can't be resolved, the function silently accepts ANY shape. Even when casts are unavoidable (frontend/build side with intentional partial-shape mocks), document each with a JSDoc reason rather than chasing types that don't match runtime.

3. **CVG adapter scaffolding before wire-up** — Establishing the boundary module BEFORE forcing route integration avoids the v16.4 grimp-evasion-hack pattern (forced transitive paths). The adapter scaffold documents the boundary + tests the mapping logic. Wire-up is the next step with proper dashboard consumption validation.

4. **Storage vs presentation shape separation is real** — Backend persistence owns `source_chapter/target_chapter` (SQLite row shape); lingwen-shared contracts own `chapter_id/source_volume/impact_volumes` (wire shape). The `_compute_volume_from_chapter` heuristic in `cvg_adapter.py` is a placeholder — `v16.5 #N.9+` must validate against actual dashboard consumption before routes call the adapter.

5. **Backend re-export uses `from lingwen_shared.contracts.python.X import *`** with explicit `__all__` for `isort` and `ruff --fix` compliance. Star-imports would also pull in optional/utility members — explicit re-exports + explicit `__all__` keep import surface minimal.

## 6. Carryover to v16.5 #N.9+

- **workflow.py split or merge** — `BudgetSetRequest` + `BudgetTierSetRequest` not in lingwen-shared; either split backend file (workflow re-export + budget local/separate file) or move budget DTOs to lingwen-shared (separate module). 2-3 commits.
- **CVG adapter wire-up** — `routes/cvg.py::list_ripples` + 3 cascade endpoints to use `cvg_adapter.ripple_storage_to_presentation` etc. Must validate field semantics with dashboard consumption. 2-4 commits.
- **useAgentTask handleStreamEvent tightening** — Drop legacy `{type?, message?, source?, ...}` shape and adopt `CreatorAgentStreamEvent` discriminated union. Requires code logic changes. 1-2 commits.
- **Async port conformance** — `LLMServiceAdapter` from sync → `async execute → LLMResult`. Major refactor, touches 12 tools/* + 4 backend route consumers. ~16-25 commits.
- **39 `as unknown as` cast cleanup** — pre-existing fragile patterns in 14 composable files. Each requires investigation + JSDoc documentation OR body-shape tightening.

## 7. Commit Timeline

```
52aa3393 refactor(studio-api): v16.5 #N.8 — decision.py re-exports lingwen-shared canonical models
e6acc443 refactor(studio-api): v16.5 #N.8 — health.py re-exports lingwen-shared canonical models
a1eb92e7 feat(studio-api): v16.5 #N.8 — CVG presentation adapter scaffolding
8a251598 refactor(dashboard): v16.5 #N.8 — T5.4 useAgentTask cast cleanup
83e42925 fix(dashboard-contracts): v16.5 #N.8 — fix 2-dot re-export shim paths + test fixture casts
59356faf (v16.5 #N.7 baseline)
```

Total: **5 commits** (4 task commits + 1 test-fixture-cleanup collateral).
