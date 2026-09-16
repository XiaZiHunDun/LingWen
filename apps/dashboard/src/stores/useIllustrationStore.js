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
      const res = await $fetch('/api/illustrations/generate', {
        method: 'POST',
        body: { project_slug: slug, ...params },
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
    loadAssets, generate, regenerate, deleteAsset,
  }
})
