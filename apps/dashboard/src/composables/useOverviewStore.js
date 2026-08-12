/**
 * 获取 overview 概览数据 + chapters 列表。
 *
 * @returns {{ overview: Object, chapters: Array, loading: boolean, lastError: string|null, refresh: Function }}
 * 注意：返回的属性是 ref 在 reactive context 中已自动解包，不需要 .value。
 */

import { ref } from 'vue'
import { fetchOverview, fetchChapters } from '../api/index.js'
import { createSingletonLifecycle, withLoadingState } from '../utils/asyncStoreUtils.js'

const overview = ref({})
const chapters = ref([])
const loading = ref(false)
const lastError = ref(null)

async function refreshFn() {
  const [overviewData, chaptersData] = await Promise.all([
    fetchOverview(),
    fetchChapters('1-30'),
  ])
  overview.value = overviewData
  chapters.value = chaptersData.chapters || []
}

const refresh = withLoadingState(refreshFn, loading, lastError)
const { useLifecycle } = createSingletonLifecycle(refresh, { autoRefresh: true, deferRefresh: true })

export function useOverviewStore() {
  useLifecycle()
  return { overview, chapters, loading, lastError, refresh }
}
