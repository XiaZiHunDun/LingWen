# Phase 106 — Delete Illustration Endpoint Failure Tracking — Handoff

> **Date**: 2026-09-21
> **Phase**: v60.3 → v60.4
> **Cluster**: Phase 102+ extension #4 (Phase 103 was #1, Phase 104 was #2, Phase 105 was #3)
> **Type**: Backend + frontend small extension (1 route file + 1 module + 1 frontend component + 2 test files)
> **Workflow**: Solo repo, no PR, direct commits on master

## What was delivered

Phase 106 wires `delete_asset` route (DELETE `/api/illustrations/{asset_id}`, Phase 90) into the per-event-type failure tracking machinery introduced in Phase 102, widened in Phase 104, and extended to `cleanup` in Phase 105. The route existed but did **not** call `notifications.record_failure()` on errors, nor `audit_log.record_event` + `notifications.publish` on success — so `notify_threshold["deletion"]` (declared in Phase 104 `KNOWN_NOTIFY_EVENT_TYPES`) could never fire, leaving sustained deletion failures invisible.

### 1. NEW helper: `_load_deletion_settings` in illustrations.py

- Reads `.lingwen/illustration_settings.yaml` with permissive fallback (missing file → `{}`; malformed yaml → `{}`)
- Mirrors `_load_cleanup_settings` from Phase 105 cleanup_route.py:67-74 (acceptable duplication for module-locality per Phase 105 lesson)
- Returns `dict` consumed by `notifications.resolve_threshold(settings, "deletion")`

### 2. DELETE endpoint failure tracking wired

- 404 LoadError on `project_root_for` → `record_failure(slug, e, project_root=None, threshold=resolve_threshold({}, "deletion"), event_type="deletion")` (counter increments; audit_log skipped since no real project context)
- 404 asset-not-found → `record_success(slug, event_type="deletion")` (**no-op success pattern** — asset is already gone, resets counter defensively to avoid stale warnings from prior transient failures)
- `StoreError` on `storage.delete_asset` → `record_failure(slug, e, project_root=real_root, threshold=resolved, event_type="deletion")` + HTTPException 500
- Successful delete → `record_success(slug, event_type="deletion")` in `else` branch of try/except + audit_log + publish + HTTPException 200
- `NPopconfirm` cancel path: purely frontend (no network call, no counter touched)

### 3. DELETE endpoint double-write (I091 completion)

- audit_log.record_event + notifications.publish share SAME ULID (per I091 invariant)
- Completes I091 coverage for **all 4 event_types** (generation / regeneration / cleanup / **deletion**)
- `extra={"trigger": "manual"}` consistent with cleanup_route pattern
- `new_event_id()` (ULID) generated once and passed to both writers

### 4. Frontend UX: Naive UI `<NPopconfirm>` wrapping

- `IllustrationCard.vue` 🗑 button wrapped in `<NPopconfirm>` (Naive UI) — `positive-text="确认删除"` / `negative-text="取消"`
- data-testid="delete-btn" preserved on inner button (Phase 90 convention preserved — existing tests don't break)
- `:aria-label` preserved for screen readers (a11y Phase 41+ convention)
- Cancel path is purely frontend (no emit, no network, no counter touched)

### 5. I090 / I091 / I095 EXTENDED via docstring only

- **I090 EXTENDED**: 4th caller of `lru_cleanup` / `audit_log.record_event` is `delete_asset` route (after `pipeline.generate_illustration` + `pipeline.regenerate_illustration` + `cleanup_route`)
- **I091 EXTENDED**: 4th double-write site is `delete_asset` route (after pipeline.generate + pipeline.regenerate + cleanup_route) — **completes coverage for all 4 event_types**
- **I095 EXTENDED via docstring** (4th extension of same invariant name): all 4 event_types now have ≥1 caller; 404 asset-not-found treated as no-op success via `record_success` to defensively reset counter; counter resets via `record_success` in else branch of `storage.delete_asset` try/except — same pattern as cleanup_route

## Validation gates (all green)

| Gate | Result |
|------|--------|
| pytest `apps/studio_api/tests/test_illustrations_api.py::test_delete_asset_*` (T1-T6) | 6/6 NEW PASS |
| pytest `packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py` (T7-T9) | 6/6 NEW PASS |
| pytest `tests/test_phase106_delete_endpoint_failure_tracking.py` (G1-G6) | 6/6 NEW guards PASS |
| pytest `packages/lingwen-illustrations/tests/test_pipeline.py + test_notifications.py` | preserved GREEN |
| pytest `tests/test_phase102/103/104/105_*.py` | 34/34 preserved GREEN |
| pytest `apps/studio_api/tests/test_cleanup_route_failure_tracking.py` (Phase 105) | 6/6 preserved GREEN |
| ruff check on all 4 introduced files | clean |
| vitest `IllustrationCard.spec.ts` (F1-F4 — after F4 dropped per Phase 106 lesson #2) | preserved |
| pnpm tsc --noEmit | 0 new errors (48 pre-existing baseline unchanged) |

## 11 atomic commits on master

1. `f459ddad` docs(phase-106): design spec
2. `cd04e148` docs(phase-106): implementation plan — 11 atomic commits
3. `3ca5a216` test(phase-106): T1-T6 delete_asset failure path tests (RED)
4. `c82a3ce0` test(phase-106): T7-T9 deletion isolation + helper resilience tests (RED-ish)
5. `d50ee0ad` feat(phase-106): _load_deletion_settings helper + module imports
6. `03e1606c` feat(phase-106): wire delete_asset failure tracking + double-write
7. `388be067` test(phase-106): F1-F4 NPopconfirm tests (RED)
8. `5d7adbbf` feat(phase-106): NPopconfirm wrapping around 🗑 delete button
9. `781cf019` fix(phase-106): remove F4 Esc-dismissal test — naive-ui NPopconfirm default
10. `8d4f4a49` test(phase-106): G1-G6 regression guards (RED-ish for G6)
11. `23466a79` docs(phase-106): extend I090/I091/I095 to include DELETE route
12. (this commit) docs(phase-106): CLAUDE.md v60.3 → v60.4 + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync

## Lessons (5 from spec + 2 new discovered)

1. **404 asset-not-found as no-op success** — defensive counter reset; treat idempotent delete as success (matches cleanup_route "0 deleted under limit" pattern). Symmetric with Phase 105.
2. **naive-ui NPopconfirm doesn't support Esc-by-default** — discovered during F4 test implementation; NPopconfirm dismisses on click-outside / button click only. F4 test was removed (`781cf019`) since the behavior is intentional, not a bug. (T6 unrelated.)
3. **Tuple-keyed counter isolation** — Phase 106 inherits Phase 104 invariant unchanged. (T7 + G5 verify.)
4. **`_resolve_threshold` defensive fallback** — `_load_deletion_settings` returns `{}` on missing/malformed yaml; `resolve_threshold({}, "deletion")` returns `INFINITY_THRESHOLD` (never warn). (T9 verifies helper resilience.)
5. **I095 EXTENDED via docstring preserves YAGNI** — Phase 106 EXTENDS again (4th extension of same invariant name). (G6 verifies invariant extension.)
6. **NEW (Phase 106)**: `import yaml` is safe at module top (no heavy deps; PyYAML); `from lingwen_illustrations import audit_log, notifications` is safe at module top (lightweight modules, no import-time side effects — verified in cleanup_route.py:27).
7. **NEW (Phase 106)**: Frontend `NPopconfirm` cancel path is purely frontend (no `emit('delete')` fires, no network call, no counter touched) — but backend counter **never sees** cancel. Counter state only mutated when DELETE request actually reaches the route.

## Cluster cumulative

- Phase 90-106 = **17 phases** / 1 NEW package (lingwen-illustrations) + 5 carryover closures + 7 REQ-002 v2 sub-projects delivered + **4 Phase 102+ extensions**:
  - Phase 103: Per-Chapter default_models Overrides (first)
  - Phase 104: notify_threshold per event_type (second)
  - Phase 105: Cleanup Route Failure Tracking (third)
  - Phase 106: DELETE Endpoint Failure Tracking (fourth, this phase)

## Future work (per BACKLOG)

- **Phase 107 candidate**: telemetry-driven chain reorder — gated on Phase 102 failure tracker data accumulation (need real deletion failures to inform reorder logic)
- **Phase 108+**: bulk DELETE endpoint (DELETE multiple assets in one request) — YAGNI for v1
- **Phase 108+**: delete from NotificationsPage dropdown — allows click-to-delete from notification history
- **deletion event_type is now FULLY wired** — all 4 event_types have ≥1 caller + counter isolation + I090/I091/I095 invariant coverage complete. No more orphan references.
- ARCHDEBT-REAL continuation — if requested (Phase 88 physically complete; only if scope expands)

## References

- Spec: `docs/superpowers/specs/2026-09-21-phase-106-delete-endpoint-failure-tracking-design.md`
- Plan: `docs/superpowers/plans/2026-09-21-phase-106-delete-endpoint-failure-tracking.md`
- Phase 102 handoff: `docs/superpowers/handoffs/2026-09-20-phase-102-settings-persistence-extension-handoff.md`
- Phase 103 handoff: `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md`
- Phase 104 handoff: `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md`
- Phase 105 handoff: `docs/superpowers/handoffs/2026-09-21-phase-105-cleanup-route-failure-tracking-handoff.md`
- `.lingwen/architecture.yml` I090/I091/I095 (with Phase 106 scope extension)
- `CLAUDE.md` v60.4 + I090/I091/I095 rows updated
