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
      vi.resetModules()
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
      vi.resetModules()
      vi.doMock('@/api/illustrations', () => ({
        deleteAsset: vi.fn(),
      }))
      const { useNotificationStore: useStore } = await import('@/stores/useNotificationStore')
      const store = useStore()
      const cleanupItem = { ...baseItem, eventType: 'cleanup', assetId: null }
      store.history = [cleanupItem]
      const result = await store.deleteAssetFromNotification(cleanupItem)
      expect(result).toEqual({ status: 'skipped' })
      expect(store.history[0]._deleted).toBeUndefined()
    })

    it('T11: marks _deleted=true on 404 (Option α UX consistency)', async () => {
      vi.resetModules()
      vi.doMock('@/api/illustrations', () => ({
        deleteAsset: vi.fn().mockRejectedValue(new Error('404 not found')),
      }))
      const { useNotificationStore: useStore } = await import('@/stores/useNotificationStore')
      const store = useStore()
      store.history = [{ ...baseItem }]
      const result = await store.deleteAssetFromNotification(store.history[0])
      expect(result.status).toBe('not_found')
      expect(store.history[0]._deleted).toBe(true)
    })

    it('T12: keeps _deleted=false on 500 StoreError (allows retry)', async () => {
      vi.resetModules()
      vi.doMock('@/api/illustrations', () => ({
        deleteAsset: vi.fn().mockRejectedValue(new Error('500 store error')),
      }))
      const { useNotificationStore: useStore } = await import('@/stores/useNotificationStore')
      const store = useStore()
      store.history = [{ ...baseItem }]
      const result = await store.deleteAssetFromNotification(store.history[0])
      expect(result.status).toBe('error')
      expect(store.history[0]._deleted).toBeUndefined()
    })
  })
})
