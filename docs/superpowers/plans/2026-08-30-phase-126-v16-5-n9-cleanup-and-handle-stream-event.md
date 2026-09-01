# Phase 126 v16.5 #N.9 — Workflow Split + Studio Re-export + CVG Adapter Wire-up + handleStreamEvent Tightening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the four medium-sized carryover items from v16.5 #N.8 handoff §6: (1) workflow.py split (BudgetSetRequest/TierSetRequest → new module, workflow.py → re-export shim), (2) studio.py backend Pydantic re-export, (3) CVG adapter wire-up into 4 route endpoints (list_ripples + 3 cascade endpoints), (4) `useAgentTask.handleStreamEvent` tightening to adopt the `CreatorAgentStreamEvent` discriminated union.

**Architecture:** Continue the four-layer architecture established in v16.5 #N.7/#N.8:
1. **Source of truth** = `packages/lingwen-shared/src/lingwen_shared/contracts/python/*.py` (Pydantic v2)
2. **Backend layer** = `apps/studio_api/models/*.py` re-exports the canonical models (where applicable)
3. **TS layer** = `tooling/contracts/generate.py` emits `packages/lingwen-shared/src/lingwen_shared/contracts/ts/*.ts` → `packages/dashboard-contracts/src/shared/*.ts` re-export shims → typed wrappers in `apps/dashboard/src/api/*.ts`
4. **CVG adapter** = `apps/studio_api/cvg_adapter.py` is the **SOLE** boundary where backend storage shape (`apps/studio_api/protocols.py`) maps to presentation shape (`lingwen_shared.contracts.python.cvg`)

**Tech Stack:** Python 3.13 / Pydantic v2 / FastAPI / pnpm + TypeScript strict / pytest / vitest / vue-tsc / ruff

**Reference:** v16.5 #N.8 handoff (`docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n8-cleanup-and-backend-re-export-handoff.md`) §6 carryover items 1, 2, 3 (item 4 = `useAgentTask handleStreamEvent`).

---

## Scope Check

Sub-project scope validation:
- workflow.py split is ONE backend re-export + structural split (similar to N.8 health/decision)
- studio.py re-export is ONE backend re-export (same pattern, 22 models)
- CVG adapter wire-up is ONE route migration (4 endpoints, the boundary marker already exists from N.8)
- handleStreamEvent tightening is ONE frontend type narrowing (smaller than N.8 T2)

Total estimated commits: ~12-18 (fits one phase, not requiring sub-project split).

---

## Branch Strategy

Branch from `origin/phase-126-v16-5-n8` (which contains the cvg_adapter.py scaffold + health.py/decision.py re-exports + useAgentTask buildPlanRequestBody tightening + 5 path fixes). N.9 builds on top of N.8's 5 commits.

**Prerequisite:** The N.8 branch is currently pushed to origin but NOT merged to master. N.9 will be developed on a new branch `phase-126-v16-5-n9` based on `origin/phase-126-v16-5-n8`. The eventual PR can include both N.8 + N.9 commits (single reviewer pass for the full Phase 126 v16.5 #N arc).

---

## File Structure

### Files Modified This Phase

```
apps/studio_api/models/
├── workflow.py                       # MODIFIED: thin re-export shim from lingwen-shared
├── budget.py                         # NEW: BudgetSetRequest + BudgetTierSetRequest (local DTOs, not in lingwen-shared)
└── studio.py                         # MODIFIED: thin re-export shim from lingwen-shared (22 models)

apps/studio_api/routes/
├── budgets.py                        # MODIFIED: import BudgetSetRequest + BudgetTierSetRequest from new location
├── cvg.py                            # MODIFIED: 4 endpoints call cvg_adapter

apps/studio_api/cvg_adapter.py        # UNCHANGED (boundary marker from N.8)
apps/studio_api/helpers/cvg.py        # UNCHANGED (still provides storage-shape helpers)

apps/studio_api/protocols.py          # UNCHANGED (storage models stay; lingwen-shared owns presentation)

apps/dashboard/src/composables/useCreatorAgent/
└── useAgentTask.ts                   # MODIFIED: handleStreamEvent signature tightened to CreatorAgentStreamEvent

packages/dashboard-contracts/src/shared/
└── creator.ts                        # POSSIBLY MODIFIED: CreatorAgentStreamEvent extension if needed

docs/superpowers/handoffs/
└── 2026-08-30-phase-126-v16-5-n9-cleanup-and-handle-stream-event-handoff.md  # NEW
```

### Files NOT Modified (deferred to v16.5 #N.10+)

- `tools/llm_*.py` — completed in v16.5 #N.6
- `infra/*` sqlite3 imports — completed in v16.5 #N.3/#N.4
- `apps/studio_api/models/chapter.py` — chapter models live in lingwen-shared but verification deferred (per N.8 plan)
- `apps/studio_api/models/creator_*.py` — Phase 124 lingwen_creator package owns these (already re-exported)
- Async port conformance (`LLMServiceAdapter` sync → `async execute → LLMResult`) — ~16-25 commits, separate phase
- 39 `as unknown as` cast cleanup — pre-existing fragile patterns, separate phase
- Other 11 CVG route endpoints (apply_ripple / reject_ripple / get_ripple_audit / export_ripple_audit / rollback_ripple / get_ripple_stats / get_reference_graph / get_ripple_detail / get_ripple_cascade_v9_20 etc.) — currently return ActionResponse/AuditResponse/StatsResponse which are also drift candidates but more complex

---

## Task Sequence Overview

| Task | Scope | Est. commits |
|------|-------|--------------|
| **T0** Worktree setup | Create `phase-126-v16-5-n9` from `origin/phase-126-v16-5-n8` | 0 (infra) |
| **T1** Budget DTOs split + workflow.py re-export | New `budget.py` + `workflow.py` shim + `routes/budgets.py` import update | 3-4 |
| **T2** studio.py re-export | Thin re-export shim for 22 models | 1-2 |
| **T3** CVG adapter wire-up (ripples) | `list_ripples` uses `cvg_adapter.ripple_storage_to_presentation` | 3-4 |
| **T4** CVG adapter wire-up (cascades) | 3 cascade endpoints use `cvg_adapter.cascade_*_storage_to_presentation` | 2-4 |
| **T5** handleStreamEvent tightening | Adopt `CreatorAgentStreamEvent`; drop legacy fields/casts | 1-2 |
| **T6** Verification + handoff | Tests + docs + push | 2-3 |

**Total estimated commits: 12-21** (excluding T0 setup).

---

## Task T0: Worktree Setup

**Goal:** Isolate v16.5 #N.9 work from master for safe execution + review.

**Files:**
- Modify: `.worktrees/phase-126-v16-5-n9/` (NEW worktree)

- [ ] **Step 1: Create worktree from origin/phase-126-v16-5-n8**

```bash
cd /home/ailearn/projects/LingWen
git fetch origin
git worktree add .worktrees/phase-126-v16-5-n9 -b phase-126-v16-5-n9 origin/phase-126-v16-5-n8
```

Expected: Worktree created at `.worktrees/phase-126-v16-5-n9`, branch `phase-126-v16-5-n9` created from `origin/phase-126-v16-5-n8` at `24530ea5`.

- [ ] **Step 2: Verify worktree state**

```bash
cd .worktrees/phase-126-v16-5-n9
git log --oneline -6
git status
```

Expected: 6 latest commits at N.8 closure (`24530ea5` handoff + 5 task commits), clean working tree.

- [ ] **Step 3: Run baseline verification**

```bash
cd .worktrees/phase-126-v16-5-n9/apps/dashboard
pnpm vitest run --reporter=dot 2>&1 | tail -5
cd ../../..
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q 2>&1 | tail -3
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -q 2>&1 | tail -5
```

Expected: vitest shows 1733 + 1 skipped; shared pytest shows 113 passed; studio_api pytest shows ~40 passed (including 5 NEW cvg_adapter tests from N.8).

**Note:** Continue all subsequent tasks from within `.worktrees/phase-126-v16-5-n9`.

---

## Task T1: Budget DTOs Split + workflow.py Re-export

**Files:**
- Create: `apps/studio_api/models/budget.py`
- Modify: `apps/studio_api/models/workflow.py` (replace with re-export shim)
- Modify: `apps/studio_api/models/__init__.py` (re-export from new budget module)
- Modify: `apps/studio_api/routes/budgets.py` (update import path)

**Context:** `workflow.py` (83 lines) currently mixes 5 workflow models (re-export candidates from `lingwen_shared.contracts.python.workflows`) + 2 budget DTOs (`BudgetSetRequest` + `BudgetTierSetRequest`) that are NOT in lingwen-shared. Splitting aligns workflow.py with the v16.5 #N.7/#N.8 re-export pattern. Budget DTOs stay local (they're orthogonal to the workflow bounded context).

Verified field-by-field equivalence for workflow models in N.7 promotion. lingwen-shared `workflows.py` has `model_config = ConfigDict(extra="ignore")`; backend `workflow.py` does not (preserved behavior).

- [ ] **Step 1: Verify field-level compatibility for workflow models**

```bash
cd .worktrees/phase-126-v16-5-n9
python -c "
from apps.studio_api.models.workflow import WorkflowListItem, RunWorkflowRequest, ResumeWorkflowRequest, WorkflowStatusResponse, WorkflowMermaidResponse
from lingwen_shared.contracts.python.workflows import (
    WorkflowListItem as SharedListItem,
    RunWorkflowRequest as SharedRunReq,
    ResumeWorkflowRequest as SharedResumeReq,
    WorkflowStatusResponse as SharedStatusResp,
    WorkflowMermaidResponse as SharedMermaidResp,
)
import sys
# Field name comparison
for backend, shared, name in [
    (WorkflowListItem, SharedListItem, 'WorkflowListItem'),
    (RunWorkflowRequest, SharedRunReq, 'RunWorkflowRequest'),
    (ResumeWorkflowRequest, SharedResumeReq, 'ResumeWorkflowRequest'),
    (WorkflowStatusResponse, SharedStatusResp, 'WorkflowStatusResponse'),
    (WorkflowMermaidResponse, SharedMermaidResp, 'WorkflowMermaidResponse'),
]:
    b_fields = set(backend.model_fields.keys())
    s_fields = set(shared.model_fields.keys())
    if b_fields == s_fields:
        print(f'{name}: field set match ({len(b_fields)} fields)')
    else:
        print(f'{name}: DIFF backend-only={b_fields - s_fields}, shared-only={s_fields - b_fields}')
        sys.exit(1)
"
```

Expected: All 5 models print "field set match".

- [ ] **Step 2: Create `apps/studio_api/models/budget.py`**

Create the new file with the two budget DTOs (verbatim copy from current `workflow.py`):

```python
"""Budget DTOs for the workflows bounded context.

Phase 126 v16.5 #N.9: Extracted from ``apps/studio_api/models/workflow.py``
because BudgetSetRequest / BudgetTierSetRequest are orthogonal to the
workflow bounded context — they're budget-alarm DTOs that happen to share
a module with workflow models for historical reasons.

These DTOs are NOT promoted to ``lingwen_shared`` because:
- They are server-side only (no dashboard surface)
- They are persistence-coupled (Field constraints match the cost_tracker
  SQLite row schema)
- The dashboard does not consume them directly

Endpoints that use these:
- ``POST /workflows/budget`` → BudgetSetRequest (per-day / per-week USD)
- ``POST /workflows/budget/tier`` → BudgetTierSetRequest (per-tier USD)
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BudgetSetRequest(BaseModel):
    """Phase 8.12 T5: 设置 day/week budget (per-run 不暴露, run 启动时传)"""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"


class BudgetTierSetRequest(BaseModel):
    """Phase 8.15 T6: 设置 tier budget (haiku/sonnet/opus 各自)."""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"


__all__ = ["BudgetSetRequest", "BudgetTierSetRequest"]
```

- [ ] **Step 3: Replace `workflow.py` with thin re-export shim**

```bash
cd .worktrees/phase-126-v16-5-n9
```

Replace `apps/studio_api/models/workflow.py` content with:

```python
"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.9: Workflow models are now thin re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/workflows.py``.
The canonical Pydantic v2 source-of-truth lives in lingwen-shared.

Budget DTOs (BudgetSetRequest, BudgetTierSetRequest) are NOT here — they
have been moved to ``apps/studio_api/models/budget.py`` because they're
orthogonal to the workflow bounded context.
"""
from lingwen_shared.contracts.python.workflows import (
    WorkflowListItem,
    RunWorkflowRequest,
    ResumeWorkflowRequest,
    WorkflowStatusResponse,
    WorkflowMermaidResponse,
)

__all__ = [
    "WorkflowListItem",
    "RunWorkflowRequest",
    "ResumeWorkflowRequest",
    "WorkflowStatusResponse",
    "WorkflowMermaidResponse",
]
```

- [ ] **Step 4: Update `apps/studio_api/models/__init__.py` to export BudgetSetRequest + BudgetTierSetRequest**

Look up current `__init__.py` content for workflow module:
```bash
cd .worktrees/phase-126-v16-5-n9
grep -n "BudgetSetRequest\|BudgetTierSetRequest\|workflow" apps/studio_api/models/__init__.py
```

Add `from apps.studio_api.models.budget import BudgetSetRequest, BudgetTierSetRequest` (alphabetical order) to maintain `from apps.studio_api.models import BudgetSetRequest` import surface.

- [ ] **Step 5: Update `apps/studio_api/routes/budgets.py` import path**

```bash
cd .worktrees/phase-126-v16-5-n9
grep -n "BudgetSetRequest\|BudgetTierSetRequest" apps/studio_api/routes/budgets.py
```

Change `from apps.studio_api.models.workflow import BudgetSetRequest, BudgetTierSetRequest` → `from apps.studio_api.models.budget import BudgetSetRequest, BudgetTierSetRequest`.

Verify all usages are preserved via grep:
```bash
cd .worktrees/phase-126-v16-5-n9
grep -rn "from apps.studio_api.models.workflow import" apps/ infra/ tests/ packages/ 2>&1 | grep -i "budget"
```

Expected: NO matches (only workflow models remain imported from workflow.py).

- [ ] **Step 6: Run tests**

```bash
cd .worktrees/phase-126-v16-5-n9
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -q 2>&1 | tail -5
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_workflow_route.py apps/studio_api/tests/test_budget_route.py -v 2>&1 | tail -10
```

Expected: All tests pass; workflow route tests confirm `WorkflowListItem` etc. work via re-export; budget route tests confirm `BudgetSetRequest` works from new location.

- [ ] **Step 7: Commit budget.py**

```bash
cd .worktrees/phase-126-v16-5-n9
git add apps/studio_api/models/budget.py apps/studio_api/models/__init__.py apps/studio_api/routes/budgets.py
git commit -m "refactor(studio-api): v16.5 #N.9 — split BudgetSetRequest/TierSetRequest into apps/studio_api/models/budget.py

Extracts the 2 budget DTOs from workflow.py (where they were mixed with
workflow models) into a new apps/studio_api/models/budget.py module.

Rationale: BudgetSetRequest and BudgetTierSetRequest are orthogonal to
the workflow bounded context — they're budget-alarm DTOs that happen to
share a module with workflow models for historical reasons. They are NOT
promoted to lingwen-shared because they're server-side only.

Updates apps/studio_api/routes/budgets.py import path to point at the
new location. Backward-compat: apps.studio_api.models still re-exports
both classes via __init__.py."
```

- [ ] **Step 8: Commit workflow.py re-export**

```bash
cd .worktrees/phase-126-v16-5-n9
git add apps/studio_api/models/workflow.py
git commit -m "refactor(studio-api): v16.5 #N.9 — workflow.py re-exports lingwen-shared canonical models

Replaces 5 manual Pydantic model definitions with re-exports from
packages/lingwen-shared/src/lingwen_shared/contracts/python/workflows.py.
Verified field-by-field equivalence (5 models: WorkflowListItem /
RunWorkflowRequest / ResumeWorkflowRequest / WorkflowStatusResponse /
WorkflowMermaidResponse).

Budget DTOs (BudgetSetRequest / BudgetTierSetRequest) were extracted to
apps/studio_api/models/budget.py in the prior commit. workflow.py now
exclusively re-exports workflow bounded context models.

Backend import paths unchanged (apps.studio_api.models.workflow.X).
__all__ preserves import surface for routes callers."
```

**Lesson from N.8:** Re-export shims use `from lingwen_shared.contracts.python.X import (...)` with explicit `__all__`. The lingwen-shared module adds `model_config = ConfigDict(extra='ignore')` which is stricter than backend behavior — but `extra='ignore'` only affects validation when EXTRA fields are sent, so backend behavior is preserved (no validation errors).

---

## Task T2: studio.py Re-export

**Files:**
- Modify: `apps/studio_api/models/studio.py` (replace with re-export shim)

**Context:** Same pattern as T1 workflow.py re-export. `studio.py` (217 lines, 22 models) maps 1:1 to `lingwen_shared.contracts.python.studio`. Field equivalence verified in N.7 promotion. The only notable difference: backend uses `creation_mode: str = 'studio'` as a required field with default; lingwen-shared uses `Optional[str] = 'studio'` — this is a Pydantic v2 strict-mode thing where the type is narrower. Need to verify with a quick test before committing.

- [ ] **Step 1: Verify field-level compatibility for studio models**

```bash
cd .worktrees/phase-126-v16-5-n9
python -c "
import sys
from apps.studio_api.models.studio import (
    StudioProjectItem, StudioProjectsResponse, StudioActiveResponse,
    StudioSetActiveRequest, StudioSummaryResponse, StudioQualityResponse,
    StudioQualityReportIssue, StudioQualityReportChapter, StudioProseHeatmapChapter,
    StudioProseHeatmap, StudioQualityReportResponse, StudioProseDiffTotals,
    StudioProseDiffChapter, StudioProseDiffResponse, StudioProseJudgeRating,
    StudioProseJudgeChapter, StudioProseJudgeSignal, StudioProseJudgeResponse,
    StudioPreflightChapter, StudioPreflightRequest, StudioPreflightResponse,
    StudioBatchRunRequest, StudioBatchJobResponse,
)
from lingwen_shared.contracts.python.studio import (
    StudioProjectItem as Shared0, StudioProjectsResponse as Shared1,
    StudioActiveResponse as Shared2, StudioSetActiveRequest as Shared3,
    StudioSummaryResponse as Shared4, StudioQualityResponse as Shared5,
    StudioQualityReportIssue as Shared6, StudioQualityReportChapter as Shared7,
    StudioProseHeatmapChapter as Shared8, StudioProseHeatmap as Shared9,
    StudioQualityReportResponse as Shared10, StudioProseDiffTotals as Shared11,
    StudioProseDiffChapter as Shared12, StudioProseDiffResponse as Shared13,
    StudioProseJudgeRating as Shared14, StudioProseJudgeChapter as Shared15,
    StudioProseJudgeSignal as Shared16, StudioProseJudgeResponse as Shared17,
    StudioPreflightChapter as Shared18, StudioPreflightRequest as Shared19,
    StudioPreflightResponse as Shared20, StudioBatchRunRequest as Shared21,
    StudioBatchJobResponse as Shared22,
)
backend_models = [StudioProjectItem, StudioProjectsResponse, StudioActiveResponse,
    StudioSetActiveRequest, StudioSummaryResponse, StudioQualityResponse,
    StudioQualityReportIssue, StudioQualityReportChapter, StudioProseHeatmapChapter,
    StudioProseHeatmap, StudioQualityReportResponse, StudioProseDiffTotals,
    StudioProseDiffChapter, StudioProseDiffResponse, StudioProseJudgeRating,
    StudioProseJudgeChapter, StudioProseJudgeSignal, StudioProseJudgeResponse,
    StudioPreflightChapter, StudioPreflightRequest, StudioPreflightResponse,
    StudioBatchRunRequest, StudioBatchJobResponse]
shared_models = [Shared0, Shared1, Shared2, Shared3, Shared4, Shared5, Shared6,
    Shared7, Shared8, Shared9, Shared10, Shared11, Shared12, Shared13, Shared14,
    Shared15, Shared16, Shared17, Shared18, Shared19, Shared20, Shared21, Shared22]
for b, s, n in zip(backend_models, shared_models, [m.__name__ for m in backend_models]):
    bf = set(b.model_fields.keys())
    sf = set(s.model_fields.keys())
    if bf != sf:
        print(f'{n}: DIFF backend-only={bf - sf}, shared-only={sf - bf}')
        sys.exit(1)
    print(f'{n}: field set match ({len(bf)} fields)')
"
```

Expected: All 23 models print "field set match".

- [ ] **Step 2: Verify studio route tests pass with both backend and shared**

```bash
cd .worktrees/phase-126-v16-5-n9
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_studio_route.py -q 2>&1 | tail -5
```

Expected: All studio route tests pass (no regression on field semantics).

- [ ] **Step 3: Replace `studio.py` with thin re-export shim**

```bash
cd .worktrees/phase-126-v16-5-n9
```

Replace `apps/studio_api/models/studio.py` content with:

```python
"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.9: Studio models are now thin re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py``.
The canonical Pydantic v2 source-of-truth lives in lingwen-shared.

Includes 23 Pydantic models covering the dashboard surface of the studio
API: projects, active, summary, quality, quality-report, prose-heatmap,
prose-diff, prose-judge, preflight, batch-run, batch-job.
"""
from lingwen_shared.contracts.python.studio import (
    StudioProjectItem,
    StudioProjectsResponse,
    StudioActiveResponse,
    StudioSetActiveRequest,
    StudioSummaryResponse,
    StudioQualityResponse,
    StudioQualityReportIssue,
    StudioQualityReportChapter,
    StudioProseHeatmapChapter,
    StudioProseHeatmap,
    StudioQualityReportResponse,
    StudioProseDiffTotals,
    StudioProseDiffChapter,
    StudioProseDiffResponse,
    StudioProseJudgeRating,
    StudioProseJudgeChapter,
    StudioProseJudgeSignal,
    StudioProseJudgeResponse,
    StudioPreflightChapter,
    StudioPreflightRequest,
    StudioPreflightResponse,
    StudioBatchRunRequest,
    StudioBatchJobResponse,
)

__all__ = [
    "StudioProjectItem",
    "StudioProjectsResponse",
    "StudioActiveResponse",
    "StudioSetActiveRequest",
    "StudioSummaryResponse",
    "StudioQualityResponse",
    "StudioQualityReportIssue",
    "StudioQualityReportChapter",
    "StudioProseHeatmapChapter",
    "StudioProseHeatmap",
    "StudioQualityReportResponse",
    "StudioProseDiffTotals",
    "StudioProseDiffChapter",
    "StudioProseDiffResponse",
    "StudioProseJudgeRating",
    "StudioProseJudgeChapter",
    "StudioProseJudgeSignal",
    "StudioProseJudgeResponse",
    "StudioPreflightChapter",
    "StudioPreflightRequest",
    "StudioPreflightResponse",
    "StudioBatchRunRequest",
    "StudioBatchJobResponse",
]
```

- [ ] **Step 4: Run studio route tests**

```bash
cd .worktrees/phase-126-v16-5-n9
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_studio_route.py -v 2>&1 | tail -10
```

Expected: All studio route tests pass.

- [ ] **Step 5: Run backend test suite**

```bash
cd .worktrees/phase-126-v16-5-n9
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -q 2>&1 | tail -5
```

Expected: Same baseline + cvg_adapter (5) + maybe 1 new test from T1 if added.

- [ ] **Step 6: Commit studio.py re-export**

```bash
cd .worktrees/phase-126-v16-5-n9
git add apps/studio_api/models/studio.py
git commit -m "refactor(studio-api): v16.5 #N.9 — studio.py re-exports lingwen-shared canonical models

Replaces 23 manual Pydantic model definitions with re-exports from
packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py.
Verified field-by-field equivalence for all 23 models.

Covers dashboard surface of studio API: projects, active, summary,
quality, quality-report, prose-heatmap, prose-diff, prose-judge,
preflight, batch-run, batch-job.

Backend import paths unchanged (apps.studio_api.models.studio.X).
__all__ preserves import surface for routes callers."
```

**Lesson from N.8 T2:** Field sets match, but `Optional[X]` vs required `X` differences in Pydantic v2 don't affect runtime when default values are present. Lingwen-shared's `ConfigDict(extra='ignore')` is stricter on extras but doesn't affect callers sending valid payloads.

---

## Task T3: CVG Adapter Wire-up (list_ripples)

**Files:**
- Modify: `apps/studio_api/routes/cvg.py` — `list_ripples` uses `cvg_adapter.ripple_storage_to_presentation`

**Context:** The CVG adapter scaffold (from N.8) establishes the boundary marker. Currently `routes/cvg.py:list_ripples` calls `_ripple_list_items` from `helpers/cvg.py` which returns the **storage shape** (RippleListItemResponse from `apps.studio_api.protocols`). After wire-up, the endpoint will call the adapter to convert storage → presentation shape (RippleListItemResponse from `lingwen_shared.contracts.python.cvg`).

**Critical constraint:** The wire-up requires the route's `response_model=` to point at the presentation shape (lingwen-shared), not the storage shape. This is a PYDANTIC-DRIFT resolution step.

**Risk:** Dashboard typed wrappers in `apps/dashboard/src/api/cvg.ts` import `RippleListItemResponse` from `@lingwen/dashboard-contracts/shared/cvg` (which re-exports lingwen-shared presentation shape). If the route was previously returning a different shape than the typed wrapper expects, this wire-up will align them — but may break tests that check the wire format.

- [ ] **Step 1: Read current `list_ripples` implementation + helper**

```bash
cd .worktrees/phase-126-v16-5-n9
sed -n '55,95p' apps/studio_api/routes/cvg.py
echo "---HELPER---"
sed -n '80,130p' apps/studio_api/helpers/cvg.py
echo "---RIPPLE TYPE IMPORTS---"
grep -n "RippleListItemResponse\|from apps.studio_api.protocols\|from lingwen_shared" apps/studio_api/routes/cvg.py | head -10
grep -n "RippleListItemResponse\|from apps.studio_api.protocols\|from lingwen_shared" apps/studio_api/helpers/cvg.py | head -10
```

Expected: 
- `routes/cvg.py` imports `RippleListItemResponse` from `apps.studio_api.protocols` (storage shape)
- `helpers/cvg.py:_ripple_list_items` returns `list[RippleListItemResponse]` (storage shape from protocols)

- [ ] **Step 2: Add a failing test that validates the wire-up contract**

Create or extend test file (verify location):
```bash
cd .worktrees/phase-126-v16-5-n9
ls apps/studio_api/tests/ | grep -i cvg
```

Add a test in `apps/studio_api/tests/test_cvg_routes.py` (or create if missing):
```python
"""Test that list_ripples returns the canonical presentation shape.

Phase 126 v16.5 #N.9: Wire-up verification. The route MUST return
``lingwen_shared.contracts.python.cvg.RippleListItemResponse`` (presentation
shape with chapter_id/source_volume/impact_volumes) instead of the storage
shape (source_chapter/target_chapter) from apps.studio_api.protocols.
"""
from lingwen_shared.contracts.python.cvg import RippleListItemResponse as PresentationRipple


def test_list_ripples_returns_presentation_shape(test_client, monkeypatch):
    """Endpoint must serialize with presentation-shape fields (chapter_id)."""
    # Use existing fixture or create minimal one
    # ... (assert response.json()[0]["chapter_id"] is present)
```

(Covered by N.8's 5 cvg_adapter tests; this step verifies the route-level wire-up, not just the adapter unit.)

- [ ] **Step 3: Update `list_ripples` to call the adapter**

In `apps/studio_api/routes/cvg.py`:

a) Update import at top:
```python
# BEFORE
from apps.studio_api.protocols import RippleListItemResponse  # storage shape

# AFTER
from lingwen_shared.contracts.python.cvg import RippleListItemResponse  # presentation shape
from apps.studio_api import cvg_adapter
```

b) Update `list_ripples` body:
```python
# In list_ripples, after `items = _ripple_list_items(ripples, storage)`:
# Add:
items = [cvg_adapter.ripple_storage_to_presentation(item.model_dump()) for item in items]
```

Wait — `_ripple_list_items` returns Pydantic models (storage shape), not raw dicts. The adapter expects dicts. Need to either:
- Modify helper to return dicts (breaking change)
- Convert via `model_dump()` then re-validate via `RippleListItemResponse(**dict)` (extra round-trip)
- Add adapter overload that accepts Pydantic models

Simplest: convert via `.model_dump()` and re-construct via `**dict`:
```python
items = [
    cvg_adapter.ripple_storage_to_presentation(item.model_dump())
    for item in _ripple_list_items(ripples, storage)
]
```

(Or call adapter on storage rows directly, bypassing `_ripple_list_items`. Investigate `_ripple_list_items` to see what it adds — it computes `impact_score` and `dimension_and_relationship` from storage rows.)

c) Update response_model:
```python
@app.get("/api/cvg/ripples", response_model=list[RippleListItemResponse])
```
The `response_model` now points at presentation shape from lingwen-shared.

- [ ] **Step 4: Run route tests**

```bash
cd .worktrees/phase-126-v16-5-n9
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_routes.py -v 2>&1 | tail -10
```

Expected: All CVG route tests pass (presentation shape now matches what typed wrappers expect).

- [ ] **Step 5: Verify dashboard typed wrapper still parses response**

```bash
cd .worktrees/phase-126-v16-5-n9/apps/dashboard
pnpm vitest run tests/unit/api/cvg-typed-wrapper.spec.ts 2>&1 | tail -5
pnpm vitest run tests/unit/stores/use-ripple-store.spec.ts tests/unit/pages/ripples-page.spec.ts 2>&1 | tail -5
```

Expected: Tests pass. If any test fails because response shape changed (e.g., `source_chapter` field is gone), update the test fixture to match the new presentation shape (`chapter_id`).

- [ ] **Step 6: Commit wire-up**

```bash
cd .worktrees/phase-126-v16-5-n9
git add apps/studio_api/routes/cvg.py apps/studio_api/tests/test_cvg_routes.py
git commit -m "refactor(studio-api): v16.5 #N.9 — list_ripples uses cvg_adapter for presentation shape

Wires cvg_adapter.ripple_storage_to_presentation into the
GET /api/cvg/ripples endpoint, converting storage shape
(source_chapter/target_chapter from apps.studio_api.protocols) to
the canonical presentation shape (chapter_id/source_volume/impact_volumes
from lingwen_shared.contracts.python.cvg).

The response_model is updated to point at the lingwen-shared
RippleListItemResponse. Dashboard typed wrapper @/api/cvg receives
the canonical shape and surface drift documented in
lingwen_shared/contracts/python/cvg.py:18-24 PYDANTIC-DRIFT is resolved.

Cross-volume storage helpers in apps/studio_api/helpers/cvg.py remain
unchanged (they own the storage-shape computation: impact_score,
dimension/relationship derivation). The adapter is the SOLE place where
storage → presentation mapping happens.

Verified: list_ripples now returns chapter_id; dashboard consumer
fixtures still parse."
```

---

## Task T4: CVG Adapter Wire-up (cascade endpoints)

**Files:**
- Modify: `apps/studio_api/routes/cvg.py` — 3 cascade endpoints use `cvg_adapter.cascade_*_storage_to_presentation`

**Context:** Three cascade endpoints return CascadeResponse variants:
- `get_ripple_cascade` (line 276) — CascadeResponse (full)
- `get_ripple_cascade_preview` (line 322) — CascadePreviewResponse
- `get_ripple_cascade_v9_20` (line 374) — CascadeResponse (variant)

Each currently builds the response from storage-shape helpers (`_build_cascade_response`, `_build_cascade_preview`). Wire-up uses `cvg_adapter.cascade_storage_to_presentation` (and `cascade_node/edge_storage_to_presentation`).

- [ ] **Step 1: Read cascade endpoint bodies + helpers**

```bash
cd .worktrees/phase-126-v16-5-n9
sed -n '276,375p' apps/studio_api/routes/cvg.py
echo "---HELPER CASCADE---"
grep -n "_build_cascade\|def.*cascade" apps/studio_api/helpers/cvg.py
```

Expected: Identify the helper that builds cascade storage dicts; identify the response shape each endpoint returns.

- [ ] **Step 2: Wire up `get_ripple_cascade`**

Update `get_ripple_cascade` to call `cvg_adapter.cascade_storage_to_presentation(cascade_dict)` after the storage helper builds the dict.

Pattern:
```python
@app.get("/api/cvg/ripples/{ripple_id}/cascade", response_model=CascadeResponse)
def get_ripple_cascade(...):
    storage = _app_module._default_storage()
    cascade_dict = _build_cascade_response(ripple_id, storage)  # storage shape
    return cvg_adapter.cascade_storage_to_presentation(cascade_dict)
```

Update the `CascadeResponse` import to come from `lingwen_shared.contracts.python.cvg`.

- [ ] **Step 3: Wire up `get_ripple_cascade_preview`**

Same pattern as Step 2, but for `CascadePreviewResponse` (different shape — preview doesn't include full edges).

If `cvg_adapter` doesn't have a preview-specific converter, either:
- Add one (extend `cvg_adapter.py` with `cascade_preview_storage_to_presentation`)
- Reuse `cascade_storage_to_presentation` if field set is compatible

Decision: Investigate lingwen-shared `CascadePreviewResponse` shape vs `CascadeResponse` shape — if subset of fields, extend cvg_adapter with a preview variant.

- [ ] **Step 4: Wire up `get_ripple_cascade_v9_20`**

Same pattern as Step 2 for `CascadeResponse` (v9_20 is a variant of the full cascade endpoint).

- [ ] **Step 5: Run all CVG route tests**

```bash
cd .worktrees/phase-126-v16-5-n9
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_cvg_routes.py apps/studio_api/tests/test_cvg_adapter.py -v 2>&1 | tail -15
```

Expected: All CVG tests pass (cascade endpoints now serve presentation shape).

- [ ] **Step 6: Verify dashboard consumers**

```bash
cd .worktrees/phase-126-v16-5-n9/apps/dashboard
pnpm vitest run tests/unit/pages/cascade-runs-panel.spec.ts tests/unit/stores/use-cascade-store.spec.ts 2>&1 | tail -5
```

Expected: Tests pass. Update fixtures if field names changed (e.g., `nodes[].chapter_id` vs `nodes[].source_chapter`).

- [ ] **Step 7: Commit cascade wire-up**

```bash
cd .worktrees/phase-126-v16-5-n9
git add apps/studio_api/routes/cvg.py apps/studio_api/cvg_adapter.py  # if adapter extended
git commit -m "refactor(studio-api): v16.5 #N.9 — 3 cascade endpoints use cvg_adapter

Wires cvg_adapter.cascade_storage_to_presentation into:
- GET /api/cvg/ripples/{ripple_id}/cascade → CascadeResponse
- GET /api/cvg/ripples/{ripple_id}/cascade/preview → CascadePreviewResponse
- GET /api/cvg/ripples/{ripple_id}/cascade/v9_20 → CascadeResponse

All three endpoints now serve the canonical presentation shape
(nodes[].chapter_id, edges[].relation) instead of the storage shape.

Adapter extended with cascade_preview_storage_to_presentation if the
preview response has a distinct field subset from the full cascade.
Cross-volume storage helpers in apps/studio_api/helpers/cvg.py remain
unchanged."
```

---

## Task T5: handleStreamEvent Tightening

**Files:**
- Modify: `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts`
- Possibly: `packages/dashboard-contracts/src/shared/creator.ts` (extend CreatorAgentStreamEvent if needed)

**Context:** `handleStreamEvent` currently has loose signature `{ type?, message?, label?, text?, source? }`. The canonical `CreatorAgentStreamEvent` (from v16.5 #N.7) is a discriminated union with start/chunk/advice/preview_label/done/error variants. Tightening requires deciding how to handle:
- The `status` event type (used in code but not in canonical union)
- The `source` field on `chunk` events (used to track streamSource but not in canonical chunk variant)

Two paths:
- **(A) Extend the canonical union**: Add `status` variant; add `source?` field to `chunk` variant. Requires Pydantic backend coordination + TS codegen regen.
- **(B) Local extension in useAgentTask**: Type handleStreamEvent as `(evt: CreatorAgentStreamEvent | { type: 'status'; message: string }) & { source?: string }` and document the drift.

For minimal scope, take **(B)** — local extension + JSDoc reason. The canonical envelope tightening is a separate concern (deferred to async port conformance phase).

- [ ] **Step 1: Read all uses of `streamSource` ref to determine if `source` field can be dropped**

```bash
cd .worktrees/phase-126-v16-5-n9/apps/dashboard
grep -rn "streamSource" src/ tests/
```

If `streamSource` is only assigned and never read, drop the field tracking entirely (simplest).
If `streamSource` is read by a template or computed, decide between (A) extending chunk variant or (B) keeping local cast.

- [ ] **Step 2: Determine `status` event usage**

```bash
cd .worktrees/phase-126-v16-5-n9/apps/dashboard
grep -rn "evt.type === 'status'" src/ tests/
grep -rn "'status'" src/composables/useCreatorAgent/ src/api/content.ts
```

If status is sent by the backend SSE stream, document the local extension. If it's an old artifact, drop the branch.

- [ ] **Step 3: Read CreatorAgentStreamEvent canonical shape**

```bash
cd .worktrees/phase-126-v16-5-n9
cat packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts | grep -A30 "CreatorAgentStreamEvent"
```

Expected: Confirms discriminated union with start/chunk/advice/preview_label/done/error variants.

- [ ] **Step 4: Update handleStreamEvent signature**

In `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:116`:

```ts
// BEFORE
handleStreamEvent: (evt: { type?: string; message?: string; label?: string; text?: string; source?: string }) => void;

// AFTER
// v16.5 #N.9: Tightened to canonical CreatorAgentStreamEvent discriminated
// union + local extension for 'status' events (backend SSE emits status
// messages not yet promoted to canonical envelope).
handleStreamEvent: (evt: CreatorAgentStreamEvent | { type: 'status'; message: string }) => void;
```

Add import:
```ts
import type { CreatorAgentStreamEvent } from '@lingwen/dashboard-contracts/shared';
```

(Verify this import path matches the existing imports in this file.)

- [ ] **Step 5: Update handleStreamEvent implementation**

In `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:285`:

```ts
// BEFORE
function handleStreamEvent(evt: { type?: string; message?: string; label?: string; text?: string; source?: string }): void {
  if (evt.type === 'status' && evt.message) {
    statusLine.value = evt.message;
  }
  // ... other branches use evt.source which is NOT in canonical chunk variant
}

// AFTER
function handleStreamEvent(evt: CreatorAgentStreamEvent | { type: 'status'; message: string }): void {
  // Local extension: 'status' events come from backend SSE during long-running
  // operations. Not yet in canonical CreatorAgentStreamEvent union.
  if (evt.type === 'status' && 'message' in evt) {
    statusLine.value = evt.message;
  }
  if (evt.type === 'preview_label' && 'label' in evt) {
    streamPreviewLabel.value = `${evt.label} · ${agentLensLabel.value}`;
  }
  if (evt.type === 'chunk' && 'text' in evt) {
    // streamSource field dropped: not part of canonical CreatorAgentStreamEvent.chunk
    streamPreviewText.value += evt.text;
  }
  if (evt.type === 'advice' && 'text' in evt) {
    streamAdvicePreview.value = [...streamAdvicePreview.value, evt.text];
  }
}
```

(Adjust based on Step 1 decision about `streamSource`.)

- [ ] **Step 6: Drop the cast at the call site**

In `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts:343-345`:

```ts
// BEFORE
const result = await runCreatorAgentPlanStream(
  body as unknown as Parameters<typeof runCreatorAgentPlanStream>[0],
  handleStreamEvent as unknown as (event: unknown) => void,
) as Record<string, unknown>;

// AFTER
const result = await runCreatorAgentPlanStream(body, handleStreamEvent);
```

The cast for `body` remains if T5.4 narrowing was partial (intersection type with `& Record<string, unknown>`). The handleStreamEvent cast is removed because the signature now matches `CreatorAgentStreamEvent | status`.

- [ ] **Step 7: Verify with tsc + tests**

```bash
cd .worktrees/phase-126-v16-5-n9/apps/dashboard
pnpm vue-tsc --noEmit 2>&1 | tail -10
pnpm vitest run tests/unit/composables/useCreatorAgent/ 2>&1 | tail -10
```

Expected: vue-tsc 0 errors; tests pass.

- [ ] **Step 8: Commit handleStreamEvent tightening**

```bash
cd .worktrees/phase-126-v16-5-n9
git add apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts
git commit -m "refactor(dashboard): v16.5 #N.9 — handleStreamEvent adopts CreatorAgentStreamEvent discriminated union

Tightens the handleStreamEvent signature from a loose
{ type?, message?, label?, text?, source? } shape to the canonical
CreatorAgentStreamEvent discriminated union (from v16.5 #N.7) with a
local extension for 'status' events.

Changes:
- Drop the streamSource field tracking (not in canonical chunk variant,
  no longer read by any template).
- Drop 'source' handling in handleStreamEvent body.
- Add local extension | { type: 'status'; message: string } for the
  'status' event type (backend SSE still emits these; not yet promoted
  to canonical envelope).
- Drop the 'as unknown as (event: unknown) => void' cast at the
  runCreatorAgentPlanStream call site.

The 'status' event extension is documented with JSDoc. Promoting
'status' to canonical CreatorAgentStreamEvent is deferred to async
port conformance phase (v16.5 #N.10+)."
```

---

## Task T6: Verification + Handoff

**Files:**
- Create: `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n9-cleanup-and-handle-stream-event-handoff.md`
- Modify: `CLAUDE.md` (add v16.5 #N.9 closure section)

- [ ] **Step 1: Full verification gate**

```bash
cd .worktrees/phase-126-v16-5-n9
cd apps/dashboard && pnpm vitest run 2>&1 | tail -5
cd ../..
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared -q 2>&1 | tail -3
env -u MINIMAX_API_KEY /home/ailearn/miniconda3/bin/python -m pytest tests/infra/ apps/studio_api/tests/ -q 2>&1 | tail -3
cd apps/dashboard && pnpm vue-tsc --noEmit 2>&1 | tail -3
cd ../..
ruff check apps/studio_api/ packages/lingwen-shared/ 2>&1 | tail -3
pnpm knip 2>&1 | tail -5
```

Expected:
- vitest: 1733+ tests pass (no regression)
- pytest: 113+ shared + ~400 infra/studio_api pass (now includes 5 NEW cvg_adapter + ~10 new from T3-T4 if added)
- vue-tsc: 0 errors
- ruff: 0 errors
- knip: 0 errors (or allowable advisories documented)

- [ ] **Step 2: Write handoff doc**

Create `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n9-cleanup-and-handle-stream-event-handoff.md` with sections:
- §0 TL;DR
- §1 Files Created/Modified
- §2 Migration Pattern (workflow.py split + re-export)
- §3 Drift Notes (CVG adapter wire-up + handleStreamEvent status extension)
- §4 Verification Matrix (before/after gate counts)
- §5 Lessons Learned
- §6 Carryover to v16.5 #N.10+

- [ ] **Step 3: Update CLAUDE.md v16.5 #N.9 section**

Add closure section following v16.5 #N.8 pattern. Include:
- Commit count + branch info
- Migration pattern (workflow.py split + CVG wire-up + handleStreamEvent)
- Lessons (specifically about CVG adapter wire-up + handleStreamEvent tightening + budget module decision)
- Carryover list (remaining 7+ CVG endpoints + async port conformance + 39 cast cleanup)

- [ ] **Step 4: Push branch**

```bash
cd .worktrees/phase-126-v16-5-n9
git push -u origin phase-126-v16-5-n9
```

Expected: Branch pushed to origin.

- [ ] **Step 5: Final commit + cleanup**

```bash
cd .worktrees/phase-126-v16-5-n9
git add docs/ CLAUDE.md
git commit -m "docs(phase-126): v16.5 #N.9 — handoff + CLAUDE.md closure"
git push origin phase-126-v16-5-n9
```

---

## Carryover to v16.5 #N.10+

Documented in handoff §6:

1. **Remaining CVG route endpoints wire-up** — `apply_ripple` / `reject_ripple` / `get_ripple_audit` / `export_ripple_audit` / `rollback_ripple` / `get_ripple_stats` / `get_reference_graph` / `get_ripple_detail` / `get_ripple_cascade_v9_20` (8 endpoints still return storage-shape responses). 4-8 commits.

2. **`status` event promotion** — Promote backend `status` event to canonical `CreatorAgentStreamEvent` (add `status` variant to lingwen-shared + regenerate TS). Requires backend Pydantic coordination. 1-2 commits.

3. **chapter.py re-export verification** — `apps/studio_api/models/chapter.py` may already be in lingwen-shared. Verify and re-export (per N.8 plan §File Structure "defer (Phase 124 owns this)"). 1-2 commits.

4. **protocols.py CVG cleanup** — After all CVG routes use the adapter, the storage-shape CVG models in `apps/studio_api/protocols.py` (lines ~706+) can be removed (no longer imported by any route). 1-2 commits.

5. **Async port conformance** — `LLMServiceAdapter` from sync → `async execute → LLMResult`. Major refactor, touches 12 tools/* + 4 backend route consumers. ~16-25 commits.

6. **39 `as unknown as` cast cleanup** — pre-existing fragile patterns in 14 composable files. Each requires investigation + JSDoc documentation OR body-shape tightening.

7. **`streamSource` field re-introduction** — If dashboards want to display chunk source again, add `source?: string` to canonical `CreatorAgentStreamEvent.chunk` variant. 1 commit (depends on product decision).

---

## Lessons Captured (anticipated)

1. **Bounded context alignment via structural split** — `BudgetSetRequest` was in `workflow.py` because of code organization history, not because it belongs there. Splitting based on bounded context (workflow vs budget) is more durable than alphabetical or date-based organization.

2. **CVG adapter wire-up is the boundary enforcer** — Once routes call `cvg_adapter.*_storage_to_presentation`, the import-linter forbidden contract `no_storage_shape_in_cvg_routes` can be added to enforce that no route imports from `apps.studio_api.protocols.Ripple*` directly.

3. **Local discriminated union extensions document drift** — When the canonical envelope doesn't cover a runtime event type (like `status`), a local union extension with JSDoc reason is cleaner than dropping the cast or extending the canonical type prematurely.

4. **Re-export shim equivalence verification is mechanical** — The 5-line field set comparison (`set(backend.model_fields) == set(shared.model_fields)`) catches drift before any test run. Use it as a pre-commit gate.

5. **Optional-vs-required defaults are runtime-equivalent** — Lingwen-shared uses `Optional[X]` with default; backend uses `X = 'studio'`. Both pass validation when callers send valid payloads. Stricter type on the shared side doesn't break backward compat.
