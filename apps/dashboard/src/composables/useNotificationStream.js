/**
 * useNotificationStream — Phase 99 SSE wrapper for illustration events.
 *
 * Mirrors Phase 24 useBatchEventStream pattern. Subscribes to
 *   GET /api/projects/{slug}/illustrations/events
 * and buffers the most recent events so the bell + dropdown render live.
 *
 * Lifecycle: open on mount or when projectSlug ref changes; close on unmount.
 */
import { onBeforeUnmount, ref, watch } from 'vue'

const EVENT_TYPES = ['generation', 'regeneration', 'cleanup', 'deletion']
const BUFFER_CAP = 200

export function useNotificationStream(projectSlug) {
  const history = ref([])
  const isConnected = ref(false)
  const lastError = ref(null)
  let source = null

  function appendEvent(type, rawData) {
    let data
    try {
      data = JSON.parse(rawData)
    } catch {
      return // malformed frame, drop
    }
    history.value = [
      ...history.value,
      {
        id: data.id,
        projectSlug: data.project_slug,
        eventType: data.event_type,
        assetId: data.asset_id,
        assetType: data.asset_type,
        chapterNum: data.chapter_num,
        stylePreset: data.style_preset,
        provider: data.provider,
        ts: data.ts,
        extra: data.extra ?? null,
      },
    ].slice(-BUFFER_CAP)
  }

  function closeSource() {
    if (source) {
      source.close()
      source = null
    }
    isConnected.value = false
  }

  function connect() {
    closeSource()
    history.value = []
    lastError.value = null
    if (!projectSlug.value) {
      return
    }
    const url = `/api/projects/${encodeURIComponent(projectSlug.value)}/illustrations/events`
    const s = new EventSource(url)
    source = s
    for (const type of EVENT_TYPES) {
      s.addEventListener(type, (event) => appendEvent(type, event.data))
    }
    s.onopen = () => {
      isConnected.value = true
      lastError.value = null
    }
    s.onerror = () => {
      isConnected.value = false
      lastError.value = '实时连接中断'
    }
  }

  watch(projectSlug, connect, { immediate: true })

  onBeforeUnmount(() => closeSource())

  return { history, isConnected, lastError }
}