import { ref } from 'vue'

export function useWriteWorkspacePersistence({ saveFn, debounceMs = 800 }) {
  const status = ref('idle') // 'idle' | 'saving' | 'saved' | 'error' | 'conflict'
  const lastSavedAt = ref(null)
  const lastMtime = ref(null)
  const errorMessage = ref(null)
  const pendingPayload = ref(null)
  let timer = null

  function scheduleSave(payload) {
    pendingPayload.value = payload
    if (timer) clearTimeout(timer)
    timer = setTimeout(executeSave, debounceMs)
  }

  async function executeSave() {
    if (!pendingPayload.value) return
    status.value = 'saving'
    try {
      const result = await saveFn(pendingPayload.value)
      lastMtime.value = result.mtime
      lastSavedAt.value = new Date().toISOString()
      status.value = 'saved'
      pendingPayload.value = null
    } catch (e) {
      errorMessage.value = e.message
      status.value = 'error'
    }
  }

  async function flushNow() {
    if (timer) { clearTimeout(timer); timer = null }
    await executeSave()
  }

  function detectConflict(currentMtime, lastSeenMtime) {
    return lastSeenMtime > currentMtime
  }

  function cancel() {
    if (timer) { clearTimeout(timer); timer = null }
    pendingPayload.value = null
  }

  return { status, lastSavedAt, lastMtime, errorMessage, scheduleSave, flushNow, detectConflict, cancel }
}
