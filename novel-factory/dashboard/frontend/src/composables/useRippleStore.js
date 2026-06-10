// useRippleStore.js — Phase 9.13 module-level singleton composable
// 管理 ripple 列表 + 统计 + 4 个 mutation actions (refresh/apply/reject/applySocketUpdate)
// 镜像 useDecisionStore 模式: module-level refs + mountedCount lifecycle
// ripple_created / ripple_status_changed 走 WS 推 (WS 权威源, per 主公 Phase 9.13 决策)
// 决策点 (跟 useDecisionStore 1:1): 首个 mount 时 deferred 1 microtask 后调 refresh() —
//   让 mount 后立即 sync 读 loading=false/ripples=[] 仍为真 (即 mount 不立即翻转 loading
//   状态), 但 await flushPromises 后能看到初始 fetch 完成. 后续 mutation (apply/reject)
//   内部用 optimistic update (不 await refresh, 用户期待 mutation 后立即看到新数据).

import { onBeforeUnmount, onMounted, ref } from 'vue'
import {
  fetchRipples,
  fetchRippleStats,
  applyRipple,
  rejectRipple,
  fetchRippleAudit,
  rollbackRipple,
} from '../api/index.js'

const ripples = ref([])
const loading = ref(false)
const lastError = ref(null)
const stats = ref({ total: 0, by_status: {}, by_volume: {} })
let mountedCount = 0

async function refresh(filters = {}) {
  loading.value = true
  lastError.value = null
  try {
    const params = new URLSearchParams()
    if (filters.status) params.set('status', filters.status)
    if (filters.volume) params.set('volume', String(filters.volume))
    ripples.value = await fetchRipples(params)
    stats.value = await fetchRippleStats()
  } catch (e) {
    lastError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function apply(rippleId) {
  try {
    const updated = await applyRipple(rippleId)
    const idx = ripples.value.findIndex((r) => r.ripple_id === rippleId)
    if (idx >= 0) {
      // immutable update via spread (跟 useDecisionStore 1:1 模式)
      ripples.value = [
        ...ripples.value.slice(0, idx),
        { ...ripples.value[idx], status: updated.status },
        ...ripples.value.slice(idx + 1),
      ]
    }
    return updated
  } catch (e) {
    lastError.value = `apply 失败: ${e?.message || e}`
    throw e
  }
}

async function reject(rippleId, reason = '') {
  try {
    const updated = await rejectRipple(rippleId, reason)
    const idx = ripples.value.findIndex((r) => r.ripple_id === rippleId)
    if (idx >= 0) {
      // immutable update via spread (跟 useDecisionStore 1:1 模式)
      ripples.value = [
        ...ripples.value.slice(0, idx),
        { ...ripples.value[idx], status: updated.status },
        ...ripples.value.slice(idx + 1),
      ]
    }
    return updated
  } catch (e) {
    lastError.value = `reject 失败: ${e?.message || e}`
    throw e
  }
}

function applySocketUpdate(update) {
  if (update.type === 'ripple_created' && update.data) {
    ripples.value = [update.data, ...ripples.value]
  } else if (update.type === 'ripple_status_changed' && update.data) {
    const idx = ripples.value.findIndex((r) => r.ripple_id === update.data.ripple_id)
    if (idx >= 0) {
      ripples.value = [
        ...ripples.value.slice(0, idx),
        { ...ripples.value[idx], status: update.data.new_status },
        ...ripples.value.slice(idx + 1),
      ]
    }
  }
}

async function fetchAudit(rippleId) {
  lastError.value = null
  try {
    const data = await fetchRippleAudit(rippleId)
    return data
  } catch (e) {
    lastError.value = e?.message || String(e)
    throw e
  }
}

async function rollback(rippleId, reason) {
  // Optimistic: snapshot before mutate (跟 apply/reject 1:1 immutable update 模式)
  const idx = ripples.value.findIndex((r) => r.ripple_id === rippleId)
  if (idx < 0) {
    throw new Error(`ripple ${rippleId} not in store`)
  }
  const snapshot = ripples.value[idx]
  try {
    const updated = await rollbackRipple(rippleId, reason)
    // Apply server response (authoritative) — immutable spread 跟 apply/reject 1:1
    if (idx >= 0) {
      ripples.value = [
        ...ripples.value.slice(0, idx),
        { ...ripples.value[idx], ...updated },
        ...ripples.value.slice(idx + 1),
      ]
    }
    return updated
  } catch (e) {
    // Rollback optimistic mutation: 恢复 snapshot
    if (idx >= 0) {
      ripples.value = [
        ...ripples.value.slice(0, idx),
        snapshot,
        ...ripples.value.slice(idx + 1),
      ]
    }
    lastError.value = e?.message || String(e)
    throw e
  }
}

export function useRippleStore() {
  onMounted(() => {
    if (mountedCount === 0) {
      // microtask defer 跟 useDecisionStore 1:1 pattern
      Promise.resolve().then(() => refresh())
    }
    mountedCount += 1
  })
  onBeforeUnmount(() => {
    mountedCount = Math.max(0, mountedCount - 1)
  })
  return {
    ripples, loading, lastError, stats,
    refresh, apply, reject, applySocketUpdate,  // 既有 0 改
    fetchAudit, rollback,                        // Phase 9.14 新增
  }
}
