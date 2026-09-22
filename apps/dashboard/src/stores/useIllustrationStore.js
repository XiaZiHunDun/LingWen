import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useIllustrationStore = defineStore('illustrations', () => {
  const assets = ref([])
  const loading = ref(false)
  const error = ref(null)
  // Track the project whose assets are currently cached. Pinia stores are
  // singletons; this guards against project-switch leaks where stale data
  // from project A is shown briefly while project B's loadAssets is in flight.
  const projectSlug = ref(null)

  async function loadAssets(slug, type = null) {
    // Project switch: clear stale state before fetching new.
    if (projectSlug.value !== slug) {
      assets.value = []
      error.value = null
      projectSlug.value = slug
    }
    loading.value = true
    error.value = null
    try {
      const query = type ? `&type=${type}` : ''
      const res = await $fetch(`/api/illustrations/list?project_slug=${slug}${query}`)
      assets.value = res.assets
    } catch (e) {
      error.value = e.message || 'load failed'
    } finally {
      loading.value = false
    }
  }

  async function generate(slug, params) {
    loading.value = true
    error.value = null
    try {
      // Phase 97 Task 11 — multipart vs JSON dispatch.
      // When params.per_call_reference is a File (browser File object from
      // <input type="file">), send multipart/form-data so the backend can
      // read the per-call override via UploadFile. Otherwise stay on the
      // Phase 96 JSON path and pass use_project_reference as a boolean so
      // the backend can decide whether to read the project's default from
      // disk. We strip per_call_reference from the JSON body because File
      // is not JSON-serializable.
      const useMultipart = params.per_call_reference instanceof File
      let body
      let headers
      if (useMultipart) {
        const formData = new FormData()
        formData.append('project_slug', slug)
        formData.append('type', params.type)
        if (params.chapter_num != null) {
          formData.append('chapter_num', String(params.chapter_num))
        }
        formData.append('style_preset', params.style_preset)
        if (params.custom_prompt) {
          formData.append('custom_prompt', params.custom_prompt)
        }
        if (params.provider) {
          formData.append('provider', params.provider)
        }
        formData.append(
          'use_project_reference',
          String(params.use_project_reference ?? true),
        )
        formData.append('file', params.per_call_reference)
        body = formData
        headers = undefined
      } else {
        const { per_call_reference: _ignored, ...rest } = params
        body = {
          project_slug: slug,
          ...rest,
          use_project_reference: params.use_project_reference ?? true,
        }
      }

      const res = await $fetch('/api/illustrations/generate', {
        method: 'POST',
        body,
        headers,
      })
      // Prepend to list (most recent first)
      assets.value = [res, ...assets.value]
      return res
    } catch (e) {
      error.value = e.data?.detail?.error || e.message || 'generate failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteAsset(slug, assetId) {
    await $fetch(`/api/illustrations/${assetId}?project_slug=${slug}`, { method: 'DELETE' })
    assets.value = assets.value.filter(a => a.id !== assetId)
  }

  // Phase 107: bulk delete (1 method).
  // Delegates to api.bulkDeleteAssets and reactively removes
  // deleted + not_found assets from local assets[] (store_error failures
  // retained for potential retry). Uses lazy dynamic import to keep the
  // initial bundle small (the bulk delete code path is only used when the
  // user opens the multi-select UI).
  async function bulkDeleteAssets(slug, assetIds) {
    if (!Array.isArray(assetIds) || assetIds.length === 0) {
      throw new Error('assetIds must be non-empty array')
    }
    const { bulkDeleteAssets: apiBulkDelete } = await import('@/api/illustrations')
    const result = await apiBulkDelete(slug, assetIds)
    const removedIds = new Set([
      ...result.deleted,
      ...result.failed.filter(f => f.status === 'not_found').map(f => f.id),
    ])
    assets.value = assets.value.filter(a => !removedIds.has(a.id))
    return result
  }

  // v55.4 Phase 94 — atomic regenerate via PUT /{id}/regenerate.
  // Replaces v1's DELETE+POST pattern (which left a window where the asset
  // didn't exist and could lose the old asset if POST failed). Backend now
  // preserves asset_id + atomically swaps bytes via temp file + POSIX rename.
  // On Stage failure, the original asset is preserved (no destructive behavior).
  async function regenerate(slug, assetId) {
    loading.value = true
    error.value = null
    try {
      const res = await $fetch(
        `/api/illustrations/${assetId}/regenerate?project_slug=${slug}`,
        { method: 'PUT' }
      )
      // Replace the existing entry in-place (same id, new content).
      const idx = assets.value.findIndex(a => a.id === assetId)
      if (idx >= 0) {
        assets.value = [
          ...assets.value.slice(0, idx),
          res,
          ...assets.value.slice(idx + 1),
        ]
      } else {
        // Asset not in cache — prepend (defensive).
        assets.value = [res, ...assets.value]
      }
      return res
    } catch (e) {
      error.value = e.data?.detail?.error || e.message || 'regenerate failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    assets, loading, error, projectSlug,
    loadAssets, generate, regenerate, deleteAsset, bulkDeleteAssets,
  }
})
