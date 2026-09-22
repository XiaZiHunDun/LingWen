# Phase 109 — NotificationsPage Delete Dropdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-row delete button to `NotificationListItem` so users can delete illustration assets directly from the notification feed (`NotificationDropdown` and `NotificationsPage`), without navigating to `IllustrationGallery`.

**Architecture:** Frontend-only. Reuse Phase 106 DELETE `/api/illustrations/{asset_id}?project_slug=...` endpoint verbatim. Add `useNotificationStore.deleteAssetFromNotification(item)` action that lazy-imports a new `api/illustrations.ts:deleteAsset` wrapper, handles 404/500 via Option α (store marks `_deleted=true` on 200 and 404; 500 leaves history intact). Add `useDeleteFromNotificationToast` composable (mirrors `useBulkDeleteToast` lazy-`useMessage` pattern). Modify `NotificationListItem.vue` to render hover-revealed ✕ button wrapped in `<NPopconfirm>` for `generation`/`regeneration` events only.

**Tech Stack:** Vue 3 + Pinia + Naive UI (NPopconfirm) + Vitest + Python pytest (regression guards). Backend untouched.

---

## File structure

| Type | Path | Purpose |
|------|------|---------|
| Create | `apps/dashboard/src/composables/useDeleteFromNotificationToast.ts` | Toast dispatcher for {status: deleted/not_found/error} |
| Create | `apps/dashboard/src/composables/useDeleteFromNotificationToast.spec.ts` | 3 vitest tests (lazy useMessage pattern) |
| Create | `tests/test_phase109_notifications_delete.py` | 6 frontend-static regression guards |
| Modify | `apps/dashboard/src/api/illustrations.ts` | + `deleteAsset(slug, assetId)` typed wrapper (mirror `bulkDeleteAssets`) |
| Modify | `apps/dashboard/src/stores/useNotificationStore.js` | + `deleteAssetFromNotification(item)` action + export |
| Modify | `apps/dashboard/src/stores/useNotificationStore.spec.js` | + 4 vitest tests (T9-T12) |
| Modify | `apps/dashboard/src/components/notifications/NotificationListItem.vue` | + NPopconfirm + hover/touch + deleted state |
| Modify | `apps/dashboard/src/components/notifications/NotificationListItem.spec.js` | + 8 vitest tests (T1-T8) |
| Modify | `CLAUDE.md` | v60.6 → v60.7 + Phase 109 line in version header |
| Modify | `collaboration/CURRENT_STATUS.md` | Phase 109 row added |
| Modify | `collaboration/BACKLOG.md` | Phase 109 completion row added |
| Modify | `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` | Phase 109 pointer in index + topic file |
| Create | `docs/superpowers/handoffs/2026-09-22-phase-109-notifications-page-delete-handoff.md` | Handoff doc |

**Backend**: zero changes. Phase 106 `routes/illustrations.py:delete_asset` is reused.

---

## Task 1: Plan document (this file)

**Files:**
- Create: `docs/superpowers/plans/2026-09-22-phase-109-notifications-page-delete.md`

- [ ] **Step 1: Verify plan committed**

This task is informational. The plan file is being committed as part of this Write operation. Verify with:
```bash
git log --oneline -1 docs/superpowers/plans/2026-09-22-phase-109-notifications-page-delete.md
```
Expected: commit hash shown.

- [ ] **Step 2: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/plans/2026-09-22-phase-109-notifications-page-delete.md
git commit -m "docs(phase-109): implementation plan"
```

---

## Task 2: `deleteAsset` typed wrapper + `useNotificationStore.deleteAssetFromNotification` action

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts` (add `deleteAsset` wrapper after `bulkDeleteAssets` at line ~217)
- Modify: `apps/dashboard/src/stores/useNotificationStore.js` (add action)
- Modify: `apps/dashboard/src/stores/useNotificationStore.spec.js` (add 4 tests)

- [ ] **Step 1: Write the failing store tests (T9-T12)**

Append to `apps/dashboard/src/stores/useNotificationStore.spec.js` (after the existing `it('recomputes unreadCount...')` block, before the closing `})`):

```js
  // Phase 109: delete asset directly from notification feed
  describe('deleteAssetFromNotification (Phase 109)', () => {
    const baseItem = {
      id: '01HZX',
      projectSlug: 'proj-X',
      eventType: 'generation',
      assetId: 'asset-1',
      assetType: 'chapter',
      chapterNum: 3,
    }

    it('T9: marks _deleted=true on 200 OK', async () => {
      vi.doMock('@/api/illustrations', () => ({
        deleteAsset: vi.fn().mockResolvedValue({ deleted: 'asset-1' }),
      }))
      const store = useNotificationStore()
      store.history = [baseItem]
      const result = await store.deleteAssetFromNotification(baseItem)
      expect(result).toEqual({ status: 'deleted' })
      expect(store.history[0]._deleted).toBe(true)
    })

    it('T10: skips non-generation/regeneration eventTypes', async () => {
      const { deleteAsset } = await import('@/api/illustrations')
      const deleteSpy = vi.spyOn({ deleteAsset }, 'deleteAsset')
      const store = useNotificationStore()
      const cleanupItem = { ...baseItem, eventType: 'cleanup', assetId: null }
      store.history = [cleanupItem]
      const result = await store.deleteAssetFromNotification(cleanupItem)
      expect(result).toEqual({ status: 'skipped' })
      expect(deleteSpy).not.toHaveBeenCalled()
      expect(store.history[0]._deleted).toBeUndefined()
    })

    it('T11: marks _deleted=true on 404 (Option α UX consistency)', async () => {
      vi.resetModules()
      vi.doMock('@/api/illustrations', () => ({
        deleteAsset: vi.fn().mockRejectedValue(new Error('404 not found')),
      }))
      const store = useNotificationStore()
      store.history = [{ ...baseItem }]
      const result = await store.deleteAssetFromNotification(store.history[0])
      expect(result.status).toBe('not_found')
      expect(store.history[0]._deleted).toBe(true)
      vi.doUnmock('@/api/illustrations')
      vi.resetModules()
    })

    it('T12: keeps _deleted=false on 500 StoreError (allows retry)', async () => {
      vi.resetModules()
      vi.doMock('@/api/illustrations', () => ({
        deleteAsset: vi.fn().mockRejectedValue(new Error('500 store error')),
      }))
      const store = useNotificationStore()
      store.history = [{ ...baseItem }]
      const result = await store.deleteAssetFromNotification(store.history[0])
      expect(result.status).toBe('error')
      expect(store.history[0]._deleted).toBeUndefined()
      vi.doUnmock('@/api/illustrations')
      vi.resetModules()
    })
  })
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useNotificationStore.spec.js
```
Expected: 4 new tests FAIL with "deleteAssetFromNotification is not a function" + module-not-found errors.

- [ ] **Step 3: Add `deleteAsset` typed wrapper**

In `apps/dashboard/src/api/illustrations.ts`, find the end of the `bulkDeleteAssets` function (search for the function and its closing brace). Add after it:

```typescript
// Phase 109: single asset delete (reuses Phase 106 backend endpoint).
// Typed wrapper so useNotificationStore can lazy-import + mock in vitest
// (mirrors bulkDeleteAssets pattern).
export async function deleteAsset(
  projectSlug: string,
  assetId: string
): Promise<{ deleted: string }> {
  return $fetch(
    `/api/illustrations/${assetId}?project_slug=${projectSlug}`,
    { method: 'DELETE' }
  )
}
```

- [ ] **Step 4: Add `deleteAssetFromNotification` action to `useNotificationStore`**

In `apps/dashboard/src/stores/useNotificationStore.js`, add the action inside the `defineStore` callback, after `recomputeUnread` and before the final `return`. Also add it to the return object. The full addition (place before `return {`):

```js
  // Phase 109: delete an asset directly from the notification feed.
  // Lazy-imports the deleteAsset API wrapper (keeps store bundle small,
  // matches Phase 107 bulkDeleteAssets pattern). Handles 404 by marking
  // _deleted=true (Option α UX consistency — user clicked delete, expect
  // deletion semantics). 500 errors leave _deleted=false for retry.
  async function deleteAssetFromNotification(item) {
    if (!item || item._deleted) return { status: 'noop' }
    if (item.eventType !== 'generation' && item.eventType !== 'regeneration') {
      return { status: 'skipped' }
    }
    if (!item.assetId || !item.projectSlug) return { status: 'skipped' }

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
      const { deleteAsset } = await import('@/api/illustrations')
      await deleteAsset(item.projectSlug, item.assetId)
      markDeleted(item)
      return { status: 'deleted' }
    } catch (e) {
      const msg = String(e?.message ?? '')
      if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
        markDeleted(item)
        return { status: 'not_found' }
      }
      return { status: 'error', error: e }
    }
  }

```

Then in the `return { ... }` object (last line of the store), add `deleteAssetFromNotification` (alphabetical with other functions — after `appendEvent` and before `markAllRead`):

```js
  return {
    history,
    unreadCount,
    isConnected,
    lastError,
    activeProjectSlug,
    setActiveProject,
    reset,
    appendEvent,
    deleteAssetFromNotification,  // NEW Phase 109
    markAllRead,
    recomputeUnread,
    loadLastSeen,
    saveLastSeen,
  }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useNotificationStore.spec.js
```
Expected: 3 existing + 4 new = 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.ts \
        apps/dashboard/src/stores/useNotificationStore.js \
        apps/dashboard/src/stores/useNotificationStore.spec.js
git commit -m "feat(phase-109): deleteAssetFromNotification store action + 4 tests"
```

---

## Task 3: `useDeleteFromNotificationToast` composable

**Files:**
- Create: `apps/dashboard/src/composables/useDeleteFromNotificationToast.ts`
- Create: `apps/dashboard/src/composables/useDeleteFromNotificationToast.spec.ts`

- [ ] **Step 1: Write the failing tests**

Create `apps/dashboard/src/composables/useDeleteFromNotificationToast.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMessage } from 'naive-ui'
import { useDeleteFromNotificationToast } from '@/composables/useDeleteFromNotificationToast'

vi.mock('naive-ui', () => ({
  useMessage: vi.fn(),
}))

describe('useDeleteFromNotificationToast', () => {
  const mockMessage = {
    success: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  }

  beforeEach(() => {
    vi.mocked(useMessage).mockReturnValue(mockMessage as any)
    vi.clearAllMocks()
  })

  it('T-success: status=deleted calls message.success', () => {
    const { showResult } = useDeleteFromNotificationToast()
    showResult({ status: 'deleted' })
    expect(mockMessage.success).toHaveBeenCalledWith('已删除资产')
    expect(mockMessage.info).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-not-found: status=not_found calls message.info', () => {
    const { showResult } = useDeleteFromNotificationToast()
    showResult({ status: 'not_found' })
    expect(mockMessage.info).toHaveBeenCalledWith('资产不存在或已被删除')
    expect(mockMessage.success).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-error: status=error calls message.error', () => {
    const { showResult } = useDeleteFromNotificationToast()
    showResult({ status: 'error', error: new Error('500') })
    expect(mockMessage.error).toHaveBeenCalledWith('删除失败')
    expect(mockMessage.success).not.toHaveBeenCalled()
    expect(mockMessage.info).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/composables/useDeleteFromNotificationToast.spec.ts
```
Expected: FAIL with "Cannot find module '@/composables/useDeleteFromNotificationToast'".

- [ ] **Step 3: Implement the composable**

Create `apps/dashboard/src/composables/useDeleteFromNotificationToast.ts`:

```typescript
import { useMessage } from 'naive-ui'

// Phase 109: single-delete toast dispatcher for NotificationListItem.
// Mirrors useBulkDeleteToast pattern (Phase 107) — lazy useMessage
// so callers don't need to mount <n-message-provider> at test time.
// Maps the {status: ...} returned by useNotificationStore.deleteAssetFromNotification
// to a Naive UI toast variant.
//
// `useMessage()` is called lazily on first toast to defer the message
// provider dependency until render-time. This lets components mount
// outside an <n-message-provider> for testing — tests that never trigger
// a toast avoid the "no message provider" runtime warning.

export type DeleteFromNotificationStatus = 'deleted' | 'not_found' | 'error'

export interface DeleteFromNotificationResult {
  status: DeleteFromNotificationStatus
  error?: unknown
}

export function useDeleteFromNotificationToast() {
  let messageInstance: ReturnType<typeof useMessage> | null = null

  function getMessage() {
    if (!messageInstance) {
      messageInstance = useMessage()
    }
    return messageInstance
  }

  function showResult(result: DeleteFromNotificationResult): void {
    const m = getMessage()
    if (result.status === 'deleted') {
      m.success('已删除资产')
    } else if (result.status === 'not_found') {
      m.info('资产不存在或已被删除')
    } else {
      m.error('删除失败')
    }
  }

  return { showResult }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/composables/useDeleteFromNotificationToast.spec.ts
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useDeleteFromNotificationToast.ts \
        apps/dashboard/src/composables/useDeleteFromNotificationToast.spec.ts
git commit -m "feat(phase-109): useDeleteFromNotificationToast composable + 3 tests"
```

---

## Task 4: `NotificationListItem.vue` — NPopconfirm + hover/touch + deleted state

**Files:**
- Modify: `apps/dashboard/src/components/notifications/NotificationListItem.vue`
- Modify: `apps/dashboard/src/components/notifications/NotificationListItem.spec.js`

- [ ] **Step 1: Write the failing component tests (T1-T8)**

Append to `apps/dashboard/src/components/notifications/NotificationListItem.spec.js` (after the existing `it('shows provider name...')` block, before the closing `})`). Also add `import { vi }` to the imports:

```js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import NotificationListItem from './NotificationListItem.vue'
import { useNotificationStore } from '@/stores/useNotificationStore'

const baseItem = {
  id: '01HZX',
  projectSlug: 'p',
  eventType: 'generation',
  assetId: 'a1',
  assetType: 'chapter',
  chapterNum: 3,
  stylePreset: 'noir',
  provider: 'minimax',
  ts: '2026-09-18T07:00:00+00:00',
  extra: null,
}

describe('NotificationListItem', () => {
  beforeEach(() => setActivePinia(createPinia()))
  // ... existing 3 tests unchanged ...

  // Phase 109: delete button eligibility + NPopconfirm + deleted state
  it('T1: generation event renders delete button', () => {
    const wrapper = mount(NotificationListItem, { props: { item: baseItem } })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(true)
  })

  it('T2: regeneration event renders delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'regeneration' } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(true)
  })

  it('T3: cleanup event does NOT render delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'cleanup', assetId: null } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
  })

  it('T4: deletion event does NOT render delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'deletion' } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
  })

  it('T5: warning event (assetId=null) does NOT render delete button', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, eventType: 'generation', assetId: null } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
  })

  it('T6: _deleted=true hides delete button + shows 资产已删除 tag', () => {
    const wrapper = mount(NotificationListItem, {
      props: { item: { ...baseItem, _deleted: true } },
    })
    expect(wrapper.find('[data-testid="delete-btn"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="deleted-tag"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('资产已删除')
  })

  it('T7: NPopconfirm negative click does NOT call store.deleteAssetFromNotification', async () => {
    const store = useNotificationStore()
    const spy = vi.spyOn(store, 'deleteAssetFromNotification').mockResolvedValue({ status: 'deleted' })
    const wrapper = mount(NotificationListItem, { props: { item: baseItem } })
    // Negative click test — verify spy is NOT called when user cancels
    // (NPopconfirm cancel path is purely frontend per Phase 106 lesson)
    expect(spy).not.toHaveBeenCalled()
    // Click the trigger button to open the popconfirm
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    // Negative branch: store should still not be called
    expect(spy).not.toHaveBeenCalled()
  })

  it('T8: positive click calls store + emits asset-deleted', async () => {
    const store = useNotificationStore()
    store.history = [{ ...baseItem }]
    vi.spyOn(store, 'deleteAssetFromNotification').mockResolvedValue({ status: 'deleted' })
    const wrapper = mount(NotificationListItem, { props: { item: store.history[0] } })
    // Click trigger to open popconfirm
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    // NPopconfirm positive click is dispatched as a custom event on the popconfirm
    // component (Naive UI). Verify the store was called.
    expect(store.deleteAssetFromNotification).toHaveBeenCalledWith(
      expect.objectContaining({ assetId: 'a1' })
    )
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/notifications/NotificationListItem.spec.js
```
Expected: 8 new tests FAIL with "delete-btn data-testid not found" / "store action missing".

- [ ] **Step 3: Modify `NotificationListItem.vue`**

Replace the entire content of `apps/dashboard/src/components/notifications/NotificationListItem.vue` with:

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
      positive-text="确认删除"
      negative-text="取消"
      @positive-click="onConfirmDelete"
    >
      <template #trigger>
        <button
          class="delete-btn"
          :class="{ 'touch-visible': isTouch }"
          :aria-label="`删除资产 ${item.assetId}`"
          data-testid="delete-btn"
          @click.stop
        >
          ✕
        </button>
      </template>
      <span>确认删除此资产？</span>
    </NPopconfirm>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { NPopconfirm } from 'naive-ui'
import { storeToRefs } from 'pinia'
import { useNotificationStore } from '@/stores/useNotificationStore'
import { useDeleteFromNotificationToast } from '@/composables/useDeleteFromNotificationToast'

const props = defineProps({
  item: { type: Object, required: true },
})

const emit = defineEmits(['asset-deleted'])

const ICONS = {
  generation: '🖼',
  regeneration: '♻️',
  cleanup: '🧹',
  deletion: '🗑',
}

const LABELS = {
  generation: '生成',
  regeneration: '重生成',
  cleanup: '清理',
  deletion: '删除',
}

// Phase 109: eligibility for delete button (mirrors store action guard)
const canDelete = computed(() => {
  if (props.item._deleted) return false
  if (props.item.eventType !== 'generation' && props.item.eventType !== 'regeneration') {
    return false
  }
  return Boolean(props.item.assetId && props.item.projectSlug)
})

// Phase 109: touch detection — always-visible on touch devices (no hover)
const isTouch = ref(false)
onMounted(() => {
  isTouch.value = window.matchMedia('(hover: none)').matches
})

const icon = computed(() => ICONS[props.item.eventType] ?? '•')
const title = computed(() => {
  const t = props.item
  const label = LABELS[t.eventType] ?? t.eventType
  if (t.assetType === 'cover') return `${label}封面`
  if (t.assetType === 'chapter') return `${label}插图 chapter ${t.chapterNum ?? '?'}`
  return label
})
const meta = computed(() => {
  const t = props.item
  const parts = []
  if (t.stylePreset) parts.push(t.stylePreset)
  if (t.provider) parts.push(t.provider)
  return parts.join(' · ')
})

// Phase 109: store action + toast dispatch + emit on success/not_found
const store = useNotificationStore()
const { history } = storeToRefs(store)
const toast = useDeleteFromNotificationToast()

async function onConfirmDelete() {
  const result = await store.deleteAssetFromNotification(props.item)
  toast.showResult(result)
  if (result.status === 'deleted' || result.status === 'not_found') {
    emit('asset-deleted', props.item.id, props.item.assetId)
  }
  // status 'noop' | 'skipped' | 'error' — no emit (defensive against duplicate fires)
}
</script>

<style scoped>
.notification-list-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
}
.icon { font-size: 18px; }
.body { flex: 1; min-width: 0; }
.title { font-weight: 500; }
.meta { color: var(--color-text-dim); font-size: var(--text-sm); }

/* Phase 109: hover-revealed delete button (desktop) + always-visible (touch) */
.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-dim);
  padding: 2px 6px;
  font-size: var(--text-sm);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.notification-list-item:hover .delete-btn,
.delete-btn:focus-visible,
.delete-btn.touch-visible { opacity: 1; }
.delete-btn:hover { color: var(--color-danger); border-color: var(--color-danger); }

/* Phase 109: deleted state visual */
.is-deleted { opacity: 0.55; }
.is-deleted .delete-btn { display: none; }
.deleted-tag {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  font-style: italic;
  margin-top: 2px;
}
</style>
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/notifications/NotificationListItem.spec.js
```
Expected: 3 existing + 8 new = 11 tests PASS.

- [ ] **Step 5: Run full vitest to verify no regressions**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run
```
Expected: all existing + 14 new = ~64 GREEN.

- [ ] **Step 6: Run tsc + eslint + knip**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit
pnpm eslint .
pnpm exec knip
```
Expected: 0 new errors (48 baseline unchanged), 0 new eslint issues, 0 new knip dead exports.

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/notifications/NotificationListItem.vue \
        apps/dashboard/src/components/notifications/NotificationListItem.spec.js
git commit -m "feat(phase-109): NotificationListItem NPopconfirm delete + 8 tests"
```

---

## Task 5: Regression guards (6 frontend-static checks)

**Files:**
- Create: `tests/test_phase109_notifications_delete.py`

- [ ] **Step 1: Write the guard file**

Create `tests/test_phase109_notifications_delete.py`:

```python
"""Phase 109 regression guards — frontend-static source scans.

Mirrors Phase 107 `test_phase107_bulk_delete.py` pattern. Verifies the
Phase 109 orthogonal UX wiring is intact without coupling to backend test
infrastructure (backend is untouched — Phase 106 contract preserved).

Guards:
  G1 — `NotificationListItem.vue` imports NPopconfirm from naive-ui
  G2 — `useNotificationStore.js` exports `deleteAssetFromNotification`
  G3 — `NotificationListItem.vue` source contains the 4-condition `canDelete`
  G4 — `_deleted` field mention exists in `useNotificationStore.js`
  G5 — `useDeleteFromNotificationToast.ts` exports default factory
  G6 — backend `routes/illustrations.py` `delete_asset` route signature
        unchanged from Phase 106 contract (regression: Phase 106 deleted_asset
        still routes through `_delete_asset_inner(mode="single")`)
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_g1_notification_list_item_imports_npopconfirm():
    """G1: NPopconfirm wrapper present in NotificationListItem.vue."""
    text = _read("apps/dashboard/src/components/notifications/NotificationListItem.vue")
    assert "NPopconfirm" in text
    assert "from 'naive-ui'" in text


def test_g2_store_exports_delete_asset_from_notification():
    """G2: useNotificationStore exposes the action."""
    text = _read("apps/dashboard/src/stores/useNotificationStore.js")
    assert "deleteAssetFromNotification" in text
    # Must be in the returned object too (exported from store)
    assert "deleteAssetFromNotification," in text


def test_g3_can_delete_predicate_contains_four_conditions():
    """G3: canDelete computed has the eligibility guard."""
    text = _read("apps/dashboard/src/components/notifications/NotificationListItem.vue")
    # The 4 conditions: _deleted check, eventType check, assetId check, projectSlug check
    assert "item._deleted" in text
    assert "item.eventType !== 'generation' && item.eventType !== 'regeneration'" in text
    assert "item.assetId" in text
    assert "item.projectSlug" in text


def test_g4_deleted_field_in_store_source():
    """G4: _deleted field mutation exists in store action."""
    text = _read("apps/dashboard/src/stores/useNotificationStore.js")
    assert "_deleted" in text
    assert "_deleted: true" in text


def test_g5_toast_composable_exists_and_exports():
    """G5: useDeleteFromNotificationToast composable exists + exports."""
    path = REPO_ROOT / "apps/dashboard/src/composables/useDeleteFromNotificationToast.ts"
    assert path.exists(), f"missing composable: {path}"
    text = path.read_text(encoding="utf-8")
    assert "export function useDeleteFromNotificationToast" in text
    assert "showResult" in text


def test_g6_phase106_delete_asset_route_signature_unchanged():
    """G6: Phase 106 delete_asset contract preserved (regression guard).

    The Phase 109 frontend routes through the Phase 106 endpoint. If anyone
    refactors `delete_asset` and changes its signature, this guard catches it.
    """
    text = _read("apps/studio_api/routes/illustrations.py")
    # Route declaration must still be @app.delete on /api/illustrations/{asset_id}
    assert '@app.delete("/api/illustrations/{asset_id}")' in text
    # Helper delegation must still use mode="single"
    assert 'mode="single"' in text
    # The 5-path state machine in _delete_asset_inner must still call record_failure
    assert "notifications.record_failure" in text
```

- [ ] **Step 2: Run guards to verify they pass**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase109_notifications_delete.py -v
```
Expected: 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add tests/test_phase109_notifications_delete.py
git commit -m "test(phase-109): 6 frontend-static regression guards G1-G6"
```

---

## Task 6: Docs sync (CLAUDE.md + CURRENT_STATUS + BACKLOG + MEMORY + handoff)

**Files:**
- Modify: `CLAUDE.md` (version bump + Phase 109 line in header)
- Modify: `collaboration/CURRENT_STATUS.md` (Phase 109 row in status table)
- Modify: `collaboration/BACKLOG.md` (Phase 109 completion entry)
- Modify: `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` (index pointer)
- Create: `docs/superpowers/handoffs/2026-09-22-phase-109-notifications-page-delete-handoff.md`

- [ ] **Step 1: Update CLAUDE.md version header**

Find the line starting with `> **版本**: v60.6 (Phase 108...` at the top of `CLAUDE.md`. Replace it with:

```markdown
> **版本**: v60.7 (Phase 109 NotificationsPage delete dropdown — seventh Phase 102+ extension after Phase 103/104/105/106/107/108; orthogonal UX: `NotificationListItem` adds hover-revealed ✕ button wrapped in `<NPopconfirm>` for `generation`/`regeneration` events only (skipping `cleanup` / `deletion` / `warning` events which have null asset_id); `useNotificationStore.deleteAssetFromNotification(item)` action (lazy-imports `api/illustrations.ts:deleteAsset` wrapper which calls Phase 106 DELETE `/api/illustrations/{asset_id}?project_slug=...` verbatim — backend untouched); Option α architecture: store internally marks `_deleted=true` on 200 AND 404 (UX consistency — user clicked delete, expect deletion semantics), returns `{status: 'deleted' | 'not_found' | 'error' | 'skipped' | 'noop'}`; 500 leaves `_deleted=false` for retry; new `useDeleteFromNotificationToast` composable (3 variants: success / info / error — lazy useMessage mirrors Phase 107 `useBulkDeleteToast`); local `_deleted` field (underscore prefix = local-only, NOT in backend `NotificationEvent` dataclass, NOT persisted across refresh — re-fetches from `audit_log`); frontend-only phase — I090/I091/I095 NOT extended (delete flows through Phase 106 route which already has full coverage); mobile/touch: `window.matchMedia('(hover: none)')` makes button always-visible (no hover on touch); frontend 14 NEW vitest tests (T1-T8 NotificationListItem + T9-T12 useNotificationStore + T-success/T-not-found/T-error useDeleteFromNotificationToast); 6 NEW pytest regression guards G1-G6 (frontend-static source scans — NPopconfirm import / store export / canDelete predicate / _deleted mutation / toast composable / Phase 106 route signature preserved); 7 atomic commits on master (1 plan + 4 impl + 1 guards + 1 docs this commit). v60.6 → v60.7)
> **Previous**: v60.6 (Phase 108 ... )
```

The new line goes BEFORE the existing `> **Previous**: v60.6 (Phase 108 ...)` line.

- [ ] **Step 2: Update CURRENT_STATUS.md**

In `collaboration/CURRENT_STATUS.md`, find the row containing `**v60.6 Phase 108**` (in the "已完成" table). After it, add a new row:

```markdown
| **v60.7 Phase 109 (NotificationsPage delete dropdown — seventh Phase 102+ extension)** | master direct commits (per 2026-09-15 simplified workflow): `NotificationListItem` adds hover-revealed ✕ button wrapped in `<NPopconfirm>` for `generation`/`regeneration` events only; `useNotificationStore.deleteAssetFromNotification` action lazy-imports new `api/illustrations.ts:deleteAsset` wrapper → Phase 106 DELETE route (backend zero changes); Option α: store marks `_deleted=true` on 200 AND 404 (UX consistency), 500 leaves intact for retry; new `useDeleteFromNotificationToast` composable (lazy useMessage, 3 variants); `window.matchMedia('(hover: none)')` touch detection → always-visible on touch devices; 14 NEW vitest tests (T1-T8 NotificationListItem + T9-T12 store + 3 toast) + 6 NEW pytest regression guards G1-G6 (frontend-static); 7 atomic commits on master. **Validation**: vitest 14/14 NEW + Phase 99/106/107/108 preserved + pnpm tsc 0 new errors (48 baseline unchanged) + eslint 0 + knip 0 + ruff clean on introduced. **Lessons**: (1) Option α keeps UX consistent — 404 also marks deleted (user clicked delete, expect deletion semantics); (2) `_deleted` underscore prefix convention signals local-only state, never crosses backend boundary; (3) Lazy `useMessage` pattern (Phase 107) lets components mount outside `<n-message-provider>` for testing; (4) Touch detection via `matchMedia('(hover: none)')` covers both desktop and mobile in one component; (5) Reuse `useNotificationStore` action contract `{deleted | not_found | error | noop | skipped}` — caller dispatches toast based on status, store owns state mutation. **Cluster cumulative**: Phase 90-109 = 20 phases / 1 NEW package + 5 carryover closures + 7 REQ-002 v2 sub-projects + **7 Phase 102+ extensions (Phase 103/104/105/106/107/108/109)**. **Future work**: Phase 109 leaves backend untouched — I090/I091/I095 invariant coverage COMPLETE (no new callers since Phase 108); next candidates: bulk delete from NotificationsPage (deferred YAGNI for Phase 109), persist `_deleted` across refresh (deferred), optimistic `useIllustrationStore.assets[]` sync (deferred). 详见 `docs/superpowers/handoffs/2026-09-22-phase-109-notifications-page-delete-handoff.md` | ✅ vitest 14/14 NEW + 6/6 guards GREEN + tsc 0 new + eslint 0 + knip 0 |
```

Also update the first paragraph header (`> **最后更新**: ... v60.5 ...`) to add the Phase 109 row above the existing entries. Find that line and replace it with:

```markdown
> **最后更新**: 2026-09-22 (Phase 109 NotificationsPage delete dropdown — seventh Phase 102+ extension after Phase 103/104/105/106/107/108; `NotificationListItem` adds hover-revealed ✕ button wrapped in `<NPopconfirm>` for `generation`/`regeneration` events only; ...)
```

- [ ] **Step 3: Update BACKLOG.md**

In `collaboration/BACKLOG.md`, find the line `**Phase 109+ delete from NotificationsPage dropdown**` and replace it with the completion entry. The exact replacement (find a suitable anchor — search for "NotificationsPage dropdown" or "Phase 109+"):

Find:
```markdown
- Phase 109+ delete from NotificationsPage dropdown (orthogonal UX)
```

Replace with (or add after):
```markdown
- ✅ Phase 109 NotificationsPage delete dropdown COMPLETE — orthogonal UX shipped (see handoff `2026-09-22-phase-109-notifications-page-delete-handoff.md`)
```

- [ ] **Step 4: Update MEMORY.md index**

In `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`, find the "Topic Files" section. After the existing Phase 108 pointer, add:

```markdown
| **Phase 109 NotificationsPage delete (v60.7; seventh Phase 102+ extension)** | → See handoff `2026-09-22-phase-109-notifications-page-delete-handoff.md` (NotificationListItem NPopconfirm + hover-revealed ✕ button for generation/regeneration only + Option α: store marks _deleted=true on 200 AND 404, 500 leaves intact + useDeleteFromNotificationToast composable 3 variants + lazy useMessage + matchMedia('(hover: none)') touch detection + frontend-only — I090/I091/I095 NOT extended + 14 vitest T1-T12 + 3 toast + 6 guards G1-G6)
```

Also bump the **Version** line at the top from `v60.6 (Phase 108 ...)` to `v60.7 (Phase 109 NotificationsPage delete — frontend-only orthogonal UX; 7th Phase 102+ extension)`.

- [ ] **Step 5: Write the handoff doc**

Create `docs/superpowers/handoffs/2026-09-22-phase-109-notifications-page-delete-handoff.md` with this content (mirror Phase 108 handoff structure):

```markdown
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
2. `docs(phase-109): implementation plan`
3. `feat(phase-109): deleteAssetFromNotification store action + 4 tests`
4. `feat(phase-109): useDeleteFromNotificationToast composable + 3 tests`
5. `feat(phase-109): NotificationListItem NPopconfirm delete + 8 tests`
6. `test(phase-109): 6 frontend-static regression guards G1-G6`
7. `docs(phase-109): CLAUDE.md v60.6 → v60.7 + docs sync + handoff`

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
```

- [ ] **Step 6: Final validation**

```bash
cd /home/ailearn/projects/LingWen
# Backend regression (Phase 106/107/108 preserved)
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase109_notifications_delete.py -v
# Frontend
cd apps/dashboard
pnpm vitest run
pnpm tsc --noEmit
pnpm eslint .
pnpm exec knip
```
Expected: 6 guards GREEN, ~64 vitest GREEN, 0 new tsc/eslint/knip issues.

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md \
        collaboration/CURRENT_STATUS.md \
        collaboration/BACKLOG.md \
        /home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md \
        docs/superpowers/handoffs/2026-09-22-phase-109-notifications-page-delete-handoff.md
git commit -m "docs(phase-109): CLAUDE.md v60.6 → v60.7 + sync + handoff"
```

---

## Self-review checklist

- [x] Spec coverage: §1 motivation → Task 4 (NotificationListItem changes); §2 scope in/out → enforced by `canDelete` predicate + guards; §3 module layout → all 7 tasks cover the 8 modified/created files; §4 state mgmt → Task 2; §5 component → Task 4; §6 delete flow → Task 2 (Option α) + Task 4 (click handler consumes status); §7 testing → Tasks 2/3/4/5 (14 + 6); §8 invariants → covered by G6 (Phase 106 signature preserved).
- [x] Placeholder scan: no "TBD"/"TODO"/"fill in" — all code blocks complete with imports, signatures, and exact paths.
- [x] Type consistency: `deleteAssetFromNotification(item) → {status: ...}` is consistent across Task 2 (store), Task 3 (toast result type), Task 4 (click handler consumes), Task 5 (G4 `_deleted: true`).
- [x] Path consistency: `_deleted` field naming, `assetId`/`projectSlug` from NotificationEvent (matches existing `useNotificationStore.js:appendEvent` test data).
- [x] Atomic commits: matches spec §11 (7 commits: this plan + 4 impl + 1 guards + 1 docs sync).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-22-phase-109-notifications-page-delete.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints