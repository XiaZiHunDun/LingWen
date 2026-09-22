# Phase 108 — Bulk Regenerate Illustration Endpoint — Design Spec

> **Date**: 2026-09-22
> **Phase**: v60.5 → v60.6 (planned)
> **Cluster**: Phase 102+ extension #6 (Phase 103 #1 + Phase 104 #2 + Phase 105 #3 + Phase 106 #4 + Phase 107 #5)
> **Type**: Backend + frontend medium extension — **mirrors Phase 107 exactly**
> **Workflow**: Solo repo, no PR, direct commits on master

## 1. Motivation

Phase 107 shipped `bulk_delete_assets` (DELETE `/api/illustrations?slug=...&ids=...`) — limit 50, sequential for-loop over `_delete_asset_inner` helper, I090/I091/I095 5th EXTENDED. The same UX surface (multi-select + sticky bottom bulk action bar in `IllustrationGallery.vue`) now needs a parallel "bulk regenerate" path.

Phase 90-94 already shipped single-asset `PUT /api/illustrations/{asset_id}/regenerate` (atomic, returns same `id` with new `scene_json` + `final_prompt`). The new endpoint re-uses that per-asset logic for batches.

**Why now**: BACKLOG §Phase 108+ explicitly reserved this. After Phase 107 the user-visible UX already supports multi-select; extending it to "regenerate selected" is the obvious next step. No spec drift, no new invariant needed (I090/I091/I095 EXTENDED via docstring per YAGNI).

## 2. Goals (in scope)

1. `PUT /api/illustrations?slug=...&ids=...` route (Phase 108 NEW)
2. `_regenerate_asset_inner` helper extracted from existing `regenerate_illustration` route handler (Phase 108 NEW)
3. `regenerate_illustration` route refactored to thin wrapper delegating to helper (mirrors Phase 107 delete_asset refactor)
4. Sequential for-loop, dedupe via `dict.fromkeys`, 1..10 validation (over-10 → 422, empty → 422)
5. Per-asset failure tracking via `record_failure` / `record_success` keyed `(slug, "regeneration")`
6. Per-asset `audit_log.record_event` + `notifications.publish` double-write (same ULID) — I091 6th double-write site
7. Returns `200 OK` + `{regenerated: [...], failed: [...], summary: {total, ok, fail}}`
8. Frontend: `<NPopconfirm>`-wrapped "批量再生" button in `IllustrationGallery.vue` bulk action bar
9. Frontend: `useBulkRegenerateToast.ts` composable (mirror `useBulkDeleteToast.ts`, 3 variants)
10. Frontend: `bulkRegenerateAssets(slug, assetIds, opts)` typed wrapper
11. Frontend: `useIllustrationStore.bulkRegenerateAssets(slug, assetIds, opts)` Pinia action
12. I090 6th caller / I091 6th double-write site / I095 6th EXTENDED via docstring

## 3. Non-Goals (out of scope, deferred)

- **Bulk generate** (bulk create new illustrations) — different UX (no source asset to select); revisit if user demand emerges
- **Bulk regenerate with per-asset override** (each asset its own provider/model) — JSON-body variant; deferred per user clarification
- **Async task queue / SSE progress** — single-route synchronous return per user clarification
- **Progress bar / "X/N 完成" live text** — NProgress or text spinner is frontend-only, NOT backend-driven; client doesn't get mid-flight progress; deferred per user clarification

## 4. Architecture

### 4.1 Backend — helper extraction pattern (mirror Phase 107)

**Current** (Phase 90-94): `regenerate_illustration` route handler is one fat function — `LoadError` handling, asset lookup, params resolution, `pipeline.regenerate_illustration()` call, error mapping. ~85 lines.

**Phase 108 refactor**: extract `_regenerate_asset_inner(project_slug, asset_id, project_root, provider, model, fallback_chain_list, threshold, *, mode: Literal["single", "bulk"]) -> Literal["ok", "not_found", "unknown_model", "stage_error"]`. Returns status string; caller maps to HTTP.

**Both call sites** (single + bulk) delegate to this helper. All failure-tracking semantics inherited verbatim:
- `LoadError` on `project_root_for` → caller maps to 404 (load error happens before helper)
- 404 asset-not-found → helper returns `"not_found"` → `record_success(slug, event_type="regeneration")` (no-op success — defensive counter reset, symmetric with Phase 107)
- `UnknownModelError` on `pipeline.regenerate_illustration` → helper returns `"unknown_model"` → caller maps to 422; NO counter increment (user input error, same as Phase 107 cleanup_route 422)
- `IllustrationError` on pipeline → helper returns `"stage_error"` → `record_failure(slug, e, project_root=root, ...)` (counter increments, threshold-cross possible)
- Success → helper returns `"ok"` → `record_success(slug, event_type="regeneration")` + `audit_log.record_event` + `notifications.publish` (same ULID, I091 double-write)

### 4.2 Backend — bulk route

**`PUT /api/illustrations?slug=...&ids=...&provider=...&model=...&fallback_chain=...`**

- `slug: str = Query(...)` — project slug
- `ids: str = Query(...)` — comma-separated asset ids (1..10)
- `provider: Optional[str] = Query(None)` — applies to all assets (int-bulk param)
- `model: Optional[str] = Query(None)` — applies to all assets
- `fallback_chain: Optional[str] = Query(None)` — comma-separated, applies to all

Sequential for-loop calls `_regenerate_asset_inner` per asset. Pre-resolves `meta_by_id` dict once before loop (perf: 10×M filesystem reads → O(1) dict lookup per asset). Dedupe via `dict.fromkeys(raw_ids)` preserving order.

Validation (422 on all):
- empty `ids`
- over 10 unique ids (mirror Phase 107 over-50)

Per-asset status:
- `"ok"` → appended to `regenerated[]` with full `GenerateResponse` shape
- `"not_found"` → appended to `failed[]` with `{id, status: "not_found"}`
- `"unknown_model"` → appended to `failed[]` with `{id, status: "unknown_model", detail: {...}}`
- `"stage_error"` → appended to `failed[]` with `{id, status: "stage_error", stage: "...", error: "..."}`

Returns `200 OK` always (after 404 slug LoadError raised before loop).

### 4.3 Frontend — IllustrationGallery.vue additions

Reuse existing `selection: Set<string>` + `selectionTick: ref` from Phase 107. Add second `<NButton>` (alongside existing "批量删除") wrapped in `<NPopconfirm>`:

```vue
<NPopconfirm
  @positive-click="onBulkRegenerate"
  positive-text="确认再生"
  negative-text="取消"
>
  <template #trigger>
    <NButton data-testid="bulk-regenerate-btn" class="bulk-regenerate-btn">
      批量再生
    </NButton>
  </template>
  将对已选的 {{ selectedCount }} 张插图重新生成。继续？
</NPopconfirm>
```

`onBulkRegenerate()` mirrors `confirmBulkDelete()`:
- Early-return if `bulkRegenerateInFlight.value` (in-flight guard, prevents race)
- Snapshot `ids = Array.from(selection.value)`
- Set in-flight flag
- Try: `await store.bulkRegenerateAssets(slug, ids, opts)` + toast + emit `'bulk-regenerated'`
- Catch: show error toast, KEEP selection so user can retry
- Finally: clear in-flight flag

### 4.4 Frontend — useBulkRegenerateToast composable

`apps/dashboard/src/composables/useBulkRegenerateToast.ts` — mirror `useBulkDeleteToast.ts`:

```ts
export function useBulkRegenerateToast() {
  const message = useMessage()
  return {
    showResult(result: BulkRegenerateResult) {
      const { ok, fail } = result.summary
      if (fail === 0) message.success(`已再生 ${ok} 张插图`)
      else if (ok === 0) message.error(`0 个成功，${fail} 个失败 — 查看详情`)
      else message.warning(`已再生 ${ok} 张，失败 ${fail} 张 — 查看详情`)
    }
  }
}
```

3 vitest unit tests covering all 3 variants.

### 4.5 Frontend — typed wrapper

`apps/dashboard/src/api/illustrations.ts` — NEW interface + function:

```ts
export interface BulkRegenerateFailedItem {
  id: string
  status: 'not_found' | 'unknown_model' | 'stage_error'
  stage?: string
  error?: string
}

export interface BulkRegenerateResult {
  regenerated: GenerateResponse[]  // reuses Phase 90 GenerateResponse shape
  failed: BulkRegenerateFailedItem[]
  summary: { total: number; ok: number; fail: number }
}

export interface BulkRegenerateOptions {
  provider?: string
  model?: string
  fallbackChain?: string
}

export async function bulkRegenerateAssets(
  slug: string,
  assetIds: string[],
  opts: BulkRegenerateOptions = {},
): Promise<BulkRegenerateResult> {
  // pre-validate 1..10, non-empty
  // build PUT /api/illustrations?slug=...&ids=...&provider=...&model=...&fallback_chain=...
}
```

### 4.6 Frontend — Pinia store action

`useIllustrationStore.bulkRegenerateAssets(slug, assetIds, opts)` — mirror `bulkDeleteAssets`:
- Lazy-imports `api.bulkRegenerateAssets`
- On success: reactively UPDATES each `result.regenerated[]` entry in local `assets[]` by id (same id, new scene_json + url + bytes — atomic update from server; use `assets[idx] = regenerated_item` per match)
- `failed[]` with `status === 'not_found'` → REMOVE from `assets[]` (defensive; should never happen in healthy state)
- `failed[]` with `status === 'unknown_model'` or `'stage_error'` → RETAIN in `assets[]` for retry
- 2 vitest tests: BulkRegenHappy + BulkRegenPartial

## 5. Failure tracking semantics (mirror Phase 107)

| Per-asset outcome | `record_failure` | `record_success` | `audit_log` | `publish` | Counter effect |
|---|---|---|---|---|---|
| `LoadError` (slug not found) | — | — | — | — | none (caller raises 404 before helper) |
| 404 asset-not-found | — | YES (no-op success) | — | — | reset to 0 |
| `UnknownModelError` (422) | — | — | — | — | none (user input error) |
| `IllustrationError` (stage error) | YES | — | YES | YES | increment, may cross threshold |
| Success | — | YES | YES | YES | reset to 0 |

`counter key = (slug, "regeneration")` — tuple-keyed, isolated from `(slug, "deletion")` etc.

Threshold crossing per `(slug, "regeneration")` pair → exactly one `severity="warning"` notification (I095 invariant).

`mode='bulk'` parameter is interpolated into `audit_log.record_event(extra=...)` and `NotificationEvent.extra` for downstream analytics but does NOT affect counter state.

## 6. Limits & validation

- 1 ≤ unique ids ≤ 10
- empty → 422
- over-10 → 422
- duplicate ids → dedupe via `dict.fromkeys` preserving order
- slug missing → 404 (LoadError, before loop)
- `provider`/`model`/`fallback_chain` query params apply to ALL assets in batch (uniform — per user clarification)

## 7. UX states

| Selection state | Bulk action bar visibility | Buttons |
|---|---|---|
| 0 selected | hidden | — |
| 1 selected | visible | 取消 / 批量删除 / 批量再生 |
| N>1 selected | visible | 取消 / 批量删除 / 批量再生 |

In-flight guard: while `bulkRegenerateInFlight === true`, both bulk buttons are disabled. NPopconfirm cancel is purely frontend — no API call, no counter touch.

## 8. Files to add / modify

### Backend (NEW)
- `apps/studio_api/routes/illustrations.py` — `_regenerate_asset_inner` helper + `bulk_regenerate_assets` route + `regenerate_illustration` refactor (thin wrapper)
- `tests/test_phase108_bulk_regenerate.py` — 10 regression guards G1-G10
- `apps/studio_api/tests/test_bulk_regenerate_api.py` — 10 backend pytest T1-T10

### Frontend (NEW)
- `apps/dashboard/src/composables/useBulkRegenerateToast.ts` — composable + spec
- `apps/dashboard/src/api/illustrations.ts` — extend with `BulkRegenerate*` interfaces + `bulkRegenerateAssets()` wrapper
- `apps/dashboard/src/stores/useIllustrationStore.js` — extend with `bulkRegenerateAssets()` Pinia action
- `apps/dashboard/src/stores/useIllustrationStore.spec.js` — extend with 2 NEW tests (BulkRegenHappy / BulkRegenPartial)
- `apps/dashboard/src/composables/useBulkRegenerateToast.spec.ts` — 3 NEW tests
- `apps/dashboard/src/components/illustrations/IllustrationGallery.vue` — add bulk-regenerate button + `onBulkRegenerate` handler + emit `'bulk-regenerated'`
- `apps/dashboard/src/components/illustrations/IllustrationGallery.spec.ts` — extend with 6 NEW tests F1-F6 (mirror Phase 107 F1-F6)

### Docs / config (UPDATE)
- `docs/superpowers/specs/2026-09-22-phase-108-bulk-regenerate-design.md` — THIS SPEC
- `docs/superpowers/plans/2026-09-22-phase-108-bulk-regenerate.md` — implementation plan
- `docs/superpowers/handoffs/2026-09-22-phase-108-bulk-regenerate-handoff.md` — handoff
- `.lingwen/architecture.yml` — I090 6th caller / I091 6th site / I095 6th EXTENDED via docstring
- `CLAUDE.md` — v60.5 → v60.6 + I-row 6th EXTENDED
- `collaboration/CURRENT_STATUS.md` — Phase 108 entry
- `collaboration/BACKLOG.md` — Phase 108 entry + remove reserved slot

## 9. Validation gates (all must pass)

| Gate | Expected |
|---|---|
| pytest `test_bulk_regenerate_api.py` T1-T10 | 10/10 NEW PASS |
| pytest `test_phase108_bulk_regenerate.py` G1-G10 | 10/10 NEW guards PASS |
| pytest Phase 90/94/96/100/101/106/107 guards preserved | preserved GREEN |
| pytest `packages/lingwen-illustrations/tests/test_pipeline.py` + `test_notifications.py` | preserved GREEN |
| ruff check on all introduced files | clean |
| vitest `IllustrationGallery.spec.ts` F1-F6 + F7/F8 (Phase 107) | 8/8 PASS |
| vitest `useBulkRegenerateToast.spec.ts` | 3/3 NEW PASS |
| vitest `useIllustrationStore.spec.js` BulkRegenHappy + BulkRegenPartial | 2/2 NEW PASS |
| pnpm tsc --noEmit | 0 NEW errors (48 pre-existing baseline) |
| pnpm exec knip (from `apps/dashboard/`) | 0 NEW unused exports |

## 10. Estimated commit count

~14 atomic commits on master, mirror Phase 107 structure:
1. spec (this doc)
2. plan
3. backend RED tests T1-T10
4. helper refactor (`_regenerate_asset_inner`)
5. `bulk_regenerate_assets` route
6. fixup (counter isolation / ULID distinctness / docstring)
7. frontend multi-select RED tests F1-F6
8. typed wrapper `bulkRegenerateAssets`
9. store action `bulkRegenerateAssets`
10. composable `useBulkRegenerateToast`
11. multi-select button + handler in `IllustrationGallery.vue`
12. lazy `useMessage` in `useBulkRegenerateToast`
13. store bulk wrapper + race comment + F7/F8 end-to-end
14. regression guards G1-G10
15. invariants EXTENDED 6th
16. CLAUDE.md v60.5 → v60.6 + handoff + BACKLOG + CURRENT_STATUS + MEMORY

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| 10×5-30s serial API call = 50-300s total (worse than Phase 107 since LLM calls not file deletes) | limit=10 (per user clarification); client-side AbortController timeout (default 180s, configurable); NPopconfirm sets user expectation; in-flight guard prevents stacking |
| `mode='bulk'` parameter collides with future `mode='parallel'` if user later wants parallel | mode literal `Literal["single", "bulk"]` allows extension via union |
| Per-asset failure tracking inflates `audit_log.jsonl` size (10×) | acceptable; same as Phase 107 pattern; phase-report-v2 (Phase 110+ deferred) can aggregate |
| Frontend timeout 60s default may not cover 10×10s | switch to `Promise.race` with explicit AbortController 180s |
| I095 EXTENDED 6th may break invariant monitoring UI (existing users may not understand) | symmetric with Phase 107 — counter key semantic already widened to (slug, event_type) tuple in Phase 104 |

## 12. Lessons inherited from Phase 107 (verbatim)

1. Helper refactor preserves single-call contract — Phase 94 regenerate tests must stay green
2. Pre-resolve `meta_by_id` dict once before loop — 10×M filesystem reads → O(1) dict lookup per asset
3. `dict.fromkeys(raw_ids)` dedupes preserving order — Python 3.7+ dict insertion order guarantee
4. Sequential for-loop is intentional — preserves audit_log.jsonl + SSE arrival order
5. Vue 3 Set reactivity requires `selectionTick.value++` — already implemented in Phase 107
6. `mode='bulk'` parameter does NOT change counter state — analytics-only
7. `<NPopconfirm>` cancel path purely frontend — backend counter never touched
8. `Literal` type import for `mode` parameter is safe at module top

## 13. Out-of-band future work (NOT in this phase)

- Phase 109+ telemetry-driven chain reorder (gated on Phase 102-108 data accumulation)
- Phase 109+ bulk generate (create new illustrations from bulk request)
- Phase 109+ bulk regenerate with per-asset provider/model override (JSON-body variant)
- Phase 110+ delete from NotificationsPage dropdown
- ARCHDEBT-REAL continuation — closed since Phase 88; reopen only on new N.14 audit

## 14. References

- Spec: `docs/superpowers/specs/2026-09-22-phase-108-bulk-regenerate-design.md` (THIS)
- Plan: TBD (after spec approved)
- Handoff: TBD (after implementation)
- Phase 107 handoff: `docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md`
- Phase 107 spec: `docs/superpowers/specs/2026-09-22-phase-107-bulk-delete-design.md`
- Phase 94 handoff: regenerate endpoint atomic PUT
- `.lingwen/architecture.yml` I090/I091/I095 (with Phase 108 6th EXTENDED via docstring)
