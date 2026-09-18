# Phase 99 Notification Center — Handoff

> **Date**: 2026-09-18
> **Phase**: v56.2 → v57.0
> **Cluster cumulative**: Phase 90-99 = 10 phases / 1 NEW package + 5 carryover closures + 4 REQ-002 v2 sub-projects delivered

## Summary

Phase 99 ships REQ-002 v2 #4 — a real-time notification center for illustration events (generation / regeneration / cleanup). Users now have visibility into background state changes triggered by Phase 98 ProjectSettings (auto_generate / max_assets / confirm_before_generate).

Backend: in-process async SSE publisher mirrors Phase 24 `studio_batch_streamer` pattern. Pipeline + cleanup_route double-write to `audit_log.record_event` (I090 durability) + `notifications.publish` (I091 fan-out) with the same ULID — single source of truth for SSE catch-up via `since_id`.

Frontend: header bell + dropdown + dedicated /notifications page with event-type tabs. Active-project-scoped SSE subscription, localStorage read-state, Pinia store with rolling 200-event buffer.

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest | lingwen-illustrations + studio_api all GREEN (preserved baselines + new tests) |
| Phase 99 guards | 15/15 (G1-G12 + G13 e2e) |
| Frontend vitest | all notification-center suites GREEN (17 tests across 7 files) |
| pnpm tsc | 0 new errors (pre-existing FactionGraphCanvas + creationModeHint untouched) |
| ruff | clean on introduced |
| I090 + I091 invariants | recorded in `.lingwen/architecture.yml` + CLAUDE.md |

## Sub-projects delivered

- `notifications.py` module (9 unit tests)
- `audit_log.read_history()` + `record_event(id=)` kwarg (5 compat tests)
- pipeline double-write: generate + regenerate (4 integration tests)
- cleanup_route double-write: 1 event per deleted asset + dry_run synthetic event
- `routes/notifications.py`: SSE GET + REST GET history (6 route tests)
- `composables/useNotificationStream.js` EventSource wrapper (3 tests)
- `stores/useNotificationStore.js` Pinia store (3 tests)
- `api/notifications.ts` typed wrappers
- `NotificationBell` + `NotificationDropdown` + `NotificationListItem` (8 tests)
- `NotificationsPage` with event-type tabs (2 tests)
- `App.vue` header mount + `/notifications` route + sidebar nav + `IconSidebarNotifications.vue`
- 15 regression guards (G1-G12 + G13 e2e + G2/G2b/G2c split)

## Lessons learned

1. **ULID > UUID for SSE + cursor** — lexicographic time-sort gives free pagination cursor. Phase 98 audit_log was pre-ULID; Phase 99 retrofit is opt-in (`id` kwarg default None).
2. **Double-write is dual invariant** — I090 (record_event) + I091 (publish). Test must verify SAME id flows to both — separate id generation on either side is a silent data drift bug.
3. **In-memory SSE queue + JSONL durability** is a known trade-off: Phase 24 established the pattern. Restart loses live events but REST history fills the gap via `since_id` cursor.
4. **Frontend localStorage read-state** is opt-in opt-out: don't push users to read-state. Bell badge is informational; clearing it is a 1-click action.
5. **Sidebar icons + nav must be added at the same commit** as the page — orphan icons and orphan pages both ship visual debt (Phase v40.0 lesson 3 reaffirmed).
6. **SSE handler needs `asyncio.wait_for` + heartbeat** — bare `await queue.get()` blocks forever with no cancellation point. Added `wait_for(timeout=1.0)` with periodic `: ping` so client disconnects propagate via `await send()` OSError. Mirrors Phase 24 pattern.
7. **python-ulid 3.x API differs from 2.x** — `ulid.new()` → `ulid.ULID()`. Minor compatibility issue caught at implementation time.

## Carryover status

- REQ-002 v2: **4 of 7 sub-projects delivered** (image provider adapters + reference image i2i + ProjectSettings extension + LRU archive + **notification center**)
- Remaining: multi-model per provider / atomic provider fallback / v2 settings persistence extension
- REQ-004 团队协作: still P4 backlog

## Cluster cumulative

Phase 90-99 = **10 phases / 1 NEW product feature package + 5 carryover closures + 4 REQ-002 v2 sub-projects delivered**.
