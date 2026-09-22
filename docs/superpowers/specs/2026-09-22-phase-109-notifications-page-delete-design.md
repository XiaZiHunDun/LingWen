# Phase 109 — NotificationsPage Delete Dropdown

> **Status**: design draft
> **Phase**: 109 (seventh Phase 102+ extension after Phase 103 default_models + Phase 104 notify_threshold per event_type + Phase 105 cleanup_route failure tracking + Phase 106 delete_asset failure tracking + Phase 107 bulk_delete_assets + Phase 108 bulk_regenerate_assets)
> **Date**: 2026-09-22
> **Scope**: orthogonal UX — single delete from NotificationsPage dropdown / full page
> **Cluster**: Phase 90-109 = 20 phases / 1 NEW package + 5 carryover closures + 7 REQ-002 v2 sub-projects + 7 Phase 102+ extensions

---

## 1. Motivation

Currently the only surface for deleting illustration assets is `IllustrationGallery.vue` (Phase 90 + Phase 106/107/108 single + bulk delete). When users see a `generation` or `regeneration` event in `NotificationDropdown` / `NotificationsPage`, they must navigate to the gallery to delete it. This is friction for the common "I generated this, don't want it" flow.

This phase adds a per-row delete button to `NotificationListItem` so users can delete the underlying asset directly from the notification feed. **Single delete only** — bulk delete remains a gallery concern.

---

## 2. Scope

### 2.1 In scope

- `generation` / `regeneration` notifications: render hover-revealed ✕ delete button (desktop) / always-visible (touch), wrapped in `<NPopconfirm>` (Naive UI, mirrors Phase 106 IllustrationGallery pattern).
- Post-delete: keep notification item in `store.history`, mark local `_deleted = true` field, render `资产已删除` tag.
- `useNotificationStore.deleteAssetFromNotification(item)` action (path A — store mutation).
- `useDeleteFromNotificationToast` composable (lazy `useMessage`, mirrors `useBulkDeleteToast` Phase 107 pattern).
- Frontend vitest: 8 `NotificationListItem` + 4 `useNotificationStore` + 3 toast + 6 regression guards.
- I090/I091/I095: not extended — delete still flows through Phase 106/107 routes.

### 2.2 Out of scope (explicit non-goals)

- **Bulk delete from notifications page** — multi-select + bulk button deferred. `IllustrationGallery` is the canonical bulk surface.
- **Delete from `cleanup` / `deletion` / `warning` notifications** — `asset_id` is null for cleanup/warning; deletion notifications reference already-gone assets. No-op UX, button hidden.
- **Persist `_deleted` across page refresh** — local-only field. Refresh re-fetches from `audit_log`; subsequent `generation` events for the same asset (if regenerated) appear naturally.
- **Refresh `useIllustrationStore.assets[]` after delete** — user has navigated away from gallery; next gallery visit re-loads via `loadAssets`. No optimistic cross-store sync.
- **Backend changes** — Phase 106/107 routes are complete. This phase is frontend-only.

---

## 3. Module layout

| Type | Path | Purpose |
|------|------|---------|
| Modify | `apps/dashboard/src/stores/useNotificationStore.js` | + `deleteAssetFromNotification(item)` action |
| Modify | `apps/dashboard/src/components/notifications/NotificationListItem.vue` | + hover delete button + NPopconfirm + deleted state branch |
| Modify | `apps/dashboard/src/components/notifications/NotificationListItem.spec.js` | + 8 new vitest tests (T1-T8) |
| Modify | `apps/dashboard/src/stores/useNotificationStore.spec.js` | + 4 new vitest tests (T9-T12) |
| New | `apps/dashboard/src/composables/useDeleteFromNotificationToast.ts` | + 3-variant toast (success / not_found / error) — mirrors `useBulkDeleteToast.ts` |
| New | `apps/dashboard/src/composables/useDeleteFromNotificationToast.spec.ts` | + 3 vitest tests (T-success / T-not-found / T-error) |
| New | `tests/test_phase109_notifications_delete.py` | + 6 regression guards G1-G6 (frontend-static + store-level) |

**Backend**: zero changes. Phase 106 DELETE `/api/illustrations/{asset_id}?project_slug=...` is reused verbatim.

---

## 4. State management — Path A (store mutation)

### 4.1 `useNotificationStore.deleteAssetFromNotification(item)`

```js
async function deleteAssetFromNotification(item) {
  // Guard: eligibility (matches NotificationListItem canDelete predicate)
  if (!item || item._deleted) return { status: 'noop' }
  if (item.eventType !== 'generation' && item.eventType !== 'regeneration') {
    return { status: 'skipped' }
  }
  if (!item.asset_id || !item.project_slug) return { status: 'skipped' }

  function markDeleted(t) {
    const idx = history.value.findIndex((e) => e.id === t.id)
    if (idx !== -1) {
      history.value = [
        ...history.value.slice(0, idx),
        { ...history.value[idx], _deleted: true },
        ...history.value.slice(idx + 1),
      ]
    }
  }

  try {
    // Lazy import keeps store bundle small (matches Phase 107 bulkDeleteAssets pattern)
    const { deleteAsset } = await import('@/api/illustrations')
    await deleteAsset(item.project_slug, item.asset_id)
    markDeleted(item)
    return { status: 'deleted' }
  } catch (e) {
    // Option α: 404 also marks deleted (UX consistency — user clicked delete)
    if (isNotFoundError(e)) {
      markDeleted(item)
      return { status: 'not_found' }
    }
    return { status: 'error', error: e }
  }
}

function isNotFoundError(e) {
  // Phase 106 delete_asset raises FastAPI HTTPException(404, detail=...) on
  // both project LoadError and asset-not-found. The api wrapper throws Error
  // with status code in the message — match by HTTP status / message substring.
  const msg = String(e?.message ?? '')
  return msg.includes('404') || msg.toLowerCase().includes('not found')
}
```

### 4.2 `_deleted` field conventions

- **Underscore prefix** — signals "local-only field, not persisted to backend, not in `NotificationEvent` dataclass".
- **Not in `NotificationEvent` type** — TypeScript JSDoc-only annotation; backend dataclass untouched.
- **Not persisted** — page refresh re-fetches from `audit_log`; for a deleted asset no future event references it unless regenerated.
- **Not in `audit_log`** — only `record_event(slug, event="deletion", ...)` flows to audit_log (Phase 106 wiring). The `_deleted` flag is purely UI state.

### 4.3 Toast feedback (caller responsibility)

The store action does **not** show toast — caller decides. Recommended: wrap in `useDeleteFromNotificationToast`:

| API response | Toast variant | Message |
|---|---|---|
| 200 OK | `message.success` | 已删除资产 |
| 404 (not_found / LoadError) | `message.info` | 资产不存在或已被删除 |
| 500 (StoreError) | `message.error` | 删除失败 |
| network error | `message.error` | 网络错误 |

404 still marks `_deleted = true` (UX consistency — user clicked delete, expect deletion semantics).
500 does **not** mark `_deleted` (allow retry).

---

## 5. Component design — `NotificationListItem.vue`

### 5.1 Template (added action)

```vue
<template>
  <div
    class="notification-list-item"
    :class="{ 'is-deleted': item._deleted }"
    data-testid="notification-list-item"
  >
    <span class="icon">{{ icon }}</span>
    <div class="body">
      <div class="title">{{ title }}</div>
      <div class="meta">{{ meta }}</div>
      <div v-if="item._deleted" class="deleted-tag" data-testid="deleted-tag">
        资产已删除
      </div>
    </div>
    <NPopconfirm
      v-if="canDelete"
      :show="showConfirm"
      positive-text="确认删除"
      negative-text="取消"
      @positive-click="onConfirmDelete"
      @negative-click="showConfirm = false"
    >
      <template #trigger>
        <button
          class="delete-btn"
          :class="{ 'touch-visible': isTouch }"
          :aria-label="`删除资产 ${item.asset_id}`"
          data-testid="delete-btn"
          @click.stop="showConfirm = true"
        >
          ✕
        </button>
      </template>
      <span>确认删除此资产？</span>
    </NPopconfirm>
  </div>
</template>
```

### 5.2 Eligibility (`canDelete`)

```js
const canDelete = computed(() => {
  if (props.item._deleted) return false
  if (props.item.eventType !== 'generation' && props.item.eventType !== 'regeneration') return false
  return Boolean(props.item.asset_id && props.item.project_slug)
})
```

Mirrors the store action's guard so visual and behavior stay in sync.

### 5.3 Touch detection (CSS + JS)

```js
import { ref, onMounted } from 'vue'
const isTouch = ref(false)
onMounted(() => {
  isTouch.value = window.matchMedia('(hover: none)').matches
})
```

### 5.4 CSS — hover behavior + deleted state

```css
.notification-list-item { position: relative; }
.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.15s;
}
.notification-list-item:hover .delete-btn,
.delete-btn:focus-visible,
.delete-btn.touch-visible { opacity: 1; }
.is-deleted { opacity: 0.55; }
.is-deleted .delete-btn { display: none; }
.deleted-tag {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  font-style: italic;
}
```

### 5.5 Click handler

```js
async function onConfirmDelete() {
  showConfirm.value = false
  const { status } = await store.deleteAssetFromNotification(props.item)
  if (status === 'deleted') {
    toast.success('已删除资产')
    emit('asset-deleted', props.item.id, props.item.asset_id)
  } else if (status === 'not_found') {
    toast.info('资产不存在或已被删除')
    emit('asset-deleted', props.item.id, props.item.asset_id)
  } else if (status === 'error') {
    toast.error('删除失败')
  }
  // status === 'noop' | 'skipped' → no toast, no emit (e.g. re-click on already-deleted row)
}
```

---

## 6. Delete flow + error handling

### 6.1 End-to-end sequence (Option α — store handles 404 marking)

```
1. User hovers notification row (desktop) OR row always shows ✕ (touch)
2. Click ✕ → showConfirm = true → NPopconfirm overlay
3. Click "确认删除"
   → showConfirm = false
   → store.deleteAssetFromNotification(item)  // Option α implementation (see §6.2)
     → guards: !item || item._deleted → {status: 'noop'}
     → guards: wrong eventType or missing asset_id/project_slug → {status: 'skipped'}
     → await deleteAsset(slug, asset_id)  // Phase 106 API
       → 200 OK
         → history[idx] = {...item, _deleted: true}
         → return {status: 'deleted'}
       → 404 (asset_id not found OR project LoadError)
         → isNotFound(e) === true
         → history[idx] = {...item, _deleted: true}  (UX consistency — Option α)
         → return {status: 'not_found'}
       → 500 (StoreError) or network error
         → return {status: 'error', error: e}
         → history unchanged
   → caller dispatches toast based on status
   → emit('asset-deleted', item.id, item.asset_id) on deleted + not_found
```

### 6.2 404 mark-deleted resolution

There are two reasonable placements for the 404-also-marks-deleted logic:

**Option α**: Store action marks `_deleted = true` on **both** 200 and 404 (exception caught internally, item always replaced).

```js
async function deleteAssetFromNotification(item) {
  if (!item || item._deleted) return { status: 'noop' }
  if (item.eventType !== 'generation' && item.eventType !== 'regeneration') return { status: 'skipped' }
  if (!item.asset_id || !item.project_slug) return { status: 'skipped' }

  try {
    const { deleteAsset } = await import('@/api/illustrations')
    await deleteAsset(item.project_slug, item.asset_id)
    markDeleted(item)
    return { status: 'deleted' }
  } catch (e) {
    if (isNotFound(e)) {
      markDeleted(item)  // UX consistency
      return { status: 'not_found' }
    }
    return { status: 'error', error: e }
  }

  function markDeleted(t) {
    const idx = history.value.findIndex((e) => e.id === t.id)
    if (idx !== -1) {
      history.value = [
        ...history.value.slice(0, idx),
        { ...history.value[idx], _deleted: true },
        ...history.value.slice(idx + 1),
      ]
    }
  }
}
```

**Option β**: Caller handles 404 explicitly.

**Recommendation**: Option α — keeps UX logic in store, caller only does toast dispatch. Mirrors Phase 107 `bulkDeleteAssets` where partial failures accumulate as a `{status: "not_found"}` shape.

### 6.3 Invariant preservation

- **I090** (audit_log.record_event): not extended — `record_event(slug, event="deletion", ...)` already called by Phase 106 delete_asset route on 200. NotificationPage path routes through the SAME backend endpoint.
- **I091** (notifications.publish + record_event shared ULID): not extended — same backend endpoint.
- **I095** (failure tracker per `(slug, event_type)`): not extended — counter state machine unchanged.
- **Phase 106 wiring intact**: G7 regression guard will verify `delete_asset` route still calls `_delete_asset_inner(mode="single")`.

### 6.4 Cross-store sync

`useIllustrationStore.assets[]` is **not** synced by this phase. Rationale:
- User has navigated away from `IllustrationGallery` (they're on `NotificationsPage` / dropdown).
- Next gallery visit re-loads via `loadAssets`.
- Optimistic cross-store sync would require emitting through the `asset-deleted` event AND the gallery subscribing — adds coupling for a transient state that resolves on next page load.

If future UX requires optimistic sync, can be added by `NotificationDropdown` listening to `asset-deleted` and calling `useIllustrationStore.removeAssetLocal(id)`. YAGNI for now.

---

## 7. Testing strategy

### 7.1 Frontend vitest — 14 new tests

**`NotificationListItem.spec.js`** — 8 tests:
- T1: `generation` event renders ✕ button (desktop)
- T2: `regeneration` event renders ✕ button
- T3: `cleanup` event does NOT render ✕ button
- T4: `deletion` event does NOT render ✕ button
- T5: `warning` event (asset_id=null) does NOT render ✕ button
- T6: `item._deleted=true` hides ✕ + renders 「资产已删除」tag
- T7: NPopconfirm three-state (show / positive / negative). Negative click does NOT call store.
- T8: positive click calls `store.deleteAssetFromNotification` + emits `asset-deleted`.

**`useNotificationStore.spec.js`** — 4 tests:
- T9: happy path 200 → `history[idx]._deleted === true`.
- T10: `generation`/`regeneration` allowed; other eventTypes (`cleanup`/`deletion`/`warning`) skip without API call.
- T11: 404 → `_deleted === true` (Option α).
- T12: 500 → `_deleted === false` (preserves retry).

**`useDeleteFromNotificationToast.spec.ts`** — 3 tests:
- T-success: `{status: 'deleted'}` → `message.success('已删除资产')`.
- T-not-found: `{status: 'not_found'}` → `message.info('资产不存在或已被删除')`.
- T-error: `{status: 'error'}` → `message.error('删除失败')`.

### 7.2 Frontend regression guards — 6 guards

`tests/test_phase109_notifications_delete.py` (Python-side static source scan — mirrors Phase 107 guard pattern):
- G1: `NotificationListItem.vue` imports `NPopconfirm` from naive-ui.
- G2: `useNotificationStore.js` exports `deleteAssetFromNotification`.
- G3: `canDelete` computed in `NotificationListItem.vue` source contains the 4-condition check.
- G4: `_deleted` field mention exists in `useNotificationStore.js` source.
- G5: `useDeleteFromNotificationToast.ts` exports default factory.
- G6: backend `routes/illustrations.py` `delete_asset` route signature unchanged (Phase 106 contract preserved).

### 7.3 Backend — zero new tests

Phase 106 `test_illustrations_api.py` 6/6 + Phase 107 `test_bulk_delete_api.py` 10/10 + `test_phase106_deletion_isolation.py` 6/6 all preserved.

### 7.4 Validation gates

- `pnpm vitest run` — 14 new tests GREEN + Phase 99/106/107/108 frontend tests preserved GREEN
- `pnpm tsc --noEmit` — 0 new errors (48 pre-existing baseline unchanged)
- `pnpm eslint .` — 0 new errors
- `pnpm exec knip` — 0 new dead exports
- `ruff check <changed_files>` — clean

---

## 8. Architecture invariants

| ID | Change |
|----|--------|
| I090 | NOT extended — `record_event` already wired in Phase 106 `delete_asset` route. This phase reuses that route verbatim. |
| I091 | NOT extended — same backend endpoint preserves shared ULID double-write. |
| I095 | NOT extended — failure counter state machine unchanged. |

`_deleted` field is frontend-local only; not exposed in backend `audit_log` schema; not in `NotificationEvent` dataclass.

---

## 9. Out of scope (deferred)

| Item | Reason | Phase candidate |
|------|--------|-----------------|
| Bulk delete from NotificationsPage | `IllustrationGallery` is canonical bulk surface; multi-select adds ~5 file changes | Phase 111+ |
| Persist `_deleted` across refresh | Refresh re-fetches from `audit_log`; transient UX acceptable | Phase 112+ |
| Optimistic `useIllustrationStore.assets[]` sync | User has navigated away; next gallery load is source of truth | Phase 112+ |
| Delete from `cleanup` / `deletion` / `warning` notifications | `asset_id` is null for cleanup/warning; deletion notifications reference already-gone assets (idempotent UX) | N/A |

---

## 10. Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| NPopconfirm Esc-dismissal not in naive-ui default (Phase 106 lesson) | known | F-test removed (Phase 106 lesson) — NPopconfirm cancel path is purely frontend (button click / click outside). Document in T7. |
| `lazy import` in store breaks Pinia SSR / hydration | very low | Project is Vite SPA, no SSR. Lazy import pattern already used by Phase 107 `bulkDeleteAssets`. |
| `_deleted` field name collisions with backend dataclass | low | Underscore prefix convention is unique to frontend; backend dataclass has no such field. Verified by G4 + G6. |
| `asset_id` from cross-project notification (user switches project mid-session) | medium | `_deleted` flag is local-only; backend DELETE uses `item.project_slug` directly; if user switched, the new project may not have that asset_id → 404 → marked deleted (Option α). Acceptable UX. |

---

## 11. Atomic commit sequence (planned)

Per 2026-09-15 simplified workflow (direct commits on master):

1. `spec` — design doc (this file)
2. `plan` — implementation plan (output of writing-plans skill)
3. `feat(store)` — `useNotificationStore.deleteAssetFromNotification` action + 4 vitest tests (T9-T12)
4. `feat(toast)` — `useDeleteFromNotificationToast` composable + 3 vitest tests
5. `feat(component)` — `NotificationListItem.vue` NPopconfirm + hover + touch + 8 vitest tests (T1-T8)
6. `feat(guards)` — 6 regression guards G1-G6
7. `docs` — CLAUDE.md v60.6 → v60.7 + CURRENT_STATUS + BACKLOG + MEMORY sync

Total: 7 atomic commits. Mirrors Phase 107/108 commit cadence.

---

## 12. Lessons learned from predecessors

| Phase | Lesson | Applied here |
|-------|--------|--------------|
| Phase 106 | NPopconfirm cancel purely frontend (no emit, no counter touched) | T7 negative-click test |
| Phase 106 | 404 = no-op success via `record_success` (defensive counter reset) | §6.2 Option α: 404 also marks `_deleted` for UX consistency |
| Phase 107 | Lazy import for store actions (small bundle) | §4.1 |
| Phase 107 | `meta_by_id` pre-resolve to avoid N×M filesystem reads | N/A — this is frontend, no filesystem |
| Phase 107 | `dict.fromkeys` dedupe preserving order | N/A |
| Phase 107 | Sequential for-loop (preserves audit_log arrival order) | N/A — frontend |
| Phase 107 | Vue 3 Set reactivity requires `selectionTick.value++` | N/A — we use immutable replace, not Set |
| Phase 107 | NPopconfirm wrapping mirrors single-delete pattern | §5.1 (mirror exactly) |
| Phase 108 | Pipeline owns emit (record_event + publish) — helper is counter-only shim | N/A — no helper; store action delegates to existing API |
| Phase 108 | Option A prevents double-emit | N/A — frontend, no emit site added |
| Phase 108 | Lazy useMessage enables test isolation without n-message-provider | §7.1 useDeleteFromNotificationToast |

---

## 13. Validation summary

| Gate | Target |
|------|--------|
| pnpm vitest | 14 new + ~50 preserved = ~64 GREEN |
| pnpm tsc | 0 new errors (48 baseline unchanged) |
| pnpm eslint | 0 new errors |
| pnpm knip | 0 new dead exports |
| ruff check (changed files) | clean |
| Backend pytest | 0 changes — Phase 106/107 preserved |

---

## 14. References

- **Phase 106** handoff: `docs/superpowers/handoffs/2026-09-21-phase-106-delete-endpoint-failure-tracking-handoff.md`
- **Phase 107** handoff: `docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md`
- **Phase 108** handoff: `docs/superpowers/handoffs/2026-09-22-phase-108-bulk-regenerate-handoff.md`
- **Phase 99** handoff: `docs/superpowers/handoffs/2026-09-18-phase-99-notification-center-handoff.md`
- **Architecture invariants**: `.lingwen/architecture.yml` (I090/I091/I095)
- **BACKLOG**: `collaboration/BACKLOG.md`