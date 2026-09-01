# Phase 126 v16.5 #N.11.d/e/g — CVG Cleanup Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the three CVG-related carryovers from v16.5 #N.10/N.11 that block PYDANTIC-DRIFT cleanup: impact_score exposure on presentation shape, dashboard cascade field naming migration, and ReferenceGraphResponse full migration to canonical lingwen-shared.

**Architecture:** All three tasks follow the established Phase 126 pattern — backend `cvg_adapter` boundary is the SOLE place where storage → presentation mapping happens; routes call the adapter; dashboard reads canonical presentation shape via typed wrapper. No new architecture; just closing the remaining 3 holes in the existing pipeline.

**Tech Stack:** Pydantic v2 + TypeScript codegen + cvg_adapter.py + Vue 3 dashboard typed wrappers.

---

## Scope & Sequencing

| Task | Title | Commits | Blocked by |
|------|-------|---------|------------|
| T1 | N.11.d: impact_score drift — extend RippleListItemResponse + adapter + drop hybrid | 4-5 | — |
| T2 | N.11.e: dashboard cascade fields — `cascadeGraphUtils.js` + `useWorkflowSocket.js` + `cascadeGraphUtils.test.js` | 3-4 | T1 |
| T3 | N.11.g: ReferenceGraphResponse full migration — adapter + endpoint + storage class removal | 4-5 | T1 |

## Architectural invariants this plan will enforce (3 NEW, 28 total)

- **#26** `RippleListItemResponse` (lingwen-shared) includes `impact_score` so dashboard filter/sort reads via typed wrapper without hybrid storage-roundtrip in route handler.
- **#27** Dashboard cascade consumers (`cascadeGraphUtils.js` + `useWorkflowSocket.js` + composables) use presentation-shape field names (`node_id`/`chapter_id`/`source`/`target`/`max_depth`) — no inline storage-shape access.
- **#28** `GET /api/cvg/reference-graph` returns canonical presentation-shape `ReferenceGraphResponse` via `cvg_adapter.reference_graph_storage_to_presentation`; storage-shape `ReferenceGraphResponse` class removed from `apps/studio_api/protocols.py`.

## Verification gates (must be green at every commit boundary)

```
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py -q
cd apps/dashboard && pnpm vitest run && pnpm tsc --noEmit && pnpm eslint .
ruff check packages/lingwen-shared/src apps/studio_api/cvg_adapter.py apps/studio_api/routes/cvg.py apps/studio_api/protocols.py apps/studio_api/helpers/cvg.py
```

---

## Task T1: N.11.d — impact_score storage-vs-presentation drift

**Root cause:** `RippleListItemResponse` (lingwen-shared, presentation) lacks `impact_score`. `apps/studio_api/routes/cvg.py:list_ripples` does a hybrid: filters/sorts on storage shape (which has the field), then converts. Dashboard (`RippleCard.vue`, `RippleFilter.vue`) reads `ripple.impact_score` directly off the typed wrapper.

**Fix:** Extend presentation `RippleListItemResponse` with `impact_score`. Adapter populates it. Route filters/sorts on presentation shape. Drop hybrid path.

### T1.1 — RED test: extended RippleListItemResponse has impact_score

**Files:**
- Modify: `packages/lingwen-shared/tests/test_cvg_dto.py`

- [ ] **Step 1: Add the test**

Open `packages/lingwen-shared/tests/test_cvg_dto.py`. Find the existing RippleListItemResponse test (test_ripple_list_item_response or similar). Append a new test:

```python
def test_ripple_list_item_response_includes_impact_score():
    """N.11.d: dashboard filter/sort needs impact_score on presentation shape."""
    from lingwen_shared.contracts.python.cvg import RippleListItemResponse
    obj = RippleListItemResponse(
        ripple_id="r1",
        chapter_id=1,
        title="t",
        status="pending",
        source_volume=1,
        impact_volumes=[1],
        created_at="2026-01-01T00:00:00Z",
        impact_score=0.42,
    )
    assert obj.impact_score == 0.42
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py::test_ripple_list_item_response_includes_impact_score -v --rootdir=packages/lingwen-shared
```

Expected: FAIL with `ValidationError: impact_score` (field missing).

### T1.2 — GREEN: extend RippleListItemResponse

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py`

- [ ] **Step 1: Add impact_score field**

In `RippleListItemResponse` (around line 37), add field after `applies_count`:

```python
    # Phase 126 v16.5 #N.11.d: expose impact_score so dashboard filter/sort
    # reads via typed wrapper without hybrid storage-roundtrip.
    impact_score: Optional[float] = None
```

- [ ] **Step 2: Run test to verify it passes**

```bash
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py::test_ripple_list_item_response_includes_impact_score -v --rootdir=packages/lingwen-shared
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py packages/lingwen-shared/tests/test_cvg_dto.py
git commit -m "feat(lingwen-shared): N.11.d RippleListItemResponse extends with impact_score"
```

### T1.3 — TS codegen regenerated

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` (auto-generated)

- [ ] **Step 1: Run codegen**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
```

Verify `cvg.ts` now has `impact_score?: number | null` on `RippleListItemResponse`.

- [ ] **Step 2: Verify dashboard-contracts re-exports**

```bash
grep -n "impact_score" packages/dashboard-contracts/src/shared/cvg.ts
```

Expected: re-export picks it up automatically (no edit needed if `cvg.ts` re-exports types from lingwen-shared).

- [ ] **Step 3: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts packages/dashboard-contracts/src/shared/cvg.ts
git commit -m "chore(lingwen-shared): N.11.d TS codegen for impact_score extension"
```

### T1.4 — cvg_adapter populates impact_score

**Files:**
- Modify: `apps/studio_api/cvg_adapter.py:125-158`

- [ ] **Step 1: RED test**

Open `apps/studio_api/tests/test_cvg_adapter.py`. Find `ripple_storage_to_presentation` test. Append:

```python
def test_ripple_storage_to_presentation_propagates_impact_score():
    """N.11.d: adapter maps storage impact_score → presentation."""
    from apps.studio_api.cvg_adapter import ripple_storage_to_presentation
    storage = {
        "ripple_id": "r1",
        "source_chapter": 10,
        "target_chapter": 11,
        "trigger_volume": 1,
        "status": "pending",
        "created_at": "2026-01-01T00:00:00Z",
        "impact_score": 0.85,
    }
    result = ripple_storage_to_presentation(storage)
    assert result.impact_score == 0.85
```

- [ ] **Step 2: Run test to verify it fails**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_ripple_storage_to_presentation_propagates_impact_score -v
```

Expected: FAIL (current adapter doesn't pass impact_score).

- [ ] **Step 3: GREEN impl**

In `cvg_adapter.py` `ripple_storage_to_presentation`, append `impact_score` to the `RippleListItemResponse(...)` constructor:

```python
        created_at=_parse_dt(storage.get("created_at")),
        impact_score=storage.get("impact_score"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_ripple_storage_to_presentation_propagates_impact_score -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "feat(cvg-adapter): N.11.d ripple_storage_to_presentation propagates impact_score"
```

### T1.5 — Route drops hybrid storage-roundtrip

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:82-118` (list_ripples)

- [ ] **Step 1: Refactor list_ripples to sort/filter on presentation shape**

The current code filters/sorts on storage, then converts. After T1.4, the presentation shape has impact_score. Refactor:

```python
        storage = _app_module._default_storage()
        ripples = storage.get_ripples(
            status=status_filter, volume=volume, limit=limit, offset=offset
        )
        items = [
            cvg_adapter.ripple_storage_to_presentation(item.model_dump())
            for item in _ripple_list_items(ripples, storage)
        ]
        if min_score is not None:
            items = [i for i in items if (i.impact_score or 0.0) >= min_score]
        if sort_by == "impact_score":
            items.sort(key=lambda i: i.impact_score or 0.0, reverse=True)
        return items
```

(removes inline comment about hybrid; adds `or 0.0` since impact_score is `Optional[float]`.)

- [ ] **Step 2: Run route test suite**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_route.py -v
```

Expected: 0 regression.

- [ ] **Step 3: Commit**

```bash
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): N.11.d list_ripples drops hybrid storage-roundtrip"
```

---

## Task T2: N.11.e — Dashboard cascade field migration

**Root cause:** `cascadeGraphUtils.js` + `useWorkflowSocket.js` access `cascade.cascade_nodes`/`cascade.cascade_edges`/edge `from_node_id`/`to_node_id`/node `id`/`chapter`/`volume`/`depth_reached` — these are storage-shape names. After cvg_adapter (N.10 onward), the typed wrapper returns presentation-shape: `node_id`/`chapter_id`/`source`/`target`/`max_depth`. The current code works by accident because the storage and presentation cascades happen to share names like `cascade_nodes`/`cascade_edges`/`cascade_actions` — but individual node/edge fields are still storage-shape.

**Fix:** Update `cascadeGraphUtils.js` to read presentation-shape fields. Update `useWorkflowSocket.js` to type the dict as presentation shape. Add a test that exercises the new field access.

### T2.1 — Update cascadeGraphUtils.js field accesses

**Files:**
- Modify: `apps/dashboard/src/utils/cascadeGraphUtils.js`

- [ ] **Step 1: Patch field accesses**

In `buildCascadeGraphSeriesData` (around line 145-205):
- Line 146: `(cascade?.cascade_nodes || []).slice(0, 100)` — keep (presentation shape same name).
- Line 147-150: edge mapping — `e.from_node_id` → `e.source`, `e.to_node_id` → `e.target` (presentation shape).
- Line 152: `cascade?.cascade_actions` — keep.
- Line 156-160: `n.id` → `n.node_id`, `${n.id}` → `${n.node_id}`, `n.chapter` → `n.chapter_id`, `n.volume` → `n.volume` (storage shape had volume=1 by default; presentation also has volume).

In `buildCascadeChartOption` (around line 212-217):
- Line 214: `cascade?.depth_reached ?? 0` → `cascade?.max_depth ?? 0` (presentation uses `max_depth`).

- [ ] **Step 2: Commit**

```bash
git add apps/dashboard/src/utils/cascadeGraphUtils.js
git commit -m "refactor(dashboard): N.11.e cascadeGraphUtils uses presentation-shape fields"
```

### T2.2 — UseWorkflowSocket declares presentation shape

**Files:**
- Modify: `apps/dashboard/src/composables/useWorkflowSocket.js:20`

- [ ] **Step 1: Inspect JSDoc**

The dict shape listed in the JSDoc at line 20 includes `cascade_edge_count, depth_reached, bfs_algorithm_version` (storage-shape names). Update to use presentation-shape names:

```js
 * Cascade graph payload (presentation shape — returned by cvg_adapter):
 *   { nodes: [{node_id, chapter_id, title, status, depth, ripple_id, volume}],
 *     edges: [{source, target, relation, weight}],
 *     cascade_actions: [...], generated_at, bfs_algorithm_version, max_depth }
```

- [ ] **Step 2: Commit**

```bash
git add apps/dashboard/src/composables/useWorkflowSocket.js
git commit -m "refactor(dashboard): N.11.e useWorkflowSocket JSDoc reflects presentation shape"
```

### T2.3 — Test exercises presentation-shape field access

**Files:**
- Modify: `apps/dashboard/tests/unit/utils/cascadeGraphUtils.spec.js` (or create if absent)

- [ ] **Step 1: Inspect existing tests**

```bash
ls apps/dashboard/tests/unit/utils/cascadeGraphUtils*
```

If no spec exists, create one. Add or extend a test case:

```javascript
import { describe, it, expect } from 'vitest'
import { buildCascadeGraphSeriesData, buildCascadeChartOption } from '@/utils/cascadeGraphUtils.js'

describe('cascadeGraphUtils — presentation shape (N.11.e)', () => {
  const presentationCascade = {
    ripple_id: 'r1',
    cascade_nodes: [{ node_id: 'n1', chapter_id: 5, title: 'X', status: 'applied', depth: 0, volume: 1 }],
    cascade_edges: [{ source: 'n1', target: 'n2', relation: 'reference', weight: 0.6 }],
    cascade_actions: [],
    max_depth: 3,
  }

  it('reads node_id/chapter_id from presentation nodes', () => {
    const { nodes } = buildCascadeGraphSeriesData(presentationCascade, 'depth-layer', false)
    expect(nodes[0].id).toBe('n1')
    expect(nodes[0].name).toContain('c5')
  })

  it('reads source/target from presentation edges', () => {
    const { edges } = buildCascadeGraphSeriesData(presentationCascade, 'depth-layer', false)
    expect(edges[0].source).toBe('n1')
    expect(edges[0].target).toBe('n2')
  })

  it('reads max_depth from presentation cascade', () => {
    const option = buildCascadeChartOption(presentationCascade, 'depth-layer', false)
    expect(option.title.text).toContain('depth 3')
  })
})
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd apps/dashboard
pnpm vitest run tests/unit/utils/cascadeGraphUtils.spec.js 2>/dev/null || pnpm vitest run tests/unit/utils/
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/tests/unit/utils/cascadeGraphUtils.spec.js
git commit -m "test(dashboard): N.11.e cascadeGraphUtils presentation-shape coverage"
```

---

## Task T3: N.11.g — ReferenceGraphResponse full migration

**Root cause:** Storage `ReferenceGraphResponse` (apps/studio_api/protocols.py:851) uses storage `CascadeNodeResponse` (with `id`/`chapter`/`volume`) + storage `CascadeEdgeResponse` (with `from_node_id`/`to_node_id`) + has `total_node_count/total_edge_count/truncated` fields but NO `by_dimension`. Presentation `ReferenceGraphResponse` (lingwen-shared) uses generic dicts + `total_nodes/total_edges/by_dimension`. There's NO adapter yet. Endpoint `GET /api/cvg/reference-graph` returns storage shape.

**Fix:** Add `reference_graph_storage_to_presentation` adapter + extend presentation shape with `truncated` field + migrate endpoint + remove storage class.

### T3.1 — Extend presentation ReferenceGraphResponse with truncated

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py:199-208`

- [ ] **Step 1: RED test**

In `packages/lingwen-shared/tests/test_cvg_dto.py`, append:

```python
def test_reference_graph_response_includes_truncated_flag():
    """N.11.g: storage shape has truncated; presentation should too."""
    from lingwen_shared.contracts.python.cvg import ReferenceGraphResponse
    obj = ReferenceGraphResponse(
        nodes=[],
        edges=[],
        total_nodes=10,
        total_edges=5,
        truncated=True,
        by_dimension={"character": 3},
    )
    assert obj.truncated is True
    assert obj.by_dimension == {"character": 3}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py::test_reference_graph_response_includes_truncated_flag -v --rootdir=packages/lingwen-shared
```

Expected: FAIL with `truncated` not a field.

- [ ] **Step 3: GREEN: add truncated field**

In `ReferenceGraphResponse`, add after `by_dimension`:

```python
    truncated: bool = False
```

- [ ] **Step 4: Run test**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py packages/lingwen-shared/tests/test_cvg_dto.py
git commit -m "feat(lingwen-shared): N.11.g ReferenceGraphResponse includes truncated flag"
```

### T3.2 — TS codegen

- [ ] **Step 1: Run codegen + commit**

```bash
/home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts packages/dashboard-contracts/src/shared/cvg.ts
git commit -m "chore(lingwen-shared): N.11.g TS codegen for ReferenceGraphResponse truncated"
```

### T3.3 — Adapter for ReferenceGraphResponse

**Files:**
- Modify: `apps/studio_api/cvg_adapter.py`

- [ ] **Step 1: RED test**

In `apps/studio_api/tests/test_cvg_adapter.py`, append:

```python
def test_reference_graph_storage_to_presentation():
    """N.11.g: storage ReferenceGraphResponse → presentation shape via adapter."""
    from apps.studio_api.cvg_adapter import reference_graph_storage_to_presentation
    storage = {
        "nodes": [
            {"id": "n1", "chapter": 5, "dimension": "character", "volume": 1},
            {"id": "n2", "chapter": 8, "dimension": "foreshadow", "volume": 1},
            {"id": "n3", "chapter": 9, "dimension": "character", "volume": 1},
        ],
        "edges": [
            {"from_node_id": "n1", "to_node_id": "n2", "relationship_type": "support"},
        ],
        "total_node_count": 3,
        "total_edge_count": 5,
        "truncated": False,
    }
    result = reference_graph_storage_to_presentation(storage)
    assert result.total_nodes == 3
    assert result.total_edges == 5
    assert result.truncated is False
    assert result.by_dimension == {"character": 2, "foreshadow": 1}
    # nodes mapped to presentation
    assert result.nodes[0]["node_id"] == "n1"
    assert result.nodes[0]["chapter_id"] == 5
    assert result.edges[0]["source"] == "n1"
    assert result.edges[0]["target"] == "n2"
    assert result.edges[0]["relation"] == "support"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_reference_graph_storage_to_presentation -v
```

Expected: FAIL (import error or not implemented).

- [ ] **Step 3: GREEN implementation**

In `cvg_adapter.py`, append after `cascade_broadcast_log_storage_to_presentation`:

```python
def reference_graph_storage_to_presentation(
    storage: dict[str, Any],
) -> "ReferenceGraphResponse":
    """Convert storage ReferenceGraphResponse → canonical presentation shape.

    Phase 126 v16.5 #N.11.g: GET /api/cvg/reference-graph endpoint migration.
    Field mapping (storage → presentation):
        CascadeNodeResponse (storage) → dict (presentation):
            id → node_id, chapter → chapter_id
            + pass through dimension, volume, title, payload
        CascadeEdgeResponse (storage) → dict (presentation):
            from_node_id → source, to_node_id → target
            relationship_type → relation
        total_node_count → total_nodes
        total_edge_count → total_edges
        truncated → truncated (passthrough)
        by_dimension → COMPUTED from node.dimension counts (not in storage)
    """
    nodes_raw = storage.get("nodes", [])
    edges_raw = storage.get("edges", [])
    by_dimension: dict[str, int] = {}
    for n in nodes_raw:
        if isinstance(n, dict):
            dim = n.get("dimension")
        else:
            dim = getattr(n, "dimension", None)
        if dim:
            by_dimension[dim] = by_dimension.get(dim, 0) + 1

    def _node_to_presentation_dict(n: Any) -> dict[str, Any]:
        if isinstance(n, dict):
            return {
                "node_id": n.get("id") or n.get("node_id", ""),
                "chapter_id": n.get("chapter") or n.get("chapter_id", 0),
                "title": n.get("title"),
                "dimension": n.get("dimension"),
                "volume": n.get("volume", 1),
            }
        return {
            "node_id": getattr(n, "id", "") or getattr(n, "node_id", ""),
            "chapter_id": getattr(n, "chapter", 0) or getattr(n, "chapter_id", 0),
            "title": getattr(n, "title", None),
            "dimension": getattr(n, "dimension", None),
            "volume": getattr(n, "volume", 1),
        }

    def _edge_to_presentation_dict(e: Any) -> dict[str, Any]:
        if isinstance(e, dict):
            return {
                "source": e.get("source") or e.get("from_node_id", ""),
                "target": e.get("target") or e.get("to_node_id", ""),
                "relation": (
                    e.get("relation")
                    or e.get("relationship_type")
                    or e.get("relationship")
                    or "reference"
                ),
                "weight": e.get("weight"),
            }
        return {
            "source": getattr(e, "source", "") or getattr(e, "from_node_id", ""),
            "target": getattr(e, "target", "") or getattr(e, "to_node_id", ""),
            "relation": (
                getattr(e, "relation", None)
                or getattr(e, "relationship_type", None)
                or "reference"
            ),
            "weight": getattr(e, "weight", None),
        }

    return ReferenceGraphResponse(
        nodes=[_node_to_presentation_dict(n) for n in nodes_raw],
        edges=[_edge_to_presentation_dict(e) for e in edges_raw],
        total_nodes=storage.get("total_nodes") or storage.get("total_node_count", 0),
        total_edges=storage.get("total_edges") or storage.get("total_edge_count", 0),
        truncated=bool(storage.get("truncated", False)),
        by_dimension=by_dimension or None,
    )
```

Update `__all__` list — append `"reference_graph_storage_to_presentation"`.

Update import block — add `ReferenceGraphResponse` to the existing lingwen-shared imports (it's already imported in cvg.py but check `__all__`).

- [ ] **Step 4: Run test**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_adapter.py::test_reference_graph_storage_to_presentation -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "feat(cvg-adapter): N.11.g reference_graph_storage_to_presentation"
```

### T3.4 — Migrate GET /api/cvg/reference-graph endpoint

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:134-150` (get_reference_graph)
- Modify: `apps/studio_api/helpers/cvg.py:_build_reference_graph_response` (preserve for storage-side use)

- [ ] **Step 1: Update endpoint to use canonical presentation shape**

In `routes/cvg.py`, change imports and the endpoint:

```python
from lingwen_shared.contracts.python.cvg import ReferenceGraphResponse as CanonicalReferenceGraphResponse
```

(Or import from `apps.studio_api.cvg_adapter` if you re-export.) Then in the endpoint:

```python
    @app.get("/api/cvg/reference-graph", response_model=CanonicalReferenceGraphResponse)
    def get_reference_graph(
        volume: Optional[int] = Query(None, ge=1, le=99),
        dimension: Optional[str] = Query(
            None,
            pattern="^(character|foreshadow|setting|plot_point)$",
        ),
        limit: int = Query(200, ge=1, le=500),
    ) -> CanonicalReferenceGraphResponse:
        """Phase 9.41 F30 / N.11.g: persisted reference graph for dashboard ImpactGraph.

        Phase 126 v16.5 #N.11.g: returns canonical presentation shape via
        cvg_adapter.reference_graph_storage_to_presentation.
        """
        storage = _app_module._default_storage()
        storage_response = _build_reference_graph_response(
            storage, volume=volume, dimension=dimension, limit=limit,
        )
        return cvg_adapter.reference_graph_storage_to_presentation(
            storage_response.model_dump()
        )
```

- [ ] **Step 2: Verify route tests pass**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_route.py -v
```

Expected: 0 regression.

- [ ] **Step 3: Commit**

```bash
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): N.11.g get_reference_graph returns canonical presentation shape"
```

### T3.5 — Remove storage-shape ReferenceGraphResponse class

**Files:**
- Modify: `apps/studio_api/protocols.py:849-858`
- Modify: `apps/studio_api/models/__init__.py` (if re-export present)
- Modify: `apps/studio_api/app.py` (if direct import)

- [ ] **Step 1: Verify nothing imports storage ReferenceGraphResponse from protocols**

```bash
grep -rn "from apps.studio_api.models import.*ReferenceGraph\|from apps.studio_api.protocols import.*ReferenceGraph\|protocols.ReferenceGraph" apps/ --include="*.py" | grep -v __pycache__
```

Expected: zero hits after T3.4 (the endpoint now uses the canonical one).

- [ ] **Step 2: Delete storage class**

In `apps/studio_api/protocols.py`, remove lines 849-858 (the `ReferenceGraphResponse` class block + comment).

In `apps/studio_api/models/__init__.py`, remove the `ReferenceGraphResponse` re-export (line 282).

- [ ] **Step 3: Run tests to verify no breakage**

```bash
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -q
```

Expected: PASS (storage class becomes truly dead after T3.4 wire-up).

- [ ] **Step 4: Commit**

```bash
git add apps/studio_api/protocols.py apps/studio_api/models/__init__.py apps/studio_api/app.py
git commit -m "refactor(studio-api): N.11.g remove storage-shape ReferenceGraphResponse class"
```

---

## Self-review checklist (run before merging)

- [ ] All 3 NEW invariants (#26, #27, #28) are testable in CI.
- [ ] No N.10/N.11 tests regress.
- [ ] `vue-tsc` 0 / ruff 0 / vitest 1733+ tests still pass.
- [ ] Cleanup of dead storage class is atomic with wire-up (T3.4+T3.5).
- [ ] Dashboard `RippleCard.vue`/`RippleFilter.vue` impact_score reads via presentation shape (verify by reading `ripple.impact_score` from typed wrapper DTO — `fetchRipples` returns `RippleListItemResponseDTO[]` which now includes `impact_score?`).
- [ ] Atom commit message uses `#N.<letter>` for `git log --grep` discoverability.

## Carryover to v16.5 #N.13+

After T1+T2+T3 merge: 39 `as unknown as` cast cleanup in `apps/dashboard/src/composables/` becomes next priority. Spec/plan should be drafted in same session.
