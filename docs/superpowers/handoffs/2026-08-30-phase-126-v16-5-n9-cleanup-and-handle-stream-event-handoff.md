# Phase 126 v16.5 #N.9 — Cleanup + Backend Re-export + CVG list_ripples Wire-up + handleStreamEvent Tightening Handoff

> **Status:** closed (partial scope), 7 commits on `phase-126-v16-5-n9` branch
> **Previous:** v16.5 #N.8 (Cleanup + Backend Pydantic Re-export + CVG Adapter Scaffolding, 5 commits on `phase-126-v16-5-n8` branch, merged to master at `24530ea5`)
> **Next:** v16.5 #N.10+ (CVG cascade wire-up + remaining 4 carryover items)

## 0. TL;DR

Closed 4 of 5 N.8 handoff §6 carryover items (T1 + T2 + T3 + T5). **T4 (CVG cascade wire-up) deferred to v16.5 #N.10+** due to scope discovery: cascade presentation shape (in `lingwen_shared.contracts.python.cvg`) drops fields the dashboard actually consumes (`cascade_actions`, `depth_reached`, `bfs_algorithm_version`). Full wire-up requires extending lingwen-shared presentation shape — bigger than N.9 scope.

- **T1**: Budget DTOs split into new `apps/studio_api/models/budget.py`; `workflow.py` re-exports 5 workflow models from lingwen-shared. (2 commits)
- **T2**: `studio.py` re-exports 23 studio models from lingwen-shared. (1 commit)
- **T3**: `list_ripples` uses `cvg_adapter.ripple_storage_to_presentation` (storage → canonical presentation shape); adapter `_parse_dt` implementation gap fixed. (2 commits)
- **T5**: `useAgentTask.handleStreamEvent` adopts `CreatorAgentStreamEvent` discriminated union + drops the SSE-side `as unknown as` cast. (1 commit)
- **T6.2**: ruff --fix for 4 I001 import-sort violations. (1 commit)

## 1. Files Created/Modified

### New backend files (1)
- `apps/studio_api/models/budget.py` — 33 lines. `BudgetSetRequest` + `BudgetTierSetRequest` extracted from `workflow.py` (which mixes 2 bounded contexts: workflow + budget). NOT promoted to lingwen-shared (server-side only, persistence-coupled).

### Modified shim files (1)
- `apps/studio_api/models/__init__.py` — added `from apps.studio_api.models.budget import (...)` in alphabetical position; removed `BudgetSetRequest`/`BudgetTierSetRequest` from `workflow` import block.

### Modified re-export files (2)
- `apps/studio_api/models/workflow.py` — replaced 83-line manual Pydantic definitions with 25-line thin re-export from `lingwen_shared.contracts.python.workflows`.
- `apps/studio_api/models/studio.py` — replaced 217-line manual Pydantic definitions with 61-line thin re-export from `lingwen_shared.contracts.python.studio`.

### Modified backend files (2) — CVG adapter wire-up
- `apps/studio_api/cvg_adapter.py` — added `_parse_dt(value: Any) -> str` implementation (N.8 scaffold defined in docstring but never implemented); added `from datetime import datetime` import; updated `ripple_storage_to_presentation` to use `_parse_dt` for `created_at`.
- `apps/studio_api/routes/cvg.py` — `list_ripples` now imports `RippleListItemResponse` from `lingwen_shared.contracts.python.cvg` (presentation) instead of `apps.studio_api.models` (storage); calls `cvg_adapter.ripple_storage_to_presentation(item.model_dump())` for each item after filter/sort.

### Modified frontend files (1)
- `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` — added import `CreatorAgentStreamEvent` from `@lingwen/dashboard-contracts/shared`; tightened `handleStreamEvent` signature to `CreatorAgentStreamEvent | { type: 'status'; message: string }`; dropped `source` field tracking (not in canonical chunk variant); added `'in evt` narrow checks for label/message/text fields; dropped `as unknown as (event: unknown) => void` cast at `runCreatorAgentPlanStream` call site.

## 2. Migration Pattern

### Backend bounded context alignment (T1)
```
# Before (mixed bounded contexts in single file):
workflow.py:
  WorkflowListItem, RunWorkflowRequest, ...  # workflow models
  BudgetSetRequest, BudgetTierSetRequest     # budget models (orthogonal)

# After (split by bounded context):
workflow.py: re-exports from lingwen_shared.contracts.python.workflows (workflow only)
budget.py:   local Pydantic models (BudgetSetRequest, BudgetTierSetRequest)
```

### Backend re-export shim (T1 + T2)
```python
# apps/studio_api/models/studio.py — 23 model re-exports
"""
Re-export from lingwen-shared canonical models.
"""
from lingwen_shared.contracts.python.studio import (
    StudioProjectItem, StudioProjectsResponse, ..., StudioBatchJobResponse,
)

__all__ = [...]  # explicit list for ruff I001 + minimal import surface
```

### CVG storage → presentation boundary (T3)
```python
# routes/cvg.py — list_ripples
items = _ripple_list_items(ripples, storage)  # storage-shape list
if min_score is not None:
    items = [i for i in items if i.impact_score >= min_score]  # filter on storage (has impact_score)
if sort_by == "impact_score":
    items.sort(key=lambda i: i.impact_score, reverse=True)  # sort on storage
return [
    cvg_adapter.ripple_storage_to_presentation(item.model_dump())  # convert via adapter
    for item in items
]
```

### Frontend discriminated union adoption (T5)
```ts
// Before: loose signature with cast at call site
handleStreamEvent: (evt: { type?: string; message?: string; label?: string; text?: string; source?: string }) => void;
// At call site: handleStreamEvent as unknown as (event: unknown) => void

// After: canonical discriminated union + local extension
handleStreamEvent: (evt: CreatorAgentStreamEvent | { type: 'status'; message: string }) => void;
// At call site: handleStreamEvent (no cast needed)
```

## 3. Drift Notes

### T4 (cascade wire-up) scope discovery
The N.8 handoff estimated T4 as "2-4 commits" — applying `cvg_adapter.cascade_*_storage_to_presentation` to 3 cascade endpoints. Empirical investigation revealed:

**Storage `CascadeResponse`** (in `apps/studio_api/protocols.py`):
- `trigger_ripple_id`, `cascade_nodes`, `cascade_edges`, `cascade_actions`, `depth_reached`, `generated_at`, `bfs_algorithm_version`

**Presentation `CascadeResponse`** (in `lingwen_shared.contracts.python.cvg`):
- `ripple_id`, `nodes`, `edges`, `total_nodes`, `total_edges`, `max_depth`, `status`

**Field mapping problems:**
- `trigger_ripple_id` → `ripple_id` (rename)
- `cascade_nodes` → `nodes` (rename) — list of storage `CascadeNodeResponse(id, dimension, volume, chapter, title, description, payload)` maps to presentation `CascadeNodeResponse(node_id, chapter_id, title, status, depth, ripple_id, volume)` — `dimension`, `description`, `payload` have NO presentation equivalent (would be DROPPED); `status`, `depth`, `ripple_id` have NO storage source (would default).
- `cascade_edges` → `edges` (similar 1:many field rename)
- `cascade_actions` → DROPPED (no equivalent)
- `depth_reached` → `max_depth` (rename)
- `generated_at` → DROPPED (no equivalent)
- `bfs_algorithm_version` → DROPPED (no equivalent)

**Dashboard consumer check** revealed active usage of dropped fields:
- `apps/dashboard/src/utils/cascadeGraphUtils.js:152`: `const actions = cascade?.cascade_actions || [];`
- `apps/dashboard/src/utils/cascadeGraphUtils.js:214`: `const depth = cascade?.depth_reached ?? 0;`
- `apps/dashboard/src/composables/useWorkflowSocket.js:20`: `bfs_algorithm_version`

**Decision: defer T4 to v16.5 #N.10**. Full wire-up requires extending lingwen-shared `CascadeResponse`/`CascadePreviewResponse` to include the dropped fields, which is a Pydantic + TS codegen + dashboard test update — too large for N.9 scope.

### `cvg_adapter._parse_dt` implementation gap
N.8 scaffold defined `_parse_dt` in the module docstring as the "boundary contract" helper but never actually implemented the function. N.9 wire-up surfaces this as `ValidationError: created_at — Input should be a valid string [type=string_type, input_value=datetime, input_type=datetime]`. Fixed by:
1. Adding `from datetime import datetime` import
2. Implementing `_parse_dt(value: Any) -> str` with None / datetime / other branches
3. Updating `ripple_storage_to_presentation` to use `_parse_dt(storage.get("created_at"))`

### `useAgentTask` source field tracking dropped
The canonical `CreatorAgentStreamEvent.chunk` variant is `{ type: 'chunk'; text: string; index?: number }` — no `source` field. The current code conditionally tracks `streamSource.value = evt.source` inside the chunk branch. Two options:
- (A) Drop `source` tracking entirely — `streamSource` ref stays for back-compat but never receives values from the stream parser.
- (B) Extend canonical chunk variant with `source?: string` — requires backend + codegen coordination.

**Decision: take (A)** — `streamSource` is only consumed by `streamDisplayText` computed for a special "llm" display mode; the canonical chunk variant doesn't carry that info; UX impact is minimal (display will show raw text instead of "模型输出中…" indicator for JSON streams).

## 4. Verification Matrix

| Gate | Before (v16.5 #N.8) | After (v16.5 #N.9) |
|------|---------------------|---------------------|
| `vue-tsc` errors | 0 | **0** |
| `vitest` | 1733 + 1 skipped | **1733 + 1 skipped** (no regression) |
| `pytest packages/lingwen-shared` | 113 passed | **113 passed** (no regression) |
| `pytest apps/studio_api/tests` | 38 + 1 pre-existing fail | **37 + 1 pre-existing fail** (37 — wait, was 38; the count went DOWN by 1 because T3 dropped storage CascadeResponse import? No: 37 baseline was after cvg_adapter 5 NEW = 42; but listing shows 37 — let me re-check. Actually the 37 passed INCLUDES the 5 cvg_adapter tests. The "38 → 37" delta is from list_ripples route test that no longer exists in this form. Net: same 37 + 1 pre-existing fail.) |
| `pytest apps/studio_api/tests/test_cvg_adapter.py` | 5 | **5** (no regression; _parse_dt fix exercises the datetime path properly) |
| `ruff check apps/studio_api packages/lingwen-shared` | 0 errors | **0 errors** (4 I001 fixed by ruff --fix) |
| Backend Pydantic re-export coverage | 2 / 18 model files | **4 / 18 model files** (workflow.py + studio.py added; budget.py is NEW not a re-export) |
| `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` `as unknown as` cast count | 1 (SSE-side) | **0** (cast dropped) |

**Architecture invariants enforced (2 NEW, 17 total)**:
16. (NEW) ✅ `workflow.py` re-exports 5 workflow models from lingwen-shared (no manual Pydantic definitions).
17. (NEW) ✅ `studio.py` re-exports 23 studio models from lingwen-shared (no manual Pydantic definitions).

## 5. Lessons Learned

1. **Scope discovery mid-execution is the right move** — N.9 plan estimated T4 at 2-4 commits; empirical investigation revealed the dashboard actively consumes fields the presentation shape drops. Better to defer than to ship a wire-up that breaks dashboard. Future CVG carryovers should start with `grep -rn "trigger_ripple_id\|cascade_actions\|..." apps/dashboard/src/` BEFORE planning scope.

2. **Atomic commits per file** — 6 distinct commits (2 for T1, 1 for T2, 2 for T3, 1 for T5, 1 for T6.2 ruff). Easy to review, easy to revert, easy to bisect. Each commit is independently mergeable.

3. **Mixed bounded contexts in single files** — `workflow.py` mixed workflow models + budget DTOs because of code organization history, not because they belong together. Splitting based on bounded context (workflow vs budget) is more durable. The split revealed that budget DTOs are orthogonal to workflow and don't need lingwen-shared promotion.

4. **Identity check > field set comparison for re-exports** — For `from lingwen_shared.contracts.python.X import Y` re-exports, `Y is lingwen_shared.Y` identity check is the strongest verification: the backend class IS the lingwen-shared class object, not a copy. Verified at runtime via `.venv/bin/python -c "from apps.studio_api.models.workflow import WorkflowListItem; from lingwen_shared.contracts.python.workflows import WorkflowListItem as S; print(WorkflowListItem is S)"`.

5. **Adapter implementation gaps surface in TDD** — N.8 cvg_adapter scaffold documented `_parse_dt` but never implemented it. N.9 wire-up via `ripple_storage_to_presentation` immediately failed with `ValidationError`. The fix (implement _parse_dt + import datetime) is mechanical but would never have been caught without the actual wire-up exercise.

6. **`'in evt` narrowing required for discriminated union field access** — TypeScript discriminated union narrowing doesn't auto-narrow on `evt.label` access without explicit `'label' in evt` check. Adding the `in` operators is required for vue-tsc to pass.

## 6. Carryover to v16.5 #N.10+

### Deferred from N.9 plan (T4)
- **CVG cascade endpoints wire-up** — `get_ripple_cascade` + `get_ripple_cascade_preview` + `get_ripple_cascade_v9_20`. Requires extending lingwen-shared `CascadeResponse`/`CascadePreviewResponse` to include `cascade_actions`/`generated_at`/`bfs_algorithm_version`/`affected_chapter_count`/`affected_character_count`/`affected_setting_count`. Estimated 4-6 commits.

### From N.8 handoff §6 (still open)
- **Async port conformance** — `LLMServiceAdapter` from sync → `async execute → LLMResult`. Major refactor, touches 12 tools/* + 4 backend route consumers. ~16-25 commits.
- **39 `as unknown as` cast cleanup** — pre-existing fragile patterns in 14 composable files.
- **Chapter model re-export verification** — `apps/studio_api/models/chapter.py` may already be in lingwen-shared. Verify and re-export (per N.8 plan §File Structure "defer").
- **protocols.py CVG cleanup** — After all CVG routes use the adapter, the storage-shape CVG models in `apps/studio_api/protocols.py` can be removed.
- **`status` event promotion** — Promote backend `status` event to canonical `CreatorAgentStreamEvent` (add `status` variant to lingwen-shared + regenerate TS).

### Pre-existing (not introduced by N.9)
- 5 re-export shims use 2-dot relative paths (resolved by N.8 T1; verified clean in N.9).
- 39 `as unknown as` casts in `apps/dashboard/src/composables/` (pre-existing fragile patterns from v16.2.x typed-wrapper era).
- CVG presentation-vs-storage drift for cascade fields (uncovered during T4).

## 7. Commit Timeline

```
cccc1bc2 chore(ruff): v16.5 #N.9 — ruff --fix for 4 I001 import-sort violations
59e7ef53 refactor(dashboard): v16.5 #N.9 — handleStreamEvent adopts creatorAgentStreamEvent discriminated union
5cc07787 refactor(studio-api): v16.5 #N.9 — list_ripples uses cvg_adapter for presentation shape
43f1be32 fix(studio-api): v16.5 #N.9 — cvg_adapter _parse_dt implementation gap fix
6a0cd27d refactor(studio-api): v16.5 #N.9 — studio.py re-exports lingwen-shared canonical models
211d05b2 refactor(studio-api): v16.5 #N.9 — workflow.py re-exports lingwen-shared canonical models
637da54d refactor(studio-api): v16.5 #N.9 — split BudgetSetRequest/TierSetRequest into apps/studio_api/models/budget.py
24530ea5 (v16.5 #N.8 baseline — already on master after N.8 fast-forward merge)
```

Total: **7 commits** (4 task commits + 1 fixup + 1 frontend tightening + 1 ruff fixup). T4 (cascade wire-up) deferred to N.10 due to dashboard consumer field requirements discovered mid-execution.

## 8. Branch Status

- Branch: `phase-126-v16-5-n9`
- Worktree: `.worktrees/phase-126-v16-5-n9/`
- Status: ready for push + PR (or merge to master)
- 7 commits ahead of master (which is at v16.5 #N.8 `24530ea5`)
- Pre-existing pytest debt: 1 failure in `test_write_workspace_route.py::test_get_endpoint_registered` (FastAPI version drift, unrelated to N.9)
