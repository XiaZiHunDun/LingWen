import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Project settings Pinia store (Phase 96).
 *
 * State: { settings: { default_provider } | null, slug: string | null, loading: bool }
 * Actions: { fetch(slug), save(slug, partial) }
 *
 * Backed by PUT/GET /api/projects/{slug}/settings endpoint.
 */
export const useProjectSettingsStore = defineStore('projectSettings', () => {
  const settings = ref(null)
  const slug = ref(null)
  const loading = ref(false)

  async function fetch(targetSlug) {
    if (!targetSlug) return
    loading.value = true
    slug.value = targetSlug
    try {
      // Use globalThis.fetch to avoid name collision with this action (which
      // is also named `fetch`). Otherwise `fetch(...)` here would recurse
      // into the action itself.
      const resp = await globalThis.fetch(`/api/projects/${targetSlug}/settings`)
      if (resp.ok) {
        settings.value = await resp.json()
      } else {
        settings.value = { default_provider: 'minimax' }
      }
    } catch {
      settings.value = { default_provider: 'minimax' }
    } finally {
      loading.value = false
    }
  }

  async function save(targetSlug, partial) {
    const current = settings.value || { default_provider: 'minimax' }
    const next = { ...current, ...partial }
    loading.value = true
    try {
      const resp = await globalThis.fetch(`/api/projects/${targetSlug}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      })
      if (resp.ok) {
        settings.value = await resp.json()
      } else {
        throw new Error(`save failed: ${resp.status}`)
      }
    } finally {
      loading.value = false
    }
  }

  return { settings, slug, loading, fetch, save }
})
