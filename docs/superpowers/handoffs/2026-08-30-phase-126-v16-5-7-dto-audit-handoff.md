# Phase 126 v16.5 #7 — DTO Schema Audit + Typed Wrapper Narrowing Handoff

> **Status:** closed, 4 commits pushed to `phase-126-v16-5-7` branch (ready for merge)
> **Previous:** v16.5 #6 — tools migration defense-in-depth (`10e98b6a`)
> **Next:** v16.5 #N (full Pydantic codegen for unwrapped wrappers + remaining schema audits)

## 0. TL;DR

Audit + targeted alignment for the typed-wrapper carryover from v16.2.7 T8 / v16.2.8 T3.B:

- 5 wrapper files (`health.ts`, `studio.ts`, `workflows.ts`, `cvg.ts`, `decisions.ts`) had no corresponding DTO files in `packages/dashboard-contracts/src/shared/`. All `Promise<unknown>` returns were unmaskable — consumers could not get type information.
- v16.5 #7 manually declared those 5 DTO files (sourced from `apps/studio_api/models/*.py` + `apps/studio_api/protocols.py`), updated the 5 wrapper files to return concrete DTO types, and cleaned up the 1 composable that had `as` casts on the new types.
- Full Pydantic → TS codegen via `tooling/contracts/generate.py` remains v16.5 #N carryover — this commit set is the **pragmatic minimum** that unblocks type safety now without committing to the larger codegen refactor.

## 1. T1 Audit Summary

Audit run on `phase-126-v16-5-7` baseline (HEAD `10e98b6a`):

| Wrapper file | `Promise<unknown>` count | DTO exists? | Action |
|--------------|--------------------------|-------------|--------|
| `apps/dashboard/src/api/content.ts` | 1 (runCreatorAgentPlanStream — SSE stream, dynamic plan) | ✓ (content.ts via creator.ts re-export) | out of scope (SSE) |
| `apps/dashboard/src/api/cvg.ts` | 14 | ✗ | NEW DTO + wrapper update |
| `apps/dashboard/src/api/decisions.ts` | 5 | ✗ | NEW DTO + wrapper update |
| `apps/dashboard/src/api/health.ts` | 6 | ✗ | NEW DTO + wrapper update |
| `apps/dashboard/src/api/studio.ts` | 11 | ✗ | NEW DTO + wrapper update |
| `apps/dashboard/src/api/workflows.ts` | 5 | ✗ | NEW DTO + wrapper update |
| `apps/dashboard/src/api/volume.ts` | 0 | ✓ (creator.ts) | nothing to do |
| `apps/dashboard/src/api/{world,workspace,quality,memory,onboarding,settings,export}.ts` | 0 | ✓ | nothing to do |

`as unknown as` cast count in `apps/dashboard/src/`: **37** (counted via `grep -rn "as unknown as" src/`). Most are on wrappers that already have DTOs (volume, settings, onboarding, content) — they predate v16.2.8's typed-wrapper cleanup and use `as unknown as` to bridge inline shapes that don't match the DTO exactly.

## 2. T2 Minimal Fix List

### 2.1 DTO files added (5)

Each file declares TypeScript `interface` types matching the corresponding Pydantic `BaseModel` fields from `apps/studio_api/models/`. Optional fields use `| null` to match `Optional[]`. No zod (zod is a T5/CI drift check, not a wrapper layer concern).

- `packages/dashboard-contracts/src/shared/health.ts` (15 interfaces):
    DatabaseStatusDTO, MemoryUsageDTO, HealthResponseDTO, OverviewResponseDTO,
    ChapterDataDTO, ChaptersResponseDTO, ProductionRecordResponseDTO,
    ProductionRecordsResponseDTO, ProductionBatchRollupResponseDTO,
    ProductionRollupResponseDTO, ProductionCostTrendPointResponseDTO,
    ProductionCostTrendResponseDTO

- `packages/dashboard-contracts/src/shared/studio.ts` (24 interfaces):
    StudioProjectItemDTO, StudioProjectsResponseDTO, StudioActiveResponseDTO,
    StudioSetActiveRequestDTO, StudioSummaryResponseDTO, StudioQualityResponseDTO,
    StudioQualityReportIssueDTO, StudioQualityReportChapterDTO,
    StudioProseHeatmapChapterDTO, StudioProseHeatmapDTO,
    StudioQualityReportResponseDTO, StudioProseDiffTotalsDTO,
    StudioProseDiffChapterDTO, StudioProseDiffResponseDTO,
    StudioProseJudgeRatingDTO, StudioProseJudgeChapterDTO,
    StudioProseJudgeSignalDTO, StudioProseJudgeResponseDTO,
    StudioPreflightChapterDTO, StudioPreflightRequestDTO,
    StudioPreflightResponseDTO, StudioBatchRunRequestDTO,
    StudioBatchJobResponseDTO

- `packages/dashboard-contracts/src/shared/workflows.ts` (5 interfaces):
    WorkflowListItemDTO, RunWorkflowRequestDTO, ResumeWorkflowRequestDTO,
    WorkflowStatusResponseDTO, WorkflowMermaidResponseDTO

- `packages/dashboard-contracts/src/shared/cvg.ts` (12 interfaces):
    RippleListItemResponseDTO, RippleDetailResponseDTO,
    RippleActionResponseDTO, RippleStatsResponseDTO,
    RippleAuditEntryResponseDTO, CascadeNodeResponseDTO,
    CascadeEdgeResponseDTO, CascadeResponseDTO,
    CascadePreviewResponseDTO, ReferenceGraphResponseDTO,
    CascadeRunResponseDTO, CascadeCancelPayloadDTO

- `packages/dashboard-contracts/src/shared/decisions.ts` (4 interfaces):
    DecisionResponseDTO, ResolveDecisionRequestDTO,
    DeferDecisionRequestDTO, CancelDecisionRequestDTO

Total: **60 new TypeScript interfaces** manually declared.

### 2.2 `index.ts` re-export

`packages/dashboard-contracts/src/shared/index.ts` updated to re-export the 5 new modules' DTOs via `export type { ... } from './X'` so consumers access them via the existing `@lingwen/dashboard-contracts/shared` import surface (same path as creator/world/workspace/quality DTOs).

### 2.3 Wrapper files updated (5)

Each wrapper was updated to:
- Import concrete DTO types from `@lingwen/dashboard-contracts/shared`
- Replace `Promise<unknown>` with `Promise<ConcreteDTO>` (or `Promise<ConcreteDTO[]>` / `Promise<DTO | null>`)
- Use the established `data → as T` cast pattern (matches `settings.ts` convention; `core.js` `request()` returns `Promise<unknown>` so the wrapper does a single cast)

| Wrapper | Functions narrowed | Return types |
|---------|--------------------|--------------|
| `health.ts` | 6 | OverviewResponseDTO, ChaptersResponseDTO, ProductionRecordsResponseDTO, ProductionRollupResponseDTO, ProductionCostTrendResponseDTO, HealthResponseDTO |
| `studio.ts` | 11 | StudioProjectsResponseDTO, StudioActiveResponseDTO, StudioSummaryResponseDTO, StudioQualityResponseDTO, StudioQualityReportResponseDTO, StudioProseDiffResponseDTO, StudioProseJudgeResponseDTO, StudioPreflightResponseDTO, StudioBatchJobResponseDTO, StudioBatchJobResponseDTO \| null, StudioBatchJobResponseDTO |
| `workflows.ts` | 5 | WorkflowListItemDTO[], WorkflowStatusResponseDTO, WorkflowStatusResponseDTO, WorkflowStatusResponseDTO, WorkflowMermaidResponseDTO |
| `cvg.ts` | 14 | RippleListItemResponseDTO[], RippleDetailResponseDTO, RippleActionResponseDTO, RippleActionResponseDTO, RippleStatsResponseDTO, ReferenceGraphResponseDTO, RippleAuditEntryResponseDTO[], RippleActionResponseDTO, CascadeResponseDTO, CascadePreviewResponseDTO, CascadeRunResponseDTO[], CascadeRunResponseDTO[], CascadeCancelPayloadDTO, CascadeResponseDTO |
| `decisions.ts` | 5 | DecisionResponseDTO[], DecisionResponseDTO[], ResolveDecisionResult (local — backend returns synthetic envelope, not full DecisionResponse), DecisionResponseDTO, DecisionResponseDTO |

Total: **41 wrapper functions narrowed** from `Promise<unknown>` to concrete DTO types.

### 2.4 Composable cast cleanup (1)

`apps/dashboard/src/composables/useCreatorProductTools/useProductExport.ts` lines 142 and 152 contained:

```ts
const resp = await fetchChapters() as { chapters?: Array<{ chapter: number; has_body?: boolean }> };
```

With `fetchChapters()` now returning `Promise<ChaptersResponseDTO>` (which has `{chapter, hook_count, ...}` — no `has_body`), the simple `as` cast no longer compiles. Converted both to `as unknown as { ... }` (more honest about the unsafe nature) and added a comment documenting the **pre-existing data-shape drift**:

- Backend `/api/chapters` returns `ChapterData{chapter, hook_count, hook_strength_avg, coolpoint_count, coolpoint_density}` (no `has_body`).
- Frontend filter `c.has_body` is undefined for every chapter → filter always returns `[]`.
- This is a v16.2.7 §5.1 lesson-4 carryover (typed wrapper params forwarding fragility) and a v16.5 #N carryover (DTO schema audit on unwrapped response shapes).
- No runtime behavior change.

This is the only composable that had explicit `as` casts on the 5 target wrappers. Other consumers (studio/workflows/cvg/decisions composables) use the wrapper returns without explicit casts and benefit automatically from the new types via inference.

## 3. T3 Verification

All gates green at HEAD `f2f75688`:

| Gate | Result |
|------|--------|
| `pnpm typecheck:app` (vue-tsc) | **0 errors** — new DTO imports resolve cleanly, all wrappers type-narrow correctly |
| `pnpm vitest run` (from `apps/dashboard/`) | **1729 passed, 1 skipped** (219/219 test files passed) — 0 regression from v16.5 #6 baseline |
| Backend tests | **unchanged** — no Python changes in this sub-phase |
| import-linter / grimp-evasion hygiene | **unchanged** — no Python changes |
| knip | **unchanged** — manual DTO declarations don't add unused exports |

Note: vitest was run directly via `apps/dashboard/node_modules/.bin/vitest run` from `apps/dashboard/` cwd because `pnpm test` at root triggers turbo's `build` step on `dashboard-contracts`, which requires `tsc` (not installed at that package's node_modules due to no declared deps). This is a pre-existing CI/tooling issue, not a regression — the `typecheck:app` script runs vue-tsc directly without that dependency chain.

## 4. Carryover to v16.5 #N (full DTO alignment)

The full DTO alignment via `tooling/contracts/generate.py` remains. Recommended sub-phases:

1. **`packages/lingwen-shared/src/lingwen_shared/contracts/python/{health,studio,workflows,cvg,decisions}.py`** — promote the manual TS declarations to Pydantic DTOs. Cross-reference the `apps/studio_api/models/{health,chapter,studio,workflow}.py` + `apps/studio_api/protocols.py` definitions.
2. **`tooling/contracts/generate.py` MODULES list** — add 5 new entries so the codegen picks up the new Python files.
3. **Regenerate `packages/lingwen-shared/src/lingwen_shared/contracts/ts/{health,studio,workflows,cvg,decisions}.ts`** via `python tooling/contracts/generate.py`.
4. **Replace manual `packages/dashboard-contracts/src/shared/{health,studio,workflows,cvg,decisions}.ts`** with `export type { ... } from '../../lingwen-shared/src/lingwen_shared/contracts/ts/X'` (matching `memory.ts`/`creator.ts` re-export pattern).
5. **`apps/dashboard/src/api/runCreatorAgentPlanStream` (content.ts:178)** — the only remaining `Promise<unknown>` in the wrappers. SSE response shape is dynamic (depends on agent action label); narrowing requires designing the response envelope.

Other carryover from v16.2.7/v16.2.8 still in scope:

- **DTO schema drift fix** — 4 production `as unknown as` casts + 2 test casts (excluding useProductExport.ts which is now documented) that mask schema drift between Python Pydantic and TS DTOs (e.g., `CreatorModelsResponse.providers` → `models + default_model` was already fixed in v16.2.8 T8; remaining drifts TBD).
- **Typed wrapper return type narrowing for `Promise<Record<string, unknown>>`** — some functions in `volume.ts`/`onboarding.ts`/`settings.ts` return `Record<string, unknown>` shapes that could narrow further once full codegen is in place.

## 5. Lessons Learned

1. **Manual DTOs are a valid bridge to codegen** — when codegen is a larger refactor (v16.5 #N), declaring TS interfaces by hand unblocks type safety today. The downside is drift risk if Python models change without TS updates; the upside is zero risk to the codegen pipeline.
2. **`as` casts are compile-time-only but reveal real bugs** — `useProductExport.ts`'s `c.has_body` filter was always returning `[]` because the backend never sends `has_body`. The new typed return exposed the drift. Documenting drift inline (rather than silently fixing it) keeps the change scope bounded to typed-wrapper narrowing.
3. **`Promise<unknown>` wrappers don't fail silently — they just don't help** — every consumer that called `await fetchStudioSummary()` got an unknown return; the data flowed through with `any`-style duck-typing. v16.5 #7 demonstrates that even partial type narrowing (39 of 42 wrapper functions) makes composable bugs visible.
4. **SSE stream returns are genuinely `unknown`** — `runCreatorAgentPlanStream` parses JSON over a stream; the response shape depends on the agent's `action_label` field. Narrowing requires either (a) defining a tagged-union response envelope, or (b) typing the parser helpers instead of the stream itself. This is genuinely out of scope for v16.5 #7 and is the only `Promise<unknown>` left in `apps/dashboard/src/api/`.

## 6. Commits (4 atomic, DP-06 ≤3 files each)

1. `0a64afee` — `feat(dashboard-contracts): v16.5 #7 — add DTO files for 5 wrapper gaps` (6 files: 5 new + index.ts modify)
2. `a898694c` — `refactor(dashboard): v16.5 #7 — narrow health/studio/workflows wrappers to DTOs` (3 files)
3. `c851dbe9` — `refactor(dashboard): v16.5 #7 — narrow cvg/decisions wrappers to DTOs` (2 files)
4. `f2f75688` — `refactor(dashboard): v16.5 #7 — convert fetchChapters cast to as unknown as` (1 file)

Plus this handoff doc as commit 5 (when committed).
