import { computed } from 'vue'
import { useIllustrationStore } from '@/stores/useIllustrationStore'
import { storeToRefs } from 'pinia'

export function useIllustration(projectSlug) {
  const store = useIllustrationStore()
  const { assets, loading, error } = storeToRefs(store)

  // Composable-scoped computed filters; equivalent to spec §3.4 type filter.
  // (Store intentionally doesn't expose a byType computed — callers always
  // need the filter wrapped in their own context.)
  const chapterAssets = computed(() => assets.value.filter(a => a.type === 'chapter'))
  const coverAssets = computed(() => assets.value.filter(a => a.type === 'cover'))

  function getForChapter(chapterNum) {
    return chapterAssets.value.find(a => a.chapter_num === chapterNum)
  }

  return {
    assets,
    chapterAssets,
    coverAssets,
    loading,
    error,
    getForChapter,
    loadAssets: () => store.loadAssets(projectSlug),
    generate: (params) => store.generate(projectSlug, params),
    regenerate: (assetId) => store.regenerate(projectSlug, assetId),
    deleteAsset: (assetId) => store.deleteAsset(projectSlug, assetId),
  }
}
