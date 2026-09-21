# Phase 106 — Delete Illustration Endpoint Failure Tracking — Design Spec

> **Date**: 2026-09-21
> **Phase**: v60.3 → v60.4
> **Cluster**: Phase 102+ extension #4 (Phase 103 was #1, Phase 104 was #2, Phase 105 was #3)
> **Type**: Backend + frontend small extension (1 route file + 1 module + 1 frontend component + 2 test files)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 106 wires `delete_asset` route (DELETE `/api/illustrations/{asset_id}`) into the per-event-type failure tracking machinery introduced in Phase 102, widened in Phase 104, and extended to `cleanup` in Phase 105. The route **already exists** at `apps/studio_api/routes/illustrations.py:336-353` (Phase 90) and is called from `useIllustrationStore.deleteAsset` (Phase 90) which is wired to `IllustrationCard.vue`'s 🗑 button. However, the route does **not** call `notifications.record_failure()` on errors, nor `audit_log.record_event` + `notifications.publish` on success — so `notify_threshold["deletion"]` (already declared in Phase 104 `KNOWN_NOTIFY_EVENT_TYPES`) can never fire, leaving sustained deletion failures invisible.

**Architectural changes**:
1. Add `_load_deletion_settings(project_root)` NEW helper in `apps/studio_api/routes/illustrations.py` (mirrors `_load_cleanup_settings` from Phase 105 cleanup_route.py).
2. Wire `delete_asset` route into `notifications.record_failure(slug, error, project_root=..., threshold=..., event_type="deletion")` on failure paths.
3. Wire `delete_asset` route into `audit_log.record_event` + `notifications.publish` (double-write, same ULID) on success — **completes I091 for all 4 event_types**.
4. Wrap `IllustrationCard.vue`'s 🗑 button in `<NPopconfirm>` to prevent accidental deletion (Naive UI pattern).

**deletion event_type wiring contract**:
- `LoadError` on `project_root_for` → `record_failure(event_type="deletion", project_root=None)` + HTTPException 404
- 404 asset-not-found → `record_success(event_type="deletion")` (no-op success: asset is gone, which is what user wanted; resets counter defensively) + HTTPException 404
- `StoreError` on `storage.delete_asset` → `record_failure(event_type="deletion", project_root=root)` + HTTPException 500
- Successful delete → `record_success(event_type="deletion")` + audit_log + publish + HTTPException 200
- `NPopconfirm` cancel → no request fired, no counter change

**Invariant extensions** (via docstring only — YAGNI):
- **I090 EXTENDED**: 4th caller of `lru_cleanup`/`audit_log.record_event` is `delete_asset` route (after `pipeline.generate_illustration` + `pipeline.regenerate_illustration` + `cleanup_route`).
- **I091 EXTENDED**: 4th double-write site is `delete_asset` route (after pipeline.generate + pipeline.regenerate + cleanup_route).
- **I095 EXTENDED via docstring** (4th extension): all 4 event_types (`generation` / `regeneration` / `cleanup` / **`deletion`**) now have at least one caller; `(slug, "deletion")` counter is independently maintained; threshold crossing for `(slug, "deletion")` emits exactly one severity="warning" notification.

**Frontend UX** (1 file modified):
- `apps/dashboard/src/components/illustrations/IllustrationCard.vue` — wrap 🗑 button in `<NPopconfirm>` (Naive UI). No backend wiring change required (`useIllustrationStore.deleteAsset` already exists).

**Out of scope** (future candidates):
- Telemetry-driven chain reorder — gated on Phase 102 failure tracker data accumulation
- Bulk delete (DELETE multiple assets in one request) — YAGNI for v1
- Delete from NotificationsPage dropdown — not requested

## Sub-projects delivered

### 1. NEW helper: `_load_deletion_settings` in illustrations.py

**Rationale**: `notifications.resolve_threshold(settings, event_type)` requires a settings dict (specifically the `notify_threshold` key, which is a per-event-type dict per Phase 104). The cleanup_route.py helper `_load_cleanup_settings` reads `.lingwen/illustration_settings.yaml` and returns `{}` on missing/malformed file (defensive). Phase 106 mirrors this pattern for the DELETE endpoint with a sibling helper `_load_deletion_settings` (identical shape, named for clarity per event_type convention).

**NEW** (`apps/studio_api/routes/illustrations.py`):

```python
def _load_deletion_settings(project_root: Path) -> dict:
    """Phase 106: load notification-relevant settings for deletion event_type.

    Reads .lingwen/illustration_settings.yaml and returns dict containing
    notify_threshold (or empty dict if file missing / malformed). Used by
    delete_asset to resolve per-event-type threshold via
    notifications.resolve_threshold(). Defensive: missing file silently
    returns {} (matches cleanup_route._load_cleanup_settings + pipeline
    _load_illustration_settings pattern).
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return dict(data) if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}
```

Mirrors `_load_cleanup_settings` from Phase 105 cleanup_route.py:67-74 (lines + content very similar — acceptable duplication for module-locality per Phase 105 pattern).

### 2. DELETE endpoint failure tracking

**Before** (`apps/studio_api/routes/illustrations.py:336-353`):

```python
@app.delete("/api/illustrations/{asset_id}")
def delete_asset(
    asset_id: str,
    project_slug: str = Query(...),
) -> dict:
    try:
        project_root = project_root_for(project_slug)
    except LoadError as e:
        raise HTTPException(404, detail=_err_detail(e)) from e

    # Find the asset by id (list_assets is idempotent and cheap)
    all_assets = storage.list_assets(project_root)
    meta = next((a for a in all_assets if a.id == asset_id), None)
    if meta is None:
        raise HTTPException(404, detail=f"asset {asset_id} not found")

    storage.delete_asset(project_root, meta)
    return {"deleted": asset_id}
```

**After** (`apps/studio_api/routes/illustrations.py:336-353`):

```python
@app.delete("/api/illustrations/{asset_id}")
def delete_asset(
    asset_id: str,
    project_slug: str = Query(...),
) -> dict:
    # Phase 106: failure tracking wiring (mirrors cleanup_route Phase 105 pattern).
    # Resolve threshold BEFORE project lookup so failure tracking has a target
    # even on the 404 LoadError path (counter still increments; warning may
    # fire if threshold is set in defaults).
    # NOTE: 404 LoadError path has project_root=None (no real project to read
    # settings from); we pass an empty settings dict — threshold stays INFINITY
    # for this path (matches cleanup_route LoadError behavior).

    try:
        project_root = project_root_for(project_slug)
    except LoadError as e:
        # Phase 106: 404 LoadError path. counter increments but no audit_log.
        notifications.record_failure(
            project_slug, e,
            project_root=None,
            threshold=notifications.resolve_threshold({}, "deletion"),
            event_type="deletion",
        )
        raise HTTPException(404, detail=_err_detail(e)) from e

    # Real project_root exists — resolve actual threshold.
    settings = _load_deletion_settings(project_root)
    threshold = notifications.resolve_threshold(settings, "deletion")

    all_assets = storage.list_assets(project_root)
    meta = next((a for a in all_assets if a.id == asset_id), None)

    if meta is None:
        # Phase 106: 404 asset-not-found = no-op success (per user decision).
        # Asset is already gone (idempotent); record_success resets the
        # (slug, "deletion") counter to avoid stale warnings from prior
        # transient failures. Symmetric with cleanup_route "0 deleted under
        # limit" success path.
        notifications.record_success(project_slug, event_type="deletion")
        raise HTTPException(404, detail=f"asset {asset_id} not found")

    # Phase 106: real delete with failure tracking + double-write.
    try:
        storage.delete_asset(project_root, meta)
    except StoreError as e:
        # Phase 106: StoreError is a system failure — record_failure with
        # the real project_root (audit_log captures the warning event).
        notifications.record_failure(
            project_slug, e,
            project_root=project_root,
            threshold=threshold,
            event_type="deletion",
        )
        raise HTTPException(500, detail=_err_detail(e)) from e
    else:
        # Phase 106: successful delete resets (slug, "deletion") counter.
        notifications.record_success(project_slug, event_type="deletion")

    # Phase 99 I091 + Phase 106: double-write audit_log + publish (same ULID).
    event_id = notifications.new_event_id()
    audit_log.record_event(
        project_root,
        event="deletion",
        asset_meta=meta,
        id=event_id,
        extra={"trigger": "manual"},
    )
    notifications.publish(notifications.NotificationEvent(
        id=event_id,
        project_slug=project_slug,
        event_type="deletion",
        asset_id=meta.id,
        asset_type=meta.type,
        chapter_num=meta.chapter_num,
        style_preset=meta.style_preset,
        provider=meta.provider,
        ts=notifications.now_iso(),
        extra={"trigger": "manual"},
    ))

    return {"deleted": asset_id}
```

Notes:
- 404 LoadError path uses `settings={}` (empty dict) because no project_root exists to read settings from. `resolve_threshold({}, "deletion")` returns `INFINITY_THRESHOLD` (never warn). This matches cleanup_route Phase 105 LoadError path.
- 404 asset-not-found uses `record_success` to defensively reset counter (not `record_failure`). This is a **deliberate deviation** from cleanup_route where 0-deleted success uses `record_success` — same semantic.
- The `extra={"trigger": "manual"}` field is consistent with cleanup_route's `extra={"max_assets": max_assets, "trigger": "manual"}` (Phase 99 pattern). Phase 106 doesn't add LRU-specific fields because DELETE has no max_assets context.
- `record_success` is called in the `else` branch of `try: storage.delete_asset()` — only on actual success (not on StoreError). Symmetric with Phase 105 cleanup_route.
- **Imports to add to illustrations.py top** (not currently imported):
  - `import yaml` — for `_load_deletion_settings` (mirrors cleanup_route.py:24)
  - `from lingwen_illustrations import audit_log, notifications` — illustrations.py currently uses lazy imports inside function bodies for `pipeline` (to avoid loading pipeline deps at module import time per existing convention), but `audit_log` and `notifications` are lightweight (no heavy deps), so module-top import is safe. **Decision**: module-top import (matches cleanup_route.py:27 pattern). If import-time issue surfaces, fall back to lazy import inside `delete_asset`.

### 3. Frontend Naive UI NPopconfirm wrapping

**Before** (`apps/dashboard/src/components/illustrations/IllustrationCard.vue:34-40`):

```vue
<button
  class="delete-btn"
  data-testid="delete-btn"
  :aria-label="`删除 ${label}`"
  @click="emit('delete', asset.id)"
>🗑 删除</button>
```

**After**:

```vue
<NPopconfirm
  positive-text="确认删除"
  negative-text="取消"
  @positive-click="emit('delete', asset.id)"
>
  <template #trigger>
    <button
      class="delete-btn"
      data-testid="delete-btn"
      :aria-label="`删除 ${label}`"
    >🗑 删除</button>
  </template>
  确定删除这张插图？删除后无法恢复。
</NPopconfirm>
```

**NPopconfirm** is a Naive UI component (already available globally via app-surfaces provider). Per Phase 100 pattern (project settings confirm modals), NPopconfirm is the lightweight popover choice — no need for full NDialog.

**IllustrationGallery.vue**: no changes required. `@delete="onDelete"` already wired; NPopconfirm lives per-card.

**useIllustrationStore.deleteAsset**: no changes required. Already calls `DELETE` endpoint + filters from assets. Phase 106 doesn't touch the silent filter pattern (YAGNI — matches Phase 96 original).

### 4. Counter isolation preserved

Phase 104 invariant: failures in different event types do NOT bleed into each other's counters. Phase 106 inherits this — `deletion` counter is independent of `generation` / `regeneration` / `cleanup` counters. Regression guard G5 verifies that 3 deletion failures do NOT increment `generation` counter.

### 5. Settings persistence integration

`delete_asset` route reads `.lingwen/illustration_settings.yaml` (same file as `cleanup_route` + `pipeline._load_illustration_settings`) to resolve `notify_threshold["deletion"]`. If the file is missing or empty, `_load_deletion_settings` returns `{}` and `resolve_threshold` returns `INFINITY_THRESHOLD` (never warn). Matches Phase 102/105 pipeline + cleanup_route pattern.

### 6. Invariant extensions via docstring only

I090 / I091 / I095 EXTENDED via docstring only — **no new invariants introduced** per YAGNI (Phase 103/104/105/106 established this pattern). The existing invariant rules are widened in their `rule` field to mention DELETE route as a caller. Scope fields add Phase 106 enforcement refs.

**I090 EXTENDED** (`.lingwen/architecture.yml`):

```
I090: packages/lingwen-illustrations/src/lingwen_illustrations/storage.py:lru_cleanup
是 illustration LRU 删除唯一入口...
pipeline.generate_illustration / pipeline.regenerate_illustration /
apps/studio_api/routes/cleanup_route.py / apps/studio_api/routes/illustrations.py
(delete_asset) 四处 caller 通过这两个入口...
(Phase 98 + Phase 106 — DELETE route extends caller list)
```

**I091 EXTENDED**:

```
I091: packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py:publish
is the sole fan-out entry point for illustration events.
pipeline.generate_illustration, pipeline.regenerate_illustration,
apps/studio_api/routes/cleanup_route.py, AND apps/studio_api/routes/illustrations.py
(delete_asset) double-write to BOTH audit_log.record_event (I090) and
notifications.publish with the SAME ULID id...
(Phase 99 + Phase 106 — DELETE route extends double-write sites)
```

**I095 EXTENDED via docstring only** (4th extension of same invariant name):

```
I095: ...keyed per (project_slug, event_type) tuple and maintained ONLY via
record_failure() / record_success() helpers... Phase 104 EXTENDED via docstring
(counter keys changed from bare slug to (slug, event_type) tuples)...
Phase 105 EXTENDED via docstring (cleanup_route is the second caller after pipeline.py;
record_failure signature now accepts project_root: Path | None for LoadError on
missing slug path)...
Phase 106 EXTENDED via docstring (delete_asset route is the third caller;
all 4 event_types — generation/regeneration/cleanup/deletion — now have ≥1 caller;
404 asset-not-found treated as no-op success via record_success to defensively
reset counter; counter resets via record_success in else branch of storage.delete_asset
try/except — same pattern as cleanup_route).
```

## Test coverage matrix

| Path | Counter state | Tested in |
|------|---------------|-----------|
| LoadError on `project_root_for` | increment `(slug, "deletion")` counter | T1 |
| Asset not found (404) | reset `(slug, "deletion")` counter (record_success) | T2 |
| Successful `storage.delete_asset` | reset `(slug, "deletion")` counter | T3 |
| `StoreError` on `storage.delete_asset` | increment `(slug, "deletion")` counter | T4 |
| 1 deletion success resets counter from 1 | counter stays 0 | T5 |
| Threshold crossing after N consecutive StoreErrors | emit severity=warning notification | T6 |
| Counter isolation: 3 deletion failures don't increment generation counter | counters stay separate | T7 |
| `resolve_threshold` values for "deletion" key (configured + INFINITY fallback) | settings parser | T8 |
| `_load_deletion_settings` permissive fallback (missing/malformed yaml → {}) | helper resilience | T9 |

## Regression guards G1-G6

| ID | Asserts | Catches |
|----|---------|---------|
| G1 | `delete_asset` route has ≥2 `notifications.record_failure(event_type="deletion")` calls | Phase 106 reverts to no-tracking state |
| G2 | `delete_asset` route has ≥1 `notifications.record_success(..., event_type="deletion")` call | Counter leak (stuck elevated) |
| G3 | `delete_asset` route calls `audit_log.record_event` + `notifications.publish` (double-write I091) | Double-write regression |
| G4 | `_load_deletion_settings` helper exists in `illustrations.py` + reads `.lingwen/illustration_settings.yaml` | Helper deletion regression |
| G5 | 3 record_failure(slug, ..., event_type="deletion") calls leave generation counter = 0 | Counter isolation break |
| G6 | I090 / I091 rule fields mention `delete_asset` route + I095 EXTENDED mentions deletion event_type | Invariant extension regression |

## Out of scope

- **Bulk delete** (DELETE multiple assets in one request) — YAGNI for v1; can be added in future phase if needed
- **Delete from NotificationsPage dropdown** — not requested; current flow uses IllustrationCard button
- **`deletion` settings validator tightening** (Pydantic dict key requirement for "deletion") — already implicit via Phase 104 KNOWN_NOTIFY_EVENT_TYPES ClassVar (which includes "deletion"); no change needed
- **Telemetry-driven chain reorder** — gated on Phase 102 failure tracker data accumulation

## Validation gates

- `pytest packages/lingwen-illustrations/` → existing tests + 3 NEW T7-T9 deletion isolation tests GREEN
- `pytest apps/studio_api/tests/test_illustrations_api.py` → existing tests preserved + 6 NEW T1-T6 deletion failure path tests GREEN
- `pytest tests/test_phase106_delete_endpoint_failure_tracking.py` → 6 NEW G1-G6 regression guards GREEN
- `pytest Phase 102 / 103 / 104 / 105 guards` → 12 + 8 + 8 + 6 = 34 preserved GREEN
- `ruff check` on introduced/changed files → clean
- `vitest apps/dashboard/tests/unit/components/illustrations/IllustrationCard.spec.ts` → existing tests preserved + 4 NEW NPopconfirm tests GREEN (F1-F4)
- `pnpm tsc --noEmit` → 0 new errors (48 pre-existing baseline unchanged)
- `pnpm eslint .` → 0 new errors

## Atomic commits (~8)

1. **spec** — design doc (this file)
2. **plan** — implementation plan
3. **feat** — `_load_deletion_settings` helper + `import yaml` in `illustrations.py`
4. **feat** — `delete_asset` route: failure tracking + double-write (record_failure on LoadError + record_success on 404 + record_failure on StoreError + record_success on success + audit_log + publish)
5. **feat** — `IllustrationCard.vue`: wrap 🗑 button in `<NPopconfirm>`
6. **test** — 6 NEW pytest tests (T1-T6 deletion failure paths + threshold trigger)
7. **test** — 3 NEW tests (T7 counter isolation + T8 resolve_threshold values + T9 helper resilience) + 4 NEW vitest NPopconfirm tests (F1-F4)
8. **test** — 6 NEW regression guards G1-G6
9. **docs** — CLAUDE.md v60.3→v60.4 + I090/I091 EXTENDED + I095 EXTENDED 4th + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync

## §A. Test files migration plan (I079)

Per I079 invariant, all P3-ARCHDEBT specs must include §A. **Phase 106 is NOT a P3-ARCHDEBT phase** (no `infra/*` migration, no test files in `tests/infra/` to migrate). New tests are added to canonical locations:

| Test file | Location | Notes |
|-----------|----------|-------|
| T1-T6 (deletion failure path tests) | `apps/studio_api/tests/test_illustrations_api.py` (append) or NEW `test_delete_asset_failure_tracking.py` | Either works; existing file has `test_delete_asset` (line 167), so append is consistent |
| T7-T9 (deletion isolation tests) | `packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py` (NEW) | Mirrors Phase 105 `test_phase105_cleanup_failure_isolation.py` |
| G1-G6 (regression guards) | `tests/test_phase106_delete_endpoint_failure_tracking.py` (NEW) | Mirrors Phase 105 guards location |
| F1-F4 (NPopconfirm tests) | `apps/dashboard/tests/unit/components/illustrations/IllustrationCard.spec.ts` (extend) | Existing spec file |

No `tests/infra/` migrations needed. No file deletions needed. New files are added in canonical package test directories.

## Risk assessment

| Risk | Mitigation |
|------|------------|
| Counter leak on success path (counter stays elevated) | `record_success` in success path AND 404 no-op path (T3, T2) |
| Double-count on both LoadError + StoreError in same request | LoadError raises before `storage.delete_asset` runs (try/except ordering); regression guard G1 verifies `record_failure` calls present (LoadError + StoreError = 2 expected) |
| NPopconfirm cancel not propagating to backend | Cancel is purely frontend — no `emit('delete')` fires, no network call made |
| 404 no-op success called too aggressively (e.g., when project_root is missing) | 404 asset-not-found requires `project_root` exists (project_root_for succeeded first); LoadError path raises 404 separately without record_success |
| Test suite pollution from in-memory counter state | Tests use unique slugs (e.g. `phase106-slug-N`) to avoid cross-test bleed (Phase 105 pattern) |
| `import yaml` collision with existing imports | Phase 96 already added yaml handling in pipeline.py; only adds to illustrations.py top — no collision |
| Invariant extension causes G2/G3 regression | G6 verifies rule field mentions + scope field additions |

## Lessons referenced

- Phase 102 §3 (threshold + counter state machine — Phase 106 inherits unchanged)
- Phase 104 §3 (per-event-type counter isolation — verified via G5)
- Phase 104 §6 (I095 EXTENDED via docstring preserves YAGNI — Phase 106 EXTENDS again, 4th extension)
- Phase 105 §1 (`_load_cleanup_settings` helper pattern — mirrored as `_load_deletion_settings`)
- Phase 105 §2 (failure tracking on LoadError + StoreError + record_success in else branch — Phase 106 applies same pattern)
- Phase 105 §3 (counter isolation preserved — Phase 106 inherits)
- Phase 98 §4 (LRU archive pattern — Phase 106 uses `storage.delete_asset` not `lru_cleanup` because single-asset DELETE)
- Phase 100 pattern (back-compat re-export for relocated helpers — not needed in Phase 106)
- Phase 102 I091 invariant (audit_log + publish double-write with same ULID — Phase 106 completes this for all 4 event_types)
- Phase 90 pattern (IllustrationCard existing delete button + emit pattern — Phase 106 wraps in NPopconfirm)

## Future phases

- **Phase 107**: telemetry-driven chain reorder — gated on Phase 102 failure tracker data accumulation (need real deletion failures to inform reorder logic)
- **Phase 108+**: bulk DELETE endpoint (YAGNI for v1)
- **Phase 108+**: delete from NotificationsPage dropdown (allows click-to-delete from notification history)
- **Phase 108+**: `deletion` settings validator tightening — already implicit via Phase 104 KNOWN_NOTIFY_EVENT_TYPES; no Pydantic change needed unless we want to enforce minimum notify_threshold for deletion
