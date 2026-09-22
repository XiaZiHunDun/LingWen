# Phase 109 — NotificationsPage Delete Dropdown — Handoff

> **Date**: 2026-09-22
> **Phase**: 109 (seventh Phase 102+ extension)
> **Status**: ✅ COMPLETE (v60.6 → v60.7, 7 atomic commits on master)

## Summary

Frontend-only orthogonal UX: added per-row delete button to `NotificationListItem` so users can delete illustration assets directly from `NotificationDropdown` and `NotificationsPage` without navigating to `IllustrationGallery`.

## Architecture decisions

- **Path A — Store mutation**: `useNotificationStore.deleteAssetFromNotification(item)` action marks local `_deleted=true` on the history item. Underscore prefix signals "local-only field, not in backend dataclass, not persisted".
- **Option α — 404 also marks deleted**: store action returns `{status: 'deleted' | 'not_found' | 'error' | 'noop' | 'skipped'}`; on 404 it still marks `_deleted=true` (UX consistency — user clicked delete, expect deletion semantics). 500 leaves history intact for retry.
- **Reuse Phase 106 backend endpoint**: zero backend changes. New `api/illustrations.ts:deleteAsset` typed wrapper calls Phase 106 DELETE route verbatim.
- **Lazy `useMessage` pattern (Phase 107)**: `useDeleteFromNotificationToast` mirrors `useBulkDeleteToast` so tests don't need `<n-message-provider>`.
- **Touch detection via `matchMedia('(hover: none)')`**: single component covers desktop (hover-revealed) and mobile (always-visible).

## Validation gates (final)

- `pnpm vitest run` — 14 NEW + ~50 preserved = ~64 GREEN
- `pnpm tsc --noEmit` — 0 new errors (48 baseline unchanged)
- `pnpm eslint .` — 0 new errors
- `pnpm exec knip` — 0 new dead exports
- `pytest tests/test_phase109_notifications_delete.py` — 6/6 NEW G1-G6 GREEN
- Backend pytest — zero changes; Phase 106/107/108 preserved

## Invariants

- **I090**: NOT extended. Phase 106 delete_asset route still emits record_event.
- **I091**: NOT extended. Same backend endpoint preserves shared ULID double-write.
- **I095**: NOT extended. Counter state machine unchanged.

## Files changed

| Type | Path |
|------|------|
| Modify | `apps/dashboard/src/api/illustrations.ts` |
| Modify | `apps/dashboard/src/stores/useNotificationStore.js` |
| Modify | `apps/dashboard/src/stores/useNotificationStore.spec.js` |
| Modify | `apps/dashboard/src/components/notifications/NotificationListItem.vue` |
| Modify | `apps/dashboard/src/components/notifications/NotificationListItem.spec.js` |
| Create | `apps/dashboard/src/composables/useDeleteFromNotificationToast.ts` |
| Create | `apps/dashboard/src/composables/useDeleteFromNotificationToast.spec.ts` |
| Create | `tests/test_phase109_notifications_delete.py` |
| Modify | `CLAUDE.md` |
| Modify | `collaboration/CURRENT_STATUS.md` |
| Modify | `collaboration/BACKLOG.md` |
| Modify | `MEMORY.md` |

## Atomic commits (7 total)

1. `docs(phase-109): NotificationsPage delete dropdown design spec` (`cf8d0f12`)
2. `docs(phase-109): implementation plan` (`6b3c1aaa`)
3. `feat(phase-109): deleteAssetFromNotification store action + 4 tests` (`2bd692cf`)
4. `feat(phase-109): useDeleteFromNotificationToast composable + 3 tests` (`1e5b5ca6`)
5. `feat(phase-109): NotificationListItem NPopconfirm delete + 8 tests` (`563628b0`)
6. `test(phase-109): 6 frontend-static regression guards G1-G6` (`c81a6bc7`)
7. `docs(phase-109): CLAUDE.md v60.6 → v60.7 + sync + handoff` (this commit)

## Lessons

1. **Option α keeps UX consistent** — 404 also marks deleted (user clicked delete, expect deletion semantics).
2. **`_deleted` underscore prefix convention** signals local-only state, never crosses backend boundary.
3. **Lazy `useMessage` pattern** (Phase 107) lets components mount outside `<n-message-provider>` for testing.
4. **Touch detection via `matchMedia('(hover: none)')`** covers desktop and mobile in one component.
5. **Reuse `{deleted | not_found | error | noop | skipped}` contract** — caller dispatches toast based on status, store owns state mutation.

## Future work (deferred)

- Phase 109+ bulk delete from NotificationsPage (multi-select + bulk button).
- Phase 109+ persist `_deleted` across refresh (refresh re-fetches from audit_log; transient UX acceptable).
- Phase 109+ optimistic `useIllustrationStore.assets[]` sync (user has navigated away from gallery; next gallery load is source of truth).

## References

- **Spec**: `docs/superpowers/specs/2026-09-22-phase-109-notifications-page-delete-design.md`
- **Plan**: `docs/superpowers/plans/2026-09-22-phase-109-notifications-page-delete.md`
- **Phase 106 handoff**: `docs/superpowers/handoffs/2026-09-21-phase-106-delete-endpoint-failure-tracking-handoff.md`
- **Phase 107 handoff**: `docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md`
- **Phase 108 handoff**: `docs/superpowers/handoffs/2026-09-22-phase-108-bulk-regenerate-handoff.md`
- **Architecture**: `.lingwen/architecture.yml` (I090/I091/I095)