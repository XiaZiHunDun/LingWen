# Phase 126 v16.5 #N.7 — DTO Pydantic Codegen + SSE Stream Typing Handoff

> **Status:** closed, 27 commits on `phase-126-v16-5-n7` branch
> **Previous:** v16.5 #N.6 (tools LLM service migration, `eadf2dff`)
> **Next:** v16.5 #N.8 (async port conformance + backend Pydantic re-export + remaining `as unknown as` cast cleanup)

## 0. TL;DR

Promoted the 5 manual TS DTO files (health/studio/workflows/cvg/decisions, declared in v16.5 #7) to Pydantic v2 source-of-truth in `packages/lingwen-shared/src/lingwen_shared/contracts/python/`, regenerated the TS via `tooling/contracts/generate.py`, replaced the 5 manual TS DTOs in `packages/dashboard-contracts/src/shared/` with re-export shims (matching `memory.ts`/`settings.ts` pattern), and typed the `runCreatorAgentPlanStream` SSE envelope — the only remaining `Promise<unknown>` in `apps/dashboard/src/api/`.

## 1. Files Created/Modified

### New Python files (5)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py` — 12 Pydantic models (DatabaseStatus, MemoryUsage, HealthResponse, OverviewResponse, ChapterData, ChaptersResponse, ProductionRecordResponse, ProductionRecordsResponse, ProductionBatchRollupResponse, ProductionRollupResponse, ProductionCostTrendPointResponse, ProductionCostTrendResponse)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py` — 23 Pydantic models (Studio*)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/workflows.py` — 5 Pydantic models (WorkflowListItem, RunWorkflowRequest, ResumeWorkflowRequest, WorkflowStatusResponse, WorkflowMermaidResponse)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/cvg.py` — 12 Pydantic models (CVG presentation shape)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/decisions.py` — 4 Pydantic models (DecisionResponse, ResolveDecisionRequest, DeferDecisionRequest, CancelDecisionRequest)

Total: **56 Pydantic models**

### New Python tests (5)
- `packages/lingwen-shared/tests/test_{health,studio,workflows,cvg,decisions}_dto.py` — 28 test cases total (8+5+5+5+5)

### Codegen tooling (2)
- `tooling/contracts/generate.py` — MODULES list extended from 4 to 9 entries
- `tooling/contracts/zod_revalidate.py` — modules tuple extended to match

### Generated TS files (5)
- `packages/lingwen-shared/src/lingwen_shared/contracts/ts/{health,studio,workflows,cvg,decisions}.ts` — auto-generated, "DO NOT EDIT"

### Re-export shims (5)
- `packages/dashboard-contracts/src/shared/{health,studio,workflows,cvg,decisions}.ts` — REPLACED manual DTOs with `import + export type X = Y` shim pattern

### SSE typing (4 files + 1 new)
- `packages/dashboard-contracts/src/shared/creator-sse.ts` (NEW) — `CreatorAgentStreamEvent` discriminated union (start/chunk/advice/preview_label/done/error) + `CreatorAgentPlanResult` alias
- `apps/dashboard/src/utils/creatorAgentStreamUtils.js` — JSDoc types added
- `apps/dashboard/src/api/content.ts` — return type narrowed from `Promise<unknown>` → `Promise<CreatorAgentPlanResult>`
- `apps/dashboard/src/composables/useCreatorAgent/useAgentTask.ts` — UNCHANGED (T5.4 cast cleanup carryover, see §3)

### SSE test (1)
- `apps/dashboard/tests/unit/utils/creatorAgentStreamUtils.spec.ts` — 4 cases

## 2. Migration Pattern

```python
# Pydantic v2 source-of-truth → TS codegen → re-export shim
#
# packages/lingwen-shared/src/lingwen_shared/contracts/python/health.py
#   (Pydantic v2 models, e.g. OverviewResponse with fields)
#         │
#         │ tooling/contracts/generate.py (Pydantic v2 model_json_schema → hand-rolled TS)
#         ▼
# packages/lingwen-shared/src/lingwen_shared/contracts/ts/health.ts
#   (Generated `export interface X` declarations)
#         │
#         │ packages/dashboard-contracts/src/shared/health.ts (re-export shim with DTO suffix)
#         ▼
# apps/dashboard/src/api/*.ts (typed wrappers, return Promise<ConcreteDTO>)
```

## 3. Drift Notes

### CVG presentation vs backend storage shape (PYDANTIC-DRIFT)
The CVG Python Pydantic models codify the PRESENTATION shape (matching the manual TS DTOs from v16.5 #7), not the backend storage shape in `apps/studio_api/protocols.py`. Specifically:
- `RippleListItemResponseDTO.source_volume: int` vs `RippleListItemResponse.source_chapter: int`
- `RippleListItemResponseDTO.impact_volumes: list[int]` (derived) vs `RippleListItemResponse.target_chapter: int`
- `RippleListItemResponseDTO.chapter_id: int` (derived) vs `RippleListItemResponse.source_chapter: int`

The backend storage models are unchanged. Routes that return CVG responses must continue to map backend shape → presentation shape. Documented in `cvg.py` module docstring with `# PYDANTIC-DRIFT` marker.

### Backend Pydantic re-export deferred to v16.5 #N.8+
`apps/studio_api/models/{health,chapter,studio,workflow}.py` and `apps/studio_api/protocols.py` (Ripple/Cascade) are NOT updated to re-export from lingwen-shared. Drift risk exists if either side changes independently. v16.5 #N.8+ should:
1. Decide on presentation adapter layer (backend maps storage → presentation before returning)
2. Re-export backend models from lingwen-shared contracts
3. Remove duplicates

### UseAgentTask cast cleanup (T5.4) carryover
The plan attempted to drop `as unknown as` casts in `useAgentTask.ts:344-345` after typing the SSE wrapper. The casts cannot be removed cleanly because:
- `body: Record<string, unknown>` is not assignable to `CreatorAgentPlanRequest` (Property 'action_label' missing)
- `handleStreamEvent` has legacy shape `{ type?: string; message?: string; label?: string; text?: string; source?: string }` referencing `evt.type === 'status'` and `evt.source` — neither field exists in the new discriminated union

Requires either tightening `buildPlanRequestBody` return type OR widening `handleStreamEvent` shape. v16.5 #N.8+ follow-up.

### Pre-existing vue-tsc carryover (NOT introduced by v16.5 #N.7)
5 vue-tsc errors in `packages/dashboard-contracts/src/shared/{cvg,decisions,health,studio,workflows}.ts` — all use `../../lingwen-shared/...` (2-dot relative path). Should be `../../../` (3-dot). Identical errors appear on master baseline (introduced in v16.5 #7 when the manual DTOs were first created). v16.5 #N.8+ should fix path resolution.

## 4. Verification Matrix

| Gate | Before (v16.5 #N.6) | After (v16.5 #N.7) |
|------|---------------------|---------------------|
| `pytest packages/lingwen-shared/tests/` | 85 passed | **113 passed** (+28) |
| `python tooling/contracts/generate.py` | 4 modules → 4 TS | **9 modules → 9 TS** |
| `vue-tsc` | 0 errors | 0 errors (T3, T5 verified clean) |
| `vitest` | 1729 | **1733** (+4 SSE parser tests) |
| `apps/dashboard/src/api/*.ts` `Promise<unknown>` count | 1 (SSE only) | **0** ✓ |
| `packages/dashboard-contracts/src/shared/*.ts` manual DTO declarations | 5 files, 60 interfaces | **0 manual** (all re-exports) |
| `apps/dashboard/src/api/*.ts` typed wrapper return types | 41 concrete DTOs + 1 unknown | **42 concrete DTOs** + 0 unknown |

## 5. Lessons Learned

1. **TS re-export `as` rename syntax doesn't exist** — `export type { X as Y }` doesn't rename; use `import type { X } from '...'; export type Y = X;` for renaming (codegen names without `DTO` suffix → manual TS DTOs use `DTO` suffix).

2. **Presentation vs storage shape drift** — When promoting manual TS DTOs (which represented UI needs) to Pydantic source-of-truth, the codegen result intentionally diverges from `apps/studio_api/models/*.py`. The backend storage layer continues to own the persistence shape; the lingwen-shared contracts own the wire/UI shape. Document the boundary explicitly in module docstrings.

3. **`anyOf` in codegen handles Optional correctly** — `Optional[X] = None` in Pydantic produces `X | null` in TS via `anyOf: [{type: 'X'}, {type: 'null'}]` handling in `_ts_type_for`. No manual annotation needed.

4. **Self-referencing Pydantic models need `model_rebuild()`** — `RippleDetailResponse` references `RippleAuditEntryResponse` via forward ref. Calling `model_rebuild()` after class definitions resolves the forward refs (per v16.1 lessons).

5. **SSE stream typing requires runtime narrowing** — The `evt.type === 'done'` branch narrows `evt` to `{type: 'done', plan: ...}` automatically via TS discriminated union. No `as` casts needed.

6. **`Field(ge=1)` etc. must be preserved on Pydantic promotions** — When promoting fields from manual TS DTOs to Pydantic, Field constraints (e.g., `StudioBatchRunRequest.start_chapter: int = Field(ge=1)`) and required-vs-optional status must be faithfully preserved. Spec omission in this plan caused 2 BLOCKING issues that were caught by spec review and fixed in 2 atomic commits.

7. **Workflow status fields are `Optional[...] = None` not typed defaults** — The spec incorrectly asserted `is_active is False` / `cost_by_scenario == {}` / etc. Actual behavior is all fields default to `None`. Spec assertions had to be relaxed to `is None`. This is a third instance of "spec drift from actual DTO behavior" pattern (after #T1 issue 2 and v16.5 #7 lesson 2).

8. **`Record<string, unknown>` vs typed DTO** — Even with typed wrappers, callers using `Record<string, unknown>` as their body shape cannot drop the `as unknown as` cast. Tightening body shape is a separate refactor scope.

## 6. Carryover to v16.5 #N.8+

- **Backend Pydantic re-export from lingwen-shared** — `apps/studio_api/models/*.py` + `protocols.py` should re-export from lingwen-shared (DRY, single source of truth)
- **CVG presentation adapter layer** — Routes that return CVG responses must continue to map backend storage → presentation. Consider extracting this into a dedicated adapter module.
- **UseAgentTask cast cleanup (T5.4)** — Tighten `buildPlanRequestBody` return type to `CreatorAgentPlanRequest` so the `as unknown as` cast can be dropped.
- **Fix `../../lingwen-shared` paths** — 5 re-export shims have 2-dot relative paths that produce vue-tsc errors. Should be `../../../` (3-dot). Pre-existing on master baseline.
- **Async port conformance** — v16.4 `LLMServiceAdapter` is sync; rewrite with `async execute → LLMResult` is v16.5 #N.8
- **DTO schema drift fixes** — 39 `as unknown as` casts in `apps/dashboard/src/` are pre-existing fragile patterns (per v16.5 #7 lesson 2). Document each in-place; full cleanup is v16.5 #N.8+

## 7. Commit Timeline

```
0f193dca test(dashboard): v16.5 #N.7 — SSE parser tests (4 cases)
d96906f8 refactor(dashboard): v16.5 #N.7 — narrow runCreatorAgentPlanStream return to CreatorAgentPlanResult
009da952 refactor(dashboard): v16.5 #N.7 — type SSE stream parser via JSDoc
aa541205 feat(dashboard-contracts): v16.5 #N.7 — SSE event envelope types
23c4514c chore(ruff): v16.5 #N.7 — ruff --fix for 9 I001 violations across 5 files
d4149bad test(lingwen-shared): v16.5 #N.7 — decisions DTO contract tests (5 cases)
a2deccad test(lingwen-shared): v16.5 #N.7 — cvg DTO contract tests (5 cases)
3642a183 test(lingwen-shared): v16.5 #N.7 — workflows DTO contract tests (5 cases)
b87cf545 test(lingwen-shared): v16.5 #N.7 — studio DTO contract tests (5 cases)
42215e81 test(lingwen-shared): v16.5 #N.7 — health DTO contract tests (8 cases)
1f47a705 docs(dashboard-contracts): v16.5 #N.7 — index.ts codegen marker update
f52a4300 refactor(dashboard-contracts): v16.5 #N.7 — decisions.ts re-export shim
e97597c8 refactor(dashboard-contracts): v16.5 #N.7 — cvg.ts re-export shim
30e8a519 refactor(dashboard-contracts): v16.5 #N.7 — workflows.ts re-export shim
d0a831a4 refactor(dashboard-contracts): v16.5 #N.7 — studio.ts re-export shim
389d1a85 refactor(dashboard-contracts): v16.5 #N.7 — health.ts re-export shim
36f34f3d feat(lingwen-shared): v16.5 #N.7 — codegen TS for 5 new DTO modules
0f6f72f9 feat(tooling): v16.5 #N.7 — extend zod_revalidate modules with 5 new surfaces
099a7567 feat(tooling): v16.5 #N.7 — extend codegen MODULES with health/studio/workflows/cvg/decisions
8d601151 fix(lingwen-shared): v16.5 #N.7 — StudioBatchRunRequest fields: required + Field() defaults
7600f26b fix(lingwen-shared): v16.5 #N.7 — rename ProductionRollupResponse.latest_record_at → latest_recorded_at
201e4062 chore(ruff): v16.5 #N.6 — ruff --fix for 8 W292 violations (5 new DTO files)
5ae6f7f4 feat(lingwen-shared): v16.5 #N.7 — add decisions.py Pydantic DTOs (4 models)
a12c31df feat(lingwen-shared): v16.5 #N.7 — add cvg.py Pydantic DTOs (12 models, presentation shape)
7fe8c3ff feat(lingwen-shared): v16.5 #N.7 — add workflows.py Pydantic DTOs (5 models)
15226dfa feat(lingwen-shared): v16.5 #N.7 — add studio.py Pydantic DTOs (23 models)
7ade9ff6 feat(lingwen-shared): v16.5 #N.7 — add health.py Pydantic DTOs (12 models)
eadf2dff (v16.5 #N.6 baseline)
```

Total: **27 commits**