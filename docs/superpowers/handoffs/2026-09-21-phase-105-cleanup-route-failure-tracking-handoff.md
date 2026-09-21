# Phase 105 — Cleanup Route Failure Tracking — Handoff

> **Date**: 2026-09-21
> **Phase**: v60.2 → v60.3
> **Cluster**: Phase 102+ extension #3
> **Type**: Backend-only extension (notifications helper relocation + 1 route file + 2 test files)
> **Workflow**: Solo repo, no PR, direct commits on master

## What was delivered

Phase 105 wires `cleanup_route` (POST `/api/projects/{slug}/illustrations/cleanup`, I090 manual LRU entry point) into the per-event-type failure tracking machinery introduced in Phase 102 and widened in Phase 104. Previously the route emitted `cleanup` notification events for dry-run and successful delete, but never called `notifications.record_failure()` for failures — so `notify_threshold["cleanup"]` could never fire, leaving sustained cleanup failures invisible.

### 1. Helper relocation: `_resolve_threshold` → `notifications.resolve_threshold`

- `pipeline.py:_resolve_threshold` (Phase 104) RELOCATED to `notifications.resolve_threshold` (Phase 105)
- Co-locate with counter state (YAML-derived threshold drives counter behavior)
- Pipeline keeps back-compat re-export: `from lingwen_illustrations.notifications import resolve_threshold as _resolve_threshold`
- `pipeline.py` removes local `_resolve_threshold` + `INFINITY_THRESHOLD = math.inf` module constant + `import math`

### 2. notifications.record_failure accepts `project_root: Path | None`

- Allows `cleanup_route` to track LoadError on missing slug (no real project context)
- `_emit_failure_warning` skips `audit_log.record_event` when project_root is None
- Still fires `publish()` for SSE fan-out (in-memory, no IO)
- Pipeline callers unchanged (they always pass real project_root)

### 3. cleanup_route failure tracking wired

- `_load_cleanup_settings(project_root)` NEW helper — reads `.lingwen/illustration_settings.yaml` with permissive fallback (missing file → {}; malformed yaml → {})
- 404 LoadError path: `record_failure(slug, error, project_root=None, threshold=INFINITY, event_type="cleanup")` — counter increments but no audit_log (no real project)
- StoreError on `lru_cleanup`: `record_failure(slug, error, project_root=real, threshold=resolved, event_type="cleanup")` — full audit_log + publish
- Successful `lru_cleanup`: `record_success(slug, event_type="cleanup")` in `else` branch (resets counter even when 0 deleted)
- 422 validation (chapter_num missing for type=chapter): NO failure tracking (user input error)
- dry_run path: NO failure tracking (synthetic notification, not a real failure)
- `_load_max_assets` silent yaml fallback: NO failure tracking (defensive read)

### 4. I095 EXTENDED via docstring only (no new invariant)

Same invariant name with wider scope:
- `cleanup_route` is the second caller after `pipeline.py`
- `project_root: Path | None` added to `record_failure` / `_emit_failure_warning` signatures
- `_resolve_threshold` RELOCATED from pipeline.py to notifications.py with pipeline back-compat re-export

## Validation gates (all green)

| Gate | Result |
|------|--------|
| pytest `apps/studio_api/tests/test_cleanup_route_failure_tracking.py` | 6/6 NEW PASS (T1-T6) |
| pytest `packages/lingwen-illustrations/tests/test_phase105_cleanup_failure_isolation.py` | 3/3 NEW PASS (T7-T9) |
| pytest `tests/test_phase105_cleanup_route_failure_tracking.py` | 6/6 NEW guards PASS (G1-G6) |
| pytest `packages/lingwen-illustrations/tests/test_pipeline.py + test_notifications.py` | 15/15 PASS (preserved) |
| pytest `packages/lingwen-illustrations/tests/test_phase103_*.py + test_phase104_*.py` | 21/21 PASS (preserved) |
| pytest `tests/test_phase102_settings_persistence_extension.py` | 12/12 PASS (preserved) |
| ruff check on all 5 introduced files | clean |
| vitest useProjectSettings + ProjectSettingsIllustration | preserved (no frontend change) |
| pnpm tsc --noEmit | 0 new errors (48 pre-existing baseline unchanged) |

## 8 atomic commits on master

1. `d84d2dbd` docs(phase-105): design spec
2. `b0b99ee0` docs(phase-105): implementation plan — 9 atomic commits
3. `8392ce8c` refactor(phase-105): relocate _resolve_threshold -> notifications.resolve_threshold
4. `a89b04e8` feat(phase-105): cleanup_route failure + success tracking
5. `d7e7b8f8` test(phase-105): T1-T6 cleanup_route failure path tests
6. `a2b7454c` test(phase-105): T7-T9 counter isolation + helper relocation + back-compat
7. `5a8e7299` test(phase-105): G1-G6 regression guards
8. (this commit) docs(phase-105): CLAUDE.md v60.2 → v60.3 + I095 EXTENDED + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync

## Lessons (6 from spec + 1 new discovered)

1. **Tuple-keyed counter isolation** — independent failure windows per event type. Phase 105 inherits from Phase 104 invariant. (T7 + G5 verify.)
2. **Pydantic `mode="before"` for type union widening** — N/A this phase (Phase 104).
3. **Strict partial-dict semantics** — N/A this phase.
4. **`_resolve_threshold` defensive fallback** — Phase 105 relocated with same defensive fallback (bool → INFINITY, dict missing key → INFINITY). (T8 + G3 verify.)
5. **`_normalize_int` failure-path defaults** — N/A this phase.
6. **I095 EXTENDED via docstring preserves YAGNI** — Phase 105 EXTENDS again (3rd extension of same invariant name). (G3 verifies pipeline back-compat re-export.)
7. **NEW (Phase 105)**: `cleanup_route` uses `from ... import X` for `project_root_for` and `lru_cleanup` (local bindings). Patching the source module attribute does NOT affect cleanup_route's local binding — tests must patch `cleanup_route.X` directly. Verified empirically: `_project_helpers.project_root_for` patched vs `cleanup_route.project_root_for` patched. (T1, T2, T3, T5, T6 all use this pattern.)

## Cluster cumulative

- Phase 90-105 = **16 phases** / 1 NEW package (lingwen-illustrations) + 5 carryover closures + 7 REQ-002 v2 sub-projects delivered + **3 Phase 102+ extensions**:
  - Phase 103: Per-Chapter default_models Overrides (first)
  - Phase 104: notify_threshold per event_type (second)
  - Phase 105: Cleanup Route Failure Tracking (third, this phase)

## Future work (per BACKLOG)

- `deletion` event_type tracking — when DELETE endpoint added (currently no DELETE endpoint exists)
- Telemetry-driven chain reorder — gated on Phase 102 failure tracker data accumulation
- ARCHDEBT-REAL continuation — if requested (Phase 88 physically complete; only if scope expands)
- cleanup_route `deletion` event_type tracking — Phase 106 candidate (when DELETE endpoint exists)

## References

- Spec: `docs/superpowers/specs/2026-09-21-phase-105-cleanup-route-failure-tracking-design.md`
- Plan: `docs/superpowers/plans/2026-09-21-phase-105-cleanup-route-failure-tracking.md`
- Phase 102 handoff: `docs/superpowers/handoffs/2026-09-20-phase-102-settings-persistence-extension-handoff.md`
- Phase 104 handoff: `docs/superpowers/handoffs/2026-09-21-phase-104-notify-threshold-per-event-type-handoff.md`
- `.lingwen/architecture.yml` I095 (with Phase 105 scope extension)
- `CLAUDE.md` v60.3 + I095 row updated