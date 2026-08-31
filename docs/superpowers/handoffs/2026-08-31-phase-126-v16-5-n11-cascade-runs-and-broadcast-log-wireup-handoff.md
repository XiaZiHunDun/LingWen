# Phase 126 v16.5 #N.11 Handoff — Cascade Runs + Broadcast Log wire-up

> **Phase**: 126 v16.5 #N.11 — `phase-126-v16-5-n11` (CLOSED, ready for PR/merge to master)
> **Date**: 2026-08-31
> **Branch**: `phase-126-v16-5-n11` (16 commits since v16.5 #N.10 master `30f1e3b0`)
> **Plan**: [`docs/superpowers/plans/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup.md`](../plans/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup.md)
> **Worktree**: `.worktrees/phase-126-v16-5-n11`

## Summary

Closed Phase 126 v16.5 #N.10 carryover (4 of 5 items: N.11.a/b/c/f). All 6 CVG cascade/run/broadcast endpoints now serve canonical lingwen-shared presentation shape via `cvg_adapter`. `CascadeBroadcastLogResponse` promoted from storage to canonical lingwen-shared + dead storage class removed. `_get_dim` helper extracted. `protocols.py` cleanup advanced (5 unused imports dropped from `helpers/cvg.py`, dead `CascadeBroadcastLogResponse` removed from `protocols.py`).

**Branch totals: 16 commits, 4 deliverables, 5 architecture invariants added.**

## Commits (16 total)

### Part A: N.11.b CascadeRunResponse wire-up (10 commits)
1. `2c79ccfa` `feat(lingwen-shared)`: CascadeRunResponse extended with 10 storage-shape fields (NOTE: actual count is 9; off-by-one in commit message)
2. `f62d5d9e` `chore(lingwen-shared)`: TS codegen for extended CascadeRunResponse
3. `36cc6e44` `feat(cvg-adapter)`: cascade_run_storage_to_presentation adapter
4. `3a2a308c` `refactor(studio-api)`: get_ripple_cascade_runs uses cvg_adapter
5. `9b1ae5dc` `refactor(studio-api)`: list_all_cascade_runs uses cvg_adapter
6. `07a77412` `refactor(studio-api)`: post_ripple_cascade_run_cancel uses cvg_adapter + cancel metadata
7. `59635d78` `test(lingwen-shared)`: extended CascadeRunResponse fields tests
8. `4dd72a0a` `refactor(studio-api)`: post_ripple_cascade_run_cancel polish (model_copy + hoist datetime import)
9. `b51569b9` `chore(ruff)`: ruff fixes (F821 Any + F822 forward-decl + I001 imports)
10. `9eafbb2a` `refactor(cvg-adapter)`: extract _get_dim helper (DRY 3 inline dim accesses) — bonus from Part C

### Part B: N.11.c CascadeBroadcastLogResponse wire-up (5 commits)
1. `74585228` `feat(lingwen-shared)`: CascadeBroadcastLogResponse promoted to canonical
2. `7e9440c9` `chore(lingwen-shared)`: TS codegen for CascadeBroadcastLogResponse
3. `b223b81b` `feat(cvg-adapter)`: cascade_broadcast_log_storage_to_presentation adapter
4. `ce9b9eaf` `refactor(studio-api)`: get_ripple_cascade_broadcast_log uses cvg_adapter
5. `a381924b` `refactor(studio-api)`: remove dead CascadeBroadcastLogResponse storage class (closes N.11.a partial scope)

### Part C: N.11.f _get_dim helper extraction (1 commit, included in Part A's commit count)
- See `9eafbb2a` above

### Part D: N.11.a protocols.py cleanup (1 commit)
1. `20f70914` `refactor(helpers)`: drop 5 unused CVG model imports from protocols.py

(Part C is 2 commits: `a4d4b971` test RED + `9eafbb2a` GREEN impl+refactor, both within Part A's range.)

## Architecture Invariants Enforced (5 NEW, 25 total)

21. (NEW) ✅ `CascadeRunResponse` in `lingwen_shared.contracts.python.cvg` includes 9 storage-shape fields (cascade_id/completed_at/depth_reached/cascade_nodes/cascade_edges/cascade_actions/cancelled_at/triggered_by/stats) so dashboard consumers can read full cascade-run payload via typed wrapper.
22. (NEW) ✅ All 4 cascade-run endpoints (get_ripple_cascade_runs + list_all_cascade_runs + post_ripple_cascade_run_cancel + get_ripple_cascade_v9_20 persist branch) route through `cvg_adapter.cascade_run_storage_to_presentation` — zero inline mapping in route handlers (extends invariant #18 from N.10).
23. (NEW) ✅ `CascadeBroadcastLogResponse` promoted from storage shape (`apps/studio_api/protocols.py`) to canonical lingwen-shared + dead storage class removed (closes Pydantic drift; storage Pydantic was redundant with dataclass source-of-truth at `infra/cross_volume/storage.py:81-88`).
24. (NEW) ✅ `apps/studio_api/cvg_adapter._get_dim(node)` polymorphic helper replaces 3 inline `n.get("dimension") if isinstance(n, dict) else getattr(...)` expressions in `cascade_preview_storage_to_presentation` (DRY).
25. (NEW) ✅ `apps/studio_api/protocols.py` CVG cleanup: 5 unused CVG model imports dropped from `helpers/cvg.py` (CascadePreviewResponse, CascadeResponse, CascadeRunResponse, RippleActionResponse, RippleStatsResponse) + dead CascadeBroadcastLogResponse class + 2 noqa F401 re-exports removed from `app.py` + `models/__init__.py`.

## Test Results

| Gate | Count | Status |
|------|-------|--------|
| `packages/lingwen-shared/tests/` | 125 passed | +1 NEW from N.11.b (test_cascade_run_response_extended_fields) |
| `apps/studio_api/tests/test_cvg_adapter.py` | 15 passed | +5 NEW from N.11.b/c/f (cascade_run_storage + 2x cascade_broadcast_log + 3x _get_dim) |
| `apps/studio_api/tests/` (full) | 48 passed | 0 regression |
| `apps/dashboard` vitest | 1733 passed + 1 skipped | 0 regression |
| `apps/dashboard` vue-tsc | 0 errors | clean |
| ruff (touched files) | All checks passed | clean |

## Files Changed

### Python (backend)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` — CascadeRunResponse extended with 9 fields + CascadeBroadcastLogResponse added
- `apps/studio_api/cvg_adapter.py` — cascade_run_storage_to_presentation + cascade_broadcast_log_storage_to_presentation adapters + _get_dim helper
- `apps/studio_api/routes/cvg.py` — 4 endpoints migrated (3 cascade runs + 1 broadcast log + bonus v9_20 persist branch); _dataclass_to_dict helper added
- `apps/studio_api/helpers/cvg.py` — 5 unused CVG model imports dropped
- `apps/studio_api/protocols.py` — dead CascadeBroadcastLogResponse class removed (15 lines)
- `apps/studio_api/app.py` — noqa F401 import for CascadeBroadcastLogResponse removed
- `apps/studio_api/models/__init__.py` — noqa F401 re-export removed

### TypeScript (frontend DTOs)
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` — auto-generated TS interfaces
- `packages/dashboard-contracts/src/shared/cvg.ts` — CascadeBroadcastLogResponseDTO re-export added

### Tests
- `packages/lingwen-shared/tests/test_cvg_dto.py` — 1 NEW test for extended CascadeRunResponse fields
- `apps/studio_api/tests/test_cvg_adapter.py` — 5 NEW tests (1 cascade_run + 2 cascade_broadcast_log + 3 _get_dim)

## Lessons Learned

1. **Pydantic extension with safe defaults is backward-compatible** (carryover from N.10 lesson #2): Adding `cascade_id: Optional[int] = None` + `cascade_actions: list = Field(default_factory=list)` + `depth_reached: int = 0` keeps existing valid uses working while exposing new fields. N.9-era minimal instances still validate.

2. **T11 cleanup scope expansion pattern**: Original T11 plan assumed all CVG routes use cvg_adapter by N.10, but CascadeRunResponse was used by 3 endpoints NOT in N.10 scope (N.11.b). Same pattern repeated in N.11: CascadeBroadcastLogResponse cleanup (storage class removal) only became possible after its endpoint was wired (N.11.c). Sequential dependency: route → wire → cleanup.

3. **`is_dataclass(x) and not isinstance(x, type)` guard is necessary**: `is_dataclass(SomeClass)` returns True even for the class itself; `asdict(SomeClass)` raises TypeError. Verified empirically (Part B code review). Defensive guard prevents subtle bug if a class is accidentally passed.

4. **Frontend typed wrapper can be deferred if no consumer exists**: Part B did NOT add `fetchCascadeBroadcastLog` to `apps/dashboard/src/api/cvg.ts` because `grep -rn "broadcast" apps/dashboard/` returns zero matches. Per N.10 §5 lesson 4, "failing tests are direct evidence of incomplete wire-up; no failing tests means no consumer yet". Add wrapper only when dashboard consumer needs it.

5. **`_dataclass_to_dict` helper evolution**: Part A added a helper for the 3 cascade-run endpoints. Part B broadcast-log endpoint uses the in-adapter polymorphic guards (is_dataclass / model_dump / dict fallback) instead — slightly different pattern because broadcast-log accepts the storage dataclass directly (not via `_dataclass_to_dict`). Both patterns coexist in the codebase; not a problem but worth noting.

6. **Cancel endpoint enrichment with `model_copy(update={...})`**: Better than `model_dump()` + dict mutation + `CascadeRunResponse(**dict)` because (a) preserves Pydantic v2 model identity, (b) avoids allocation round-trip, (c) more readable. Recommended pattern for future Pydantic v2 mutations.

7. **Test count claims vs reality**: Plan estimated 11+2=13 cvg_dto tests, actual was 10+1=11. Off-by-one in plan estimates is a recurring pattern (see N.10 carryover count drift). Plans should specify field NAMES not field COUNTS where possible.

8. **Atomic-commit counts vs plan estimates**: Plan estimated ~18 commits, actual was 16. Variance came from: (a) Part C's 2 commits collapsed with Part A's polish commit, (b) lint fixups embedded within task commits rather than separate. Acceptable — atomicity is about logical not numerical granularity.

## Carryover to v16.5 #N.12+

- **#N.11.d** `impact_score` storage-vs-presentation drift: cascade v9_20 endpoints don't include `impact_score`. Carryover if dashboard needs.
- **#N.11.e** Dashboard cascade field migration: `cascadeGraphUtils.js` still has local refs to `depth_reached` + other storage-shape names (runtime correct via cvg_adapter mapping, but readability suffers). 1-2 commits.
- **#N.11.g (renamed from N.11.e-extended)** `ReferenceGraphResponse` full migration to presentation shape (currently still uses storage-shape from `apps.studio_api.models`). Would require extending lingwen-shared `ReferenceGraphResponse` with `by_dimension` field + new adapter + endpoint migration. 2-3 commits.
- **#N.12+** Async port conformance: LLMServiceAdapter sync → `async execute → LLMResult` (~16-25 commits).
- **#N.13+** 39 `as unknown as` cast cleanup in composables.

## Final State

- **Branch**: `phase-126-v16-5-n11` (16 commits since master `30f1e3b0`)
- **Master**: at v16.5 #N.10 closure (no merge yet — pending PR)
- **Tests**: All 5 verification gates green (1733 vitest / 125 backend shared / 15 cvg_adapter / 48 studio_api / vue-tsc 0 / ruff 0)
- **Architecture invariants**: 25 total enforced (5 NEW in N.11)
- **Carryover**: 4 items (#N.11.d, #N.11.e, #N.11.g, #N.12+, #N.13+) documented above
