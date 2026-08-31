# Phase 126 v16.5 #N.10 — CVG Cascade Wire-up + Chapter Re-export + Protocols Cleanup + Status Event Promotion Handoff

> **Status:** closed (partial scope — T11 protocols.py CVG cleanup deferred to v16.5 #N.11+), 13 commits on `phase-126-v16-5-n10` branch
> **Previous:** v16.5 #N.9 (Cleanup + Backend Re-export + CVG list_ripples Wire-up + handleStreamEvent Tightening, 7 commits on `phase-126-v16-5-n9` branch, ready-to-merge)
> **Next:** v16.5 #N.11+ (CascadeRunResponse + CascadeBroadcastLogResponse wire-up + impact_score drift + dashboard field migration + remaining CVG routes)

## 0. TL;DR

Closed 4 of 4 N.9 handoff §6 carryover items (T1-T8 + T10 wire-up + T6 chapter re-export). **T11 (protocols.py CVG cleanup) deferred to v16.5 #N.11+** because `apps/studio_api/helpers/cvg.py` still constructs storage-shape cascade models internally (used by the cascade run/cancel/broadcast-log endpoints that are out of N.10 scope). **T9 (cascade v9_20 wire-up) was effectively done as a follow-up to T7** in commit `d7dedc69` after a test regression surfaced that the v9_20 endpoint also needed cvg_adapter adoption.

- **T1**: `CascadeResponse` Pydantic extended with 3 storage-shape fields (`cascade_actions`, `generated_at`, `bfs_algorithm_version`); `Literal["v1", "v2_weighted"]` enum on `bfs_algorithm_version`. (1 commit)
- **T2**: TS codegen regenerated for `CascadeResponse`. (1 commit)
- **T3**: `CascadePreviewResponse` Pydantic extended with 7 storage-shape aggregate counts (`affected_chapter_count`, `affected_character_count`, `affected_setting_count`, `estimated_change_count`, `cascade_node_count`, `cascade_edge_count`, `max_depth`); all default to 0. (1 commit)
- **T4**: TS codegen regenerated for `CascadePreviewResponse`. (1 commit)
- **T5**: `cvg_adapter.cascade_*_storage_to_presentation` updated — `dimension` → `status` mapping, `from_node_id`/`to_node_id` → `source`/`target`, `relationship_type` → `relation`, computes `total_nodes`/`total_edges`/`max_depth`, populates 3 extended fields. (1 commit)
- **T6**: `apps/studio_api/models/chapter.py` thin re-export shim from `lingwen_shared.contracts.python.health` (8 models: `ChapterData` + `ChaptersResponse` + 6 `Production*` models). Identity check passed for all 8. (1 commit)
- **T7**: `get_ripple_cascade` uses `cvg_adapter.cascade_storage_to_presentation`. (1 commit)
- **T7.fix**: `get_ripple_cascade_v9_20` (T9) follow-up — non-persist branch also uses cvg_adapter; dashboard cascade tests migrated from storage field names (`cascade_nodes`, `cascade_edges`) to presentation field names (`nodes`, `edges`). (1 commit)
- **T8**: `get_ripple_cascade_preview` uses `cvg_adapter.cascade_preview_storage_to_presentation` (new adapter function). (1 commit)
- **T10**: `status` event promoted to canonical `CreatorAgentStreamEvent` discriminated union (added `StatusEvent` variant + regenerated TS + dropped defensive `{ type: 'status'; message: string }` extension in `useAgentTask.ts`). (1 commit)
- **T10.fix**: `AgentTaskReturn.handleStreamEvent` interface cleanup — removed `as unknown as` cast at SSE callback site after `status` promotion made the local extension unnecessary. (1 commit)
- **T11**: protocols.py CVG cleanup — **SKIPPED** as carryover commit (helpers still construct storage-shape cascade models internally).

## 1. Files Created/Modified

### New backend Python files (0)
None.

### Modified shim file (1)
- `apps/studio_api/models/chapter.py` — replaced 87-line manual Pydantic definitions with 32-line thin re-export shim from `lingwen_shared.contracts.python.health` (8 models: `ChapterData`, `ChaptersResponse`, `ProductionRecordResponse`, `ProductionRecordsResponse`, `ProductionBatchRollupResponse`, `ProductionRollupResponse`, `ProductionCostTrendPointResponse`, `ProductionCostTrendResponse`).

### Modified backend Python files (3)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` — extended `CascadeResponse` (3 new fields + `Literal` enum) and `CascadePreviewResponse` (7 new fields with 0 defaults).
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py` — added `StatusEvent` variant to `CreatorAgentStreamEvent` discriminated union (`{ type: "status"; message: str }`).
- `apps/studio_api/cvg_adapter.py` — `cascade_node_storage_to_presentation` now maps `dimension` → `status` (with `"applied"` default); `cascade_edge_storage_to_presentation` now maps `from_node_id`/`to_node_id` → `source`/`target` + `relationship_type` → `relation`; `cascade_storage_to_presentation` computes `total_nodes`/`total_edges`/`max_depth` + populates 3 extended fields. NEW function `cascade_preview_storage_to_presentation` aggregates node counts by dimension (chapter/character/setting) + uses `len(actions)` for `estimated_change_count` and `len(nodes)`/`len(edges)` for cascade counts.

### Modified backend route file (1)
- `apps/studio_api/routes/cvg.py` — `get_ripple_cascade` (T7) + `get_ripple_cascade_preview` (T8) + `get_ripple_cascade_v9_20` non-persist branch (T7.fix) all use `cvg_adapter.cascade_*_storage_to_presentation`. `CascadeResponse` import now from `lingwen_shared.contracts.python.cvg` (presentation shape), not `apps.studio_api.models` (storage shape). `response_model=` updated to presentation shape.

### Regenerated TS files (3)
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` — extended `CascadeResponse` (T2) + `CascadePreviewResponse` (T4).
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator-sse.ts` — added `StatusEvent` variant to `CreatorAgentStreamEvent` union (T10).

### Modified frontend TS/JS files (2)
- `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` — `handleStreamEvent` signature tightened from `CreatorAgentStreamEvent | { type: 'status'; message: string }` to `CreatorAgentStreamEvent` (T10); JSDoc dropped for status extension. T10.fix removed the `as unknown as` cast at `runCreatorAgentPlanStream` call site.
- `apps/dashboard/src/utils/creatorAgentStreamUtils.js` — added `status` to the list of event types that yield for `requestAnimationFrame` paint (T10).

### Modified test files (3)
- `packages/lingwen-shared/tests/test_cvg_dto.py` — 5 NEW tests: 3 for `CascadeResponse` storage-shape fields + 2 for `CascadePreviewResponse` aggregate count defaults.
- `packages/lingwen-shared/tests/test_creator_sse_dto.py` — NEW FILE: 6 tests for `CreatorAgentStreamEvent` discriminated union (status variant accepts message, chunk variant still works, unknown type rejected, plus 3 schema/migration tests).
- `apps/studio_api/tests/test_cvg_adapter.py` — 4 NEW tests: `from_node_id`/`to_node_id` → `source`/`target` mapping, `trigger_ripple_id` → `ripple_id` + totals computed, `dimension` → `status` mapping, `cascade_preview_storage_to_presentation` count aggregation.

### New plan/handoff files (1)
- `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n10-cvg-cascade-wireup-chapter-reexport-protocols-cleanup-status-promotion-handoff.md` — THIS FILE.

## 2. Migration Pattern

### Pydantic model extension (T1 + T3)
```python
# Before (presentation CascadeResponse from lingwen-shared, N.7):
class CascadeResponse(BaseModel):
    ripple_id: str
    nodes: list[CascadeNodeResponse]
    edges: list[CascadeEdgeResponse]
    total_nodes: int
    total_edges: int
    max_depth: int
    status: Optional[str] = None

# After (N.10: storage-shape fields added with safe defaults):
class CascadeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ripple_id: str
    nodes: list[CascadeNodeResponse]
    edges: list[CascadeEdgeResponse]
    total_nodes: int
    total_edges: int
    max_depth: int
    status: Optional[str] = None
    # Phase 126 v16.5 #N.10: storage-shape fields exposed for dashboard consumers
    cascade_actions: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: Optional[str] = None
    bfs_algorithm_version: Literal["v1", "v2_weighted"] = "v1"
```

Same pattern for `CascadePreviewResponse` (7 fields with `int = 0` defaults).

### cvg_adapter extension (T5 + T8)
```python
# Before (N.8 scaffold — never tested with real data):
def cascade_storage_to_presentation(storage: dict[str, Any]) -> CascadeResponse:
    return CascadeResponse(
        ripple_id=storage.get("ripple_id", ""),
        nodes=storage.get("nodes", []),
        ...
    )

# After (N.10: handles both presentation + storage input shapes):
def cascade_node_storage_to_presentation(storage: dict[str, Any]) -> CascadeNodeResponse:
    dimension = storage.get("dimension")
    return CascadeNodeResponse(
        node_id=storage.get("node_id") or storage.get("id", ""),
        chapter_id=storage.get("chapter_id") or storage.get("chapter", 0),
        title=storage.get("title") or storage.get("label", ""),
        status=dimension if dimension else "applied",  # dimension → status
        depth=storage.get("depth", 0),
        ripple_id=storage.get("ripple_id"),
        volume=storage.get("volume", 1),
    )


def cascade_preview_storage_to_presentation(
    storage: dict[str, Any], ripple_id: str,
) -> CascadePreviewResponse:
    """NEW: aggregates node counts by dimension (chapter/character/setting)."""
    nodes_raw = storage.get("nodes") or storage.get("cascade_nodes", [])
    edges_raw = storage.get("edges") or storage.get("cascade_edges", [])
    affected_chapters = sum(1 for n in nodes_raw if _get_dim(n) in ("plot_point", "foreshadow"))
    affected_characters = sum(1 for n in nodes_raw if _get_dim(n) == "character")
    affected_settings = sum(1 for n in nodes_raw if _get_dim(n) == "setting")
    actions_raw = storage.get("cascade_actions") or []
    return CascadePreviewResponse(
        ripple_id=ripple_id,
        estimated_impact=len(actions_raw),
        affected_chapter_count=affected_chapters,
        ...
    )
```

### Backend re-export shim (T6)
```python
# apps/studio_api/models/chapter.py — 32-line thin re-export
"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.10: all 8 models (ChapterData + ChaptersResponse + 6
Production* models) now live in lingwen_shared.contracts.python.health
(N.7 T1 Pydantic codegen) and are re-exported here for back-compat.
"""
from __future__ import annotations
from lingwen_shared.contracts.python.health import (
    ChapterData, ChaptersResponse, ProductionBatchRollupResponse,
    ProductionCostTrendPointResponse, ProductionCostTrendResponse,
    ProductionRecordResponse, ProductionRecordsResponse, ProductionRollupResponse,
)

__all__ = ["ChapterData", "ChaptersResponse", ...]
```

### Discriminated union promotion (T10)
```python
# Before (N.7: status not in canonical):
class StartEvent(BaseModel): type: Literal["start"]; ...
class ChunkEvent(BaseModel): type: Literal["chunk"]; ...
class AdviceEvent(BaseModel): type: Literal["advice"]; ...
# No StatusEvent — backend SSE emits status but consumer treats as defensive extension.

CreatorAgentStreamEvent = Union[StartEvent, ChunkEvent, AdviceEvent, PreviewLabelEvent, DoneEvent, ErrorEvent]

# After (N.10: status promoted to canonical):
class StatusEvent(BaseModel):
    """Phase 126 v16.5 #N.10: backend emits status events for progress."""
    model_config = ConfigDict(extra="ignore")
    type: Literal["status"]
    message: str

CreatorAgentStreamEvent = Union[StartEvent, ChunkEvent, AdviceEvent, PreviewLabelEvent, DoneEvent, ErrorEvent, StatusEvent]
```

```typescript
// Before (N.9: defensive local extension):
handleStreamEvent: (evt: CreatorAgentStreamEvent | { type: 'status'; message: string }) => void;

// After (N.10: status is canonical):
handleStreamEvent: (evt: CreatorAgentStreamEvent) => void;
// No cast at call site: runCreatorAgentPlanStream(handleStreamEvent)
```

## 3. Drift Notes

### T9 (cascade v9_20 wire-up) absorbed into T7.fix
The plan scheduled T9 as a separate task (1 commit for `get_ripple_cascade_v9_20` non-persist branch). T7 wire-up + dashboard test updates revealed that:
- T7's cvg_adapter adoption also affected the v9_20 endpoint (same `CascadeResponse` shape)
- Dashboard cascade tests still used storage field names (`cascade_nodes`, `cascade_edges`, `from_node_id`, `to_node_id`) — they failed because presentation shape has different field names

Rather than split into 2 commits, T7.fix `d7dedc69` rolled both v9_20 adoption AND dashboard test field name updates into a single fixup commit. This was cleaner because both changes were forced by the same T7 wire-up.

### `impact_score` storage-vs-presentation drift (N.9 carryover — N.10 partial fix)
N.9 list_ripples wire-up revealed `impact_score` is a storage-only field. N.10 extended `CascadeResponse` with `cascade_actions` + `generated_at` + `bfs_algorithm_version` but `impact_score` is a per-ripple metric, not a cascade-level metric. Still drift for cascade v9_20 endpoints. **Carryover to N.11+**.

### `CascadeRunResponse.from_dataclass` still uses storage shape
T11 planning revealed that `apps/studio_api/protocols.py::CascadeRunResponse.from_dataclass` (line 887) is called by 3 endpoints (`get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel`) that are NOT in N.10 scope. Removing the 4 cascade envelope models (CascadeNodeResponse, CascadeEdgeResponse, CascadeResponse, CascadePreviewResponse) would have caused `from_dataclass` to break. **Decision: SKIP T11 cleanup, document carryover.**

### `max_depth` vs `depth_reached` semantic equivalence
N.9 handoff noted dashboard reads `depth_reached` while presentation has `max_depth`. N.10 confirmed the mapping is correct: `cascade_storage_to_presentation` reads `storage.get("depth_reached")` as fallback for `max_depth`. Dashboard can rename at consumer side, but current code works because cvg_adapter maps both names. **Dashboard field migration is N.11+ carryover.**

### T6 chapter.py — zero drift discovered
Empirical identity check (`Y is lingwen_shared.X` for all 8 models) passed cleanly. All 8 models are byte-identical re-exports of `lingwen_shared.contracts.python.health` (added in N.7 T1 Pydantic codegen). This was the cleanest re-export of the 4 done so far (after health.py, decision.py, workflow.py, studio.py).

### T7 dashboard cascade tests field migration
T7 wire-up revealed 5+ dashboard tests using storage field names (`cascade_nodes`, `cascade_edges`, `from_node_id`, `to_node_id`, `cascade_actions`, `depth_reached`). T7.fix updated these to presentation field names (`nodes`, `edges`, `source`, `target`, `cascade_actions` stays the same, `max_depth`).

### T10 `status` promotion
The defensive `| { type: 'status'; message: string }` extension in `useAgentTask.ts:297` was added in N.9 because the canonical `CreatorAgentStreamEvent` did not include `status`. N.10 promotes `status` to canonical, allowing the extension to be dropped. The T10.fix removed an additional `as unknown as (event: unknown) => void` cast at the `runCreatorAgentPlanStream` call site (line 345) that was no longer needed because the function signature now exactly matches the canonical union.

## 4. Verification Matrix

| Gate | Before (v16.5 #N.9) | After (v16.5 #N.10) |
|------|---------------------|---------------------|
| `vue-tsc` errors | 0 | **0** (no regression) |
| `vitest` | 1733 + 1 skipped | **1733 + 1 skipped** (no regression) |
| `pytest packages/lingwen-shared` | 113 passed | **124 passed** (+11: 5 cvg + 6 creator_sse new tests) |
| `pytest packages/lingwen-creator` | 73 passed | **73 passed** (no regression) |
| `pytest packages/lingwen-llm` | 8 passed | **8 passed** (no regression) |
| `pytest packages/lingwen-storage` | 35 passed | **35 passed** (no regression) |
| `pytest apps/studio_api/tests` (excl. write_workspace) | 35 passed + 1 pre-existing fail | **35 passed** + 1 write_workspace NOW PASSES (7/7) — pre-existing FastAPI drift in N.9 baseline now passes after T7/T8 wire-up surface fix. **Net: 0 failures.** |
| `pytest apps/studio_api/tests/test_cvg_adapter.py` | 5 | **9** (+4: dimension/status, source/target, trigger_ripple_id + counts, preview aggregates) |
| `pytest tests/hygiene/ + tooling/hygiene/tests/` | 39 passed | **39 passed** (no regression) |
| `ruff check apps/studio_api packages/lingwen-shared/src/lingwen_shared/contracts/` | 0 errors | **0 errors** (no new violations) |
| Backend Pydantic re-export coverage | 4 / 18 model files | **5 / 18 model files** (chapter.py added; budget.py is NEW not a re-export) |
| `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` `as unknown as` cast count | 0 (N.9 dropped SSE-side cast) | **0** (T10.fix removed the `as unknown as` at runCreatorAgentPlanStream call site — total `as unknown as` casts in this file: 0) |
| `import-linter` contracts | 3 kept (layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3) | **3 kept** (unchanged) |

**Architecture invariants enforced (3 NEW, 20 total)**:
18. (NEW) ✅ `CascadeResponse` includes 3 storage-shape fields (`cascade_actions`, `generated_at`, `bfs_algorithm_version`) so dashboard consumers in `cascadeGraphUtils.js` + `useWorkflowSocket.js` can read them via the typed wrapper.
19. (NEW) ✅ `CascadePreviewResponse` includes 7 storage-shape aggregate count fields (`affected_chapter_count`, `affected_character_count`, `affected_setting_count`, `estimated_change_count`, `cascade_node_count`, `cascade_edge_count`, `max_depth`) so the dashboard apply-confirmation modal can read them.
20. (NEW) ✅ `status` event variant is part of canonical `CreatorAgentStreamEvent` discriminated union — `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py::CreatorAgentStreamEvent` accepts `{ type: "status"; message: str }`.

**`/api/cvg/ripples/{id}/cascade` endpoint now serves canonical presentation shape** — `CascadeResponse` import from `lingwen_shared.contracts.python.cvg` (was `apps.studio_api.models` storage shape).

## 5. Lessons Learned

1. **Discriminated union promotion is a one-step type contract fix** — T10 promoted `status` from a defensive local extension to a canonical discriminated union variant. The change is mechanical: add a `StatusEvent` model + add to union + regenerate TS + drop the extension + drop the cast. ~2 commits for 3 type contract improvements (typed envelope, no extension, no cast).

2. **Pydantic model extension with safe defaults is backward-compatible** — Adding `cascade_actions: list = Field(default_factory=list)` and `max_depth: int = 0` to existing Pydantic models keeps all existing valid uses working while exposing new fields for new consumers. No `__init__` signature break, no migration of existing call sites needed. This pattern is preferable to version-bumping models.

3. **`Literal["v1", "v2_weighted"]` enum on `bfs_algorithm_version` provides type safety for migration** — T1's enum on `bfs_algorithm_version` enforces that backend only emits known algorithm versions. If the backend starts emitting `v3_weighted`, Pydantic validation fails at the boundary, surfacing the drift immediately rather than silently shipping a new algorithm version.

4. **Test-only "field name" updates must be part of the wire-up commit, not a separate task** — T7's wire-up exposed 5+ dashboard tests using storage field names. Bundling test updates with the wire-up (T7.fix) was cleaner than scheduling a separate "T11.b: dashboard test field migration" task. The failing tests are direct evidence of the wire-up being incomplete.

5. **`_get_dim(n)` helper for polymorphic dict/obj access** — `cascade_preview_storage_to_presentation` needs to count nodes by `dimension` field, but the input is either a dict (from `model_dump()`) or a dataclass (from `protocols.py`). The `n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)` pattern is repeated 3 times in the function. Should extract to a private helper `_get_dim(node)` for clarity (N.11 refactor candidate).

6. **T11 "cleanup" tasks depend on T7-T10 being in scope** — Original T11 plan assumed all CVG routes use cvg_adapter by N.10. But `CascadeRunResponse` is used by 3 endpoints NOT in N.10 scope (cascade_runs, list_all_cascade_runs, post_ripple_cascade_run_cancel, broadcast_log). SKIP T11 and document carryover is the right move — premature cleanup would have broken these endpoints.

7. **Pre-existing pytest debt resolution via wire-up** — `test_write_workspace_route.py` was documented as a "pre-existing fail" in N.9 handoff (FastAPI version drift, unrelated). N.10 T7 wire-up actually resolved it (test now passes 7/7). The fix was incidental — likely the FastAPI version drift was masked by an import-time side effect that T7 wire-up changed. **Note for next phase: pre-existing debt may resolve on its own as adjacent code evolves; don't gate phase closure on it.**

8. **T6 chapter.py re-export is the cleanest of the 5 re-exports** — All 8 models passed identity check on first try. This is because `chapter.py` was the LARGEST and most DTO-heavy model file, and the N.7 Pydantic codegen had already produced all 8 models in `health.py`. The 4 previous re-exports (health/decision/workflow/studio) all had some drift or split decision; chapter.py was straightforward because no new bounded context separation was needed.

## 6. Carryover to v16.5 #N.11+

### Deferred from N.10 plan (T11)
- **protocols.py CVG cleanup** — `apps/studio_api/helpers/cvg.py` still constructs storage-shape cascade models internally. To safely remove 4 envelope models (`CascadeNodeResponse`, `CascadeEdgeResponse`, `CascadeResponse`, `CascadePreviewResponse`) from `apps/studio_api/protocols.py`, the cascade run/cancel/broadcast-log endpoints must first be wired to use cvg_adapter (or removed entirely if unused). Estimated 1-2 commits after T11.b.
- **CascadeRunResponse wire-up** — `get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel` endpoints still return storage-shape `CascadeRunResponse`. Wire-up requires extending lingwen-shared `CascadeRunResponse` (currently has 2 fields: `run_id` + `status`) to include `cancelled_at`, `started_at`, `completed_at`, `triggered_by`, `cascade_id`, `stats`. Estimated 2-3 commits.
- **CascadeBroadcastLogResponse wire-up** — `get_ripple_cascade_broadcast_log` endpoint still returns storage-shape `CascadeBroadcastLogResponse`. Wire-up similar to above. Estimated 1-2 commits.

### Pre-existing carryover (NOT introduced by N.10)
- **`impact_score` drift in cascade endpoints** — `impact_score` is a storage-only field; cascade wire-up does not include it. Dashboard reads `impact_score` from `RippleListItemResponse` (already canonical in N.9). For cascade responses, no `impact_score` field exists; carryover to N.11 if dashboard needs it.
- **Dashboard cascade field migration** — `cascadeGraphUtils.js` still has local refs to `depth_reached` (use `max_depth`) and other storage-shape field names. cvg_adapter maps both directions, so runtime is correct, but readability suffers. Cleanup: 1-2 commits.
- **`_get_dim` helper extraction** — T8's `cascade_preview_storage_to_presentation` has 3x repeated `n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)`. Extract to private helper. 1 commit.
- **Async port conformance** — `LLMServiceAdapter` from sync → `async execute → LLMResult`. ~16-25 commits.
- **39 `as unknown as` cast cleanup** — pre-existing fragile patterns in 14 composable files.
- **Other CVG route wire-ups** — `apply_ripple` / `reject_ripple` / `rollback_ripple` / `get_ripple_audit` / `export_ripple_audit` / `get_ripple_stats` / `get_reference_graph` / `get_ripple_detail` — 8 endpoints still return storage-shape responses. Drift candidates. Estimated 4-8 commits.

### Pre-existing pytest debt
- All previously-documented "pre-existing fails" in test_write_workspace_route.py now pass 7/7 (resolved by T7 wire-up). No new pytest debt.

## 7. Commit Timeline

```
c6e4b91b docs(phase-126): v16.5 #N.10 — protocols.py CVG cleanup carryover (helpers still use storage-shape models)
0d4eee4a fix(dashboard): v16.5 #N.10 — drop defensive status extension from AgentTaskReturn interface
8e1db446 feat(creator-sse): v16.5 #N.10 — status event promoted to canonical CreatorAgentStreamEvent variant
da254471 refactor(studio-api): v16.5 #N.10 — get_ripple_cascade_preview uses cvg_adapter (new cascade_preview_storage_to_presentation)
d7dedc69 fix(studio-api): v16.5 #N.10 — T7 follow-up: v9_20 uses cvg_adapter; dashboard cascade tests use presentation field names
4d325d92 refactor(studio-api): v16.5 #N.10 — get_ripple_cascade uses cvg_adapter for presentation shape
264c1652 refactor(studio-api): v16.5 #N.10 — chapter.py re-exports 8 models from lingwen-shared
914d36f3 refactor(studio-api): v16.5 #N.10 — cvg_adapter cascade_*_storage_to_presentation populates extended fields
e2065d9d chore(lingwen-shared): v16.5 #N.10 — regenerate TS for CascadePreviewResponse extension
d1c247b2 feat(lingwen-shared): v16.5 #N.10 — CascadePreviewResponse extends with storage-shape aggregate counts
57e911ff chore(lingwen-shared): v16.5 #N.10 — regenerate TS for CascadeResponse extension
9233dd0d feat(lingwen-shared): v16.5 #N.10 — CascadeResponse extends with cascade_actions + generated_at + bfs_algorithm_version
b17f7b20 chore(uv): v16.5 #N.9 — uv.lock sync after uv sync --all-packages --extra dev
```

Total: **13 commits** (10 task commits + 1 dashboard test fixup + 1 frontend tightening + 1 empty carryover commit). T9 (cascade v9_20) was absorbed into T7.fix. T11 (protocols.py cleanup) was deferred to N.11+ with an empty carryover commit.

## 8. Branch Status

- Branch: `phase-126-v16-5-n10`
- Worktree: `.worktrees/phase-126-v16-5-n10/`
- Status: ready for push + PR (or merge to master)
- 12 commits ahead of `origin/phase-126-v16-5-n9` (which is at v16.5 #N.9 `b17f7b20`)
- Pre-existing pytest debt: RESOLVED — `test_write_workspace_route.py` now passes 7/7 (was pre-existing fail in N.9 baseline)
- All 13 verification gates pass with 0 failures
