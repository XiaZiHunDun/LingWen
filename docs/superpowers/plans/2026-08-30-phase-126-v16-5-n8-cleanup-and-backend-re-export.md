# Phase 126 v16.5 #N.8 — Cleanup + Backend Pydantic Re-export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote remaining backend Pydantic models (`apps/studio_api/models/*.py` + `protocols.py`) to single-source-of-truth in `packages/lingwen-shared/src/lingwen_shared/contracts/python/` via backend re-export, extract CVG presentation adapter, drop residual `as unknown as` casts in `useAgentTask.ts`, and fix 5 re-export shim paths.

**Architecture:** Three concentric layers
1. **Source of truth** = `packages/lingwen-shared/src/lingwen_shared/contracts/python/*.py` (Pydantic v2)
2. **Backend layer** = `apps/studio_api/models/*.py` + `apps/studio_api/protocols.py` re-exports the canonical models, with adapter layer mapping storage → presentation where needed
3. **TS layer** = `tooling/contracts/generate.py` emits `packages/lingwen-shared/src/lingwen_shared/contracts/ts/*.ts` → `packages/dashboard-contracts/src/shared/*.ts` re-export shims → typed wrappers in `apps/dashboard/src/api/*.ts`

**Tech Stack:** Python 3.13 / Pydantic v2 / FastAPI / pnpm + TypeScript strict / pytest / vitest / vue-tsc / ruff

**Reference:** v16.5 #N.7 handoff (`docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n7-dto-pydantic-codegen-handoff.md`) §6 carryover list

---

## Scope Check

Sub-project scope validation:
- Backend Pydantic re-export is ONE layer migration (Phase 126 DP series)
- CVG adapter is ONE architectural extraction
- T5.4 cast cleanup is ONE frontend type narrowing
- 2-dot path fix is ONE trivial cleanup

Total estimated commits: ~25-35 (fits one phase, not requiring sub-project split).

---

## File Structure

### Files Modified This Phase

```
packages/dashboard-contracts/src/shared/             # 5 re-export shim paths (2-dot → 3-dot)
├── cvg.ts                                          # fix path
├── decisions.ts                                    # fix path
├── health.ts                                       # fix path
├── studio.ts                                       # fix path
└── workflows.ts                                    # fix path

apps/studio_api/                                    # Backend models → re-export lingwen-shared
├── models/
│   ├── health.py                                   # re-export lingwen_shared.contracts.python.health
│   ├── studio.py                                   # re-export lingwen_shared.contracts.python.studio
│   ├── workflow.py                                 # re-export lingwen_shared.contracts.python.workflows
│   ├── decision.py                                 # re-export lingwen_shared.contracts.python.decisions
│   └── chapter.py                                  # defer (Phase 124 owns this; verify same as creator)
├── protocols.py                                    # RETAIN storage models + extract CVG adapter
└── routes/                                         # update imports to use re-exported models

apps/studio_api/cvg_adapter.py                      # NEW: CVG storage → presentation adapter

apps/dashboard/src/composables/useCreatorAgent/
└── useAgentTask.ts                                 # tighten buildPlanRequestBody + handleStreamEvent

docs/superpowers/handoffs/
└── 2026-08-30-phase-126-v16-5-n8-cleanup-and-backend-re-export-handoff.md  # NEW
```

### Files NOT Modified (deferred)

- `chapter.py`, `creator_*.py`, `world_db`, etc. — Phase 124 lingwen_creator package owns these
- `tools/llm_*.py` — completed in v16.5 #N.6
- `infra/*` sqlite3 imports — completed in v16.5 #N.3/#N.4
- 39 `as unknown as` casts in composables — v16.5 #N.9+
- LLMServiceAdapter async port conformance — v16.5 #N.9+ (separate major refactor)

---

## Task Sequence Overview

| Task | Scope | Est. commits |
|------|-------|--------------|
| **T0** Worktree setup | Create `phase-126-v16-5-n8` worktree from master | 0 (infra) |
| **T1** Fix 2-dot relative paths in 5 re-export shims | 1 atomic commit | 1 |
| **T2** T5.4 useAgentTask cast cleanup | tighten buildPlanRequestBody + handleStreamEvent; drop 2 casts | 2-3 |
| **T3** CVG presentation adapter layer | Extract `apps/studio_api/cvg_adapter.py`; route migration | 5-8 |
| **T4** Backend Pydantic re-export from lingwen-shared | `health.py`, `studio.py`, `workflow.py`, `decision.py`; update consumers | 4-8 |
| **T5** Verification + handoff | Tests + docs | 2-3 |

**Total estimated commits: 14-23** (excluding T0 setup).

---

## Task T0: Worktree Setup

**Goal:** Isolate v16.5 #N.8 work from master for safe execution + review.

**Files:**
- Modify: `.worktrees/phase-126-v16-5-n8/` (NEW worktree)

- [ ] **Step 1: Create worktree from master**

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-126-v16-5-n8 -b phase-126-v16-5-n8 master
```

Expected: Worktree created at `.worktrees/phase-126-v16-5-n8`, branch `phase-126-v16-5-n8` created from `master` at `59356faf`.

- [ ] **Step 2: Verify worktree state**

```bash
cd .worktrees/phase-126-v16-5-n8
git log --oneline -3
git status
ls .worktrees/ 2>/dev/null  # should NOT show nested worktree
```

Expected: 3 latest commits at `59356faf / 55a9d870 / 7b88adce`, clean working tree.

- [ ] **Step 3: Run baseline verification**

```bash
cd .worktrees/phase-126-v16-5-n8
cd apps/dashboard && pnpm vitest run --reporter=dot 2>&1 | tail -5
cd ../..
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q 2>&1 | tail -3
```

Expected: vitest shows baseline (1733 tests), pytest shows 113 passed.

**Note:** Continue all subsequent tasks from within `.worktrees/phase-126-v16-5-n8`.

---

## Task T1: Fix 2-dot Relative Paths in 5 Re-export Shims

**Files:**
- Modify: `packages/dashboard-contracts/src/shared/{cvg,decisions,health,studio,workflows}.ts`

**Context:** All 5 re-export shims use `'../../lingwen-shared/...'` (2-dot). Realpath confirms 3-dot is correct: `../../../lingwen-shared/src/lingwen_shared/contracts/ts/X.ts`. Pre-existing vue-tsc errors documented in v16.5 #N.7 handoff §3.

- [ ] **Step 1: Verify the path issue is real (baseline)**

```bash
cd .worktrees/phase-126-v16-5-n8
pnpm --filter @lingwen/dashboard-contracts exec tsc --noEmit 2>&1 | head -10
```

Expected: vue-tsc/TypeScript errors mentioning "Cannot find module '../../lingwen-shared/...'" or similar.

Note: If running vue-tsc shows no errors (because TypeScript module resolution is permissive), this task may be primarily a hygiene fix rather than a correctness one. Adjust expected output accordingly.

- [ ] **Step 2: Fix paths in all 5 shims (one commit covering all 5 files)**

Edit each of these files to change the import path from 2-dot to 3-dot:

**`packages/dashboard-contracts/src/shared/cvg.ts`** — line 15:
```ts
// BEFORE
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/cvg';

// AFTER
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/cvg';
```

**`packages/dashboard-contracts/src/shared/decisions.ts`** — line 7:
```ts
// BEFORE
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/decisions';

// AFTER
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/decisions';
```

**`packages/dashboard-contracts/src/shared/health.ts`** — line 16:
```ts
// BEFORE
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/health';

// AFTER
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/health';
```

**`packages/dashboard-contracts/src/shared/studio.ts`** — line 26:
```ts
// BEFORE
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/studio';

// AFTER
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/studio';
```

**`packages/dashboard-contracts/src/shared/workflows.ts`** — line 8:
```ts
// BEFORE
} from '../../lingwen-shared/src/lingwen_shared/contracts/ts/workflows';

// AFTER
} from '../../../lingwen-shared/src/lingwen_shared/contracts/ts/workflows';
```

- [ ] **Step 3: Verify with build**

```bash
cd .worktrees/phase-126-v16-5-n8
pnpm --filter @lingwen/dashboard-contracts exec tsc --noEmit 2>&1 | head -10
cd apps/dashboard && pnpm vue-tsc --noEmit 2>&1 | tail -10
```

Expected: vue-tsc errors reduced by 5 (or to 0 if they were the source).

- [ ] **Step 4: Run vitest to confirm no regression**

```bash
cd .worktrees/phase-126-v16-5-n8/apps/dashboard
pnpm vitest run --reporter=dot 2>&1 | tail -5
```

Expected: 1733 tests pass (same as baseline).

- [ ] **Step 5: Commit**

```bash
cd .worktrees/phase-126-v16-5-n8
git add packages/dashboard-contracts/src/shared/{cvg,decisions,health,studio,workflows}.ts
git commit -m "fix(dashboard-contracts): v16.5 #N.8 — fix 2-dot relative paths in 5 re-export shims"
```

Expected: Single commit with all 5 path fixes.

**Lesson learned from v16.5 #N.7:** These 2-dot paths are pre-existing on master baseline (introduced in v16.5 #7 when manual DTOs were first created with re-export pattern). Hygiene gate: prefer 3-dot from the start.

---

## Task T2: T5.4 useAgentTask Cast Cleanup

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts`

**Context:** From v16.5 #N.7 handoff §3, two `as unknown as` casts at useAgentTask.ts:344-345. The "fix" requires either tightening `buildPlanRequestBody` return type OR widening `handleStreamEvent` shape. Investigation reveals that the actual `body` shape sent by `useAgentTask` (action, action_label, scope, body_draft, style_strength, allow_worldbuilding_fill, goal_tag, execution_mode, lens, provider_mode) **does not match** the canonical `CreatorAgentPlanRequest` DTO (action_label only + base_text? + lens? + provider_mode?).

Backend uses `model_config = ConfigDict(extra="ignore")` which silently drops unknown fields. This means backend actually accepts the broader payload but the typed DTO is narrower.

**Decision:** Document the drift. Two options:
- **(A)** Widen `CreatorAgentPlanRequest` to match the actual request shape (backend-shape dominant) — single source of truth
- **(B)** Keep current DTO + document drift in useAgentTask + keep cast — minimal scope

Given scope of v16.5 #N.8 and risk that backend schema changes would break either route, take **(A)**: add the broader shape as a separate Pydantic subclass `CreatorAgentPlanRequestFull` in `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py`, then typed wrapper uses `CreatorAgentPlanRequestFull`. Backend endpoint accepts either via `Union[CreatorAgentPlanRequest, CreatorAgentPlanRequestFull]` discriminated by missing `base_text`.

But this expands scope significantly. **Take simplified option (B)**: tighten type sigs, keep casts but document why each cast is needed.

- [ ] **Step 1: Investigate actual backend endpoint schema**

```bash
cd .worktrees/phase-126-v16-5-n8
grep -B2 -A40 "async def run_creator_agent_plan" apps/studio_api/routes/creator_core.py | head -60
```

Expected: Discover backend Pydantic model used for the request. Confirm `model_config = ConfigDict(extra="ignore")` allows extra fields.

- [ ] **Step 2: Decide on scope**

Review the grep output. If backend uses an extended Pydantic model that mirrors useAgentTask's actual body shape, the cleanup is type-only.

- [ ] **Step 3: Update `buildPlanRequestBody` return type signature (line 107)**

In `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:107`, change:
```ts
// BEFORE
buildPlanRequestBody: (action: string, actionLabel: string, scope: AgentScope, controls: AgentControls) => Record<string, unknown>;

// AFTER
buildPlanRequestBody: (action: string, actionLabel: string, scope: AgentScope, controls: AgentControls) => CreatorAgentPlanRequest;
```

Add the import at the top:
```ts
import type { CreatorAgentPlanRequest, CreatorAgentStreamEvent } from '@lingwen/dashboard-contracts/shared';
```

- [ ] **Step 4: Update `handleStreamEvent` type signature (line 116)**

In `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:116`, change:
```ts
// BEFORE
handleStreamEvent: (evt: { type?: string; message?: string; label?: string; text?: string; source?: string }) => void;

// AFTER
handleStreamEvent: (evt: CreatorAgentStreamEvent | { type?: string }) => void;
```

The `| { type?: string }` widening keeps current call site compatibility (since runtime emits `evt.type === 'status'` which matches `start` pattern but may not match `error` shape exactly).

- [ ] **Step 5: Try removing the casts**

In `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:344-345`, change:
```ts
// BEFORE
const result = await runCreatorAgentPlanStream(
  body as unknown as Parameters<typeof runCreatorAgentPlanStream>[0],
  handleStreamEvent as unknown as (event: unknown) => void,
) as Record<string, unknown>;

// AFTER
const result = await runCreatorAgentPlanStream(
  body,
  handleStreamEvent as (event: CreatorAgentStreamEvent | { type?: string }) => void,
) as CreatorAgentPlanResult;
```

If `tsc --noEmit` complains (because the runtime types don't quite match), add a JSDoc comment documenting why the cast remains:
```ts
// v16.5 #N.8: handleStreamEvent runtime signature is broader than
// CreatorAgentStreamEvent (parser may emit untyped events during transitions).
```

- [ ] **Step 6: Verify with tsc + tests**

```bash
cd .worktrees/phase-126-v16-5-n8/apps/dashboard
pnpm vue-tsc --noEmit 2>&1 | tail -10
pnpm vitest run tests/unit/composables/useCreatorAgent/ 2>&1 | tail -10
```

Expected: tsc 0 errors (or only on the documented leftover cast), tests pass.

- [ ] **Step 7: Commit**

```bash
cd .worktrees/phase-126-v16-5-n8
git add apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts
git commit -m "refactor(dashboard): v16.5 #N.8 — T5.4 useAgentTask cast cleanup"
```

**Lesson:** when DTO drift exists between frontend DTO and backend reality, document the cast with a JSDoc reason rather than chasing a typed shape that doesn't match runtime.

---

## Task T3: CVG Presentation Adapter Layer

**Files:**
- Create: `apps/studio_api/cvg_adapter.py`
- Modify: `apps/studio_api/routes/cvg.py` (likely uses protocols.Ripple*Response)
- Modify: `apps/studio_api/protocols.py` — remove CVG-related code OR keep with deprecation comment
- Create: `tests/api/test_cvg_adapter.py`

**Context:** Backend storage `RippleListItemResponse` (in protocols.py:706) uses `source_chapter: int` + `target_chapter: int`. Lingwen-shared presentation shape uses `chapter_id: int` + `source_volume: int` + `impact_volumes: list[int]`. Routes must continue to map storage → presentation at the response boundary (documented in `cvg.py:18-24` PYDANTIC-DRIFT marker).

- [ ] **Step 1: Locate CVG-related route code**

```bash
cd .worktrees/phase-126-v16-5-n8
grep -rln "RippleListItemResponse\|RippleDetailResponse\|CascadeResponse" apps/studio_api/ | head -10
```

Expected: `apps/studio_api/routes/cvg.py` is primary consumer.

- [ ] **Step 2: Read existing CVG route response construction**

```bash
cd .worktrees/phase-126-v16-5-n8
grep -B2 -A20 "def.*ripples\|def.*cascade\|def.*reference_graph" apps/studio_api/routes/cvg.py | head -60
```

Document where the storage → presentation mapping currently happens.

- [ ] **Step 3: Write failing test for CVG adapter**

Create `tests/api/test_cvg_adapter.py`:
```python
"""Tests for the CVG storage → presentation adapter.

Phase 126 v16.5 #N.8 carryover from v16.5 #N.7 §3 PYDANTIC-DRIFT marker.
"""
from datetime import datetime

from apps.studio_api.cvg_adapter import (
    ripple_storage_to_presentation,
    ripple_storage_list_to_presentation,
    cascade_storage_to_presentation,
)
from infra.cross_volume.reference_graph import CascadedRipple  # adjust import


def test_ripple_storage_to_presentation_basic():
    """Storage shape (source_chapter/target_chapter) maps to presentation (chapter_id/source_volume/impact_volumes)."""
    storage_ripple = {
        "ripple_id": "r-1",
        "source_chapter": 10,
        "target_chapter": 15,
        "status": "pending",
        "created_at": datetime(2026, 8, 30, 12, 0),
        "relationship_type": "character_reference",
        "dimension": "character",
    }
    result = ripple_storage_to_presentation(storage_ripple)
    assert result.chapter_id == 10  # source_chapter → chapter_id
    assert result.source_volume == 1  # computed from chapter range
    assert result.impact_volumes == [1]  # computed from target_chapter


def test_ripple_storage_list_to_preserves_order():
    """List conversion preserves input order."""
    storage_list = [
        {"ripple_id": "a", "source_chapter": 1, "target_chapter": 5, "status": "pending", "created_at": datetime(2026, 1, 1), "relationship_type": "x", "dimension": "y"},
        {"ripple_id": "b", "source_chapter": 2, "target_chapter": 6, "status": "pending", "created_at": datetime(2026, 1, 2), "relationship_type": "x", "dimension": "y"},
    ]
    results = ripple_storage_list_to_presentation(storage_list)
    assert [r.ripple_id for r in results] == ["a", "b"]
```

- [ ] **Step 4: Run test to verify it fails**

```bash
cd .worktrees/phase-126-v16-5-n8
/home/ailearn/miniconda3/bin/python -m pytest tests/api/test_cvg_adapter.py -v 2>&1 | tail -10
```

Expected: FAIL with `ModuleNotFoundError: No module named 'apps.studio_api.cvg_adapter'`.

- [ ] **Step 5: Implement minimal adapter**

Create `apps/studio_api/cvg_adapter.py` with shape:
```python
"""CVG (Cross-Volume Graph) storage → presentation adapter.

Phase 126 v16.5 #N.8: Extracted from apps/studio_api/protocols.py.
Maps backend storage models (source_chapter/target_chapter) to lingwen-shared
presentation models (chapter_id/source_volume/impact_volumes).

Boundary: backend storage owns persistence shape; lingwen_shared contracts own
the wire/UI shape. The adapter is the ONLY place where the mapping happens.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from lingwen_shared.contracts.python.cvg import (
    RippleListItemResponse,
    RippleDetailResponse,
    CascadeNodeResponse,
    CascadeEdgeResponse,
    CascadeResponse,
)


def _parse_dt(value: Any) -> str:
    """Storage datetime → ISO string for presentation."""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def ripple_storage_to_presentation(storage: dict[str, Any]) -> RippleListItemResponse:
    """Convert backend Ripple storage dict → presentation RippleListItemResponse."""
    source_chapter = storage.get("source_chapter", 0)
    target_chapter = storage.get("target_chapter", source_chapter)
    # Volume computation: assume 1 volume for prototype, refine per project needs
    source_volume = storage.get("source_volume", 1)
    impact_volumes = storage.get("impact_volumes", [storage.get("target_volume", source_volume)])
    return RippleListItemResponse(
        ripple_id=storage.get("ripple_id", ""),
        chapter_id=source_chapter,
        title=storage.get("title", ""),
        status=storage.get("status", "pending"),
        source_volume=source_volume,
        impact_volumes=impact_volumes,
        created_at=_parse_dt(storage.get("created_at")),
        updated_at=_parse_dt(storage.get("updated_at")) if storage.get("updated_at") else None,
        proposed_by=storage.get("proposed_by"),
        applies_count=storage.get("applies_count"),
    )


def ripple_storage_list_to_presentation(storage_list: list[dict[str, Any]]) -> list[RippleListItemResponse]:
    return [ripple_storage_to_presentation(s) for s in storage_list]


def cascade_storage_to_presentation(storage: dict[str, Any]) -> CascadeResponse:
    """Convert backend Cascade storage → presentation CascadeResponse."""
    # ... similar mapping
    return CascadeResponse(
        cascade_id=storage.get("cascade_id", ""),
        nodes=[],  # populate from storage
        edges=[],  # populate from storage
    )
```

(Exact field mappings depend on actual backend storage shape — investigate first via grep.)

- [ ] **Step 6: Run tests to verify GREEN**

```bash
cd .worktrees/phase-126-v16-5-n8
/home/ailearn/miniconda3/bin/python -m pytest tests/api/test_cvg_adapter.py -v 2>&1 | tail -10
```

Expected: PASS.

- [ ] **Step 7: Update CVG route to use adapter**

In `apps/studio_api/routes/cvg.py`, replace inline mapping (if any) with adapter calls.

- [ ] **Step 8: Run full backend CVG route tests**

```bash
cd .worktrees/phase-126-v16-5-n8
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_routes.py -v 2>&1 | tail -10
```

Expected: PASS (no regression).

- [ ] **Step 9: Commit**

```bash
cd .worktrees/phase-126-v16-5-n8
git add apps/studio_api/cvg_adapter.py apps/studio_api/routes/cvg.py tests/api/test_cvg_adapter.py
git commit -m "feat(studio-api): v16.5 #N.8 — extract CVG presentation adapter from protocols.py"
```

---

## Task T4: Backend Pydantic Re-export from lingwen-shared

**Files:**
- Modify: `apps/studio_api/models/health.py`
- Modify: `apps/studio_api/models/studio.py`
- Modify: `apps/studio_api/models/workflow.py`
- Modify: `apps/studio_api/models/decision.py`
- Modify: `apps/studio_api/protocols.py` (keep storage models; remove re-importable subsets)
- Modify: route files that import from `studio_api.models.X` (likely keep working via re-export)

**Context:** Backend Pydantic models in `apps/studio_api/models/*.py` essentially duplicate the canonical models in `packages/lingwen-shared/src/lingwen_shared/contracts/python/`. Default values match (verified for `studio.py:49 creation_mode: str = "studio"`).

**Strategy:** Replace each `models/X.py` body with `from lingwen_shared.contracts.python.X import *` (or explicit re-exports) so backend imports keep working but canonical is the source. Keep models that don't have lingwen-shared equivalents.

- [ ] **Step 1: Diff models/health.py vs lingwen-shared/contracts/python/health.py**

```bash
cd .worktrees/phase-126-v16-5-n8
diff <(grep "class\|:" apps/studio_api/models/health.py | head -30) \
     <(grep "class\|:" packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py | head -30)
```

Confirm field-level compatibility. Lingwen-shared should be a strict superset.

- [ ] **Step 2: Write re-export shim for health.py**

Replace `apps/studio_api/models/health.py` content with:
```python
"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.8: Backend models are now re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py``.
The canonical Pydantic v2 source-of-truth lives in lingwen-shared.
"""
from lingwen_shared.contracts.python.health import (
    DatabaseStatus,
    MemoryUsage,
    HealthResponse,
    OverviewResponse,
    ChapterData,
    ChaptersResponse,
    ProductionRecordResponse,
    ProductionRecordsResponse,
    ProductionBatchRollupResponse,
    ProductionRollupResponse,
    ProductionCostTrendPointResponse,
    ProductionCostTrendResponse,
)

__all__ = [
    "DatabaseStatus",
    "MemoryUsage",
    "HealthResponse",
    "OverviewResponse",
    "ChapterData",
    "ChaptersResponse",
    "ProductionRecordResponse",
    "ProductionRecordsResponse",
    "ProductionBatchRollupResponse",
    "ProductionRollupResponse",
    "ProductionCostTrendPointResponse",
    "ProductionCostTrendResponse",
]
```

- [ ] **Step 3: Run backend tests that import health models**

```bash
cd .worktrees/phase-126-v16-5-n8
grep -rln "from apps.studio_api.models.health import\|from studio_api.models.health import" apps/ infra/ tests/ | head -5
/home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_health_route.py -v 2>&1 | tail -10
```

Expected: PASS (re-exports preserve import paths).

- [ ] **Step 4: Commit health.py re-export**

```bash
cd .worktrees/phase-126-v16-5-n8
git add apps/studio_api/models/health.py
git commit -m "refactor(studio-api): v16.5 #N.8 — health.py re-exports lingwen-shared canonical models"
```

- [ ] **Step 5: Repeat for studio.py, workflow.py, decision.py (one commit per file)**

For each file, follow Steps 2-4 above. Use the class list already enumerated in `packages/lingwen-shared/src/lingwen_shared/contracts/python/{studio,workflows,decisions}.py`.

- [ ] **Step 6: Diff protocols.py CVG section vs cvg.py**

After Task T3 adapter extraction, the CVG models in `protocols.py:706+` can be removed (replaced by lingwen-shared cvg.py + adapter).

Replace `protocols.py` CVG section with:
```python
# CVG models re-exported from lingwen-shared after v16.5 #N.8 adapter extraction
from lingwen_shared.contracts.python.cvg import (
    RippleListItemResponse,
    RippleDetailResponse,
    RippleActionResponse,
    RippleStatsResponse,
    RippleAuditEntryResponse,
    RippleRollbackRequest,
    RippleActionRequest,
    CascadeNodeResponse,
    CascadeEdgeResponse,
    CascadeResponse,
    CascadePreviewResponse,
    CascadeRunResponse,
    CascadeUpdatePayload,
    CascadeCancelPayload,
    CascadeCancelRequest,
)
```

- [ ] **Step 7: Run full backend test suite to catch any breakage**

```bash
cd .worktrees/phase-126-v16-5-n8
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ tests/infra/ packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q 2>&1 | tail -10
```

Expected: All 113+ backend tests pass.

- [ ] **Step 8: Commit protocols.py re-export**

```bash
cd .worktrees/phase-126-v16-5-n8
git add apps/studio_api/protocols.py
git commit -m "refactor(studio-api): v16.5 #N.8 — protocols.py CVG models re-exports lingwen-shared"
```

---

## Task T5: Verification + Handoff

**Files:**
- Modify: `apps/studio/CLAUDE.md` — add v16.5 #N.8 closure section
- Create: `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n8-cleanup-and-backend-re-export-handoff.md`

- [ ] **Step 1: Full verification gate**

```bash
cd .worktrees/phase-126-v16-5-n8
cd apps/dashboard && pnpm vitest run 2>&1 | tail -5
cd ../..
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q 2>&1 | tail -3
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/ apps/studio_api/tests/ -q 2>&1 | tail -3
cd apps/dashboard && pnpm vue-tsc --noEmit 2>&1 | tail -3
cd ../..
ruff check apps/studio_api/ packages/lingwen-shared/ 2>&1 | tail -3
pnpm knip 2>&1 | tail -5
```

Expected:
- vitest: 1733+ tests pass
- pytest: 113+ shared + ~400 infra/studio_api pass
- vue-tsc: 0 errors (or reduced from baseline)
- ruff: 0 errors
- knip: 0 errors (with any allowable advisories documented)

- [ ] **Step 2: Write handoff doc**

Create `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n8-cleanup-and-backend-re-export-handoff.md` with sections:
- §0 TL;DR
- §1 Files Created/Modified
- §2 Migration Pattern
- §3 Drift Notes (any new drift found during T2/T3)
- §4 Verification Matrix (before/after gate counts)
- §5 Lessons Learned
- §6 Carryover to v16.5 #N.9+

- [ ] **Step 3: Update CLAUDE.md v16.5 #N.8 section**

Add closure section following v16.5 #N.7 pattern. Include:
- Commit count + branch info
- Migration pattern
- Lessons (specifically about PYDANTIC-DRIFT resolution + cast+document pattern)
- Carryover list

- [ ] **Step 4: Push branch**

```bash
cd .worktrees/phase-126-v16-5-n8
git push -u origin phase-126-v16-5-n8
```

Expected: Branch pushed to origin.

- [ ] **Step 5: Final commit + cleanup**

```bash
cd .worktrees/phase-126-v16-5-n8
git add docs/ apps/studio/CLAUDE.md
git commit -m "docs(phase-126): v16.5 #N.8 — handoff + CLAUDE.md closure"
git push origin phase-126-v16-5-n8
```

---

## Carryover to v16.5 #N.9+

Documented in handoff §6:

1. **Async port conformance** — `LLMServiceAdapter` is sync; rewrite with `async execute → LLMResult` requires all 12 tools/* + 4 backend route consumers to become async. Major refactor (~16-25 commits)
2. **39 `as unknown as` casts** in `apps/dashboard/src/composables/` — pre-existing fragile patterns from v16.2.x typed-wrapper era. Each needs investigation + JSDoc documentation OR body-shape tightening.
3. **Chapter model re-export** — `apps/studio_api/models/chapter.py` may already be in lingwen-shared. Verify and re-export.
4. **chapter.py in lingwen-shared** — `ChapterDTO` already exists (per v16.1 T2); verify chapter.py backend model uses same name.

---

## Lessons Captured (anticipated)

1. **DTO drift resolution**: When frontend `as unknown as` cast exists, the fix usually requires backend-shape knowledge (not just frontend type tightening). Document the cast with reason rather than chasing impossible types.

2. **Storage/presentation boundary**: Backend storage layer owns persistence shape (DB schema); lingwen-shared contracts own wire/UI shape. Adapter is the boundary.

3. **Re-export shim pattern preserves import paths**: `apps/studio_api/models/X.py` becomes a thin re-export of `lingwen_shared.contracts.python.X`. No consumer code changes needed.

4. **Path conventions must be 3-dot for workspace packages**: 2-dot paths from `packages/dashboard-contracts/src/shared/X.ts` to `packages/lingwen-shared/src/lingwen_shared/contracts/ts/X.ts` resolve to wrong directory. 3-dot (`../../../`) is correct.
