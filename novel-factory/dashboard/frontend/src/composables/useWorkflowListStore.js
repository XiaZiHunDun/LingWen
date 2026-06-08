// useWorkflowListStore.js — Phase 8.34 module-level singleton composable
// 管理 workflows 列表 (REST 拉) + refresh action
// 比 useDecisionStore 简单: 无 mutation (workflow 启动/停止/状态走 useWorkflowSocket WS 推,
// Phase 6.4+ 契约, per 主公 Phase 8.34 决策)
// 镜像 useCostWindow 模式: module-level refs + mountedCount lifecycle
// 决策点 (主公 Phase 8.34): 首个 mount 时 deferred 1 microtask 后调 refresh() —
//   让 mount() 同步快照仍是默认值 (workflows=[]/loading=false), 但 await flushPromises
//   后能看到初始 fetch 完成. 后续 mutation 不存在, refresh 由 useWorkflowSocket WS 推
//   触发或用户主动调用.

import { onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchWorkflows } from '../api/index.js'

const workflows = ref([])
const loading = ref(false)
const lastError = ref(null)
let mountedCount = 0

async function refresh() {
  loading.value = true
  lastError.value = null
  try {
    workflows.value = await fetchWorkflows()
  } catch (e) {
    lastError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

export function useWorkflowListStore() {
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
  return { workflows, loading, lastError, refresh }
}
