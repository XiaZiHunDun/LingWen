# Phase 126 v16.5 #N.10 — CVG Cascade Wire-up + Chapter Re-export + Protocols Cleanup + Status Event Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the four medium-sized carryover items from v16.5 #N.9 handoff §6: (1) CVG cascade endpoints wire-up (`get_ripple_cascade` + `get_ripple_cascade_preview` + `get_ripple_cascade_v9_20`), (2) `apps/studio_api/models/chapter.py` re-export shim from lingwen-shared, (3) `apps/studio_api/protocols.py` CVG cleanup after wire-up, (4) `status` event promotion to canonical `CreatorAgentStreamEvent`.

**Architecture:** Continue the four-layer architecture established in v16.5 #N.7/#N.8/#N.9:
1. **Source of truth** = `packages/lingwen-shared/src/lingwen_shared/contracts/python/*.py` (Pydantic v2)
2. **Backend layer** = `apps/studio_api/models/*.py` re-exports the canonical models (where applicable); storage-shape CVG models stay in `apps/studio_api/protocols.py` for internal use only
3. **TS layer** = `tooling/contracts/generate.py` emits `packages/lingwen-shared/src/lingwen_shared/contracts/ts/*.ts` → `packages/dashboard-contracts/src/shared/*.ts` re-export shims → typed wrappers in `apps/dashboard/src/api/*.ts`
4. **CVG adapter** = `apps/studio_api/cvg_adapter.py` is the **SOLE** boundary where backend storage shape (`apps/studio_api/protocols.py`) maps to presentation shape (`lingwen_shared.contracts.python.cvg`). Routes call cvg_adapter; no inline mapping in route handlers.

**Tech Stack:** Python 3.13 / Pydantic v2 / FastAPI / pnpm + TypeScript strict / pytest / vitest / vue-tsc / ruff

**Reference:** v16.5 #N.9 handoff (`docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n9-cleanup-and-handle-stream-event-handoff.md`) §6 carryover items N.10.a, N.10.b, N.10.c, N.10.d.

**Worktree:** Already created — `phase-126-v16-5-n10` worktree branched from `origin/phase-126-v16-5-n9` (commit `b17f7b20`).

---

## Scope Check

Sub-project scope validation:
- **N.10.a** CVG cascade wire-up requires extending 2 Pydantic models (CascadeResponse + CascadePreviewResponse) in lingwen-shared, updating cvg_adapter, wiring 3 routes, regenerating TS. ~6-8 commits.
- **N.10.b** chapter.py re-export is trivial: all 8 models already exist in lingwen-shared health.py (verified). 1 commit.
- **N.10.c** protocols.py CVG cleanup is mechanical after N.10.a wire-up: storage-shape CVG models can be removed/moved. 1 commit.
- **N.10.d** status event promotion: add 1 variant to canonical enum, regenerate TS, drop defensive check. 2 commits.

Total estimated commits: **10-13** (fits one phase, not requiring sub-project split).

---

## File Structure

### Files Modified This Phase

```
packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py        # MODIFIED: extend CascadeResponse + CascadePreviewResponse
packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts             # REGENERATED via tooling/contracts/generate.py
packages/dashboard-contracts/src/shared/cvg.ts                             # unchanged (re-export shim)
packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py # MODIFIED: add status variant
packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator_sse.ts    # REGENERATED
packages/dashboard-contracts/src/shared/creator-sse.ts                     # MODIFIED: regenerated types propagated

apps/studio_api/models/chapter.py                  # MODIFIED: thin re-export shim from lingwen-shared
apps/studio_api/cvg_adapter.py                     # MODIFIED: extend cascade_*_storage_to_presentation with new fields
apps/studio_api/routes/cvg.py                      # MODIFIED: 3 endpoints use cvg_adapter
apps/studio_api/protocols.py                       # MODIFIED: remove storage-shape CVG models (after N.10.a)
apps/studio_api/tests/test_cvg_adapter.py          # MODIFIED: new tests for extended mappings

apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts  # MODIFIED: drop local status extension
apps/dashboard/src/utils/creatorAgentStreamUtils.js             # MODIFIED: handle status as canonical variant

packages/lingwen-shared/tests/test_cvg_dto.py      # MODIFIED: tests for extended CascadeResponse/CascadePreviewResponse
packages/lingwen-shared/tests/test_creator_sse_dto.py  # NEW: tests for status variant

docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n10-cvg-cascade-wireup-chapter-reexport-protocols-cleanup-status-promotion-handoff.md  # NEW
```

### Files NOT Modified (deferred to v16.5 #N.11+)

- `tools/llm_*.py` — completed in v16.5 #N.6
- `infra/*` sqlite3 imports — completed in v16.5 #N.3/#N.4
- Async port conformance (`LLMServiceAdapter` sync → `async execute → LLMResult`) — ~16-25 commits, separate phase
- 39 `as unknown as` cast cleanup in composables — pre-existing fragile patterns, separate phase
- Other CVG route endpoints (`apply_ripple`, `reject_ripple`, `get_ripple_audit`, `export_ripple_audit`, `rollback_ripple`, `get_ripple_stats`, `get_reference_graph`, `get_ripple_detail`) — currently return storage-shape responses that may have separate drift issues but are out of N.10 scope
- `apply_ripple` / `reject_ripple` / `rollback_ripple` / `cancel_cascade_run` — these return `RippleActionResponse` etc. which are currently drift candidates; verification + wire-up deferred
- `CascadeRunResponse.from_dataclass` (line 887 of protocols.py) — still uses storage shape; if `protocols.py` CVG cleanup is too aggressive in T9, leave CascadeRunResponse in protocols.py and document as carryover

---

## Task Sequence Overview

| Task | Scope | Est. commits |
|------|-------|--------------|
| **T0** Worktree setup | Already done in this session | 0 |
| **T1** Extend CascadeResponse Pydantic | Add cascade_actions + generated_at + bfs_algorithm_version + cascading fields | 1-2 |
| **T2** Regenerate TS for CascadeResponse | Run tooling/contracts/generate.py | 1 |
| **T3** Extend CascadePreviewResponse Pydantic | Add affected_*_count + estimated_change_count + cascade_*_count | 1 |
| **T4** Regenerate TS for CascadePreviewResponse | Run tooling/contracts/generate.py | 1 |
| **T5** Update cvg_adapter.cascade_storage_to_presentation | Populate new CascadeResponse fields + handle 3 cascade endpoints via dict conversion | 2-3 |
| **T6** chapter.py re-export shim | All 8 models already in lingwen-shared health.py | 1 |
| **T7** Wire up get_ripple_cascade endpoint | routes/cvg.py uses cvg_adapter | 1 |
| **T8** Wire up get_ripple_cascade_preview endpoint | routes/cvg.py uses cvg_adapter | 1 |
| **T9** Wire up get_ripple_cascade_v9_20 endpoint | routes/cvg.py uses cvg_adapter (non-persist branch only) | 1 |
| **T10** Status event promotion | Add status variant to canonical CreatorAgentStreamEvent + regenerate + drop defensive check | 2 |
| **T11** Protocols.py CVG cleanup | Remove storage-shape CVG models after all wire-up complete | 1 |
| **T12** Verification + handoff | Tests + docs + push | 2-3 |

**Total estimated commits: 14-19** (excluding T0).

---

## Task T0: Worktree Setup — ALREADY DONE

**Files:**
- Create: `/home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10/` (worktree)
- Symlink: `.venv` → `../phase-126-v16-5-n9/.venv` (deps reuse)

- [x] **Step 1: Worktree created**

```bash
git worktree add -b phase-126-v16-5-n10 \
  /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10 \
  origin/phase-126-v16-5-n9
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
ln -s ../phase-126-v16-5-n9/.venv .venv
```

Status: HEAD at `b17f7b20`, working tree clean, .venv symlinked.

---

## Task T1: Extend CascadeResponse Pydantic in lingwen-shared

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py:142-153` (CascadeResponse class)

### Why

Backend storage `CascadeResponse` has fields the dashboard actively consumes (`cascade_actions`, `generated_at`, `bfs_algorithm_version`) but presentation `CascadeResponse` does not. Empirical evidence (N.9 handoff §3):
- `apps/dashboard/src/utils/cascadeGraphUtils.js:152`: `const actions = cascade?.cascade_actions || [];`
- `apps/dashboard/src/utils/cascadeGraphUtils.js:214`: `const depth = cascade?.depth_reached ?? 0;` (NOTE: presentation uses `max_depth`, dashboard reads `depth_reached` — see step 2 for resolution)
- `apps/dashboard/src/composables/useWorkflowSocket.js:20` (JSDoc documents expected fields)

Adding `depth_reached` ALIAS to `max_depth` is NOT acceptable (no aliasing pattern in TS codegen). Instead: keep `max_depth` as canonical, but document migration path for dashboard to rename `depth_reached` → `max_depth` (carried over to dashboard consumer update task).

### Step 1.1: Write failing test

Create file `packages/lingwen-shared/tests/test_cvg_dto.py` (extend existing file). Append these tests:

```python
def test_cascade_response_includes_cascade_actions_field():
    """CascadeResponse must include cascade_actions list (dashboard consumer cascadeGraphUtils.js:152)."""
    from lingwen_shared.contracts.python.cvg import CascadeResponse, CascadeNodeResponse, CascadeEdgeResponse
    response = CascadeResponse(
        ripple_id="r1",
        nodes=[CascadeNodeResponse(node_id="n1", chapter_id=1, title="T", status="applied", depth=1)],
        edges=[CascadeEdgeResponse(source="a", target="b", relation="ref")],
        total_nodes=1,
        total_edges=1,
        max_depth=1,
        cascade_actions=[{"type": "apply", "target": "ch1"}],
    )
    assert len(response.cascade_actions) == 1
    assert response.cascade_actions[0]["type"] == "apply"


def test_cascade_response_includes_generated_at_field():
    """CascadeResponse must include generated_at string (dashboard consumer uses for display)."""
    from lingwen_shared.contracts.python.cvg import CascadeResponse
    response = CascadeResponse(
        ripple_id="r1",
        nodes=[],
        edges=[],
        total_nodes=0,
        total_edges=0,
        max_depth=0,
        cascade_actions=[],
        generated_at="2026-08-30T12:00:00",
    )
    assert response.generated_at == "2026-08-30T12:00:00"


def test_cascade_response_includes_bfs_algorithm_version_field():
    """CascadeResponse must include bfs_algorithm_version (Literal v1|v2_weighted)."""
    from lingwen_shared.contracts.python.cvg import CascadeResponse
    response_v1 = CascadeResponse(
        ripple_id="r1", nodes=[], edges=[], total_nodes=0, total_edges=0, max_depth=0,
        cascade_actions=[], generated_at="", bfs_algorithm_version="v1",
    )
    assert response_v1.bfs_algorithm_version == "v1"
    with pytest.raises(ValidationError):
        CascadeResponse(
            ripple_id="r1", nodes=[], edges=[], total_nodes=0, total_edges=0, max_depth=0,
            cascade_actions=[], generated_at="", bfs_algorithm_version="v9_invalid",
        )
```

Add `from pydantic import ValidationError` import at top of test file.

### Step 1.2: Run test to verify it fails

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10 && source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -k "cascade_response_includes" -v`

Expected: 3 FAIL with `TypeError: __init__() got an unexpected keyword argument 'cascade_actions'` (field not yet in model).

### Step 1.3: Extend CascadeResponse Pydantic

Modify `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py:142-153`. Replace the existing `CascadeResponse` class:

```python
class CascadeResponse(BaseModel):
    """Full cascade graph returned by ``GET /cvg/ripples/{id}/cascade``.

    Phase 126 v16.5 #N.10: extended with storage-shape fields (cascade_actions,
    generated_at, bfs_algorithm_version) so dashboard consumers in
    cascadeGraphUtils.js + useWorkflowSocket.js can read them via the typed wrapper.
    The dashboard currently reads these as untyped fields (PYDANTIC-DRIFT pre-N.10);
    adding them to the canonical enum closes the drift.
    """

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

Add `from typing import Any, Literal` to imports if not already there (verify by reading existing imports at top of file).

### Step 1.4: Run test to verify it passes

Run: `cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10 && source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -v`

Expected: All tests pass (existing 5 + 3 new = 8 tests pass; no regression).

### Step 1.5: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py packages/lingwen-shared/tests/test_cvg_dto.py
git commit -m "feat(lingwen-shared): v16.5 #N.10 — CascadeResponse extends with cascade_actions + generated_at + bfs_algorithm_version"
```

---

## Task T2: Regenerate TS for CascadeResponse

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` (regenerated)

### Step 2.1: Run codegen

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
source .venv/bin/activate
python tooling/contracts/generate.py
```

Expected: codegen succeeds; `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` updated.

### Step 2.2: Verify TS contract has new fields

```bash
grep -A 2 "cascade_actions\|generated_at\|bfs_algorithm_version" packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts | head -20
```

Expected: 3 fields present in `CascadeResponse` interface (codegen output).

### Step 2.3: Verify dashboard consumer TypeScript compiles

```bash
cd apps/dashboard && pnpm tsc --noEmit 2>&1 | tail -10
```

Expected: 0 errors (cascadeGraphUtils.js reads `cascade_actions` etc. as untyped — adding to TS type union makes them typed, no compilation errors expected).

### Step 2.4: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts
git commit -m "chore(lingwen-shared): v16.5 #N.10 — regenerate TS for CascadeResponse extension"
```

---

## Task T3: Extend CascadePreviewResponse Pydantic

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py:156-165` (CascadePreviewResponse class)

### Why

Backend storage `CascadePreviewResponse` exposes 7 aggregate counts (`affected_chapter_count`, `affected_character_count`, `affected_setting_count`, `estimated_change_count`, `cascade_node_count`, `cascade_edge_count`, `max_depth`) that presentation currently does NOT expose (presentation has `estimated_impact: int` + `affected_chapters: list[int]` which are semantically different shapes).

Decision: ADD storage-shape count fields as Optional on presentation so dashboard can read them. Keep existing presentation fields for forward-compat.

### Step 3.1: Write failing test

Append to `packages/lingwen-shared/tests/test_cvg_dto.py`:

```python
def test_cascade_preview_response_includes_storage_counts():
    """CascadePreviewResponse must include storage-shape aggregate counts."""
    from lingwen_shared.contracts.python.cvg import CascadePreviewResponse
    response = CascadePreviewResponse(
        ripple_id="r1",
        estimated_impact=10,
        affected_chapters=[],
        affected_chapter_count=3,
        affected_character_count=5,
        affected_setting_count=2,
        estimated_change_count=10,
        cascade_node_count=8,
        cascade_edge_count=7,
        max_depth=4,
    )
    assert response.affected_chapter_count == 3
    assert response.affected_character_count == 5
    assert response.affected_setting_count == 2
    assert response.estimated_change_count == 10
    assert response.cascade_node_count == 8
    assert response.cascade_edge_count == 7
    assert response.max_depth == 4


def test_cascade_preview_response_storage_counts_default_zero():
    """CascadePreviewResponse storage-shape counts must default to 0 (not None)."""
    from lingwen_shared.contracts.python.cvg import CascadePreviewResponse
    response = CascadePreviewResponse(ripple_id="r1", estimated_impact=0)
    assert response.affected_chapter_count == 0
    assert response.affected_character_count == 0
    assert response.affected_setting_count == 0
    assert response.estimated_change_count == 0
    assert response.cascade_node_count == 0
    assert response.cascade_edge_count == 0
    assert response.max_depth == 0
```

### Step 3.2: Run test to verify it fails

Run: `source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -k "cascade_preview_response_includes or cascade_preview_response_storage_counts" -v`

Expected: 2 FAIL with `TypeError: __init__() got an unexpected keyword argument 'affected_chapter_count'`.

### Step 3.3: Extend CascadePreviewResponse Pydantic

Modify `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py:156-165`. Replace existing class:

```python
class CascadePreviewResponse(BaseModel):
    """Cascade preview returned by ``GET /cvg/ripples/{id}/cascade/preview``.

    Phase 126 v16.5 #N.10: extended with storage-shape aggregate counts
    (affected_*_count + estimated_change_count + cascade_*_count + max_depth)
    so dashboard apply-confirmation modal can read them via the typed wrapper.
    """

    model_config = ConfigDict(extra="ignore")

    ripple_id: str
    estimated_impact: int
    affected_chapters: list[int] = Field(default_factory=list)
    preview_tree: Optional[CascadeResponse] = None
    warnings: Optional[list[str]] = None
    # Phase 126 v16.5 #N.10: storage-shape aggregate counts
    affected_chapter_count: int = 0
    affected_character_count: int = 0
    affected_setting_count: int = 0
    estimated_change_count: int = 0
    cascade_node_count: int = 0
    cascade_edge_count: int = 0
    max_depth: int = 0
```

### Step 3.4: Run test to verify it passes

Run: `source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/test_cvg_dto.py -v`

Expected: All tests pass (8 previous + 2 new = 10 tests pass).

### Step 3.5: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py packages/lingwen-shared/tests/test_cvg_dto.py
git commit -m "feat(lingwen-shared): v16.5 #N.10 — CascadePreviewResponse extends with storage-shape aggregate counts"
```

---

## Task T4: Regenerate TS for CascadePreviewResponse

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts` (regenerated)

### Step 4.1: Run codegen

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
source .venv/bin/activate
python tooling/contracts/generate.py
```

Expected: codegen succeeds; `cvg.ts` updated.

### Step 4.2: Verify TS contract has new fields

```bash
grep -A 1 "affected_chapter_count\|affected_character_count\|estimated_change_count\|cascade_node_count\|cascade_edge_count" packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts | head -20
```

Expected: 7 new fields present in `CascadePreviewResponse` interface.

### Step 4.3: Verify dashboard consumer TypeScript compiles

```bash
cd apps/dashboard && pnpm tsc --noEmit 2>&1 | tail -5
```

Expected: 0 errors.

### Step 4.4: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add packages/lingwen-shared/src/lingwen_shared/contracts/ts/cvg.ts
git commit -m "chore(lingwen-shared): v16.5 #N.10 — regenerate TS for CascadePreviewResponse extension"
```

---

## Task T5: Update cvg_adapter to populate new fields

**Files:**
- Modify: `apps/studio_api/cvg_adapter.py:155-192` (3 cascade adapter functions)
- Modify: `apps/studio_api/tests/test_cvg_adapter.py` (add tests)

### Why

The existing cvg_adapter functions:
- `cascade_node_storage_to_presentation`: maps `id`→`node_id`, `chapter`→`chapter_id`, etc. but `dimension` (storage) has NO presentation mapping. Need to add `dimension` mapping (or accept it's stored separately).
- `cascade_edge_storage_to_presentation`: maps `relationship_type`→`relation`, but doesn't map `from_node_id`→`source` / `to_node_id`→`target`.
- `cascade_storage_to_presentation`: doesn't map `trigger_ripple_id`→`ripple_id`, doesn't compute `total_nodes`/`total_edges` from storage.

These are pre-existing bugs in the N.9 adapter scaffold (never tested with real data). Wire-up exposes them.

### Step 5.1: Write failing tests

Append to `apps/studio_api/tests/test_cvg_adapter.py`:

```python
def test_cascade_node_storage_to_presentation_maps_from_node_id_and_to_node_id():
    """Storage edge (from_node_id, to_node_id) must map to presentation (source, target)."""
    from apps.studio_api.cvg_adapter import cascade_edge_storage_to_presentation
    result = cascade_edge_storage_to_presentation({
        "id": "e1",
        "from_node_id": "n1",
        "to_node_id": "n2",
        "relationship_type": "reference",
        "weight": 0.5,
    })
    assert result.source == "n1"
    assert result.target == "n2"
    assert result.relation == "reference"
    assert result.weight == 0.5


def test_cascade_storage_to_presentation_maps_trigger_ripple_id_and_computes_totals():
    """Storage cascade (trigger_ripple_id + cascade_nodes + cascade_edges) must map correctly."""
    from apps.studio_api.cvg_adapter import cascade_storage_to_presentation
    result = cascade_storage_to_presentation({
        "trigger_ripple_id": "r1",
        "cascade_nodes": [
            {"id": "n1", "chapter": 1, "title": "T1", "dimension": "character", "volume": 1, "depth": 1},
            {"id": "n2", "chapter": 2, "title": "T2", "dimension": "setting", "volume": 1, "depth": 2},
        ],
        "cascade_edges": [
            {"id": "e1", "from_node_id": "n1", "to_node_id": "n2", "relationship_type": "ref", "weight": 0.3},
        ],
        "cascade_actions": [{"type": "apply", "target": "ch1"}],
        "depth_reached": 2,
        "generated_at": "2026-08-30T12:00:00",
        "bfs_algorithm_version": "v1",
    })
    assert result.ripple_id == "r1"
    assert len(result.nodes) == 2
    assert result.nodes[0].node_id == "n1"
    assert result.nodes[0].chapter_id == 1
    assert result.total_nodes == 2
    assert len(result.edges) == 1
    assert result.edges[0].source == "n1"
    assert result.edges[0].target == "n2"
    assert result.total_edges == 1
    assert result.max_depth == 2
    assert result.status is None
    assert len(result.cascade_actions) == 1
    assert result.cascade_actions[0]["type"] == "apply"
    assert result.generated_at == "2026-08-30T12:00:00"
    assert result.bfs_algorithm_version == "v1"


def test_cascade_node_storage_to_presentation_maps_dimension_to_status():
    """Storage node dimension field should populate presentation status (default 'applied')."""
    from apps.studio_api.cvg_adapter import cascade_node_storage_to_presentation
    result_char = cascade_node_storage_to_presentation({
        "id": "n1", "chapter": 1, "title": "T", "dimension": "character",
        "volume": 1, "depth": 1,
    })
    assert result_char.status == "character"  # dimension mapped to status

    result_default = cascade_node_storage_to_presentation({
        "id": "n2", "chapter": 2, "title": "T2", "volume": 1, "depth": 1,
    })
    assert result_default.status == "applied"  # default when no dimension
```

### Step 5.2: Run tests to verify they fail

Run: `source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/test_cvg_adapter.py -k "cascade_node_storage_to_presentation_maps_from_node_id or cascade_storage_to_presentation_maps_trigger or cascade_node_storage_to_presentation_maps_dimension" -v`

Expected: 3 FAIL (existing implementation doesn't map these fields correctly).

### Step 5.3: Update cvg_adapter

Replace `cascade_node_storage_to_presentation`, `cascade_edge_storage_to_presentation`, `cascade_storage_to_presentation` in `apps/studio_api/cvg_adapter.py`:

```python
def cascade_node_storage_to_presentation(storage: dict[str, Any]) -> CascadeNodeResponse:
    """Map storage cascade node → presentation shape.

    Phase 126 v16.5 #N.10: extend mapping to include dimension→status and ripple_id.
    Storage CascadeNodeResponse has fields: id, dimension, volume, chapter, title,
    description, payload. Presentation has: node_id, chapter_id, title, status,
    depth, ripple_id, volume.
    """
    # dimension is the closest storage analog to status (character/setting/plot_point/foreshadow)
    # When absent, default to 'applied' (matches dashboard expectation)
    dimension = storage.get("dimension")
    return CascadeNodeResponse(
        node_id=storage.get("node_id") or storage.get("id", ""),
        chapter_id=storage.get("chapter_id") or storage.get("chapter", 0),
        title=storage.get("title") or storage.get("label", ""),
        status=dimension if dimension else "applied",
        depth=storage.get("depth", 0),
        ripple_id=storage.get("ripple_id"),
        volume=storage.get("volume", 1),
    )


def cascade_edge_storage_to_presentation(storage: dict[str, Any]) -> CascadeEdgeResponse:
    """Map storage cascade edge → presentation shape.

    Phase 126 v16.5 #N.10: storage fields from_node_id/to_node_id map to
    presentation source/target. relationship_type maps to relation.
    """
    return CascadeEdgeResponse(
        source=storage.get("source") or storage.get("from_node_id", ""),
        target=storage.get("target") or storage.get("to_node_id", ""),
        relation=(
            storage.get("relation")
            or storage.get("relationship_type")
            or storage.get("relationship")
            or "reference"
        ),
        weight=storage.get("weight", 0.0),
    )


def cascade_storage_to_presentation(storage: dict[str, Any]) -> CascadeResponse:
    """Map storage cascade envelope → presentation shape.

    Phase 126 v16.5 #N.10: extend mapping to populate:
    - ripple_id (from trigger_ripple_id)
    - total_nodes / total_edges (computed from len)
    - max_depth (from depth_reached)
    - status (from optional status field)
    - cascade_actions / generated_at / bfs_algorithm_version (storage passthrough)
    """
    nodes_raw = storage.get("nodes") or storage.get("cascade_nodes", [])
    edges_raw = storage.get("edges") or storage.get("cascade_edges", [])
    nodes = [cascade_node_storage_to_presentation(n) for n in nodes_raw]
    edges = [cascade_edge_storage_to_presentation(e) for e in edges_raw]
    max_depth = storage.get("max_depth") or storage.get("depth_reached") or max(
        (n.depth for n in nodes), default=0
    )
    return CascadeResponse(
        ripple_id=(
            storage.get("ripple_id")
            or storage.get("trigger_ripple_id")
            or storage.get("cascade_id")
            or storage.get("id", "")
        ),
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
        max_depth=max_depth,
        status=storage.get("status"),
        cascade_actions=list(storage.get("cascade_actions") or []),
        generated_at=storage.get("generated_at"),
        bfs_algorithm_version=storage.get("bfs_algorithm_version") or "v1",
    )
```

### Step 5.4: Run tests to verify they pass

Run: `source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v`

Expected: All tests pass (5 existing + 3 new = 8 tests pass).

### Step 5.5: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add apps/studio_api/cvg_adapter.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "refactor(studio-api): v16.5 #N.10 — cvg_adapter cascade_*_storage_to_presentation populates extended fields"
```

---

## Task T6: chapter.py re-export shim

**Files:**
- Modify: `apps/studio_api/models/chapter.py` (full file → thin re-export shim)

### Why

Empirical verification (N.9 handoff §6 + direct grep):
- `apps/studio_api/models/chapter.py` has 8 manual Pydantic definitions: ChapterData, ChaptersResponse, ProductionRecordResponse, ProductionRecordsResponse, ProductionBatchRollupResponse, ProductionRollupResponse, ProductionCostTrendPointResponse, ProductionCostTrendResponse
- ALL 8 models already exist in `packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py` (verified via N.7 T1 description: "health.py (12 models: ...ChapterData, ChaptersResponse, ProductionRecordResponse/Records/BatchRollup/Rollup/CostTrendPoint/CostTrendResponse)")
- Field-by-field identity check required before re-export (same pattern as N.8 T4 / N.9 T2)

### Step 6.1: Verify field-by-field equivalence

Run identity + field-set check before modifying:

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
source .venv/bin/activate
python -c "
from apps.studio_api.models.chapter import (
    ChapterData, ChaptersResponse,
    ProductionRecordResponse, ProductionRecordsResponse,
    ProductionBatchRollupResponse, ProductionRollupResponse,
    ProductionCostTrendPointResponse, ProductionCostTrendResponse,
)
from lingwen_shared.contracts.python.health import (
    ChapterData as H_Ch, ChaptersResponse as H_Chs,
    ProductionRecordResponse as H_Pr, ProductionRecordsResponse as H_Prs,
    ProductionBatchRollupResponse as H_Pbr, ProductionRollupResponse as H_Prl,
    ProductionCostTrendPointResponse as H_Pct, ProductionCostTrendResponse as H_PctR,
)
import sys
mappings = [
    ('ChapterData', ChapterData, H_Ch),
    ('ChaptersResponse', ChaptersResponse, H_Chs),
    ('ProductionRecordResponse', ProductionRecordResponse, H_Pr),
    ('ProductionRecordsResponse', ProductionRecordsResponse, H_Prs),
    ('ProductionBatchRollupResponse', ProductionBatchRollupResponse, H_Pbr),
    ('ProductionRollupResponse', ProductionRollupResponse, H_Prl),
    ('ProductionCostTrendPointResponse', ProductionCostTrendPointResponse, H_Pct),
    ('ProductionCostTrendResponse', ProductionCostTrendResponse, H_PctR),
]
failures = []
for name, local, shared in mappings:
    identity_ok = local is shared
    fields_match = set(local.model_fields.keys()) == set(shared.model_fields.keys())
    if not identity_ok or not fields_match:
        failures.append(f'{name}: identity={identity_ok} fields_match={fields_match} local={set(local.model_fields.keys())} shared={set(shared.model_fields.keys())}')
if failures:
    print('FAIL:')
    for f in failures: print(f)
    sys.exit(1)
print('OK: all 8 models are identical re-exports of lingwen-shared')
"
```

Expected output: `OK: all 8 models are identical re-exports of lingwen-shared`

If FAIL: STOP — field drift exists. Document drift in carryover list; do NOT proceed with re-export. Skip to T6.5 (carryover commit).

### Step 6.2: Replace chapter.py with thin re-export shim

Replace entire contents of `apps/studio_api/models/chapter.py` with:

```python
"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.10: all 8 models (ChapterData + ChaptersResponse + 6
Production* models) now live in lingwen_shared.contracts.python.health
(N.7 T1 Pydantic codegen) and are re-exported here for back-compat with
existing backend imports.

Field-by-field identity verified at migration time (see v16.5 #N.10 T6.1).
"""
from __future__ import annotations

from lingwen_shared.contracts.python.health import (
    ChapterData,
    ChaptersResponse,
    ProductionBatchRollupResponse,
    ProductionCostTrendPointResponse,
    ProductionCostTrendResponse,
    ProductionRecordResponse,
    ProductionRecordsResponse,
    ProductionRollupResponse,
)

__all__ = [
    "ChapterData",
    "ChaptersResponse",
    "ProductionBatchRollupResponse",
    "ProductionCostTrendPointResponse",
    "ProductionCostTrendResponse",
    "ProductionRecordResponse",
    "ProductionRecordsResponse",
    "ProductionRollupResponse",
]
```

### Step 6.3: Run tests to verify no regression

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/ -q --ignore=apps/studio_api/tests/test_write_workspace_route.py
```

Expected: 37 tests pass (same as N.9 baseline; no regression).

### Step 6.4: Verify ruff is clean

```bash
ruff check apps/studio_api/models/chapter.py
```

Expected: `All checks passed!`

### Step 6.5: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add apps/studio_api/models/chapter.py
git commit -m "refactor(studio-api): v16.5 #N.10 — chapter.py re-exports 8 models from lingwen-shared"
```

---

## Task T7: Wire up get_ripple_cascade endpoint via cvg_adapter

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:282-328` (get_ripple_cascade endpoint)

### Step 7.1: Update endpoint to use cvg_adapter

Modify the existing endpoint `get_ripple_cascade` (lines 282-328 in current file). Replace the cascade_nodes/cascade_edges/cascade_actions/depth_reached/generated_at/bfs_algorithm_version construction block (lines 312-328) with a single cvg_adapter call:

Replace lines 312-328 in `apps/studio_api/routes/cvg.py`:

```python
        cascade_dict = cascade.model_dump() if hasattr(cascade, "model_dump") else dict(cascade)
        return cvg_adapter.cascade_storage_to_presentation(cascade_dict)
```

Update the import section at top of file (lines 43-59) to remove `CascadeNodeResponse, CascadeEdgeResponse, CascadeResponse` from `apps.studio_api.models` import if no other endpoints use them (verify first; preview and v9_20 also use them — defer cleanup to T11).

Update the `response_model=` declaration at line 286:
```python
    @app.get(
        "/api/cvg/ripples/{ripple_id}/cascade",
        response_model=CascadeResponse,  # presentation CascadeResponse from lingwen-shared
    )
```

Verify the import resolves: `CascadeResponse` should now come from `lingwen_shared.contracts.python.cvg` (not `apps.studio_api.models`). Add this import if not already present at the top of `cvg.py`.

If `CascadeResponse` is still imported from `apps.studio_api.models` (storage shape), replace that import with `from lingwen_shared.contracts.python.cvg import CascadeResponse, CascadePreviewResponse` at the top of the file (alongside `RippleListItemResponse` which was added in N.9 T3).

### Step 7.2: Run studio_api tests to verify no regression

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/ -q --ignore=apps/studio_api/tests/test_write_workspace_route.py
```

Expected: 37 tests pass (no regression; cvg_adapter tests still pass).

### Step 7.3: Smoke-test endpoint manually (optional)

If `lingwen_storage` has cascade test fixtures, run a curl smoke test. Otherwise skip (covered by unit tests).

### Step 7.4: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): v16.5 #N.10 — get_ripple_cascade uses cvg_adapter for presentation shape"
```

---

## Task T8: Wire up get_ripple_cascade_preview endpoint via cvg_adapter

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:330-378` (get_ripple_cascade_preview endpoint)

### Step 8.1: Update endpoint to use cvg_adapter

Replace lines 358-378 in `apps/studio_api/routes/cvg.py`:

```python
        cascade_dict = cascade.model_dump() if hasattr(cascade, "model_dump") else dict(cascade)
        preview = cvg_adapter.cascade_preview_storage_to_presentation(cascade_dict, ripple_id)
        return preview
```

Note: `cascade_preview_storage_to_presentation` is a NEW adapter function (not yet implemented). Add it to `cvg_adapter.py` after `cascade_storage_to_presentation`:

```python
def cascade_preview_storage_to_presentation(
    storage: dict[str, Any],
    ripple_id: str,
) -> CascadePreviewResponse:
    """Map storage cascade envelope → CascadePreviewResponse (presentation shape).

    Phase 126 v16.5 #N.10: computes the 7 storage-shape aggregate counts that
    the backend CascadePreviewResponse exposes and populates both presentation
    fields (estimated_impact, affected_chapters) and storage-shape counts
    (affected_chapter_count, etc.) on the returned presentation model.

    Storage CascadePreviewResponse fields (apps/studio_api/protocols.py:834-846):
    - ripple_id
    - affected_chapter_count, affected_character_count, affected_setting_count
    - estimated_change_count, cascade_node_count, cascade_edge_count, max_depth

    Presentation CascadePreviewResponse fields (lingwen-shared):
    - ripple_id, estimated_impact, affected_chapters, preview_tree, warnings
    - + storage-shape count fields (added in T3)
    """
    nodes_raw = storage.get("nodes") or storage.get("cascade_nodes", [])
    edges_raw = storage.get("edges") or storage.get("cascade_edges", [])
    affected_chapters = sum(
        1 for n in nodes_raw if (n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)) in ("plot_point", "foreshadow")
    )
    affected_characters = sum(
        1 for n in nodes_raw if (n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)) == "character"
    )
    affected_settings = sum(
        1 for n in nodes_raw if (n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)) == "setting"
    )
    actions_raw = storage.get("cascade_actions") or []
    return CascadePreviewResponse(
        ripple_id=ripple_id,
        estimated_impact=len(actions_raw),
        affected_chapters=[],  # storage doesn't track actual chapter IDs in preview response
        affected_chapter_count=affected_chapters,
        affected_character_count=affected_characters,
        affected_setting_count=affected_settings,
        estimated_change_count=len(actions_raw),
        cascade_node_count=len(nodes_raw),
        cascade_edge_count=len(edges_raw),
        max_depth=storage.get("depth_reached") or storage.get("max_depth", 0),
    )
```

Add to `__all__` in cvg_adapter.py:
```python
__all__ = [
    ...,
    "cascade_preview_storage_to_presentation",
]
```

### Step 8.2: Add test for cascade_preview_storage_to_presentation

Append to `apps/studio_api/tests/test_cvg_adapter.py`:

```python
def test_cascade_preview_storage_to_presentation_populates_counts():
    from apps.studio_api.cvg_adapter import cascade_preview_storage_to_presentation
    result = cascade_preview_storage_to_presentation(
        {
            "cascade_nodes": [
                {"id": "n1", "dimension": "character", "chapter": 1, "volume": 1, "title": "C1", "depth": 1},
                {"id": "n2", "dimension": "setting", "chapter": 2, "volume": 1, "title": "S1", "depth": 2},
                {"id": "n3", "dimension": "plot_point", "chapter": 3, "volume": 1, "title": "P1", "depth": 3},
            ],
            "cascade_edges": [
                {"id": "e1", "from_node_id": "n1", "to_node_id": "n2", "relationship_type": "ref", "weight": 0.5},
            ],
            "cascade_actions": [{"type": "apply"}],
            "depth_reached": 3,
        },
        "r1",
    )
    assert result.ripple_id == "r1"
    assert result.affected_chapter_count == 1  # plot_point
    assert result.affected_character_count == 1
    assert result.affected_setting_count == 1
    assert result.estimated_change_count == 1
    assert result.cascade_node_count == 3
    assert result.cascade_edge_count == 1
    assert result.max_depth == 3
```

### Step 8.3: Run tests to verify

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v
```

Expected: 9 tests pass (8 previous + 1 new).

### Step 8.4: Run all studio_api tests to verify no regression

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/ -q --ignore=apps/studio_api/tests/test_write_workspace_route.py
```

Expected: 38 tests pass (37 + 1 new from cascade_preview_storage_to_presentation).

### Step 8.5: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add apps/studio_api/cvg_adapter.py apps/studio_api/routes/cvg.py apps/studio_api/tests/test_cvg_adapter.py
git commit -m "refactor(studio-api): v16.5 #N.10 — get_ripple_cascade_preview uses cvg_adapter (new cascade_preview_storage_to_presentation)"
```

---

## Task T9: Wire up get_ripple_cascade_v9_20 endpoint (non-persist branch)

**Files:**
- Modify: `apps/studio_api/routes/cvg.py:382-444` (get_ripple_cascade_v9_20 endpoint)

### Step 9.1: Update non-persist branch to use cvg_adapter

Replace lines 428-444 in `apps/studio_api/routes/cvg.py`:

```python
        cascade_dict = cascade.model_dump() if hasattr(cascade, "model_dump") else dict(cascade)
        return cvg_adapter.cascade_storage_to_presentation(cascade_dict)
```

Leave the persist=True branch (lines 400-414) untouched — it returns `CascadeRunResponse.from_dataclass(run)` which is a different shape and out of scope.

### Step 9.2: Run tests to verify no regression

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/ -q --ignore=apps/studio_api/tests/test_write_workspace_route.py
```

Expected: 38 tests pass.

### Step 9.3: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add apps/studio_api/routes/cvg.py
git commit -m "refactor(studio-api): v16.5 #N.10 — get_ripple_cascade_v9_20 (non-persist) uses cvg_adapter"
```

---

## Task T10: Promote status event to canonical CreatorAgentStreamEvent

**Files:**
- Modify: `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py` (add `status` variant)
- Regenerate: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator-sse.ts`
- Modify: `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` (drop local extension)
- Modify: `apps/dashboard/src/utils/creatorAgentStreamUtils.js` (drop defensive check + status as canonical)
- New tests: `packages/lingwen-shared/tests/test_creator_sse_dto.py`

### Why

Backend emits `status` events at 3 points (`packages/lingwen-creator/src/lingwen_creator/content/agent.py:534, 537, 592`). Frontend useAgentTask.ts:297-298 handles `status` as defensive extension to the canonical `CreatorAgentStreamEvent`. The canonical enum (defined in N.7 T5 at `packages/dashboard-contracts/src/shared/creator-sse.ts`) does NOT include `status`. Promoting status to canonical:
1. Closes the type contract gap (canonical enum matches actual event types)
2. Removes the defensive extension in useAgentTask.ts
3. Allows downstream composables (other useCreatorAgent composables) to receive status events with full type safety

### Step 10.1: Find creator_sse.py location and check current definition

```bash
find packages/lingwen-shared -name "creator_sse*" -type f
find packages/lingwen-shared -name "*creator*sse*" -type f
```

Expected: file at `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py`. If not found, search more broadly.

If `CreatorAgentStreamEvent` is defined inline in `creator.py` (N.7 Pydantic DTO consolidation), edit there instead. Verify with:

```bash
grep -rn "class CreatorAgentStreamEvent\|class CreatorAgentPlanResult" packages/lingwen-shared/src/lingwen_shared/contracts/python/ | head -5
```

### Step 10.2: Write failing test

Create file `packages/lingwen-shared/tests/test_creator_sse_dto.py`:

```python
"""Tests for CreatorAgentStreamEvent discriminated union.

Phase 126 v16.5 #N.10: status event promoted from defensive extension to canonical variant.
"""


def test_creator_agent_stream_event_status_variant_is_canonical():
    """CreatorAgentStreamEvent must accept a 'status' variant with 'message' field."""
    from lingwen_shared.contracts.python.creator_sse import CreatorAgentStreamEvent

    # Use model_validate to test discriminated union accepts status variant
    event = CreatorAgentStreamEvent.model_validate({
        "type": "status",
        "message": "正在分析写作范围…",
    })
    assert event.type == "status"
    assert event.message == "正在分析写作范围…"


def test_creator_agent_stream_event_chunk_variant_still_works():
    """Existing chunk variant must continue to validate (no regression)."""
    from lingwen_shared.contracts.python.creator_sse import CreatorAgentStreamEvent

    event = CreatorAgentStreamEvent.model_validate({"type": "chunk", "text": "hello"})
    assert event.type == "chunk"
    assert event.text == "hello"


def test_creator_agent_stream_event_unknown_type_rejected():
    """Unknown event types must be rejected (strict discriminated union)."""
    import pytest
    from pydantic import ValidationError
    from lingwen_shared.contracts.python.creator_sse import CreatorAgentStreamEvent

    with pytest.raises(ValidationError):
        CreatorAgentStreamEvent.model_validate({"type": "unknown_event_type"})
```

If `creator_sse.py` doesn't exist (status was in `creator.py`), adapt the import paths and add tests to existing `test_creator_dto.py` instead.

### Step 10.3: Run test to verify it fails

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/test_creator_sse_dto.py -v
```

Expected: 1 FAIL (status variant not yet in canonical enum), 2 PASS (chunk + unknown rejection already work).

### Step 10.4: Add status variant to CreatorAgentStreamEvent

In `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py` (or `creator.py` if that's where the canonical enum lives), find the `CreatorAgentStreamEvent` discriminated union definition. Add a `status` variant:

If the existing definition uses `Union[StartEvent, ChunkEvent, ...]` style with separate sub-models, add:
```python
class StatusEvent(BaseModel):
    """Phase 126 v16.5 #N.10: backend emits status events to communicate
    progress between LLM chunks (e.g., '正在分析写作范围…')."""

    model_config = ConfigDict(extra="ignore")
    type: Literal["status"]
    message: str
```

Then update `CreatorAgentStreamEvent` union:
```python
CreatorAgentStreamEvent = Union[
    StartEvent, ChunkEvent, AdviceEvent, PreviewLabelEvent, DoneEvent, ErrorEvent,
    StatusEvent,  # Phase 126 v16.5 #N.10: promoted from defensive extension
]
```

If using Pydantic tagged union (`Annotated[Union[...], Field(discriminator="type")]`), ensure StatusEvent is added to the union list.

If using a single BaseModel with optional fields (less strict discriminated union), add:
```python
class CreatorAgentStreamEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["start", "chunk", "advice", "preview_label", "done", "error", "status"]
    # ... existing optional fields ...
    message: Optional[str] = None  # used by status + error variants
```

Choose the appropriate pattern based on existing structure. Match the existing style.

### Step 10.5: Run test to verify it passes

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/test_creator_sse_dto.py -v
```

Expected: 3 tests pass.

### Step 10.6: Regenerate TS

```bash
source .venv/bin/activate
python tooling/contracts/generate.py
```

Expected: `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator-sse.ts` updated with `status` variant.

### Step 10.7: Verify dashboard type-check passes

```bash
cd apps/dashboard && pnpm tsc --noEmit 2>&1 | tail -5
```

Expected: 0 errors (the canonical type now matches what backend emits).

### Step 10.8: Drop defensive check in useAgentTask.ts

Modify `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts`. Find the local extension signature:

```typescript
handleStreamEvent: (evt: CreatorAgentStreamEvent | { type: 'status'; message: string }) => void;
```

Replace with canonical:
```typescript
handleStreamEvent: (evt: CreatorAgentStreamEvent) => void;
```

Remove any `as unknown as (event: unknown) => void` casts that were needed because of the local extension. The runtime behavior is unchanged because backend already emits status as canonical now.

### Step 10.9: Update creatorAgentStreamUtils.js

Modify `apps/dashboard/src/utils/creatorAgentStreamUtils.js`. The current parser yields on `chunk`, `advice`, `preview_label` for preview paint. Add status to canonical handling (currently no special action — just pass through):

The current code (from N.7 T5):
```js
if (evt.type === 'chunk' || evt.type === 'advice' || evt.type === 'preview_label') {
  await new Promise((resolve) => { requestAnimationFrame(() => resolve()); });
}
```

Status events should also yield (they're progress messages). Add `evt.type === 'status'` to the condition:
```js
if (['chunk', 'advice', 'preview_label', 'status'].includes(evt.type)) {
  await new Promise((resolve) => { requestAnimationFrame(() => resolve()); });
}
```

This allows status messages to paint incrementally on the UI.

### Step 10.10: Run frontend tests

```bash
cd apps/dashboard && pnpm vitest run tests/unit/utils/creatorAgentStreamUtils.spec.ts 2>&1 | tail -10
pnpm vitest run tests/unit/use-agent-task.spec.ts 2>&1 | tail -10
```

Expected: all tests pass.

### Step 10.11: Run all frontend tests to verify no regression

```bash
cd apps/dashboard && pnpm vitest run 2>&1 | tail -5
```

Expected: 1733 tests pass + 1 skipped (no regression).

### Step 10.12: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add packages/lingwen-shared/src/lingwen_shared/contracts/python/creator_sse.py \
        packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py \
        packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator-sse.ts \
        packages/lingwen-shared/tests/test_creator_sse_dto.py \
        apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts \
        apps/dashboard/src/utils/creatorAgentStreamUtils.js
git commit -m "feat(creator-sse): v16.5 #N.10 — status event promoted to canonical CreatorAgentStreamEvent variant"
```

---

## Task T11: Protocols.py CVG cleanup

**Files:**
- Modify: `apps/studio_api/protocols.py` (remove CVG storage-shape models)

### Why

After T7-T9, the 3 cascade endpoints use cvg_adapter for storage → presentation conversion. The storage-shape CVG models in `apps/studio_api/protocols.py` (CascadeNodeResponse, CascadeEdgeResponse, CascadeResponse, CascadePreviewResponse at lines 799-846, plus related cascade models) are no longer used by route endpoints.

BUT: `CascadeRunResponse` (lines 851+) is still used by `get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel` (lines 446-516). And `CascadeBroadcastLogResponse` (line 994) is used by `get_ripple_cascade_broadcast_log` (line 515). These are NOT in scope for N.10 wire-up.

Decision: Remove ONLY the cascade envelope models (CascadeNodeResponse, CascadeEdgeResponse, CascadeResponse, CascadePreviewResponse at lines 799-846). Leave CascadeRunResponse + CascadeBroadcastLogResponse in place (used by unwired endpoints — carryover to N.11+).

Verify CascadeNodeResponse + CascadeEdgeResponse are NOT used by other routes or helpers before removing. Run:

```bash
grep -rn "from apps.studio_api.protocols import.*CascadeNodeResponse\|from apps.studio_api.protocols import.*CascadeEdgeResponse" apps/ 2>/dev/null | head -10
grep -rn "CascadeNodeResponse\|CascadeEdgeResponse" apps/studio_api/routes/cvg.py apps/studio_api/helpers/cvg.py 2>/dev/null | head -20
```

If still used in helpers/cvg.py, keep them in protocols.py (helpers still construct storage-shape responses internally).

### Step 11.1: Investigate usage before deletion

```bash
grep -rn "CascadeNodeResponse\|CascadeEdgeResponse\|CascadeResponse\b\|CascadePreviewResponse" apps/studio_api/helpers/cvg.py 2>/dev/null | head -20
grep -rn "CascadePreviewResponse" apps/ 2>/dev/null | head -10
```

Document findings. If helpers still use the storage-shape models, SKIP this task and move to T12 (handoff) — leave carryover for N.11+.

### Step 11.2: If safe to remove — delete from protocols.py

Delete lines 799-846 from `apps/studio_api/protocols.py` (4 classes: CascadeNodeResponse, CascadeEdgeResponse, CascadeResponse, CascadePreviewResponse). Keep CascadeRunResponse (lines 851+) and ReferenceGraphResponse (line 851, used by `_build_reference_graph_response` helper).

### Step 11.3: Run all studio_api tests to verify no regression

```bash
source .venv/bin/activate && env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/ -q --ignore=apps/studio_api/tests/test_write_workspace_route.py
```

Expected: 38 tests pass (no regression).

### Step 11.4: Run ruff to verify clean

```bash
ruff check apps/studio_api/protocols.py
```

Expected: `All checks passed!`

### Step 11.5: Commit

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add apps/studio_api/protocols.py
git commit -m "refactor(studio-api): v16.5 #N.10 — remove storage-shape Cascade envelope models from protocols.py"
```

If task was skipped (helpers still use them), commit a docs-only carryover note:

```bash
git commit --allow-empty -m "docs(phase-126): v16.5 #N.10 — document protocols.py CVG cleanup carryover (helpers still use storage-shape models)"
```

---

## Task T12: Verification + handoff

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n10-cvg-cascade-wireup-chapter-reexport-protocols-cleanup-status-promotion-handoff.md`
- Modify: `CLAUDE.md` (add N.10 update section)

### Step 12.1: Run all verification gates

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
source .venv/bin/activate

# Backend tests
env -u MINIMAX_API_KEY python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q
env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/ -q --ignore=apps/studio_api/tests/test_write_workspace_route.py
env -u MINIMAX_API_KEY python -m pytest apps/studio_api/tests/test_cvg_adapter.py -v

# Frontend tests
cd apps/dashboard
pnpm vitest run 2>&1 | tail -5
pnpm tsc --noEmit 2>&1 | tail -5
pnpm eslint . 2>&1 | tail -5
pnpm exec knip 2>&1 | tail -5

# Lint
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
ruff check apps/studio_api packages/lingwen-shared/src/lingwen_shared/contracts/

# Import-linter
python tooling/hygiene/check_import_linter.py

# Hygiene tests
python -m pytest tests/hygiene/ tooling/hygiene/tests/ -q
```

Expected results:
- pytest shared: 116 passed (113 + 3 from T1)
- pytest studio_api: 38 passed (37 + 1 from T8) + 1 pre-existing fail (test_write_workspace_route, FastAPI version drift)
- pytest cvg_adapter: 9 passed (5 + 3 from T5 + 1 from T8)
- vitest: 1733 passed + 1 skipped (no regression)
- vue-tsc: 0 errors
- ESLint: 0 errors
- knip: same advisory count as N.9 baseline
- ruff: 0 errors
- import-linter: 1 contract kept
- hygiene: 39 passed

### Step 12.2: Write handoff doc

Create `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n10-cvg-cascade-wireup-chapter-reexport-protocols-cleanup-status-promotion-handoff.md` with sections mirroring N.9 handoff structure (TL;DR, Files Created/Modified, Migration Pattern, Drift Notes, Verification Matrix, Lessons Learned, Carryover to N.11+, Commit Timeline, Branch Status).

### Step 12.3: Update CLAUDE.md

Add N.10 update section to `CLAUDE.md` mirroring N.9 update section format. Document:
- 4 carryover items completed (N.10.a/b/c/d)
- Architecture invariants enforced (new invariants for cascade + status)
- Lessons learned
- Carryover to v16.5 #N.11+

### Step 12.4: Push branch

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git push -u origin phase-126-v16-5-n10
```

Expected: branch pushed to origin; ready for PR/merge.

### Step 12.5: Commit handoff + CLAUDE.md

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-126-v16-5-n10
git add docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n10-*.md CLAUDE.md
git commit -m "docs(phase-126): v16.5 #N.10 — handoff + CLAUDE.md closure"
```

---

## Carryover to v16.5 #N.11+

- **CascadeRunResponse wire-up** (carryover from T11): `get_ripple_cascade_runs` + `list_all_cascade_runs` + `post_ripple_cascade_run_cancel` + `get_ripple_cascade_broadcast_log` endpoints still return storage-shape models. Wire-up requires extending lingwen-shared CascadeRunResponse + CascadeBroadcastLogResponse. Estimated 2-4 commits.
- **Async port conformance**: `LLMServiceAdapter` from sync → `async execute → LLMResult`. ~16-25 commits.
- **39 `as unknown as` cast cleanup** in composables — pre-existing fragile patterns.
- **Dashboard cascade field migration**: cascadeGraphUtils.js still reads storage-shape field names (`cascade_nodes`, `cascade_edges`, `from_node_id`, `to_node_id`, `cascade_actions`, `depth_reached`). Typed wrapper now returns both presentation AND storage fields (intentional dual-shape for backward compat). Future cleanup: rename dashboard reads to presentation field names (`nodes`, `edges`, `source`, `target`, `cascade_actions` stays the same, `max_depth`). Estimated 1-2 commits.
- **Other CVG route wire-ups**: `apply_ripple` / `reject_ripple` / `rollback_ripple` / `get_ripple_audit` / `export_ripple_audit` / `get_ripple_stats` / `get_reference_graph` / `get_ripple_detail` — 8 endpoints still return storage-shape responses. Drift candidates. Estimated 4-8 commits.
