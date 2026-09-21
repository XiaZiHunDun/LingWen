# Phase 105 — Cleanup Route Failure Tracking — Design Spec

> **Date**: 2026-09-21
> **Phase**: v60.2 → v60.3
> **Cluster**: Phase 102+ extension #3 (Phase 103 was #1, Phase 104 was #2)
> **Type**: Backend-only extension (1 route file + 1 module helper move + 2 test files)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 105 wires `cleanup_route` (POST `/api/projects/{slug}/illustrations/cleanup`) into the per-event-type failure tracking machinery introduced in Phase 102 and widened in Phase 104. Currently the route emits `cleanup` notification events for dry-run and successful delete, but does **not** call `notifications.record_failure()` when `lru_cleanup` or `project_root_for` raises — so `notify_threshold["cleanup"]` can never fire, leaving sustained cleanup failures invisible.

**Architectural fix**: relocate `_resolve_threshold()` from `pipeline.py` to `notifications.py` as `notifications.resolve_threshold()`. The threshold resolver naturally belongs with the counter state (the YAML that configures `notify_threshold` is the source-of-truth that drives counter behavior). Pipeline keeps a back-compat re-export so existing callers/tests are unchanged.

**cleanup_route behavior change**:
- `LoadError` on `project_root_for` → `record_failure(event_type="cleanup")` + HTTPException 404
- `StoreError` on `lru_cleanup` → `record_failure(event_type="cleanup")` + HTTPException 422
- Successful `lru_cleanup` (≥1 asset deleted) → `record_success(event_type="cleanup")` to reset counter
- 422 validation (`chapter_num` missing for `type=chapter`) → **no** failure tracking (user input error, not system failure)
- `_load_max_assets` silent fallback (yaml/OSError) → **no** failure tracking (defensive read, not a cleanup failure)

**Out of scope** (future candidates):
- `deletion` event_type usage — DELETE endpoint does not exist yet
- Telemetry-driven chain reorder — gated on Phase 102 failure tracker data accumulation

## Sub-projects delivered

### 1. Helper relocation: `_resolve_threshold` → `notifications.resolve_threshold`

**Rationale**: The threshold resolver queries `settings["notify_threshold"]` (a YAML-derived dict) and returns `int` or `INFINITY_THRESHOLD`. The counter state machine in `notifications.py` is the consumer of that threshold value. Co-locating resolver with state eliminates the implicit dependency `pipeline.py → notifications.py` (settings consumer → state owner) by making the resolver a peer of the state. Pipeline retains `_resolve_threshold` as a thin re-export for existing callers and tests.

**Before** (`packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py:60-88`):

```python
INFINITY_THRESHOLD = math.inf

def _resolve_threshold(settings: dict, event_type: str) -> int | float:
    """Phase 104 spec §3."""
    nt = settings.get("notify_threshold", INFINITY_THRESHOLD)
    if isinstance(nt, bool):
        return INFINITY_THRESHOLD
    if isinstance(nt, (int, float)):
        return nt
    if isinstance(nt, dict):
        return nt.get(event_type, INFINITY_THRESHOLD)
    return INFINITY_THRESHOLD
```

**After** (`packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py`):

```python
# NEW — was pipeline._resolve_threshold (Phase 104)
def resolve_threshold(settings: dict, event_type: str) -> int | float:
    """Resolve notify_threshold for specific event_type.

    After Pydantic normalization, settings["notify_threshold"] is dict[str, int]
    where keys are subset of ("generation", "regeneration", "cleanup", "deletion").
    Missing key → INFINITY_THRESHOLD (never warn for that event type).

    Defensive: if int legacy form slips through, returns int directly. If
    something else (bool, None), returns INFINITY to err on "don't warn".

    Phase 105 relocation: moved from pipeline.py so cleanup_route can use the
    same resolver without depending on pipeline module.
    """
    nt = settings.get("notify_threshold", INFINITY_THRESHOLD)
    if isinstance(nt, bool):
        return INFINITY_THRESHOLD
    if isinstance(nt, (int, float)):
        return nt
    if isinstance(nt, dict):
        return nt.get(event_type, INFINITY_THRESHOLD)
    return INFINITY_THRESHOLD
```

Pipeline retains a thin re-export for backwards compat (Phase 100 pattern: `pipeline._resolve_threshold = notifications.resolve_threshold`):

```python
# In pipeline.py — back-compat re-export
from lingwen_illustrations.notifications import resolve_threshold as _resolve_threshold
```

This preserves the existing pipeline.py call sites (`generate_illustration` + `regenerate_illustration`) without renaming the local reference.

### 2. cleanup_route failure tracking

**Before** (`apps/studio_api/routes/cleanup_route.py`):

```python
async def cleanup_illustrations(slug: str, request: CleanupRequest) -> CleanupResponse:
    try:
        root = project_root_for(slug)
    except LoadError as e:
        raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

    max_assets = _load_max_assets(root)

    if request.type == "chapter" and request.chapter_num is None:
        raise HTTPException(422, ...)

    if request.dry_run:
        # ... emits synthetic NotificationEvent, returns ...
        return CleanupResponse(...)

    try:
        deleted = lru_cleanup(root, type=request.type, chapter_num=request.chapter_num, max_count=max_assets)
    except StoreError as e:
        raise HTTPException(422, detail={"stage": "cleanup", "error": str(e)}) from e

    # Phase 99 I091: emit per-deleted-asset cleanup event (double-write)
    for meta in deleted:
        # ... audit_log.record_event + notifications.publish ...
        pass

    return CleanupResponse(...)
```

**After**:

```python
async def cleanup_illustrations(slug: str, request: CleanupRequest) -> CleanupResponse:
    # Phase 105: settings load + threshold resolution for failure tracking.
    # Pipeline-style helper relocated to notifications.resolve_threshold (Phase 105).
    settings = _load_cleanup_settings(_load_settings_root(slug))
    threshold = notifications.resolve_threshold(settings, "cleanup")

    try:
        root = project_root_for(slug)
    except LoadError as e:
        # Phase 105: record cleanup failure for threshold tracking.
        notifications.record_failure(slug, e, project_root=_settings_root, threshold=threshold, event_type="cleanup")
        raise HTTPException(404, detail={"stage": "load", "error": e.message}) from e

    max_assets = _load_max_assets(root)

    if request.type == "chapter" and request.chapter_num is None:
        raise HTTPException(422, ...)  # validation: NO failure tracking

    if request.dry_run:
        # ... emits synthetic NotificationEvent ...
        return CleanupResponse(...)

    try:
        deleted = lru_cleanup(root, type=request.type, chapter_num=request.chapter_num, max_count=max_assets)
    except StoreError as e:
        # Phase 105: record cleanup failure for threshold tracking.
        notifications.record_failure(slug, e, project_root=root, threshold=threshold, event_type="cleanup")
        raise HTTPException(422, detail={"stage": "cleanup", "error": str(e)}) from e
    else:
        # Phase 105: successful cleanup resets counter for "cleanup" only.
        notifications.record_success(slug, event_type="cleanup")

    # Phase 99 I091: emit per-deleted-asset cleanup event (double-write)
    for meta in deleted:
        # ... audit_log.record_event + notifications.publish ...
        pass

    return CleanupResponse(...)
```

Notes:
- `_load_cleanup_settings(root)` reads `.lingwen/illustration_settings.yaml` and returns dict (matches pipeline's `_load_illustration_settings` shape). Reuses `_load_max_assets` already in the file. For Phase 105 simplicity, both helpers share the same yaml file.
- The 422 validation path (`chapter_num is None` for `type=chapter`) does NOT call `record_failure` — this is a user input validation error, not a system failure. Documented as a deliberate exclusion in the regression guard.
- `_load_max_assets` silent fallback (line 49-50) does NOT call `record_failure` — defensive read; the actual cleanup may still succeed with default `max_assets=20`.

### 3. Counter isolation preserved

Phase 104 invariant: failures in different event types do NOT bleed into each other's counters. Phase 105 inherits this — `cleanup` counter is independent of `generation` / `regeneration` counters. Regression guard G5 verifies that 3 cleanup failures do NOT increment `generation` counter.

### 4. Settings persistence integration

`cleanup_route` reads `.lingwen/illustration_settings.yaml` (same file as pipeline) to resolve `notify_threshold["cleanup"]`. If the file is missing or empty, `_load_cleanup_settings` returns `{}` and `resolve_threshold` returns `INFINITY_THRESHOLD` (never warn). Matches Phase 102 pipeline pattern.

## Test coverage matrix

| Path | Counter state | Tested in |
|------|---------------|-----------|
| LoadError on project_root_for | increment `(slug, "cleanup")` counter | T1 |
| StoreError on lru_cleanup | increment `(slug, "cleanup")` counter | T2 |
| Successful lru_cleanup (≥1 deleted) | reset `(slug, "cleanup")` counter | T3 |
| Successful lru_cleanup (0 deleted, under limit) | reset `(slug, "cleanup")` counter | T3 |
| 422 validation chapter_num missing | NO counter change | T4 |
| dry_run path | NO counter change | T5 |
| Threshold crossing after N consecutive StoreErrors | emit severity=warning notification | T6 |
| Counter isolation: 3 cleanup failures don't increment generation counter | counters stay separate | T7 |
| Helper relocation: `notifications.resolve_threshold` exists | API contract preserved | T8 |
| Back-compat: `pipeline._resolve_threshold` still callable | no caller regression | T9 |

## Regression guards G1-G6

| ID | Asserts | Catches |
|----|---------|---------|
| G1 | `cleanup_route` imports `notifications` AND calls `record_failure(event_type="cleanup")` ≥ 2 times | Phase 105 reverts to no-tracking state |
| G2 | `cleanup_route` calls `notifications.record_success(slug, event_type="cleanup")` ≥ 1 time in success path | Phase 105 reverts counter leak (stuck elevated) |
| G3 | `notifications.resolve_threshold` exists AND is the same callable as `pipeline._resolve_threshold` | Helper relocation drift / orphan re-export |
| G4 | Pipeline code (`generate_illustration` + `regenerate_illustration`) still uses `_resolve_threshold` (re-exported) | Pipeline caller regression |
| G5 | 3 record_failure(slug, ..., event_type="cleanup") calls leave generation counter = 0 | Counter isolation break |
| G6 | `_load_cleanup_settings` reads `.lingwen/illustration_settings.yaml` with permissive fallback | Settings reader regression |

## Out of scope

- `deletion` event_type — DELETE endpoint for illustrations does not exist; deletion events would come from a future DELETE route
- Telemetry-driven chain reorder — Phase 102 failure tracker needs real-world data accumulation before reorder logic is justified
- Per-type UI for `cleanup` failure status — already provided by Phase 104's NotifyEvent stream + existing bell dropdown (no new UI needed)

## Validation gates

- `pytest packages/lingwen-illustrations/` → 现有测试 + 6 NEW T1-T9 cleanup failure tests GREEN
- `pytest apps/studio_api/tests/` → cleanup_route tests preserved + 6 NEW GREEN
- `pytest tests/test_phase105_cleanup_route_failure_tracking.py` → 6 NEW guards GREEN
- `ruff check` on introduced files → clean
- Phase 102 / 103 / 104 regression guards preserved (40 tests)
- vitest useProjectSettings + ProjectSettingsIllustration preserved (no frontend change)
- pnpm tsc 0 new errors

## Atomic commits (~9)

1. **spec** — design doc (this file)
2. **plan** — implementation plan
3. **refactor** — move `_resolve_threshold` → `notifications.resolve_threshold`; pipeline re-exports
4. **feat** — cleanup_route: `_load_cleanup_settings` + `record_failure` on LoadError
5. **feat** — cleanup_route: `record_failure` on StoreError + `record_success` on success
6. **test** — 6 NEW pytest tests (T1-T6 failure paths + threshold trigger)
7. **test** — 3 NEW tests (T7 counter isolation + T8 helper relocation + T9 back-compat)
8. **test** — 6 NEW regression guards G1-G6
9. **docs** — CLAUDE.md v60.2→v60.3 + I095 EXTENDED scope + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync

## Risk assessment

| Risk | Mitigation |
|------|------------|
| Counter leak on success path (counter stays elevated) | `record_success` in success path (T3) |
| Double-count on both LoadError + StoreError in same request | LoadError raises before lru_cleanup runs (try/except ordering) |
| Validation errors (422 chapter_num) pollute counter | Explicit skip — G4 verifies no record_failure in validation path |
| Pipeline caller regression on helper rename | Back-compat re-export (`pipeline._resolve_threshold = notifications.resolve_threshold`) |
| Test suite pollution from in-memory counter state | Tests use unique slugs (e.g. `phase105-slug-N`) to avoid cross-test bleed |

## Lessons referenced

- Phase 102 §3 (threshold + counter state machine)
- Phase 104 §3 (per-event-type counter isolation)
- Phase 104 §4 (`_resolve_threshold` defensive fallback pattern — bool excluded to prevent silent truthy acceptance)
- Phase 104 §5 (`_normalize_int` failure-path defaults to 3 not raise — preserves user UX)
- Phase 104 §6 (I095 EXTENDED via docstring preserves YAGNI — same invariant name with wider scope)
- Phase 100 pattern (back-compat re-export for relocated helpers)

## Future phases

- **Phase 106**: `deletion` event_type tracking — when DELETE endpoint added
- **Phase 107**: telemetry-driven chain reorder — gated on real failure tracker data
- **Phase 108+**: `deletion` settings validator tightening — requires DELETE endpoint existence