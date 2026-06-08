/**
 * useCostWindow.js — 时间窗口成本 composable (Phase 8.16 + 8.18)
 *
 * Mirror useWorkflowSocket.js module-level singleton pattern.
 * 拉 /api/workflows/active?time_window=X 拿 windowed cost, 跟 WS-pushed
 * status (含全量 cost) 共存但不冲突 — 本 composable 维护独立的 windowedCost,
 * 2 cost-displaying component (WorkflowStatus + SidebarCostBanner) 读 windowedCost
 * 覆盖 WS status.cost_* 字段.
 *
 * 用法:
 *   const { timeWindow, windowedCost, setTimeWindow } = useCostWindow();
 *   setTimeWindow('7d')  // → 自动 re-fetch + 同步写 URL ?time_window=7d
 *   <button @click="setTimeWindow('7d')" :class="{active: timeWindow === '7d'}">7天</button>
 *
 * 自动:
 * - 首个 mount → 立即 fetch + 启动 5s 轮询
 * - 最后一个 unmount → 停止轮询
 * - timeWindow 变 → 立即 re-fetch
 * - Phase 8.18: URL ?time_window=X ↔ timeWindow 双向同步 (replaceState, 非 push,
 *   back/forward 不循环 window; 默认 'all' 删 param 保持 URL 干净)
 *
 * 状态:
 * - timeWindow: ref<'7d'|'30d'|'all'> 默认 'all' 保 backward compat
 *   (Phase 8.18: 初始化时读 URL ?time_window=X 覆盖, refresh 保留选择)
 * - windowedCost: ref<{cost_by_scenario, cost_by_tier, total_cost_usd}|null> 默认 null
 *   (null 时 component fallback 到 useWorkflowSocket status.cost_*)
 */

import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

const VALID_WINDOWS = ['7d', '30d', 'all'];
const POLL_INTERVAL_MS = 5000;

// ---- Module-level singleton state ----
const timeWindow = ref('all');
const windowedCost = ref(null);
const loading = ref(false);
const lastError = ref(null);

let pollTimer = null;
let mountedCount = 0;

async function fetchCost() {
  if (timeWindow.value === 'all') {
    // "all" 不需要 fetch — component 读 WS status.cost_* (default path)
    windowedCost.value = null;
    return;
  }
  loading.value = true;
  lastError.value = null;
  try {
    const url = new URL('/api/workflows/active', window.location.origin);
    url.searchParams.set('time_window', timeWindow.value);
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    windowedCost.value = {
      cost_by_scenario: data.cost_by_scenario || {},
      cost_by_tier: data.cost_by_tier || {},
      total_cost_usd: data.total_cost_usd || 0.0,
    };
  } catch (e) {
    lastError.value = e?.message || String(e);
    // Silent degrade: 保留旧 windowedCost (避免 race 闪空)
  } finally {
    loading.value = false;
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(fetchCost, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

// ---- Phase 8.18: URL state persistence (?time_window=X ↔ timeWindow) ----
// 用 vanilla history.replaceState (0 dep, 不用 Vue Router). 首次 import 读 URL
// 覆盖 timeWindow 默认 'all' (refresh 保留选择, shareable link 生效). setTimeWindow
// 同步写 URL — 默认 'all' 删 param 保持 URL 干净, 7d/30d 写 param.
const URL_QUERY_KEY = 'time_window';

function _initFromUrl() {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams(window.location.search);
  const w = params.get(URL_QUERY_KEY);
  if (w && VALID_WINDOWS.includes(w)) {
    timeWindow.value = w;
  }
}
_initFromUrl();

function _writeToUrl(w) {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  if (w === 'all') {
    url.searchParams.delete(URL_QUERY_KEY);
  } else {
    url.searchParams.set(URL_QUERY_KEY, w);
  }
  window.history.replaceState(null, '', url.toString());
}

export function useCostWindow() {
  onMounted(() => {
    if (mountedCount === 0) {
      fetchCost();  // 立即 fetch
      startPolling();
    }
    mountedCount += 1;
    // timeWindow 变 → re-fetch (immediate, 不等下一个 poll tick)
    watch(timeWindow, () => fetchCost());
  });

  onBeforeUnmount(() => {
    mountedCount = Math.max(0, mountedCount - 1);
    if (mountedCount === 0) {
      stopPolling();
    }
  });

  return {
    timeWindow,
    windowedCost,
    loading,
    lastError,
    setTimeWindow: (w) => {
      if (VALID_WINDOWS.includes(w)) {
        timeWindow.value = w;
        _writeToUrl(w);  // Phase 8.18: 同步写 URL (replaceState, 非 push)
      }
    },
  };
}
