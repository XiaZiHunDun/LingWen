/**
 * Phase 99: useNotificationStore — Pinia store managing notification history,
 * unread count, SSE lifecycle, and localStorage read-state.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useNotificationStore } from './useNotificationStore'

describe('useNotificationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('initializes with empty state', () => {
    const store = useNotificationStore()
    expect(store.history).toEqual([])
    expect(store.unreadCount).toBe(0)
    expect(store.activeProjectSlug).toBe(null)
  })

  it('marks all read by updating lastSeenId', () => {
    const store = useNotificationStore()
    store.activeProjectSlug = 'proj-X'
    store.history = [
      { id: '01HZX', eventType: 'generation', projectSlug: 'proj-X' },
      { id: '01HZY', eventType: 'generation', projectSlug: 'proj-X' },
    ]
    store.unreadCount = 2
    store.markAllRead()
    expect(store.unreadCount).toBe(0)
    expect(localStorage.getItem('lingwen.notifications.lastSeen.proj-X')).toBe('01HZY')
  })

  it('recomputes unreadCount on active project switch using lastSeenId', () => {
    localStorage.setItem('lingwen.notifications.lastSeen.proj-Y', '01HZ0')
    const store = useNotificationStore()
    store.setActiveProject('proj-Y')
    store.history = [
      { id: '01HZ2', eventType: 'generation', projectSlug: 'proj-Y' },
      { id: '01HZ1', eventType: 'generation', projectSlug: 'proj-Y' },
      { id: '01HZ0', eventType: 'generation', projectSlug: 'proj-Y' },
    ]
    store.recomputeUnread()
    expect(store.unreadCount).toBe(2) // two events with id > '01HZ0'
  })
})
