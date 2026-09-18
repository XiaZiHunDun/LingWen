/**
 * useNotificationStream — Phase 99 SSE wrapper for illustration events.
 * Mirrors Phase 24 useBatchEventStream pattern.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useNotificationStream } from './useNotificationStream'

class MockEventSource {
  constructor(url) {
    this.url = url
    this.readyState = 0
    this.listeners = {}
    MockEventSource.last = this
  }
  addEventListener(type, cb) {
    (this.listeners[type] = this.listeners[type] || []).push(cb)
  }
  removeEventListener(type, cb) {
    this.listeners[type] = (this.listeners[type] || []).filter((f) => f !== cb)
  }
  close() {
    this.readyState = 2
  }
  emit(type, data) {
    ;(this.listeners[type] || []).forEach((cb) => cb({ data: JSON.stringify(data) }))
  }
  fireOpen() {
    this.readyState = 1
    if (this.onopen) this.onopen()
  }
  fireError() {
    this.readyState = 2
    if (this.onerror) this.onerror()
  }
}

describe('useNotificationStream', () => {
  beforeEach(() => {
    globalThis.EventSource = MockEventSource
    MockEventSource.last = null
  })

  it('opens EventSource with correct URL on mount', async () => {
    const projectSlug = ref('my-project')
    useNotificationStream(projectSlug)
    await nextTick()
    expect(MockEventSource.last).toBeTruthy()
    expect(MockEventSource.last.url).toBe('/api/projects/my-project/illustrations/events')
  })

  it('appends received events to history', async () => {
    const projectSlug = ref('my-project')
    const { history, isConnected } = useNotificationStream(projectSlug)
    await nextTick()
    MockEventSource.last.fireOpen()
    MockEventSource.last.emit('generation', {
      id: '01HZX7K3',
      project_slug: 'my-project',
      event_type: 'generation',
      asset_id: 'a1',
      asset_type: 'chapter',
      chapter_num: 1,
      ts: '2026-09-18T07:00:00+00:00',
    })
    expect(isConnected.value).toBe(true)
    expect(history.value).toHaveLength(1)
    expect(history.value[0].id).toBe('01HZX7K3')
    expect(history.value[0].eventType).toBe('generation')
  })

  it('closes old EventSource when projectSlug changes', async () => {
    const projectSlug = ref('proj-A')
    const { history } = useNotificationStream(projectSlug)
    await nextTick()
    const firstSource = MockEventSource.last
    firstSource.emit('generation', { id: 'id-A', project_slug: 'proj-A', event_type: 'generation' })
    expect(history.value).toHaveLength(1)
    projectSlug.value = 'proj-B'
    await nextTick()
    expect(firstSource.readyState).toBe(2) // closed
    expect(MockEventSource.last).not.toBe(firstSource)
    expect(MockEventSource.last.url).toContain('/api/projects/proj-B/illustrations/events')
    expect(history.value).toHaveLength(0)
  })
})