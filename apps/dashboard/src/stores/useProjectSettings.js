import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Project settings Pinia store (Phase 96 + Phase 97 reference image).
 *
 * State:
 *   - settings: { default_provider } | null
 *   - slug: string | null
 *   - loading: bool
 *   - referenceImage: { exists, size_bytes, mime_type } | null (Phase 97)
 *
 * Actions:
 *   - fetch(slug), save(slug, partial)
 *   - fetchReferenceImage(slug), fetchReferenceImageBlob(slug),
 *     uploadReferenceImage(slug, file), deleteReferenceImage(slug) (Phase 97)
 *
 * Backed by:
 *   - PUT/GET /api/projects/{slug}/settings
 *   - GET/POST/DELETE /api/projects/{slug}/reference-image (Phase 97)
 */
export const useProjectSettingsStore = defineStore('projectSettings', () => {
  const settings = ref(null)
  const slug = ref(null)
  const loading = ref(false)
  const referenceImage = ref(null)

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

  // ---- Phase 97 reference image methods ----
  async function fetchReferenceImage(targetSlug) {
    try {
      const resp = await globalThis.fetch(`/api/projects/${targetSlug}/reference-image`)
      if (resp.status === 404) {
        referenceImage.value = null
        return null
      }
      if (!resp.ok) {
        referenceImage.value = null
        return null
      }
      const data = await resp.json()
      referenceImage.value = data
      return data
    } catch {
      referenceImage.value = null
      return null
    }
  }

  async function fetchReferenceImageBlob(targetSlug) {
    const resp = await globalThis.fetch(`/api/projects/${targetSlug}/reference-image`)
    if (!resp.ok) {
      throw new Error(`fetchReferenceImageBlob failed: ${resp.status}`)
    }
    return await resp.blob()
  }

  async function uploadReferenceImage(targetSlug, file) {
    const formData = new FormData()
    formData.append('file', file)
    const resp = await globalThis.fetch(`/api/projects/${targetSlug}/reference-image`, {
      method: 'POST',
      body: formData,
    })
    if (!resp.ok) {
      throw new Error(`uploadReferenceImage failed: ${resp.status}`)
    }
    // Refresh cached metadata so consumers see the new size_bytes/mime_type.
    await fetchReferenceImage(targetSlug)
  }

  async function deleteReferenceImage(targetSlug) {
    const resp = await globalThis.fetch(`/api/projects/${targetSlug}/reference-image`, {
      method: 'DELETE',
    })
    if (!resp.ok) {
      throw new Error(`deleteReferenceImage failed: ${resp.status}`)
    }
    referenceImage.value = null
  }

  return {
    settings,
    slug,
    loading,
    referenceImage,
    fetch,
    save,
    fetchReferenceImage,
    fetchReferenceImageBlob,
    uploadReferenceImage,
    deleteReferenceImage,
  }
})
