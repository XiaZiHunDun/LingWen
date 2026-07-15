// useDecisionStore.js — Phase 8.34 module-level singleton composable
// 管理 decision 全部历史 (REST 拉) + 4 个 mutation actions (refresh/resolve/defer/cancel)
// pending 仍走 useWorkflowSocket 推 (WS 权威源, Phase 6.4+ 契约, per 主公 Phase 8.34 决策)
// 镜像 useCostWindow 模式: module-level refs + mountedCount lifecycle
// 决策点 (主公 Phase 8.34): 首个 mount 时 deferred 1 microtask 后调 refresh() —
//   让 mount 后立即 sync 读 loading=false/all=[] 仍为真 (即 mount 不立即翻转 loading
//   状态), 但 await flushPromises 后能看到初始 fetch 完成. 后续 mutation (resolve/defer/
//   cancel) 内部 await refresh() 是 sync 触发 (用户期待 mutation 后立即看到新数据).

import { onBeforeUnmount, onMounted, ref } from 'vue'
import {
  fetchAllDecisions,
  resolveDecision,
  deferDecision,
  cancelDecision,
} from '../api/index.js'

const all = ref([])
const loading = ref(false)
const lastError = ref(null)
let mountedCount = 0

async function refresh() {
  loading.value = true
  lastError.value = null
  try {
    all.value = await fetchAllDecisions()
  } catch (e) {
    lastError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function resolve(decisionId, option) {
  try {
    await resolveDecision(decisionId, option)
    await refresh()
  } catch (e) {
    lastError.value = `解决失败: ${e?.message || e}`
    throw e
  }
}

async function defer(decisionId, reason) {
  try {
    await deferDecision(decisionId, reason)
    await refresh()
  } catch (e) {
    lastError.value = `推迟失败: ${e?.message || e}`
    throw e
  }
}

async function cancel(decisionId, reason) {
  try {
    await cancelDecision(decisionId, reason)
    await refresh()
  } catch (e) {
    lastError.value = `取消失败: ${e?.message || e}`
    throw e
  }
}

export function useDecisionStore() {
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
  return { all, loading, lastError, refresh, resolve, defer, cancel }
}
