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

  // NOTE: regenerate is intentionally non-atomic (DELETE then POST). If the
  // POST fails after the DELETE succeeds, the old asset is permanently lost.
  // A confirmation dialog at the call site (Task 15-17) is the v1 mitigation.
  // v2: backend could add a PUT /{id}/regenerate endpoint for atomic swap.
  async function regenerate(slug, assetId) {
    const original = assets.value.find(a => a.id === assetId)
    if (!original) throw new Error(`asset ${assetId} not found`)

    const params = {
      type: original.type,
      chapter_num: original.chapter_num,
      style_preset: original.style_preset,
      custom_prompt: original.custom_prompt,
    }
    await deleteAsset(slug, assetId)
    return await generate(slug, params)
  }

  return {
    assets, loading, error, projectSlug,
    loadAssets, generate, regenerate, deleteAsset,
  }
})
