# Phase 126 v16.5 #N.11.d/e/g — CVG Cleanup Completion Handoff

> **Phase**: 126 v16.5 #N.11.d/e/g
> **Date**: 2026-08-31
> **Branch**: `phase-126-v16-5-n11-d-e-g`
> **Plan**: [`docs/superpowers/plans/2026-08-31-phase-126-v16-5-n11-d-e-g-cvg-cleanup-completion.md`](../plans/2026-08-31-phase-126-v16-5-n11-d-e-g-cvg-cleanup-completion.md)
> **Worktree**: `.worktrees/phase-126-v16-5-n11-d-e-g`

## Summary

Closes the three CVG-related carryovers from v16.5 #N.10/#N.11 in a single phase:
- **#N.11.d — impact_score drift:** extends `RippleListItemResponse` (lingwen-shared) with `impact_score`; cvg_adapter propagates it; `list_ripples` route drops its hybrid storage-roundtrip and serves canonical presentation shape end-to-end.
- **#N.11.e — dashboard cascade fields:** `cascadeGraphUtils.js` + `useWorkflowSocket.js` JSDoc read presentation-shape names (`node_id` / `chapter_id` / `source` / `target` / `max_depth`).
- **#N.11.g — ReferenceGraphResponse full migration:** extends `ReferenceGraphResponse` with `truncated` flag; new `reference_graph_storage_to_presentation` adapter; endpoint migrated to canonical; storage-shape class removed from `apps/studio_api/protocols.py`; `ImpactGraph.vue` end-to-end.

**Branch totals:** 13 commits, 5 files backend + 4 files frontend + 4 test files.

## Commits (13 total)

### Part A: N.11.d (4 commits)
1. `c01615ef` `feat(lingwen-shared)`: `RippleListItemResponse.impact_score: Optional[float] = None` + 2 RED-then-GREEN tests (direct set + default None back-compat). Backward-compatible (default None).
2. `08d20bee` `chore(lingwen-shared)`: TS codegen for extended RippleListItemResponse (RippleDetailResponse inherits).
3. `46928023` `feat(cvg-adapter)`: `ripple_storage_to_presentation` propagates `impact_score`; 2 NEW tests (storage-shape propagation + default None).
4. `d796f42e` `refactor(studio-api)`: `list_ripples` drops hybrid storage-roundtrip — convert to presentation shape first, filter/sort on presentation values. The bulk child_count + impact_score N+1-avoiding batch ops in `_ripple_list_items` remain.

### Part B: N.11.e (2 commits)
5. `a792f311` `refactor(dashboard)`: `cascadeGraphUtils.js` reads `source/target` (was `from_node_id/to_node_id`), `node_id/chapter_id` (was `id/chapter`), `max_depth` (was `depth_reached`). Test fixture `cascade-graph-utils-full.spec.ts` migrated to match the new shape so chart-title `depth 3` and depth-layer/action-cluster layouts exercise the canonical names.
6. `8f0bd9f4` `refactor(dashboard)`: `useWorkflowSocket.js` JSDoc reflects `cascade.update` event payload field rename (`depth_reached → max_depth`). Pure docstring change.

### Part C: N.11.g (7 commits)
7. `9429e9d1` `feat(lingwen-shared)`: `ReferenceGraphResponse.truncated: bool = False` + 2 RED-then-GREEN tests. Backward-compatible (default False).
8. `a1336c6a` `chore(lingwen-shared)`: TS codegen for truncated.
9. `f33803b1` `feat(cvg-adapter)`: `reference_graph_storage_to_presentation` (storage CascadeNode id/chapter → presentation node_id/chapter_id; storage CascadeEdge from_node_id/to_node_id/relationship_type → presentation source/target/relation; total_node_count/total_edge_count → total_nodes/total_edges; truncated passthrough; **by_dimension COMPUTED from node.dimension counts**). 2 NEW tests (storage-shape mapping + idempotence).
10. `fdd1c55d` `refactor(studio-api)`: `get_reference_graph` returns canonical `ReferenceGraphResponse` via `cvg_adapter.reference_graph_storage_to_presentation`. Storage-shape import removed.
11. `639c4b82` `chore(ruff)`: import-block ordering (I001) fix.
12. `394d8af6` `refactor(studio-api)`: removes storage-shape `ReferenceGraphResponse` class from `apps/studio_api/protocols.py` + drops `noqa F401` re-exports from `app.py` and `models/__init__.py`. **Rewrites `_build_reference_graph_response` in `apps/studio_api/helpers/cvg.py`** to construct lingwen-shared canonical `ReferenceGraphResponse` directly (node_id/chapter_id/source/target/total_nodes/total_edges/by_dimension/truncated) instead of building storage-shape models that no longer exist. Drops now-unused `CascadeNodeResponse`/`CascadeEdgeResponse` imports.
13. `c1244097` `refactor(dashboard)`: `ImpactGraph.vue` end-to-end. Click handler reads `node_id/chapter_id`, edge mapping reads `source/target`, nodeLabel reads `node_id/chapter_id`. Test fixture migrated identically.

## Architecture Invariants Enforced (3 NEW, 28 total)

- **#26 (NEW)** `RippleListItemResponse` (lingwen-shared) includes `impact_score: Optional[float] = None` so dashboard filter/sort reads via typed wrapper without hybrid storage-roundtrip in the route handler.
- **#27 (NEW)** Dashboard cascade consumers (`cascadeGraphUtils.js` + `useWorkflowSocket.js`) use presentation-shape field names. Reference-graph consumers (`ImpactGraph.vue`) also migrated end-to-end per N.11.g.
- **#28 (NEW)** `GET /api/cvg/reference-graph` returns canonical presentation-shape `ReferenceGraphResponse` via `cvg_adapter.reference_graph_storage_to_presentation`. Storage-shape `ReferenceGraphResponse` class removed from `apps/studio_api/protocols.py` (no orphan code).

## Test Results

| Gate | Count | Status |
|------|-------|--------|
| `packages/lingwen-shared/tests/` | 129 passed | +4 NEW (2 impact_score + 2 truncated_flag) |
| `apps/studio_api/tests/test_cvg_adapter.py` | 19 passed | +2 NEW (reference_graph shape + idempotence) |
| `apps/studio_api/tests/` full (excl. pre-existing write_workspace fail) | 45 passed | 0 regression |
| `apps/dashboard` vitest | 1733 passed + 1 skipped | 0 regression |
| `apps/dashboard` vue-tsc | 0 errors | clean |
| ruff (touched files) | All checks passed | clean |
| `Dashboard-contracts` cvg.ts re-export | truncated + by_dimension propagated | OK |

## Files Changed

### Python (backend)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` — `RippleListItemResponse.impact_score` + `ReferenceGraphResponse.truncated` extensions
- `apps/studio_api/cvg_adapter.py` — `ripple_storage_to_presentation.impact_score` + NEW `reference_graph_storage_to_presentation` adapter
- `apps/studio_api/routes/cvg.py` — `list_ripples` hybrid removal + `get_reference_graph` migration to canonical
- `apps/studio_api/helpers/cvg.py` — `_build_reference_graph_response` rewrites for canonical shape + `_get_dim` consumer cleanup
- `apps/studio_api/protocols.py` — storage-shape `ReferenceGraphResponse` class removed
- `apps/studio_api/app.py` — `ReferenceGraphResponse` import dropped
- `apps/studio_api/models/__init__.py` — `noqa F401` re-export dropped

### TypeScript (frontend DTOs)
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` — auto-generated (impact_score + truncated)
- `apps/dashboard/src/utils/cascadeGraphUtils.js` — edge + node + depth reads migration
- `apps/dashboard/src/composables/useWorkflowSocket.js` — JSDoc `max_depth` rename
- `apps/dashboard/src/components/ImpactGraph.vue` — node_id/chapter_id/source/target end-to-end migration

### Tests
- `packages/lingwen-shared/tests/test_cvg_dto.py` — 4 NEW tests (impact_score direct + default None + truncated explicit + truncated default)
- `apps/studio_api/tests/test_cvg_adapter.py` — 2 NEW reference_graph tests
- `apps/dashboard/tests/unit/cascade-graph-utils-full.spec.ts` — fixture migrate to presentation shape
- `apps/dashboard/tests/unit/impact-graph.spec.ts` — fixture migrate to presentation shape

## Lessons Learned

1. **Pydantic v2 `extra="ignore"` silently swallows mismatched field names** — extending the existing `RippleListItemResponse` with `impact_score` (default `None`) is the *least invasive* fix; storage-shape adapters continue to work because they call `.model_dump()` and `RippleListItemResponse` silently ignores `dimension` / `relationship_type` / `parent_ripple_id` / `child_count` (storage-only fields) when reading from a presentation object. No consumer had to change.

2. **Hybrid storage-roundtrip pattern recurs as a diagnostic signal** — the inline comment in `list_ripples` ("Storage shape has impact_score for filter/sort; presentation shape drops it. Filter/sort on storage, then convert via adapter.") was the canary that a presentation field was missing. Removing the comment + removing the storage-shape intermediate is the actual close.

3. **End-to-end migration requires touching storage-shape consumers too** — T3.5 closed the storage class but `ImpactGraph.vue` still read `n.id` / `n.chapter` / `e.from_node_id` (storage-shape keys no longer present in backend response). Without the dashboard migration commit, the endpoint migration would have been a silent break at runtime. TDD via component test fixtures catches this; runtime breakage in browser would not.

4. **`_get_dim` helper generalizes to `_node_to_presentation_dict` / `_edge_to_presentation_dict`** — same shape (polymorphic dict/dataclass accessor + alias fallback for back-compat). Pattern repeats 3x across adapters (cascade_node, cascade_edge, reference_graph). Future adapters should extract a shared polymorphic helper instead of inlining the dict/dataclass branches.

5. **Adapter idempotence is a robustness win** — `reference_graph_storage_to_presentation` accepts BOTH storage-shape (id/chapter/from_node_id) AND presentation-shape (node_id/chapter_id/source/target) inputs. Lets the route funnel both pre-T3.4 helpers AND post-T3.5 helpers through the same adapter as a final boundary check.

6. **Cascade preview polling test (test_get_dim_*) passed in N.11 but is unused post-N.11.g** — the `_get_dim` helper from N.11.f applies to cascade preview nodes but not reference-graph nodes (different field sets). Future work: factor out a shared `polymorphic_get(node, field)` helper to reduce the inline `if isinstance(n, dict)` patterns that proliferated across the 3 adapters.

## Carryover to v16.5 #N.13+

After this branch merges: 39 `as unknown as` cast cleanup in `apps/dashboard/src/composables/` becomes next priority. Spec/plan should be drafted in same session.

Pre-existing carryover (NOT touched by this phase):
- `lingwen_quality` module missing (15 `tests/infra/` test failures — v15.7.1 debt)
- `plugin_manager.py:_discover_internal_providers` module path bug (v15.7.1 debt)

## Final State

- **Branch**: `phase-126-v16-5-n11-d-e-g` (13 commits since master `940d3c7b`)
- **Master**: at v16.5 #N.12 closure
- **Tests**: 1733 vitest / 129 shared / 45 studio_api (excl. write_workspace pre-existing) / 19 cvg_adapter / vue-tsc 0 / ruff 0 / knip 0 / ESLint 0 / lint-imports 3 contracts KEPT
- **Architecture invariants**: 28 total enforced (3 NEW in N.11.d/e/g)
- **Carryover**: clean (everything N.10/N.11 carryover now closed)
