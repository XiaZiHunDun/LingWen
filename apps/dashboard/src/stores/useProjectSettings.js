import { defineStore } from 'pinia'
import { ref } from 'vue'
import { NOTIFY_EVENT_TYPES } from '@/api/illustrations'

/**
 * Phase 104: normalize notify_threshold response into the per-event-type dict
 * shape used by the rest of the frontend.
 *
 * Backend behavior (post-Phase 104):
 *   - Pydantic NormalizedNotifyThreshold always returns a dict with one key
 *     per NotifyEventType (default = Number.MAX_SAFE_INTEGER when absent).
 *   - Legacy int payload (single threshold applied to all event types) is
 *     auto-expanded by the backend to a 4-key dict on read.
 *
 * This helper exists as a defensive boundary at the store level so that:
 *   - older API responses (raw int, or partial dict) render correctly in UI
 *   - the UI table (Phase 104 Task 8) can iterate NOTIFY_EVENT_TYPES uniformly
 *   - opt-out (undefined / null) renders an empty table (no thresholds)
 *
 * Pure function — safe to export and call from UI components.
 *
 * @param {number | Record<string, number> | undefined | null} value
 * @returns {Record<string, number>}
 */
export function normalizeNotifyThreshold(value) {
  if (typeof value === 'number') {
    return Object.fromEntries(NOTIFY_EVENT_TYPES.map((et) => [et, value]))
  }
  if (value && typeof value === 'object') {
    return { ...value }
  }
  return {}
}

/**
 * Project settings Pinia store
 *   Phase 96: default_provider + auto_generate + max_assets + confirm_before_generate
 *   Phase 97: reference image state
 *   Phase 101: fallback_chain
 *   Phase 102: fallback_models + chapter_overrides + notify_threshold (int)
 *   Phase 104: notify_threshold widened to per-event-type dict
 *
 * State:
 *   - settings: object | null
 *       { default_provider, fallback_chain,
 *         fallback_models: Record<string, string>,
 *         chapter_overrides: Record<number, ChapterOverrideSubset>,
 *         notify_threshold: number | Record<NotifyEventType, number> (Phase 104),
 *         auto_generate?, max_assets?, confirm_before_generate? } | null
 *   - slug: string | null
 *   - loading: bool
 *   - referenceImage: { exists, size_bytes, mime_type } | null (Phase 97)
 *
 * Actions:
 *   - fetch(slug), save(slug, partial)
 *     Phase 104: fetch() normalizes notify_threshold into per-event-type dict
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
        const data = await resp.json()
        // Phase 104: defensive normalization of notify_threshold.
        // Backend already returns a dict post-Pydantic, but if the API surface
        // ever leaks a legacy int payload (or a partial dict from a stale
        // client), we normalize at the store boundary so downstream consumers
        // (UI table, save() round-trip) see a uniform dict shape.
        const normalized = {
          ...data,
          notify_threshold: normalizeNotifyThreshold(data.notify_threshold),
        }
        settings.value = normalized
      } else {
        settings.value = {
          default_provider: 'minimax',
          fallback_chain: [],
          fallback_models: {},
          chapter_overrides: {},
          notify_threshold: 3,
        }
      }
    } catch {
      settings.value = {
        default_provider: 'minimax',
        fallback_chain: [],
        fallback_models: {},
        chapter_overrides: {},
        notify_threshold: 3,
      }
    } finally {
      loading.value = false
    }
  }

  async function save(targetSlug, partial) {
    const current = settings.value || {
      default_provider: 'minimax',
      fallback_chain: [],
      fallback_models: {},
      chapter_overrides: {},
      notify_threshold: 3,
    }
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
