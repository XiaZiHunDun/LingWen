# Phase 126 v16.5 #N.11 — Cascade Runs + Broadcast Log Wire-up

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `CascadeRunResponse` (3 endpoints) + `CascadeBroadcastLogResponse` (1 endpoint) through `cvg_adapter` so all 6 CVG cascade/run/broadcast endpoints serve canonical lingwen-shared presentation shape. Extract `_get_dim` helper. Drop unused protocols.py imports from helpers/cvg.py.

**Architecture:** Mirror the N.10 pattern (T1/T3 Pydantic extension + T2/T4 TS regen + T5 adapter extension + T6-T8 route wire-up). Extend `CascadeRunResponse` with storage-shape fields (cascade_id/completed_at/depth_reached/cascade_nodes/cascade_edges/cascade_actions/cancelled_at/triggered_by/stats) so dashboard consumers can read them via typed wrapper. Add new `CascadeBroadcastLogResponse` to lingwen-shared (currently only exists in storage shape). Extract `_get_dim` polymorphic accessor for DRY in `cascade_preview_storage_to_presentation`. Final cleanup: drop 5 unused imports from helpers/cvg.py.

**Tech Stack:** Python 3.13 + Pydantic v2 + FastAPI (backend), TypeScript + Zod (frontend DTOs). Same toolchain as N.10.

**Carryover from v16.5 #N.10:**
- #N.11.a protocols.py CVG cleanup — **scope reduced**: drop 5 unused imports only (NOT full ReferenceGraphResponse migration; that follows N.11.b/c)
- #N.11.b CascadeRunResponse wire-up — 3 endpoints (get_ripple_cascade_runs + list_all_cascade_runs + post_ripple_cascade_run_cancel)
- #N.11.c CascadeBroadcastLogResponse wire-up — 1 endpoint (get_ripple_cascade_broadcast_log)
- #N.11.f _get_dim helper extraction in cvg_adapter.py — 1 commit
- **Deferred to N.12+**: #N.11.d (impact_score drift), #N.11.e (dashboard cascade field migration to presentation names), #N.11.e-extended (ReferenceGraphResponse full migration to presentation shape)

**Final gates:**
- ✅ 6/6 CVG cascade endpoints serve canonical lingwen-shared presentation shape (currently 3/6: get_ripple_cascade + get_ripple_cascade_preview + get_ripple_cascade_v9_20 done in N.10)
- ✅ helpers/cvg.py no longer imports unused CascadePreviewResponse, CascadeResponse, CascadeRunResponse, RippleActionResponse, RippleStatsResponse from protocols.py
- ✅ cvg_adapter._get_dim replaces 3 inline `n.get("dimension") if isinstance(n, dict) else getattr(...)` repetitions
- ✅ dashboard typed wrapper `fetchCascadeRuns`/`fetchAllCascadeRuns`/`cancelCascadeRun` continue to work without breaking change
- ✅ Tests: 124+10 backend shared / 9+6 cvg_adapter / 1733 vitest / vue-tsc 0 / ruff 0
- ✅ Carryover list updated in CLAUDE.md

---

## File Structure

**Files Modified (5):**
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` — extend CascadeRunResponse + add CascadeBroadcastLogResponse
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` — TS codegen (auto-regenerated)
- `apps/studio_api/cvg_adapter.py` — add cascade_run_storage_to_presentation + cascade_broadcast_log_storage_to_presentation + _get_dim helper
- `apps/studio_api/routes/cvg.py` — 4 endpoints use cvg_adapter (replace CascadeRunResponse.from_dataclass + CascadeBroadcastLogResponse.from_dataclass)
- `apps/studio_api/helpers/cvg.py` — drop 5 unused imports from protocols.py

**Files Created (3):**
- `packages/lingwen-shared/tests/test_cvg_dto.py` — add CascadeRunResponse extension tests + CascadeBroadcastLogResponse tests
- `apps/studio_api/tests/test_cvg_adapter.py` — extend with cascade_run_storage_to_presentation + cascade_broadcast_log_storage_to_presentation + _get_dim tests
- `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup-handoff.md` — handoff doc

**Tests Modified (if any):**
- None required — typed wrapper field additions are backward-compatible (default values)

---

## Part A: CascadeRunResponse Wire-up (Tasks A1-A9)

### Task A1: Extend CascadeRunResponse Pydantic with storage-shape fields

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py:211-228` (CascadeRunResponse class)

- [ ] **Step 1: Add storage-shape fields to CascadeRunResponse**

Edit `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py`. Find the `CascadeRunResponse` class (line 211) and extend it:

```python
class CascadeRunResponse(BaseModel):
    """Cascade-run descriptor returned by ``GET /ripples/cascade/{id}/runs``.

    Phase 126 v16.5 #N.11.b: extended with storage-shape fields
    (cascade_id/completed_at/depth_reached/cascade_nodes/cascade_edges/
    cascade_actions) so dashboard consumers can read the full cascade-run
    payload via typed wrapper without needing to refetch the cascade.

    Also extended with cancel-endpoint fields (cancelled_at/triggered_by)
    and aggregate stats dict so the cancel response carries the same
    surface as the runs list response.
    """

    model_config = ConfigDict(extra="ignore")

    # Existing presentation fields (canonical dashboard surface)
    run_id: str
    ripple_id: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    nodes_processed: int = 0
    max_depth: int
    algorithm: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    # Phase 126 v16.5 #N.11.b: storage-shape fields exposed for dashboard consumers
    cascade_id: Optional[int] = None  # storage 'id' (int PK)
    completed_at: Optional[str] = None  # storage 'completed_at' (datetime → ISO)
    depth_reached: int = 0
    cascade_nodes: list[CascadeNodeResponse] = Field(default_factory=list)
    cascade_edges: list[CascadeEdgeResponse] = Field(default_factory=list)
    cascade_actions: list[dict[str, Any]] = Field(default_factory=list)
    # Phase 126 v16.5 #N.11.b: cancel endpoint + stats fields
    cancelled_at: Optional[str] = None
    triggered_by: Optional[str] = None
    stats: Optional[dict[str, Any]] = None
```

- [ ] **Step 2: Run shared tests to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -v`
Expected: PASS (existing 11 cvg_dto tests still pass; no model regression)

- [ ] **Step 3: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py
git commit -m "feat(lingwen-shared): v16.5 #N.11.b — CascadeRunResponse extended with 10 storage-shape fields"
```

---

### Task A2: Regenerate TS codegen for extended CascadeRunResponse

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` (auto-regenerated)

- [ ] **Step 1: Run codegen**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py`
Expected: TS file regenerated. Open `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` and verify `CascadeRunResponse` interface now includes `cascade_id?: number`, `completed_at?: string`, `depth_reached?: number`, `cascade_nodes: CascadeNodeResponse[]`, `cascade_edges: CascadeEdgeResponse[]`, `cascade_actions: Array<Record<string, any>>`, `cancelled_at?: string`, `triggered_by?: string`, `stats?: Record<string, any> | null`.

- [ ] **Step 2: Run TypeScript type check**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`
Expected: 0 errors (typed wrappers use `CascadeRunResponseDTO` which now includes the new fields)

- [ ] **Step 3: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts
git commit -m "chore(lingwen-shared): v16.5 #N.11.b — TS codegen for extended CascadeRunResponse"
```

---

### Task A3: Add cascade_run_storage_to_presentation adapter

**Files:**
- Modify: `apps/studio_api/cvg_adapter.py` (add new function)

- [ ] **Step 1: Write failing test for cascade_run_storage_to_presentation**

Append to `apps/studio_api/tests/test_cvg_adapter.py`:

```python
def test_cascade_run_storage_to_presentation_basic():
    """Storage CascadeRun → presentation CascadeRunResponse (N.11.b)."""
    from apps.studio_api.cvg_adapter import cascade_run_storage_to_presentation
    from datetime import datetime

    started = datetime(2026, 8, 30, 10, 0, 0)
    completed = datetime(2026, 8, 30, 10, 1, 30)
    storage = {
        "id": 42,
        "ripple_id": "ripple-abc",
        "max_depth": 5,
        "depth_reached": 3,
        "algorithm": "v2_weighted",
        "started_at": started,
        "completed_at": completed,
        "status": "completed",
        "cascade_nodes": [
            {"id": "n1", "dimension": "character", "volume": 1, "chapter": 5, "title": "Lin"},
        ],
        "cascade_edges": [
            {"id": "e1", "from_node_id": "n1", "to_node_id": "n2", "relationship_type": "mentions", "weight": 1.0},
        ],
        "cascade_actions": [{"action": "update", "chapter": 5}],
    }
    result = cascade_run_storage_to_presentation(storage)
    assert result.run_id == "42"
    assert result.ripple_id == "ripple-abc"
    assert result.status == "completed"
    assert result.started_at == started.isoformat()
    assert result.finished_at == completed.isoformat()
    assert result.completed_at == completed.isoformat()
    assert result.cascade_id == 42
    assert result.max_depth == 5
    assert result.depth_reached == 3
    assert result.algorithm == "v2_weighted"
    assert result.nodes_processed == 1
    assert len(result.cascade_nodes) == 1
    assert result.cascade_nodes[0].node_id == "n1"
    assert len(result.cascade_edges) == 1
    assert result.cascade_edges[0].source == "n1"
    assert result.cascade_actions == [{"action": "update", "chapter": 5}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_cascade_run_storage_to_presentation_basic -v`
Expected: FAIL with `ImportError: cannot import name 'cascade_run_storage_to_presentation'`

- [ ] **Step 3: Implement cascade_run_storage_to_presentation**

Append to `apps/studio_api/cvg_adapter.py` (before `cascade_preview_storage_to_presentation`):

```python
def cascade_run_storage_to_presentation(storage: dict[str, Any]) -> CascadeRunResponse:
    """Convert storage CascadeRun dataclass (or dict) → presentation CascadeRunResponse.

    Phase 126 v16.5 #N.11.b: route wire-up for /ripples/cascade/{id}/runs,
    /cascade/runs, /ripples/cascade/{id}/runs/{runId}/cancel.

    Field mapping (storage → presentation):
        id (int)              → run_id (str via str(int)) + cascade_id (int)
        ripple_id             → ripple_id
        max_depth             → max_depth
        depth_reached         → depth_reached
        algorithm             → algorithm
        started_at (datetime) → started_at (ISO string)
        completed_at (datetime) → finished_at + completed_at (both ISO)
        status                → status
        cascade_nodes         → cascade_nodes (via cascade_node_storage_to_presentation)
        cascade_edges         → cascade_edges (via cascade_edge_storage_to_presentation)
        cascade_actions       → cascade_actions (passthrough list)
        nodes_processed       → len(cascade_nodes) (computed)

    NOTE: cancel-endpoint fields (cancelled_at/triggered_by) and stats dict
    are populated by route layer after adapter call (route knows which
    endpoint is calling and can attach endpoint-specific metadata).
    """
    nodes_raw = storage.get("cascade_nodes") or []
    edges_raw = storage.get("cascade_edges") or []
    nodes = [cascade_node_storage_to_presentation(n) for n in nodes_raw]
    edges = [cascade_edge_storage_to_presentation(e) for e in edges_raw]
    started_at = _parse_dt(storage.get("started_at"))
    completed_at_raw = storage.get("completed_at")
    completed_at = _parse_dt(completed_at_raw) if completed_at_raw is not None else None
    return CascadeRunResponse(
        run_id=str(storage.get("id", "")),
        cascade_id=storage.get("id"),
        ripple_id=storage.get("ripple_id", ""),
        max_depth=storage.get("max_depth", 0),
        depth_reached=storage.get("depth_reached", 0),
        algorithm=storage.get("algorithm"),
        started_at=started_at,
        finished_at=completed_at,
        completed_at=completed_at,
        status=storage.get("status", "running"),
        nodes_processed=len(nodes),
        cascade_nodes=nodes,
        cascade_edges=edges,
        cascade_actions=list(storage.get("cascade_actions") or []),
    )
```

Also add `CascadeRunResponse` to the import block at top of `cvg_adapter.py` (around line 60-67):

```python
from lingwen_shared.contracts.python.cvg import (
    CascadeBroadcastLogResponse,  # NEW in N.11.c
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,  # NEW in N.11.b
    RippleDetailResponse,
    RippleListItemResponse,
)
```

Update `__all__` (around line 69-76):

```python
__all__ = [
    "ripple_storage_to_presentation",
    "ripple_detail_storage_to_presentation",
    "cascade_node_storage_to_presentation",
    "cascade_edge_storage_to_presentation",
    "cascade_storage_to_presentation",
    "cascade_preview_storage_to_presentation",
    "cascade_run_storage_to_presentation",  # NEW in N.11.b
    "cascade_broadcast_log_storage_to_presentation",  # NEW in N.11.c
]
```

- [ ] **Step 4: Re-export CascadeBroadcastLogResponse stub**

Since `CascadeBroadcastLogResponse` doesn't exist in lingwen-shared yet, add a placeholder import or defer to Task B1. Simplest: comment out the CascadeBroadcastLogResponse import for now, add it in Task B1.

Replace the import block with:

```python
from lingwen_shared.contracts.python.cvg import (
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,  # NEW in N.11.b
    RippleDetailResponse,
    RippleListItemResponse,
)
```

(`CascadeBroadcastLogResponse` import will be added in Task B1.)

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_cascade_run_storage_to_presentation_basic -v`
Expected: PASS

- [ ] **Step 6: Run all cvg_adapter tests to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v`
Expected: All 9+1=10 tests PASS

- [ ] **Step 7: Commit**

```bash
git add apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "feat(cvg-adapter): v16.5 #N.11.b — cascade_run_storage_to_presentation adapter"
```

---

### Task A4: Update get_ripple_cascade_runs to use cvg_adapter

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:432-453` (get_ripple_cascade_runs endpoint)

- [ ] **Step 1: Add CascadeRunResponse to lingwen-shared import**

Edit `apps/studio_api/routes/cvg.py` line 29-33 to add CascadeRunResponse:

```python
from lingwen_shared.contracts.python.cvg import (
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,  # NEW in N.11.b
    RippleListItemResponse,
)
```

- [ ] **Step 2: Drop CascadeRunResponse from models import**

Edit `apps/studio_api/routes/cvg.py` line 49-61. Remove `CascadeRunResponse` from the `from apps.studio_api.models import (...)` block. Keep `CascadeCancelPayload`, `CascadeCancelRequest`, `CascadeBroadcastLogResponse`, etc.

Result:
```python
from apps.studio_api.models import (
    CascadeBroadcastLogResponse,  # will be dropped in Task B4
    CascadeCancelPayload,
    CascadeCancelRequest,
    ReferenceGraphResponse,
    RippleActionRequest,
    RippleActionResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleRollbackRequest,
    RippleStatsResponse,
)
```

- [ ] **Step 3: Update get_ripple_cascade_runs endpoint**

Edit `apps/studio_api/routes/cvg.py` lines 432-453. Replace the endpoint body:

```python
@app.get(
    "/api/ripples/cascade/{ripple_id}/runs",
    response_model=list[CascadeRunResponse],
)
def get_ripple_cascade_runs(
    ripple_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None, pattern="^(running|completed|cancelled|failed)$"),
    min_depth: int | None = Query(default=None, ge=1, le=10),
    max_depth: int | None = Query(default=None, ge=1, le=10),
    algorithm: str | None = Query(default=None, pattern="^(v1|v2_weighted)$"),
) -> list[CascadeRunResponse]:
    """Phase 9.20: list historical cascade runs for a ripple.
    Phase 9.23: 4 filter query params.
    Phase 126 v16.5 #N.11.b: serves canonical presentation CascadeRunResponse
    via cvg_adapter.cascade_run_storage_to_presentation.
    """
    storage = _app_module._default_storage()
    runs = storage.get_cascade_runs(
        ripple_id, limit=limit, offset=offset,
        status=status, min_depth=min_depth, max_depth=max_depth, algorithm=algorithm,
    )
    return [cvg_adapter.cascade_run_storage_to_presentation(_dataclass_to_dict(r)) for r in runs]


def _dataclass_to_dict(obj: Any) -> dict:
    """Phase 126 v16.5 #N.11.b: helper to convert CascadeRun dataclass to dict.

    Mirrors the inline pattern in get_ripple_cascade endpoint (N.10):
    if dataclass → asdict, if has model_dump → model_dump, else → dict().
    """
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return dict(obj)
```

- [ ] **Step 4: Add helper function near top of file (after imports)**

Place `_dataclass_to_dict` helper at module-level after imports (around line 62, after `from apps.studio_api.routes.ctx import RoutesContext`):

```python
def _dataclass_to_dict(obj: Any) -> dict:
    """Convert dataclass / Pydantic model / mapping → dict for cvg_adapter."""
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return dict(obj)
```

- [ ] **Step 5: Run studio_api tests to verify wire-up**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v -k "cascade_run"`
Expected: Existing cascade-run route tests PASS (any pre-existing tests for this endpoint continue to work because CascadeRunResponse is now from lingwen-shared with all storage fields preserved as defaults)

- [ ] **Step 6: Commit**

```bash
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): v16.5 #N.11.b — get_ripple_cascade_runs uses cvg_adapter"
```

---

### Task A5: Update list_all_cascade_runs to use cvg_adapter

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:455-481` (list_all_cascade_runs endpoint)

- [ ] **Step 1: Update list_all_cascade_runs endpoint body**

Edit `apps/studio_api/routes/cvg.py` lines 455-481. Replace the endpoint body:

```python
@app.get(
    "/api/cascade/runs",
    response_model=list[CascadeRunResponse],
)
def list_all_cascade_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None, pattern="^(running|completed|cancelled|failed)$"),
    min_depth: int | None = Query(default=None, ge=1, le=10),
    max_depth: int | None = Query(default=None, ge=1, le=10),
    algorithm: str | None = Query(default=None, pattern="^(v1|v2_weighted)$"),
    ripple_id: str | None = Query(default=None, min_length=1),
    since_days: int | None = Query(default=None, ge=1, le=3650),
) -> list[CascadeRunResponse]:
    """Phase 9.46 F35: global cascade_runs list across all ripples.
    Phase 126 v16.5 #N.11.b: serves canonical presentation via cvg_adapter.
    """
    storage = _app_module._default_storage()
    runs = storage.list_all_cascade_runs(
        limit=limit,
        offset=offset,
        status=status,
        min_depth=min_depth,
        max_depth=max_depth,
        algorithm=algorithm,
        ripple_id=ripple_id,
        since_days=since_days,
    )
    return [cvg_adapter.cascade_run_storage_to_presentation(_dataclass_to_dict(r)) for r in runs]
```

- [ ] **Step 2: Run studio_api tests to verify wire-up**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v -k "cascade_run or list_all_cascade_runs"`
Expected: PASS (no pre-existing tests for this specific endpoint, but no regression in nearby endpoints)

- [ ] **Step 3: Commit**

```bash
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): v16.5 #N.11.b — list_all_cascade_runs uses cvg_adapter"
```

---

### Task A6: Update post_ripple_cascade_run_cancel to use cvg_adapter

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:483-507` (post_ripple_cascade_run_cancel endpoint)

- [ ] **Step 1: Update post_ripple_cascade_run_cancel endpoint body**

Edit `apps/studio_api/routes/cvg.py` lines 483-507. Replace the endpoint body:

```python
@app.post(
    "/api/ripples/cascade/{ripple_id}/runs/{run_id}/cancel",
    response_model=CascadeRunResponse,
)
def post_ripple_cascade_run_cancel(
    ripple_id: str,
    run_id: int,
    body: CascadeCancelRequest = CascadeCancelRequest(),
) -> CascadeRunResponse:
    """Phase 9.21: cancel a persisted cascade run.
    Side-effect: WS push 'cascade.cancel' event (best-effort, if flipped).
    Phase 126 v16.5 #N.11.b: serves canonical presentation via cvg_adapter.
    """
    storage = _app_module._default_storage()
    try:
        flipped = storage.cancel_cascade_run(run_id, reason=body.reason)
    except KeyError:
        raise HTTPException(404, f"Cascade run {run_id} not found")
    run = storage.get_cascade_run_by_id(run_id)
    if flipped:
        notify_cascade_cancel(CascadeCancelPayload(
            run_id=run_id,
            ripple_id=ripple_id,
            reason=body.reason,
        ))
    # Phase 126 v16.5 #N.11.b: route enriches presentation response with
    # cancel-specific fields (cancelled_at = now, triggered_by = "system").
    from datetime import datetime, timezone
    response = cvg_adapter.cascade_run_storage_to_presentation(_dataclass_to_dict(run))
    response_dict = response.model_dump()
    response_dict["cancelled_at"] = datetime.now(timezone.utc).isoformat()
    response_dict["triggered_by"] = "system"
    return CascadeRunResponse(**response_dict)
```

- [ ] **Step 2: Run studio_api tests to verify wire-up**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v -k "cancel_cascade or cancel_run"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): v16.5 #N.11.b — post_ripple_cascade_run_cancel uses cvg_adapter + cancel metadata"
```

---

### Task A7: Add backend shared tests for extended CascadeRunResponse fields

**Files:**
- Modify: `packages/lingwen-shared/tests/test_cvg_dto.py`

- [ ] **Step 1: Find the existing CascadeRunResponse test in test_cvg_dto.py**

Run: `cd /home/ailearn/projects/LingWen && grep -n "CascadeRunResponse\|test_cascade_run" packages/lingwen-shared/tests/test_cvg_dto.py`
Expected: List existing tests for CascadeRunResponse

- [ ] **Step 2: Append tests for the N.11.b extended fields**

Append to `packages/lingwen-shared/tests/test_cvg_dto.py`:

```python
def test_cascade_run_response_extended_fields():
    """Phase 126 v16.5 #N.11.b: CascadeRunResponse extended with 10 storage-shape fields.

    Verifies safe defaults for backward compat with N.9-era minimal instances.
    """
    from lingwen_shared.contracts.python.cvg import CascadeRunResponse

    # Minimal canonical (N.7 presentation shape)
    minimal = CascadeRunResponse(
        run_id="42",
        ripple_id="ripple-abc",
        status="completed",
        started_at="2026-08-30T10:00:00",
        max_depth=5,
    )
    assert minimal.cascade_id is None
    assert minimal.completed_at is None
    assert minimal.finished_at is None
    assert minimal.depth_reached == 0
    assert minimal.cascade_nodes == []
    assert minimal.cascade_edges == []
    assert minimal.cascade_actions == []
    assert minimal.cancelled_at is None
    assert minimal.triggered_by is None
    assert minimal.stats is None

    # Full storage-shape extended (N.11.b)
    full = CascadeRunResponse(
        run_id="42",
        cascade_id=42,
        ripple_id="ripple-abc",
        max_depth=5,
        depth_reached=3,
        algorithm="v2_weighted",
        started_at="2026-08-30T10:00:00",
        finished_at="2026-08-30T10:01:30",
        completed_at="2026-08-30T10:01:30",
        status="completed",
        nodes_processed=10,
        cancelled_at="2026-08-30T10:02:00",
        triggered_by="system",
        stats={"duration_ms": 90000},
    )
    assert full.cascade_id == 42
    assert full.completed_at == "2026-08-30T10:01:30"
    assert full.cancelled_at == "2026-08-30T10:02:00"
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -v`
Expected: All tests PASS (11 existing + 2 new = 13)

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-shared/tests/test_cvg_dto.py
git commit -m "test(lingwen-shared): v16.5 #N.11.b — extended CascadeRunResponse fields tests"
```

---

### Task A8: Run full backend test suite to verify N.11.b wire-up

- [ ] **Step 1: Run shared + cvg_adapter + studio_api tests**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ apps/studio_api/tests/test_cvg_adapter.py apps/studio_api/tests/ -v`
Expected: All PASS (124 shared + 10 cvg_adapter + ~40 studio_api)

- [ ] **Step 2: Run ruff to verify lint clean**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check packages/lingwen-shared/src apps/studio_api/cvg_adapter.py apps/studio_api/routes/cvg.py apps/studio_api/tests/test_cvg_adapter.py packages/lingwen-shared/tests/test_cvg_dto.py`
Expected: 0 errors

- [ ] **Step 3: Run vue-tsc to verify frontend types still work**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Run vitest to verify no frontend regression**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run`
Expected: 1733 passed + 1 skipped

- [ ] **Step 5: If any ruff violations, fix and commit separately**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check --fix packages/lingwen-shared/src apps/studio_api/cvg_adapter.py apps/studio_api/routes/cvg.py apps/studio_api/tests/test_cvg_adapter.py packages/lingwen-shared/tests/test_cvg_dto.py`
If changes:
```bash
git add -u
git commit -m "chore(ruff): v16.5 #N.11.b — import sort fixes"
```

---

## Part B: CascadeBroadcastLogResponse Wire-up (Tasks B1-B4)

### Task B1: Add CascadeBroadcastLogResponse to lingwen-shared

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` (add new class after CascadeCancelPayload)

- [ ] **Step 1: Add CascadeBroadcastLogResponse class**

Edit `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py`. After `CascadeCancelPayload` class (around line 245), add:

```python
class CascadeBroadcastLogResponse(BaseModel):
    """Cascade-broadcast-log row returned by ``GET /ripples/cascade/{id}/broadcast-log``.

    Phase 126 v16.5 #N.11.c: promoted from storage shape
    (``apps/studio_api/protocols.py::CascadeBroadcastLogResponse``) so
    dashboard consumers can read broadcast-latency history via typed
    wrapper. Field set is identical to storage shape (id/ripple_id/
    latency_ms/created_at) — storage format matches dashboard needs.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    ripple_id: str
    latency_ms: int
    created_at: str
```

- [ ] **Step 2: Add to __all__ export list**

Edit `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` __all__ block (around line 255). Add `CascadeBroadcastLogResponse`:

```python
__all__ = [
    "RippleListItemResponse",
    "RippleDetailResponse",
    "RippleActionResponse",
    "RippleStatsResponse",
    "RippleAuditEntryResponse",
    "CascadeNodeResponse",
    "CascadeEdgeResponse",
    "CascadeResponse",
    "CascadePreviewResponse",
    "ReferenceGraphResponse",
    "CascadeRunResponse",
    "CascadeCancelPayload",
    "CascadeBroadcastLogResponse",  # NEW in N.11.c
]
```

- [ ] **Step 3: Run shared tests to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py
git commit -m "feat(lingwen-shared): v16.5 #N.11.c — CascadeBroadcastLogResponse promoted to canonical"
```

---

### Task B2: Regenerate TS codegen for CascadeBroadcastLogResponse

- [ ] **Step 1: Run codegen**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py`
Expected: TS file regenerated with `CascadeBroadcastLogResponse` interface (4 fields: id, ripple_id, latency_ms, created_at)

- [ ] **Step 2: Verify TS file**

Run: `grep -A 6 "CascadeBroadcastLogResponse" packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts`
Expected: TS interface defined with 4 fields

- [ ] **Step 3: Add typed wrapper re-export**

Edit `packages/dashboard-contracts/src/shared/cvg.ts`. Add `CascadeBroadcastLogResponseDTO` type alias:

```typescript
import type {
  CascadeBroadcastLogResponse,  // NEW in N.11.c
  CascadeCancelPayload,
  /* ...existing imports... */
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/cvg';

export type CascadeBroadcastLogResponseDTO = CascadeBroadcastLogResponse;
```

- [ ] **Step 4: Run vue-tsc to verify types**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts packages/dashboard-contracts/src/shared/cvg.ts
git commit -m "chore(lingwen-shared): v16.5 #N.11.c — TS codegen for CascadeBroadcastLogResponse"
```

---

### Task B3: Add cascade_broadcast_log_storage_to_presentation adapter

**Files:**
- Modify: `apps/studio_api/cvg_adapter.py` (add new function)

- [ ] **Step 1: Add CascadeBroadcastLogResponse to lingwen-shared import in cvg_adapter**

Edit `apps/studio_api/cvg_adapter.py` import block (around line 60-67):

```python
from lingwen_shared.contracts.python.cvg import (
    CascadeBroadcastLogResponse,  # NEW in N.11.c
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,  # NEW in N.11.b
    RippleDetailResponse,
    RippleListItemResponse,
)
```

- [ ] **Step 2: Write failing test for cascade_broadcast_log_storage_to_presentation**

Append to `apps/studio_api/tests/test_cvg_adapter.py`:

```python
def test_cascade_broadcast_log_storage_to_presentation_basic():
    """Storage CascadeBroadcastLogEntry → presentation CascadeBroadcastLogResponse (N.11.c)."""
    from apps.studio_api.cvg_adapter import cascade_broadcast_log_storage_to_presentation

    storage = {
        "id": 7,
        "ripple_id": "ripple-xyz",
        "latency_ms": 150,
        "created_at": "2026-08-30T10:00:00",
    }
    result = cascade_broadcast_log_storage_to_presentation(storage)
    assert result.id == 7
    assert result.ripple_id == "ripple-xyz"
    assert result.latency_ms == 150
    assert result.created_at == "2026-08-30T10:00:00"


def test_cascade_broadcast_log_storage_to_presentation_handles_dict_or_dataclass():
    """Accept both dict and dataclass input (defensive)."""
    from apps.studio_api.cvg_adapter import cascade_broadcast_log_storage_to_presentation
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FakeLogEntry:
        id: int
        ripple_id: str
        latency_ms: int
        created_at: str

    entry = FakeLogEntry(id=1, ripple_id="r1", latency_ms=50, created_at="2026-08-30T10:00:00")
    result = cascade_broadcast_log_storage_to_presentation(entry)
    assert result.id == 1
    assert result.ripple_id == "r1"
    assert result.latency_ms == 50
    assert result.created_at == "2026-08-30T10:00:00"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_cascade_broadcast_log_storage_to_presentation_basic -v`
Expected: FAIL with `ImportError: cannot import name 'cascade_broadcast_log_storage_to_presentation'`

- [ ] **Step 4: Implement cascade_broadcast_log_storage_to_presentation**

Append to `apps/studio_api/cvg_adapter.py` (after `cascade_run_storage_to_presentation`):

```python
def cascade_broadcast_log_storage_to_presentation(
    storage: Any,
) -> CascadeBroadcastLogResponse:
    """Convert storage CascadeBroadcastLogEntry (dataclass or dict) → presentation CascadeBroadcastLogResponse.

    Phase 126 v16.5 #N.11.c: route wire-up for /ripples/cascade/{id}/broadcast-log.

    Field mapping (storage → presentation):
        id (int)            → id
        ripple_id (str)     → ripple_id
        latency_ms (int)    → latency_ms
        created_at (str/datetime) → created_at (ISO string)

    Field set is identical between storage and presentation shape — only
    source-of-truth migration (storage Pydantic class → lingwen-shared
    canonical). No semantic mapping needed.
    """
    if is_dataclass(storage):
        d = asdict(storage)
    elif hasattr(storage, "model_dump"):
        d = storage.model_dump()
    elif isinstance(storage, dict):
        d = storage
    else:
        d = dict(storage)
    return CascadeBroadcastLogResponse(
        id=d.get("id", 0),
        ripple_id=d.get("ripple_id", ""),
        latency_ms=d.get("latency_ms", 0),
        created_at=_parse_dt(d.get("created_at")),
    )
```

Also update the imports at top of `cvg_adapter.py` to include `asdict` and `is_dataclass`:

```python
from dataclasses import asdict, is_dataclass
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_cascade_broadcast_log_storage_to_presentation_basic apps/studio_api/tests/test_cvg_adapter.py::test_cascade_broadcast_log_storage_to_presentation_handles_dict_or_dataclass -v`
Expected: PASS

- [ ] **Step 6: Run all cvg_adapter tests to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v`
Expected: All 12 tests PASS (10 from N.10 + 2 new)

- [ ] **Step 7: Commit**

```bash
git add apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "feat(cvg-adapter): v16.5 #N.11.c — cascade_broadcast_log_storage_to_presentation adapter"
```

---

### Task B4: Update get_ripple_cascade_broadcast_log to use cvg_adapter

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:509-523` (get_ripple_cascade_broadcast_log endpoint)

- [ ] **Step 1: Update lingwen-shared import in routes/cvg.py**

Edit `apps/studio_api/routes/cvg.py` line 29-33:

```python
from lingwen_shared.contracts.python.cvg import (
    CascadeBroadcastLogResponse,  # NEW in N.11.c
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,  # NEW in N.11.b
    RippleListItemResponse,
)
```

- [ ] **Step 2: Drop CascadeBroadcastLogResponse from models import**

Edit `apps/studio_api/routes/cvg.py` line 49-61. Remove `CascadeBroadcastLogResponse` from the models import block.

Result:
```python
from apps.studio_api.models import (
    CascadeCancelPayload,
    CascadeCancelRequest,
    ReferenceGraphResponse,
    RippleActionRequest,
    RippleActionResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleRollbackRequest,
    RippleStatsResponse,
)
```

- [ ] **Step 3: Update get_ripple_cascade_broadcast_log endpoint**

Edit `apps/studio_api/routes/cvg.py` lines 509-523. Replace the endpoint body:

```python
@app.get(
    "/api/ripples/cascade/{ripple_id}/broadcast-log",
    response_model=list[CascadeBroadcastLogResponse],
)
def get_ripple_cascade_broadcast_log(
    ripple_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CascadeBroadcastLogResponse]:
    """Phase 9.44 F33: list persisted cascade WS broadcast latency history.
    Phase 126 v16.5 #N.11.c: serves canonical presentation via cvg_adapter.
    """
    storage = _app_module._default_storage()
    rows = storage.get_cascade_broadcast_logs(
        ripple_id, limit=limit, offset=offset
    )
    return [cvg_adapter.cascade_broadcast_log_storage_to_presentation(r) for r in rows]
```

- [ ] **Step 4: Run studio_api tests to verify wire-up**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v -k "broadcast_log or broadcast"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): v16.5 #N.11.c — get_ripple_cascade_broadcast_log uses cvg_adapter"
```

---

## Part C: `_get_dim` Helper Extraction (Tasks C1-C3)

### Task C1: Write failing test for _get_dim helper

**Files:**
- Modify: `apps/studio_api/tests/test_cvg_adapter.py`

- [ ] **Step 1: Append test for _get_dim helper**

Append to `apps/studio_api/tests/test_cvg_adapter.py`:

```python
def test_get_dim_dict_input():
    """Phase 126 v16.5 #N.11.f: _get_dim reads dimension from dict."""
    from apps.studio_api.cvg_adapter import _get_dim
    assert _get_dim({"dimension": "character"}) == "character"
    assert _get_dim({"dimension": None}) is None
    assert _get_dim({}) is None


def test_get_dim_dataclass_input():
    """Phase 126 v16.5 #N.11.f: _get_dim reads dimension from dataclass via getattr."""
    from apps.studio_api.cvg_adapter import _get_dim
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FakeNode:
        dimension: str

    assert _get_dim(FakeNode(dimension="setting")) == "setting"


def test_get_dim_unknown_object_uses_getattr_default():
    """Phase 126 v16.5 #N.11.f: _get_dim defaults to None for objects without dimension."""
    from apps.studio_api.cvg_adapter import _get_dim

    class RandomObj:
        pass

    assert _get_dim(RandomObj()) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_get_dim_dict_input -v`
Expected: FAIL with `ImportError: cannot import name '_get_dim' from 'apps.studio_api.cvg_adapter'`

- [ ] **Step 3: Commit failing tests**

```bash
git add apps/studio_api/tests/test_cvg_adapter.py
git commit -m "test(cvg-adapter): v16.5 #N.11.f — _get_dim helper tests (RED)"
```

---

### Task C2: Extract _get_dim helper and refactor call sites

**Files:**
- Modify: `apps/studio_api/cvg_adapter.py` (add helper, refactor 3 call sites)

- [ ] **Step 1: Add _get_dim helper after _parse_dt**

Edit `apps/studio_api/cvg_adapter.py` after `_parse_dt` (around line 103):

```python
def _get_dim(node: Any) -> Optional[str]:
    """Polymorphic accessor for cascade node ``dimension`` field.

    Phase 126 v16.5 #N.11.f: DRY helper for cascade_preview_storage_to_presentation.
    Replaces 3x repeated ``n.get("dimension") if isinstance(n, dict) else
    getattr(n, "dimension", None)`` inline expressions.

    Used for both dict (from asdict() output) and dataclass (from
    CascadedRipple.cascade_nodes) inputs.
    """
    if isinstance(node, dict):
        return node.get("dimension")
    return getattr(node, "dimension", None)
```

- [ ] **Step 2: Refactor 3 call sites in cascade_preview_storage_to_presentation**

Edit `apps/studio_api/cvg_adapter.py` lines 256-264. Replace the 3 inline expressions:

```python
    affected_chapters = sum(
        1 for n in nodes_raw if _get_dim(n) in ("plot_point", "foreshadow")
    )
    affected_characters = sum(
        1 for n in nodes_raw if _get_dim(n) == "character"
    )
    affected_settings = sum(
        1 for n in nodes_raw if _get_dim(n) == "setting"
    )
```

- [ ] **Step 3: Run _get_dim tests to verify they pass**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v -k "get_dim"`
Expected: PASS (3 new tests)

- [ ] **Step 4: Run all cvg_adapter tests to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v`
Expected: All 15 tests PASS (12 from Parts A+B + 3 new)

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "refactor(cvg-adapter): v16.5 #N.11.f — extract _get_dim helper (DRY 3 inline dim accesses)"
```

---

### Task C3: Run full backend test suite to verify Part C

- [ ] **Step 1: Run shared + cvg_adapter + studio_api tests**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ apps/studio_api/tests/test_cvg_adapter.py apps/studio_api/tests/ -v`
Expected: All PASS

- [ ] **Step 2: Run ruff to verify lint clean**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py`
Expected: 0 errors

---

## Part D: protocols.py CVG Cleanup (Tasks D1-D3)

### Task D1: Drop 5 unused imports from helpers/cvg.py

**Files:**
- Modify: `apps/studio_api/helpers/cvg.py:14-26` (import block)

- [ ] **Step 1: Verify which imports are unused**

Run: `cd /home/ailearn/projects/LingWen && grep -E "\b(CascadePreviewResponse|CascadeResponse|CascadeRunResponse|RippleActionResponse|RippleStatsResponse)\b" apps/studio_api/helpers/cvg.py | grep -v "^from apps.studio_api.protocols"`
Expected: No usages of these 5 names elsewhere in helpers/cvg.py (only in the import block)

- [ ] **Step 2: Edit import block to drop unused imports**

Edit `apps/studio_api/helpers/cvg.py` lines 14-26:

```python
from apps.studio_api.protocols import (
    CascadeEdgeResponse,        # used by _build_reference_graph_response
    CascadeNodeResponse,        # used by _build_reference_graph_response
    ReferenceGraphResponse,     # used by _build_reference_graph_response
    RippleAuditEntryResponse,   # used by _audit_to_response
    RippleDetailResponse,       # used by _ripple_to_detail
    RippleListItemResponse,     # used by _ripple_to_list_item, _ripple_list_items
)
```

Removed: `CascadePreviewResponse`, `CascadeResponse`, `CascadeRunResponse`, `RippleActionResponse`, `RippleStatsResponse`.

- [ ] **Step 3: Verify no breakage by importing the module**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -c "from apps.studio_api.helpers import cvg; print('Import OK:', cvg.__file__)"`
Expected: `Import OK: /home/ailearn/projects/LingWen/apps/studio_api/helpers/cvg.py`

- [ ] **Step 4: Run studio_api tests to verify no regression**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/helpers/cvg.py
git commit -m "refactor(helpers): v16.5 #N.11.a — drop 5 unused CVG model imports from protocols.py"
```

---

### Task D2: Run full backend + frontend test suite to verify Part D

- [ ] **Step 1: Run shared + cvg_adapter + studio_api tests**

Run: `cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ apps/studio_api/tests/test_cvg_adapter.py apps/studio_api/tests/ -v`
Expected: All PASS

- [ ] **Step 2: Run ruff**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check apps/studio_api/helpers/cvg.py`
Expected: 0 errors

---

## Part E: Handoff + CLAUDE.md Closure (Tasks E1-E2)

### Task E1: Write handoff doc

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup-handoff.md`

- [ ] **Step 1: Write handoff doc**

Create `docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup-handoff.md` with content matching the structure of `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n10-cvg-cascade-wireup-chapter-reexport-protocols-cleanup-status-promotion-handoff.md`:

Sections:
1. **Summary**: 4 NEW commits, 6/6 CVG cascade endpoints now serve canonical presentation shape
2. **Commits**: T1-T13 with type/scope/subject
3. **Architecture invariants**: 3 NEW (21-23) — CascadeRunResponse extended with 10 fields, CascadeBroadcastLogResponse promoted, _get_dim helper extracted
4. **Tests**: 124+2+2 backend / 9+5+1 cvg_adapter / 1733 vitest / vue-tsc 0 / ruff 0
5. **Lessons**: 5-6 lessons learned
6. **Carryover to v16.5 #N.12+**: ReferenceGraphResponse full migration, dashboard cascade field migration, impact_score storage drift

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/handoffs/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup-handoff.md
git commit -m "docs(phase-126): v16.5 #N.11 — handoff + CLAUDE.md closure"
```

---

### Task E2: Update CLAUDE.md + verify all gates

- [ ] **Step 1: Update CLAUDE.md v16.5 #N.11 entry**

Edit `CLAUDE.md` to add v16.5 #N.11 closure entry at the top of the "更新" history. Mirror the N.10 entry structure. Include:
- Part A (N.11.b CascadeRunResponse wire-up): 4 endpoints (3 + 1 for broadcast log) updated
- Part B (N.11.c CascadeBroadcastLogResponse promotion): new DTO in lingwen-shared
- Part C (N.11.f _get_dim helper): DRY 3 inline dim accesses
- Part D (N.11.a protocols.py cleanup): 5 unused imports dropped
- 3 NEW architecture invariants (#21/#22/#23)
- Updated carryover to N.12+

- [ ] **Step 2: Run ALL verification gates**

```bash
# Backend shared
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -v
# cvg_adapter
cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v
# studio_api
cd /home/ailearn/projects/LingWen && env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -v
# vitest
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run
# vue-tsc
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit
# ruff
cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m ruff check .
```

Expected:
- 126 backend shared tests (124 + 2 new)
- 15 cvg_adapter tests (10 from N.10 + 5 new)
- ~42 studio_api tests
- 1733 vitest + 1 skipped
- vue-tsc 0 errors
- ruff 0 errors

- [ ] **Step 3: Commit CLAUDE.md update**

```bash
git add CLAUDE.md
git commit -m "docs: v16.5 #N.11 — CLAUDE.md closure"
```

- [ ] **Step 4: Verify final commit count + open PR**

```bash
git log --oneline -20
gh pr create --base master --head phase-126-v16-5-n11 --title "Phase 126 v16.5 #N.11 — Cascade Runs + Broadcast Log wire-up" --body "..."
```

---

## Self-Review

**Spec coverage:**
- ✅ N.11.b (CascadeRunResponse wire-up): Tasks A1-A7 cover extend Pydantic → regen TS → adapter → 3 endpoint wire-ups → tests → verification
- ✅ N.11.c (CascadeBroadcastLogResponse wire-up): Tasks B1-B4 cover add Pydantic → regen TS → adapter → endpoint wire-up
- ✅ N.11.f (_get_dim helper): Tasks C1-C3 cover RED tests → GREEN helper + refactor → verification
- ✅ N.11.a (protocols.py cleanup): Tasks D1-D2 cover import removal + verification

**Placeholder scan:** No TBD/TODO/"implement later"/"similar to Task X" found. All code blocks are complete.

**Type consistency:**
- `cascade_run_storage_to_presentation` returns `CascadeRunResponse` (matches lingwen-shared Pydantic)
- `cascade_broadcast_log_storage_to_presentation` returns `CascadeBroadcastLogResponse` (matches lingwen-shared Pydantic)
- `_get_dim` signature: `node: Any -> Optional[str]` (used 3 times in cascade_preview_storage_to_presentation)
- `_dataclass_to_dict` defined once in routes/cvg.py, used by 3 endpoints (get_ripple_cascade_runs, list_all_cascade_runs, post_ripple_cascade_run_cancel)
- Helper test naming matches existing pattern (`test_<helper_name>_<scenario>`)

**Plan check against carryover:**
- #N.11.a — scope reduced per CLAUDE.md update: 5 unused imports dropped (not full ReferenceGraphResponse migration; deferred to N.12+)
- #N.11.b — full wire-up with 3 endpoints + 10 storage fields extended
- #N.11.c — full wire-up with new Pydantic promotion
- #N.11.f — _get_dim helper extracted with 3 inline dim accesses consolidated
- #N.11.d, #N.11.e — deferred to N.12+ per scope decision

**Estimated commits: ~12 atomic commits**
- Part A: 7 commits (T1, T2, T3 test + impl, T4, T5, T6, T7, T8 fixup if needed)
- Part B: 5 commits (T1, T2, T3 test + impl, T4)
- Part C: 3 commits (T1 test, T2 impl+refactor, T3 fixup if needed)
- Part D: 1 commit
- Part E: 2 commits (handoff, CLAUDE.md)
- Total: ~18 commits (rough estimate; some tasks may merge)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-08-31-phase-126-v16-5-n11-cascade-runs-and-broadcast-log-wireup.md`.**

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Best for this plan because each task is mechanical (Pydantic extension → TS regen → adapter → wire-up) and benefits from fresh context per file.

2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Best when commit granularity is coarser (1 commit per Part) and verification gates run between Parts.

**Recommended for N.11:** Option 1 (Subagent-Driven) — 18 commits × 1 subagent per task = clean review/rollback surface, mirrors N.10 execution pattern.

**Which approach?**

If subagent-driven: invoke `superpowers:subagent-driven-development` skill next.
If inline: invoke `superpowers:executing-plans` skill next.
