/**
 * useNotificationStore — Pinia store for Phase 99 notification center.
 *
 * Owns:
 * - history (capped 200, most-recent-first)
 * - unreadCount (badge number)
 * - isConnected + lastError (SSE status)
 * - activeProjectSlug (drives SSE reconnect)
 * - localStorage read-state (lastSeenId per project)
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

const LS_KEY_PREFIX = 'lingwen.notifications.lastSeen.'

export const useNotificationStore = defineStore('notifications', () => {
  const history = ref([])
  const unreadCount = ref(0)
  const isConnected = ref(false)
  const lastError = ref(null)
  const activeProjectSlug = ref(null)

  function lsKey(slug) {
    return `${LS_KEY_PREFIX}${slug}`
  }

  function loadLastSeen(slug) {
    try {
      const raw = localStorage.getItem(lsKey(slug))
      return raw || null
    } catch {
      return null
    }
  }

  function saveLastSeen(slug, id) {
    try {
      localStorage.setItem(lsKey(slug), id)
    } catch {
      // ignore quota / private mode
    }
  }

  function setActiveProject(slug) {
    activeProjectSlug.value = slug
  }

  function reset() {
    history.value = []
    unreadCount.value = 0
    lastError.value = null
  }

  function appendEvent(item) {
    history.value = [item, ...history.value].slice(0, 200)
    if (item.id) {
      const lastSeen = activeProjectSlug.value ? loadLastSeen(activeProjectSlug.value) : null
      if (!lastSeen || item.id > lastSeen) {
        unreadCount.value += 1
      }
    }
  }

  function markAllRead() {
    if (history.value.length === 0 || !activeProjectSlug.value) return
    // Use max ID across history (order-agnostic): ULIDs are lexicographically
    // sortable, so the latest event has the highest id regardless of array order.
    const latest = history.value.reduce(
      (max, e) => (e.id && (!max || e.id > max) ? e.id : max),
      null
    )
    if (latest) {
      saveLastSeen(activeProjectSlug.value, latest)
    }
    unreadCount.value = 0
  }

  function recomputeUnread() {
    if (!activeProjectSlug.value) {
      unreadCount.value = 0
      return
    }
    const lastSeen = loadLastSeen(activeProjectSlug.value)
    if (!lastSeen) {
      unreadCount.value = history.value.length
      return
    }
    unreadCount.value = history.value.filter((e) => e.id > lastSeen).length
  }

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
})
