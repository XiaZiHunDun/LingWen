/**
 * 获取 ripple 列表 + 统计 + mutation actions。
 *
 * @returns {{
 *   ripples: Array, loading: boolean, lastError: string|null,
 *   stats: Object, cascadeByRippleId: Map, previewByRippleId: Map,
 *   refresh: Function, apply: Function, reject: Function,
 *   applySocketUpdate: Function, fetchAudit: Function, rollback: Function,
 *   loadCascade: Function, loadCascadePreview: Function
 * }}
 * 注意：返回的属性是 ref 在 reactive context 中已自动解包，不需要 .value。
 */

import { onBeforeUnmount, onMounted, ref } from 'vue'
// Phase 126 v16.2.8 T3.A: migrate to typed wrapper (per v16.2.1 convention).
import {
  fetchRipples,
  fetchRippleStats,
  applyRipple,
  rejectRipple,
  fetchRippleAudit,
  rollbackRipple,
  fetchRippleCascade,     // Phase 9.15
  fetchRipplePreview,     // Phase 9.15
} from '@/api/cvg'
import { logger } from '../utils/logger.js'

const ripples = ref([])
const loading = ref(false)
const lastError = ref(null)
const stats = ref({ total: 0, by_status: {}, by_volume: {} })
const cascadeByRippleId = ref(new Map())  // Phase 9.15
const previewByRippleId = ref(new Map())  // Phase 9.15
let mountedCount = 0

async function refresh(filters = {}) {
  loading.value = true
  lastError.value = null
  try {
    const params = new URLSearchParams()
    if (filters.status) params.set('status', filters.status)
    if (filters.volume) params.set('volume', String(filters.volume))
    if (filters.sort_by) params.set('sort_by', filters.sort_by)
    if (filters.min_score != null) params.set('min_score', String(filters.min_score))
    ripples.value = await fetchRipples(params)
  } catch (e) {
    lastError.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
  fetchRippleStats()
    .then((s) => { stats.value = s })
    .catch((err) => { logger.warn('fetchRippleStats failed in refresh', err); })
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
    // audit is read-only (no mutation risk), use raw error message unlike apply/reject wrap
    lastError.value = e?.message || String(e)
    throw e
  }
}

async function rollback(rippleId, reason) {
  // Optimistic: snapshot before mutate (跟 apply/reject 1:1 immutable update 模式)
  const idx = ripples.value.findIndex((r) => r.ripple_id === rippleId)
  const snapshot = idx >= 0 ? ripples.value[idx] : null
  try {
    if (idx < 0) {
      throw new Error(`ripple ${rippleId} not in store`)
    }
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
    // Rollback optimistic mutation: 恢复 snapshot (only if we had a valid snapshot)
    if (idx >= 0 && snapshot) {
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

// === Phase 9.15: cascade BFS + dry-run preview actions ===

async function loadCascade(rippleId) {
  lastError.value = null
  try {
    const data = await fetchRippleCascade(rippleId)
    cascadeByRippleId.value.set(rippleId, data)
    return data
  } catch (e) {
    lastError.value = e?.message || String(e)
    throw e
  }
}

async function loadCascadePreview(rippleId) {
  lastError.value = null
  try {
    const data = await fetchRipplePreview(rippleId)
    previewByRippleId.value.set(rippleId, data)
    return data
  } catch (e) {
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
    loadCascade, loadCascadePreview,             // Phase 9.15 新增
    cascadeByRippleId, previewByRippleId,        // Phase 9.15 新增
  }
}
