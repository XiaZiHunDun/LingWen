# Phase 108 — Bulk Regenerate Illustration Endpoint — Handoff

> **Date**: 2026-09-22
> **Phase**: v60.5 → v60.6
> **Cluster**: Phase 102+ extension #6 (Phase 103 was #1, Phase 104 was #2, Phase 105 was #3, Phase 106 was #4, Phase 107 was #5)
> **Type**: Backend + frontend medium extension (1 backend route file helper extraction + 1 new route + 4 new frontend files + 1 modified component + 5 test files)
> **Workflow**: Solo repo, no PR, direct commits on master

## What was delivered

Phase 108 introduces a `bulk_regenerate_assets` endpoint (`PUT /api/illustrations?slug=...&ids=...`) and bulk-regenerate UX in `IllustrationGallery.vue` (alongside the bulk-delete UX from Phase 107). The existing `regenerate_illustration` route was NOT modified — instead, a NEW module-private `_regenerate_asset_inner` helper was extracted to centralize counter logic for bulk iteration. **CRITICAL Option A architectural decision**: the helper is a **counter-only shim** — pipeline.regenerate_illustration ALREADY emits `audit_log.record_event` + `notifications.publish` internally at pipeline.py:585-607 with the same ULID via `new_event_id()`. Calling these directly in the helper would break I091 "shared ULID double-write" invariant. So the helper calls `record_failure/record_success` (counter + warning emission) but DOES NOT call `audit_log` or `notifications.publish`.

### 1. NEW helper: `_regenerate_asset_inner` in illustrations.py

- Extracted from existing `regenerate_illustration` route's counter patterns
- **Counter-only shim** — Option A: no audit_log or notifications direct calls
- Returns 3-tuple: `(status: Literal["ok", "not_found", "unknown_model", "stage_error"], new_meta: IllustrationMetadata | None, exc: Exception | None)` — preserves exception detail for STAGE_HTTP_CODES mapping
- Calls `record_failure(slug, error, *, project_root=None, threshold, event_type="regeneration")` on LoadError + `record_failure(slug, error, *, project_root=real_root, threshold, event_type="regeneration")` on StoreError; `record_success(slug, event_type="regeneration")` on success
- All failure-tracking semantics inherited verbatim from Phase 102/104/105/106/107 patterns; counter keys `(slug, "regeneration")` per Phase 104 tuple-keyed widening
- `_load_regeneration_settings(project_root)` NEW helper reads `.lingwen/illustration_settings.yaml` with permissive fallback (mirrors Phase 105 `_load_cleanup_settings` + Phase 106 `_load_deletion_settings`)

### 2. NEW route: `bulk_regenerate_assets` in illustrations.py

- `@app.put("/api/illustrations")` (placed before `/{asset_id}` for explicit route ordering documentation)
- `slug: str = Query(...)` + `ids: str = Query(...)` + uniform per-call `provider` / `model` / `fallback_chain` params
- Sequential per-asset iteration (preserves audit_log.jsonl + SSE arrival order)
- Dedupe via `dict.fromkeys(raw_ids)` preserving order
- Validation: 422 on empty ids; 422 on > 10 unique ids (lower than delete's 50 because LLM calls take 5-30s/asset)
- 404 on slug LoadError (raised before loop)
- Pre-resolves `meta_by_id: dict = {a.id: a for a in storage.list_assets(project_root)}` ONCE before the loop
- Returns 200 + `{regenerated: [...], failed: [{id, status}, ...], summary: {total, ok, fail}}`
- Per-asset status: `"ok"` → appended to `regenerated` (with new metadata); `"not_found"` / `"unknown_model"` / `"stage_error"` → appended to `failed[]` with `id` + `status`
- Per-asset uniform params (no per-asset override) — Phase 108 scope limit; documented as future work

### 3. Frontend UX: bulk-regenerate button alongside bulk-delete

- `IllustrationGallery.vue` — selection `Set<string>` local state SHARED with Phase 107 bulk-delete (reuses same selection)
- New bulk-regenerate button in sticky bottom bulk action bar (alongside bulk-delete button from Phase 107)
- Wrapped in `<NPopconfirm>` mirroring Phase 106/107 pattern (`positive-text="确认重新生成"` / `negative-text="取消"`)
- `confirmBulkRegenerate()` calls `store.bulkRegenerateAssets` + `useBulkRegenerateToast` + emits `'bulk-regenerated'`
- `AbortController` per-asset for timeout handling (T11 test)

### 4. NEW frontend composable: `useBulkRegenerateToast`

- Wraps Naive UI `useMessage` for 3 toast variants:
  - `fail === 0` → `message.success("已重新生成 N 张插图")`
  - `ok === 0` → `message.error("0 个成功，M 个失败 — 查看详情")`
  - mixed → `message.warning("已重新生成 N 张，失败 M 张 — 查看详情")`
- **Lazy useMessage** for test isolation (no n-message-provider needed)
- 3 vitest unit tests covering all 3 variants

### 5. NEW typed wrapper: `bulkRegenerateAssets`

- `apps/dashboard/src/api/illustrations.ts` — `BulkRegenerateResult` + `BulkRegenerateFailedItem` interfaces + `bulkRegenerateAssets(slug, assetIds, provider, model, fallbackChain)` function
- Pre-validates `assetIds` (1..10, non-empty) before fetch
- Maps to `PUT /api/illustrations?slug=...&ids=...` with proper `encodeURIComponent`

### 6. NEW store action: `bulkRegenerateAssets`

- `useIllustrationStore.bulkRegenerateAssets(slug, assetIds, provider, model, fallbackChain)` — Pinia action
- Lazy-imports `api.bulkRegenerateAssets` to keep initial bundle small
- Reactively REPLACES `result.regenerated` metadata in local `assets[]` (regenerated asset keeps same id, new metadata)
- `failed[]` entries RETAINED in `assets[]` (may be retried)
- 2 vitest tests: BulkHappy (full success path) + BulkPartial (mixed retention)

### 7. I090 / I095 EXTENDED via docstring only (6th extension)

- **I090 EXTENDED 6th**: `bulk_regenerate_assets` is the 6th caller of `audit_log.record_event` (transitively via pipeline.regenerate_illustration) + `lru_cleanup` (transitively via pipeline)
- **I095 EXTENDED 6th via docstring**: per-asset `record_failure/record_success` semantics inherited from shared `_regenerate_asset_inner` helper; counter keys still `(slug, "regeneration")`; threshold crossing per `(slug, "regeneration")` pair emits exactly one severity="warning" notification regardless of bulk iteration size; helper does NOT call audit_log/publish — Option A: pipeline.regenerate_illustration owns emit to avoid breaking I091
- **I091 NOT EXTENDED**: no new double-write site added (Option A: pipeline emits once)

## CRITICAL — Option A architectural decision

Phase 108's `_regenerate_asset_inner` helper is fundamentally different from Phase 107's `_delete_asset_inner` helper:

- Phase 107 `_delete_asset_inner`: **complete shim** — helper calls `record_failure/record_success` + `audit_log.record_event` + `notifications.publish` directly. Phase 107 single delete route ALSO calls these directly in its non-bulk path. Helper mirrors single-delete 5-path logic verbatim.

- Phase 108 `_regenerate_asset_inner`: **counter-only shim** — helper calls `record_failure/record_success` (counter + warning emission) only. Audit_log + publish transits via `pipeline.regenerate_illustration` which ALREADY emits these with same ULID.

**Why Option A was chosen**: pipeline.py:585-607 has a `try/except` block that wraps the entire regenerate flow with:
```python
new_event_id = ulid.new().str
audit_log.record_event(slug=slug, event=event_type, payload={...}, extra={...})
notifications.publish(slug=slug, event=event_type, payload={...}, extra={...})
```
The `new_event_id` is generated ONCE per regenerate call. If the helper ALSO called audit_log/publish, it would generate a SECOND ULID — breaking I091 "audit_log + publish share same ULID per event" invariant. Option A preserves this by NOT calling them in helper; pipeline owns the full double-emit block scope.

**Validation**: G10 regression guard verifies helper has ZERO `audit_log.record_event` / `notifications.publish` direct calls.

## Validation gates (all green)

| Gate | Result |
|------|--------|
| pytest `apps/studio_api/tests/test_bulk_regenerate_api.py` (T1-T12) | 12/12 NEW PASS |
| pytest `tests/test_phase108_bulk_regenerate.py` (G1-G10) | 10/10 NEW guards PASS |
| pytest `apps/studio_api/tests/test_illustrations_api.py` Phase 106 T1-T6 + G1-G6 | 12/12 preserved GREEN |
| pytest `apps/studio_api/tests/test_bulk_delete_api.py` Phase 107 T1-T10 + G1-G10 | 20/20 preserved GREEN |
| pytest `tests/test_phase102/103/104/105/106/107_*.py` | 60+ guards preserved GREEN |
| pytest `packages/lingwen-illustrations/tests/test_notifications.py` + `test_pipeline.py` | preserved GREEN |
| ruff check on all 4 introduced files | clean |
| vitest `IllustrationGallery.spec.ts` (F1-F8) | 8 NEW PASS + existing preserved |
| vitest `useBulkRegenerateToast.spec.ts` | 3 NEW PASS |
| vitest `useIllustrationStore.spec.ts` (BulkHappy + BulkPartial) | 2 NEW PASS |
| pnpm tsc --noEmit | 0 new errors (48 pre-existing baseline unchanged) |

## 13 atomic commits on master

1. `ffc59497` docs(phase-108): bulk regenerate illustration endpoint design spec
2. `d0aac86c` docs(phase-108): bulk regenerate implementation plan
3. `e602c8ae` fix(phase-108): spec self-review fixes — LoadError → 404, store update semantics, AbortController timeout
4. `8e671d4c` test(phase-108): bulk regenerate API 10 RED tests
5. `ac6761bc` feat(phase-108): _regenerate_asset_inner counter-only helper + _load_regeneration_settings
6. `1ff59d61` fix(phase-108): add unknown_model + T12 perf guard + minor cleanups
7. `89a8df07` fix(phase-108): Option A architecture — helper is counter-only, pipeline owns emit
8. `3f089604` fix(phase-108): align tests with Option A — fake_regenerate mimics pipeline emit
9. `c4da91cb` test(phase-108): IllustrationGallery bulk-regenerate 8 RED tests
10. `1b34bd26` feat(phase-108): useBulkRegenerateToast composable + 3 tests
11. `52ac5c58` feat(phase-108): bulkRegenerateAssets typed wrapper + 4 tests
12. `4b176cd3` feat(phase-108): useIllustrationStore.bulkRegenerateAssets action + 2 tests
13. `63b26f3f` feat(phase-108): IllustrationGallery bulk-regenerate button + handler
14. `997a2382` feat(phase-108): lazy useMessage in useBulkRegenerateToast for test isolation
15. `6785b2df` test(phase-108): bulk regenerate regression guards G1-G10
16. `a3875436` docs(phase-108): extend I090/I091/I095 to include bulk_regenerate_assets

(Final atomic count on master is 16 — includes 2 prior docs + 1 spec self-review fixup + 4 task-A commits + 4 task-B commits + 1 lazy useMessage + 3 task-C commits + 1 Option A fixup + 1 align tests fixup. The original Phase 108 task list was 13 commits but real implementation had 16 commits due to Option A pivot + spec self-review + lazy useMessage optimization.)

## Lessons (5 from spec + 5 new discovered)

### From spec
1. **Option A architecture prevents double-emit breaking I091** — `_regenerate_asset_inner` is counter-only shim; pipeline.regenerate_illustration ALREADY emits audit_log + publish with shared ULID via `new_event_id()`. Calling again in helper would generate a SECOND ULID, breaking I091. Validation: G10 verifies ZERO direct calls in helper.
2. **3-tuple helper return preserves exception detail** — `(status, new_meta, exc)` shape allows STAGE_HTTP_CODES mapping for granular HTTP response codes per failure type (e.g., `unknown_model` → 422 validation, `stage_error` → 502 bad gateway).
3. **`dict.fromkeys(raw_ids)` dedupes preserving order** — Python 3.7+ dict insertion order guarantee; idiomatic dedupe. T7 + G9 verify.
4. **Sequential for-loop preserves audit_log arrival order** — parallel iteration would break I091 (shared ULID per asset). Predictable failure tracking + rate-limit safety.
5. **Pipeline emit block scope ONLY on success** — pipeline.py:585-607 wraps the FULL regenerate flow; failure paths exit early without audit_log/publish calls (counter incremented via helper, audit deferred). I095 contract preserved.

### NEW (Phase 108 discovered)
6. **Lazy useMessage enables test isolation without n-message-provider** — `useMessage()` called inside composable function body (not at module top) avoids Naive UI's message provider dependency in vitest. Pattern mirrors Phase 107 `2a117839` lazy useMessage.
7. **Lower limit for regenerate (10 vs delete's 50)** — reflects 5-30s/asset LLM latency. Bulk delete is ~0ms/asset; can absorb 50 ops in ~2s. Bulk regenerate is ~30s/asset worst-case; 10 ops × 30s = 5min realistic upper bound.
8. **Per-asset uniform params (no per-asset override)** simplifies scope — `provider` / `model` / `fallback_chain` set ONCE for the entire bulk call. Phase 108 doesn't pre-orthize per-asset override UX (YAGNI; can extend later if needed).
9. **AbortController per-asset timeout** — frontend can cancel mid-bulk via `AbortController.abort()`; backend AbortController wired into pipeline to surface cancellation (T11 test verifies).
10. **Pipeline emit block scope discipline** — `pipeline.regenerate_illustration` emit scope ONLY on success path; failure paths exit without emit (counter incremented via helper, audit deferred). I095 contract preserved because helper owns counter but pipeline owns emit.

## Cluster cumulative

- Phase 90-108 = **19 phases** / 1 NEW package (lingwen-illustrations) + 5 carryover closures + 7 REQ-002 v2 sub-projects delivered + **6 Phase 102+ extensions**:
  - Phase 103: Per-Chapter default_models Overrides (first)
  - Phase 104: notify_threshold per event_type (second)
  - Phase 105: Cleanup Route Failure Tracking (third)
  - Phase 106: DELETE Endpoint Failure Tracking (fourth)
  - Phase 107: BULK DELETE Endpoint Failure Tracking (fifth)
  - Phase 108: BULK REGENERATE Endpoint Failure Tracking (sixth, this phase)

## Future work (per BACKLOG)

- **Phase 109+**: telemetry-driven chain reorder — gated on Phase 102-108 data accumulation (need real failure telemetry to inform reorder logic)
- **Phase 109+**: delete from NotificationsPage dropdown — orthogonal UX (click-to-delete from notification history)
- **Phase 110+**: bulk UPDATE settings (chapter_overrides via Settings page) — orthogonal UX to per-asset regeneration
- **Phase 110+**: bulk EXPORT — download all selected illustrations as a zip
- **ARCHDEBT-REAL continuation** — closed since Phase 88; reopen only on new N.14 audit
- **regeneration event_type is now FULLY wired for both single and bulk paths** — all 4 event_types have ≥1 caller for bulk; counter isolation preserved; I090/I091/I095 invariant coverage complete (I091 inherits via pipeline.emit, no new double-write site)

## References

- Spec: `docs/superpowers/specs/2026-09-22-phase-108-bulk-regenerate-design.md`
- Plan: `docs/superpowers/plans/2026-09-22-phase-108-bulk-regenerate.md`
- Phase 102 handoff: `docs/superpowers/handoffs/2026-09-20-phase-102-settings-persistence-extension-handoff.md`
- Phase 103 handoff: `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md`
- Phase 104 handoff: `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md`
- Phase 105 handoff: `docs/superpowers/handoffs/2026-09-21-phase-105-cleanup-route-failure-tracking-handoff.md`
- Phase 106 handoff: `docs/superpowers/handoffs/2026-09-21-phase-106-delete-endpoint-failure-tracking-handoff.md`
- Phase 107 handoff: `docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md`
- `.lingwen/architecture.yml` I090/I091/I095 (with Phase 108 scope extension)
- `CLAUDE.md` v60.6 + I090/I091/I095 rows updated