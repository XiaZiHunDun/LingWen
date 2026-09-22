# Phase 107 — Bulk Delete Illustration Endpoint — Handoff

> **Date**: 2026-09-22
> **Phase**: v60.4 → v60.5
> **Cluster**: Phase 102+ extension #5 (Phase 103 was #1, Phase 104 was #2, Phase 105 was #3, Phase 106 was #4)
> **Type**: Backend + frontend medium extension (1 backend route file helper refactor + 1 new route + 4 new frontend files + 1 modified component + 4 test files)
> **Workflow**: Solo repo, no PR, direct commits on master

## What was delivered

Phase 107 introduces a `bulk_delete_assets` endpoint (`DELETE /api/illustrations?slug=...&ids=...`) and multi-select UX in `IllustrationGallery.vue`. The existing `delete_asset` route (DELETE `/api/illustrations/{asset_id}`, Phase 90 + Phase 106 failure tracking) was refactored to delegate to a NEW module-private `_delete_asset_inner` helper so single and bulk share identical per-asset failure tracking (I090/I091/I095 contract). A `mode: Literal["single", "bulk"]` discriminator is interpolated into `audit_log.record_event(extra=...)` and `notifications.publish(extra=...)` for downstream analytics.

### 1. NEW helper: `_delete_asset_inner` in illustrations.py

- Extracted from `delete_asset` route handler (Phase 106 5-path logic) into module-private async helper
- Returns `Literal["ok", "not_found", "load_error", "store_error"]` status
- Takes `mode: Literal["single", "bulk"] = "single"` parameter; interpolates into `audit_log.extra` and `NotificationEvent.extra` for downstream analytics
- Both `delete_asset` (Phase 106) and `bulk_delete_assets` (Phase 107 NEW) delegate to this helper
- All failure-tracking semantics inherited verbatim: 404 LoadError on `project_root_for` → `record_failure(slug, e, project_root=None, ...)`; 404 asset-not-found → `record_success(slug, event_type="deletion")` (no-op success); `StoreError` on `storage.delete_asset` → `record_failure(slug, e, project_root=real_root, ...)`; success → `record_success(slug, event_type="deletion")` + audit_log + publish (same ULID)

### 2. NEW route: `bulk_delete_assets` in illustrations.py

- `@app.delete("/api/illustrations")` (placed before `/{asset_id}` for explicit route ordering documentation)
- `slug: str = Query(...)` + `ids: str = Query(...)` parameters
- Sequential per-asset iteration (preserves audit_log.jsonl + SSE arrival order)
- Dedupe via `dict.fromkeys(raw_ids)` preserving order — handles `"a,a,b,b,b,c,d,d"` → 4 unique entries
- Validation: 422 on empty ids; 422 on > 50 unique ids
- 404 on slug LoadError (raised before loop)
- Pre-resolves `meta_by_id: dict = {a.id: a for a in storage.list_assets(project_root)}` ONCE before the loop (perf: 50×M filesystem reads → O(1) dict lookup per asset)
- Returns 200 + `{deleted: [...], failed: [{id, status}, ...], summary: {total, ok, fail}}`
- Per-asset status: `"ok"` → appended to `deleted`; `"not_found"` / `"store_error"` → appended to `failed[]` with `id` + `status`

### 3. Frontend UX: multi-select + bulk action bar

- `IllustrationGallery.vue` — selection `Set<string>` local state + per-card `<NCheckbox>` overlay + sticky bottom `<div class="bulk-action-bar">` (visible when `selection.size > 0`)
- `selectionTick: ref<number>` increment forces Vue 3 Set reactivity (Vue 3 doesn't track Set mutations directly)
- Bulk action bar contains: count + `<NButton>` cancel + `<NPopconfirm>`-wrapped bulk delete button (Phase 106 NPopconfirm pattern reused)
- `confirmBulkDelete()` calls `store.bulkDeleteAssets` + toast + emits `'bulk-deleted'`
- Component-local selection survives asset prop changes (cross-page safe); cleared after successful confirmBulkDelete
- `props.selectable: boolean = true` — checkbox only renders when not explicitly disabled (orthogonal UX)

### 4. NEW frontend composable: `useBulkDeleteToast`

- Wraps Naive UI `useMessage` for 3 toast variants:
  - `fail === 0` → `message.success("已删除 N 张插图")`
  - `ok === 0` → `message.error("0 个成功，M 个失败 — 查看详情")`
  - mixed → `message.warning("已删除 N 张，失败 M 张 — 查看详情")`
- 3 vitest unit tests covering all 3 variants

### 5. NEW typed wrapper: `bulkDeleteAssets`

- `apps/dashboard/src/api/illustrations.ts` — `BulkDeleteResult` + `BulkDeleteFailedItem` interfaces + `bulkDeleteAssets(slug, assetIds)` function
- Pre-validates `assetIds` (1..50, non-empty) before fetch (defensive UX)
- Maps to `DELETE /api/illustrations?slug=...&ids=...` with proper `encodeURIComponent`

### 6. NEW store action: `bulkDeleteAssets`

- `useIllustrationStore.bulkDeleteAssets(slug, assetIds)` — Pinia action
- Lazy-imports `api.bulkDeleteAssets` to keep initial bundle small (consistent with `regenerate` action)
- Reactively removes `result.deleted` + `result.failed.filter(not_found)` from local `assets[]`
- `store_error` failures RETAINED in `assets[]` (may be retried)
- 2 vitest tests: BulkHappy (full success path) + BulkPartial (mixed retention)

### 7. I090 / I091 / I095 EXTENDED via docstring only (5th extension)

- **I090 EXTENDED 5th**: `bulk_delete_assets` is the 5th caller of `lru_cleanup` / `audit_log.record_event` (after pipeline.generate + pipeline.regenerate + cleanup_route + delete_asset)
- **I091 EXTENDED 5th**: `bulk_delete_assets` is the 5th double-write site (audit_log + publish with same ULID per asset)
- **I095 EXTENDED 5th via docstring**: per-asset `record_failure/record_success` semantics inherited from shared `_delete_asset_inner` helper; counter keys still `(slug, "deletion")`; threshold crossing per `(slug, "deletion")` pair still emits exactly one severity="warning" notification regardless of bulk iteration size; `mode='bulk'` parameter is interpolated into `audit_log` + `NotificationEvent` extra dict for downstream analytics but does NOT affect counter state — bulk iteration does NOT change I095 invariants

## Validation gates (all green)

| Gate | Result |
|------|--------|
| pytest `apps/studio_api/tests/test_bulk_delete_api.py` (T1-T10) | 10/10 NEW PASS |
| pytest `tests/test_phase107_bulk_delete.py` (G1-G10) | 10/10 NEW guards PASS |
| pytest `apps/studio_api/tests/test_illustrations_api.py` Phase 106 T1-T6 + G1-G6 | 12/12 preserved GREEN |
| pytest `tests/test_phase102/103/104/105/106_*.py` | 30+ guards preserved GREEN |
| pytest `packages/lingwen-illustrations/tests/test_notifications.py` + `test_pipeline.py` | preserved GREEN |
| ruff check on all 4 introduced files | clean |
| vitest `IllustrationGallery.spec.ts` (F1-F6) | 6 NEW PASS + existing preserved |
| vitest `useBulkDeleteToast.spec.ts` | 3 NEW PASS |
| vitest `useIllustrationStore.spec.ts` (BulkHappy + BulkPartial) | 2 NEW PASS |
| pnpm tsc --noEmit | 0 new errors (48 pre-existing baseline unchanged) |

## 13 atomic commits on master

1. `1e2fcac8` docs(phase-107): bulk delete illustration endpoint design spec
2. `5485f879` docs(phase-107): bulk delete implementation plan
3. `44cfc5cc` test(phase-107): bulk delete API 10 RED tests
4. `70c529f6` refactor(phase-107): extract _delete_asset_inner helper
5. `f50d0888` feat(phase-107): bulk_delete_assets endpoint
6. `59e340c3` fix(phase-107): bulk pre-resolves meta_by_id + ULID distinctness + docstring
7. `f764d107` test(phase-107): IllustrationGallery multi-select 6 RED tests
8. `b616ddd0` feat(phase-107): bulkDeleteAssets typed wrapper
9. `1f32c898` feat(phase-107): useIllustrationStore.bulkDeleteAssets action
10. `8322a3d5` feat(phase-107): useBulkDeleteToast composable
11. `c836b26b` feat(phase-107): IllustrationGallery multi-select + bulk action bar
12. `33a32384` fix(phase-107): useIllustration bulk wrapper + race comment + F7/F8
13. `2a117839` feat(phase-107): lazy useMessage in useBulkDeleteToast
14. `d2f3315d` test(phase-107): bulk delete regression guards G1-G10
15. `79945b33` docs(phase-107): extend I090/I091/I095 to include bulk_delete_assets
16. (this commit) docs(phase-107): CLAUDE.md v60.4 → v60.5 + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync

(Note: 16 commits total — Task A 4 + Task B 7 + Task C 3 = 14 commits; the count discrepancy is because Task B has 7 commits with 1 fixup, plus the prior 2 doc commits at the start. Final atomic count on master is 16.)

## Lessons (5 from spec + 4 new discovered)

1. **Helper refactor preserves single-delete contract** — `_delete_asset_inner` extracted from `delete_asset` route; `mode="single"` is the default parameter; Phase 106 T1-T6 + G1-G6 preserved GREEN. Test isolation was crucial (helper refactor without test breakage).
2. **Pre-resolve `meta_by_id` dict once before loop** — 50×M filesystem reads → O(1) dict lookup per asset. Pattern: pre-resolve shared state before for-loop, not inside it. Fixup commit `59e340c3` applied this perf improvement.
3. **`dict.fromkeys(raw_ids)` dedupes while preserving insertion order** — Python 3.7+ dict insertion order guarantee makes this idiomatic; no need for `set()` (which loses order) or `sorted()` (which changes order). T7 + G9 verify.
4. **Sequential for-loop is intentional** — preserves audit_log.jsonl + SSE arrival order; parallel iteration would break I091 invariant (ULID-shared double-write per asset). Spec note: rate-limit safety, predictable failure tracking.
5. **Vue 3 Set reactivity requires `selectionTick.value++`** — Vue 3 doesn't track Set/Map mutations directly; the standard fix is to either replace the Set (`selection.value = new Set(...)`) or use a `tick` ref that increments after each mutation. `IllustrationGallery.vue` uses both patterns.
6. **NEW (Phase 107)**: `mode='bulk'` parameter does NOT change counter state — interpolated into `audit_log` + `NotificationEvent` extra dict for downstream analytics only. I095 invariant preserved unchanged.
7. **NEW (Phase 107)**: `<NPopconfirm>` cancel path purely frontend (inherited from Phase 106) — even with bulk iteration, cancel emits nothing; backend counter never touched.
8. **NEW (Phase 107)**: `Literal` type import for `mode` parameter is safe at module top (no runtime cost); provides static type narrowing for callers.
9. **NEW (Phase 107)**: NPopconfirm wrapping bulk delete button mirrors single-delete (Phase 106); `positive-text="确认删除"` / `negative-text="取消"`; data-testid preserved.

## Cluster cumulative

- Phase 90-107 = **18 phases** / 1 NEW package (lingwen-illustrations) + 5 carryover closures + 7 REQ-002 v2 sub-projects delivered + **5 Phase 102+ extensions**:
  - Phase 103: Per-Chapter default_models Overrides (first)
  - Phase 104: notify_threshold per event_type (second)
  - Phase 105: Cleanup Route Failure Tracking (third)
  - Phase 106: DELETE Endpoint Failure Tracking (fourth)
  - Phase 107: BULK DELETE Endpoint Failure Tracking (fifth, this phase)

## Future work (per BACKLOG)

- **Phase 108+**: telemetry-driven chain reorder — gated on Phase 102-107 data accumulation (need real failure telemetry to inform reorder logic)
- **Phase 108+**: delete from NotificationsPage dropdown — orthogonal UX (click-to-delete from notification history)
- **Phase 110+**: bulk REGENERATE — YAGNI eval after bulk-delete ships; same `_regenerate_asset_inner` helper extraction pattern would apply
- **ARCHDEBT-REAL continuation** — closed since Phase 88; reopen only on new N.14 audit
- **deletion event_type is now FULLY wired for both single and bulk paths** — all 4 event_types have ≥1 caller + counter isolation + I090/I091/I095 invariant coverage complete; no more orphan references. The I091 invariant is now the most-covered invariant (5 double-write sites).

## References

- Spec: `docs/superpowers/specs/2026-09-22-phase-107-bulk-delete-design.md`
- Plan: `docs/superpowers/plans/2026-09-22-phase-107-bulk-delete.md`
- Phase 102 handoff: `docs/superpowers/handoffs/2026-09-20-phase-102-settings-persistence-extension-handoff.md`
- Phase 103 handoff: `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md`
- Phase 104 handoff: `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md`
- Phase 105 handoff: `docs/superpowers/handoffs/2026-09-21-phase-105-cleanup-route-failure-tracking-handoff.md`
- Phase 106 handoff: `docs/superpowers/handoffs/2026-09-21-phase-106-delete-endpoint-failure-tracking-handoff.md`
- `.lingwen/architecture.yml` I090/I091/I095 (with Phase 107 scope extension)
- `CLAUDE.md` v60.5 + I090/I091/I095 rows updated