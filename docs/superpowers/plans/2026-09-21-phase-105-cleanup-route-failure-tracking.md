# Phase 105 — Cleanup Route Failure Tracking — Implementation Plan

> **Date**: 2026-09-21
> **Spec**: `docs/superpowers/specs/2026-09-21-phase-105-cleanup-route-failure-tracking-design.md`
> **Phase**: v60.2 → v60.3
> **Cluster**: Phase 102+ extension #3
> **Workflow**: Solo repo, no PR, direct commits on master

## Overview

This plan executes Phase 105 in 9 atomic commits. Each commit is independently buildable and testable. No commit depends on uncommitted state.

## Commit-by-commit breakdown

### Commit 1: spec

**File**: `docs/superpowers/specs/2026-09-21-phase-105-cleanup-route-failure-tracking-design.md`

Write the design spec covering helper relocation rationale, cleanup_route behavior change, counter isolation, test matrix, regression guards, validation gates.

### Commit 2: plan

**File**: `docs/superpowers/plans/2026-09-21-phase-105-cleanup-route-failure-tracking.md`

This file.

### Commit 3: refactor — relocate `_resolve_threshold` to notifications

**Files**:
- `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` — add `resolve_threshold()` function (move from pipeline.py, remove INFINITY_THRESHOLD duplicate)
- `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` — replace local `_resolve_threshold` with `from lingwen_illustrations.notifications import resolve_threshold as _resolve_threshold`; remove local `INFINITY_THRESHOLD = math.inf`

**Validation**:
- ruff clean on both files
- pytest `packages/lingwen-illustrations/tests/` all preserved (pipeline callers unchanged)
- Phase 102/103/104 guards preserved (no behavior change)

**Risk mitigation**:
- Back-compat re-export via `from ... import ... as _resolve_threshold` preserves all local call sites
- `__all__` in notifications.py adds `"resolve_threshold"` (additive, no removal)

### Commit 4: feat — cleanup_route: `_load_cleanup_settings` + record_failure on LoadError

**Files**:
- `apps/studio_api/routes/cleanup_route.py` — add `_load_cleanup_settings(root)` helper (mirrors `_load_max_assets` pattern with `notify_threshold` key extraction); modify `cleanup_illustrations` to (1) load settings, (2) resolve threshold, (3) record_failure on LoadError

**Validation**:
- ruff clean on file
- pytest `apps/studio_api/tests/test_cleanup_route.py` preserved
- Existing cleanup_route tests unchanged (no new tests yet — covered in Commit 6)

**Risk mitigation**:
- `_load_cleanup_settings` returns `{}` on missing file (defensive)
- `record_failure` called BEFORE `raise HTTPException` to ensure counter increment before exception propagation

### Commit 5: feat — cleanup_route: record_failure on StoreError + record_success on success

**Files**:
- `apps/studio_api/routes/cleanup_route.py` — wrap `lru_cleanup` call in `try/except/else`; record_failure in `except StoreError` branch; record_success in `else` branch

**Validation**:
- ruff clean on file
- pytest `apps/studio_api/tests/test_cleanup_route.py` preserved
- Existing cleanup_route tests unchanged

**Risk mitigation**:
- `else` branch (record_success) only runs after successful lru_cleanup — never on exception path
- Validation 422 path (chapter_num missing) NOT in try/except — no double-counting

### Commit 6: test — 6 NEW pytest tests (T1-T6 failure paths + threshold trigger)

**File**: `apps/studio_api/tests/test_cleanup_route_failure_tracking.py` (NEW)

Tests:
- T1: `LoadError` on project_root_for → `record_failure` called with `event_type="cleanup"` (monkeypatch `project_root_for` to raise; assert via mock on notifications.record_failure)
- T2: `StoreError` on lru_cleanup → `record_failure` called with `event_type="cleanup"`
- T3: Successful lru_cleanup (≥1 deleted) → `record_success` called
- T4: 422 validation (chapter_num missing) → NO `record_failure` called
- T5: dry_run path → NO `record_failure` or `record_success` called
- T6: Threshold crossing after N consecutive StoreErrors → 1 severity=warning notification emitted

**Validation**:
- pytest `apps/studio_api/tests/test_cleanup_route_failure_tracking.py` → 6/6 NEW tests PASS

**Risk mitigation**:
- Use `monkeypatch.setattr(notifications, "record_failure", MagicMock())` to capture calls
- Use `monkeypatch.setattr(project_root_for, ...)` for failure injection
- Use unique slug per test (`phase105-test-N`) to avoid counter bleed

### Commit 7: test — 3 NEW tests (T7 counter isolation + T8 helper relocation + T9 back-compat)

**Files**:
- `packages/lingwen-illustrations/tests/test_phase105_cleanup_failure_isolation.py` (NEW)
  - T7: 3 cleanup failures don't increment generation counter
  - T8: `notifications.resolve_threshold` exists and returns expected values
  - T9: `pipeline._resolve_threshold` still callable (back-compat re-export)

**Validation**:
- pytest `packages/lingwen-illustrations/tests/test_phase105_cleanup_failure_isolation.py` → 3/3 NEW tests PASS

### Commit 8: test — 6 NEW regression guards G1-G6

**File**: `tests/test_phase105_cleanup_route_failure_tracking.py` (NEW)

Guards:
- G1: cleanup_route imports notifications AND calls `record_failure(event_type="cleanup")` ≥ 2 times (regex search source file)
- G2: cleanup_route calls `notifications.record_success` with `event_type="cleanup"` ≥ 1 time
- G3: `notifications.resolve_threshold` exists AND `pipeline._resolve_threshold` is callable (sentinel same)
- G4: Pipeline generate/regenerate use `_resolve_threshold` (no caller regression)
- G5: 3 record_failure(event_type="cleanup") calls leave generation counter = 0 (counter isolation)
- G6: `_load_cleanup_settings` reads `.lingwen/illustration_settings.yaml` with permissive fallback

**Validation**:
- pytest `tests/test_phase105_cleanup_route_failure_tracking.py` → 6/6 guards PASS

**N.14 pattern** (lesson 22nd recurrence):
- G1 uses regex anchored search for `record_failure.*event_type="cleanup"` — strip docstrings per N.14 v21
- G3 uses importable sentinel comparison (not raw text grep)

### Commit 9: docs — CLAUDE.md + I095 + handoff + BACKLOG + CURRENT_STATUS + MEMORY

**Files**:
- `CLAUDE.md` — version line v60.2 → v60.3 (add Phase 105 entry, demote Phase 104 to Previous); update I095 invariant scope (per Phase 104 EXTENDED pattern)
- `docs/superpowers/handoffs/2026-09-21-phase-105-cleanup-route-failure-tracking-handoff.md` (NEW)
- `collaboration/BACKLOG.md` — add Phase 105 row + 最近变更 entry
- `collaboration/CURRENT_STATUS.md` — sync v60.3 (new row + git main SHA + future work update)
- `~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` — add v60.3 entry + topic file pointer

**Validation**:
- ruff clean on introduced files
- All previous phase guards preserved (Phase 102/103/104)

## Validation gates summary

| Gate | Expected |
|------|----------|
| `pytest packages/lingwen-illustrations/tests/` | all preserved + 3 NEW PASS (T7-T9) |
| `pytest apps/studio_api/tests/test_cleanup_route.py` | preserved |
| `pytest apps/studio_api/tests/test_cleanup_route_failure_tracking.py` | 6/6 NEW PASS (T1-T6) |
| `pytest tests/test_phase105_cleanup_route_failure_tracking.py` | 6/6 NEW guards PASS (G1-G6) |
| Phase 102 + 103 + 104 guards preserved | 30+ tests PASS |
| `ruff check` on introduced files | clean |
| vitest useProjectSettings + ProjectSettingsIllustration | preserved (no frontend change) |
| pnpm tsc --noEmit | 0 new errors (48 pre-existing baseline unchanged) |

## Risk assessment (revisit)

| Risk | Mitigation in plan |
|------|---------------------|
| Counter leak on success path (stuck elevated) | record_success in `else` branch of lru_cleanup try/except (Commit 5) |
| Double-count on LoadError + StoreError same request | LoadError raises BEFORE lru_cleanup runs (Commit 4) |
| Validation 422 pollutes counter | Explicit no-record in validation path (T4 verifies) |
| Pipeline caller regression on helper rename | Back-compat re-export via `import as _resolve_threshold` (Commit 3) |
| Test counter bleed across tests | Unique slug per test (`phase105-test-N`) — Commit 6 + 8 |
| Settings file missing breaks cleanup | `_load_cleanup_settings` returns `{}` defensively (Commit 4) |

## Commit message format

Following repo convention from Phase 104:
```
feat(phase-105): <description>
fixup(phase-105): <description>
docs(phase-105): <description>
test(phase-105): <description>
refactor(phase-105): <description>
```

## Rollback strategy

If Commit 3 (refactor) breaks callers: revert via `git revert <sha>` — pipeline callers unchanged by design.

If Commit 4-5 (route changes) break behavior: revert to Phase 104 state where cleanup_route has no failure tracking. Settings are additive; deleting the new helpers preserves Phase 104 baseline.

If Commit 6-8 (tests) are flaky: tests use unique slugs + monkeypatch isolation — should not interfere with other test suites.

## Estimated timeline

- Spec + plan: ~15 min (already written)
- Commit 3 (refactor): ~5 min
- Commit 4-5 (cleanup_route): ~10 min
- Commit 6 (pytest tests): ~15 min
- Commit 7 (counter isolation tests): ~10 min
- Commit 8 (regression guards): ~15 min
- Commit 9 (docs sync): ~15 min

Total: ~90 min for all 9 commits.

## Lessons applied from prior phases

1. **N.14 v21**: regression guard regex strips docstrings before search (G1)
2. **N.14 v22**: parsed-value check not raw text grep (G3 back-compat)
3. **Phase 100 pattern**: back-compat re-export via `import as _check`
4. **Phase 104 pattern**: defensive fallback for non-validated scalars (`resolve_threshold` returns INFINITY for bool/non-int)
5. **Phase 104 pattern**: counter isolation via tuple key (`(slug, event_type)`)
6. **Phase 102 pattern**: `_warning_emitted` flag prevents spam (already in notifications.py)

## Open questions for confirmation

None — scope is well-defined by spec. Awaiting user approval to proceed with Commit 3 onwards.