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

  return {
    history,
    unreadCount,
    isConnected,
    lastError,
    activeProjectSlug,
    setActiveProject,
    reset,
    appendEvent,
    markAllRead,
    recomputeUnread,
    loadLastSeen,
    saveLastSeen,
  }
})
