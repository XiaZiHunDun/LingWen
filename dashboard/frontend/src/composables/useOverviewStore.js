// useOverviewStore — Phase 8.34 module-level singleton composable
// 管理 overview 概览数据 + chapters 列表 (REST 拉, Promise.all 并行 fetch)
// 比 useDecisionStore / useWorkflowListStore 简单: 只 1 个 refresh action, 无 mutation
// 镜像 useCostWindow 模式: module-level refs + mountedCount lifecycle
// 决策点 (主公 Phase 8.34): 首个 mount 时 deferred 1 microtask 后调 refresh() —
//   让 mount() 同步快照仍是默认值 (overview={}/chapters=[]/loading=false), 但
//   await flushPromises 后能看到初始 fetch 完成.
// fetchChapters 镜像 OverviewPage 原 page-local 调用签名 (硬编码 '1-30' 范围)
//   — Task 6 refactor 时再决定是否参数化.

import { onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchOverview, fetchChapters } from '../api/index.js'

const overview = ref({})
const chapters = ref([])
const loading = ref(false)
const lastError = ref(null)
let mountedCount = 0

async function refresh() {
  loading.value = true
  lastError.value = null
  try {
    const [overviewData, chaptersData] = await Promise.all([
      fetchOverview(),
      fetchChapters('1-30'),
    ])
    overview.value = overviewData
    // Phase 8.34 修正 (Task 3 subagent 误用 envelope-as-array):
    //   fetchChapters 实际返回 { chapters: [...] } envelope (mirror OverviewPage 原 L110),
    //   store 应解包为 array, 保 page 透传 store.chapters 即可直接用于 v-for
    chapters.value = chaptersData.chapters || []
  } catch (e) {
    lastError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

export function useOverviewStore() {
  onMounted(() => {
    if (mountedCount === 0) {
      // microtask defer 让 mount() 同步快照仍是默认值, 但 await flushPromises
      // 后能看到初始 fetch 完成
      Promise.resolve().then(() => refresh())
    }
    mountedCount += 1
  })
  onBeforeUnmount(() => {
    mountedCount = Math.max(0, mountedCount - 1)
  })
  return { overview, chapters, loading, lastError, refresh }
}
