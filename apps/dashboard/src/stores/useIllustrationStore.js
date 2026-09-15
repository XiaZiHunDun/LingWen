import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useIllustrationStore = defineStore('illustrations', () => {
  const assets = ref([])
  const loading = ref(false)
  const error = ref(null)

  const byType = computed(() => (type) => assets.value.filter(a => a.type === type))

  async function loadAssets(projectSlug, type = null) {
    loading.value = true
    error.value = null
    try {
      const query = type ? `&type=${type}` : ''
      const res = await $fetch(`/api/illustrations/list?project_slug=${projectSlug}${query}`)
      assets.value = res.assets
    } catch (e) {
      error.value = e.message || 'load failed'
    } finally {
      loading.value = false
    }
  }

  async function generate(projectSlug, params) {
    loading.value = true
    error.value = null
    try {
      const res = await $fetch('/api/illustrations/generate', {
        method: 'POST',
        body: { project_slug: projectSlug, ...params },
      })
      // Prepend to list
      assets.value = [res, ...assets.value]
      return res
    } catch (e) {
      error.value = e.data?.detail?.error || e.message || 'generate failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function regenerate(projectSlug, assetId) {
    // Find original metadata, call generate again with same params
    const original = assets.value.find(a => a.id === assetId)
    if (!original) throw new Error(`asset ${assetId} not found`)

    const params = {
      type: original.type,
      chapter_num: original.chapter_num,
      style_preset: original.style_preset,
      custom_prompt: original.custom_prompt,
    }
    // Delete old
    await $fetch(`/api/illustrations/${assetId}?project_slug=${projectSlug}`, { method: 'DELETE' })
    // Generate new
    return await generate(projectSlug, params)
  }

  async function deleteAsset(projectSlug, assetId) {
    await $fetch(`/api/illustrations/${assetId}?project_slug=${projectSlug}`, { method: 'DELETE' })
    assets.value = assets.value.filter(a => a.id !== assetId)
  }

  return { assets, loading, error, byType, loadAssets, generate, regenerate, deleteAsset }
})
