/**
 * useWorkflowSocket.js — Vue composable for WebSocket workflow subscription (Phase 6.4 + 8.11)
 *
 * 替换 WorkflowsPage 的 2s 轮询为实时推送。
 *
 * 用法:
 *   const { status, pendingDecisions, connected } = useWorkflowSocket();
 *
 * 自动:
 * - 首个调用者 mount 时建立 WS 连接
 * - 最后一个调用者 unmount 时断开
 * - close 时 1s 后重连
 * - 中间 mount/unmount 仅递增/递减引用计数,共享同一 WS
 *
 * 事件:
 * - connected (initial): { type, snapshot: <workflow>, pending_decisions: <list> }
 * - workflow.status: { type, payload: <workflow> }
 * - decision.snapshot: { type, payload: <pending list> }
 * - cascade.update (Phase 9.16): { type, payload: { ripple_id, cascade_node_count,
 *     cascade_edge_count, depth_reached, bfs_algorithm_version } }
 *
 * Phase 8.11: 重构为 module-level singleton state — App.vue 和 WorkflowsPage.vue
 * 同时调用此 composable 时,共享同一 WebSocket 连接和同一组 status/connected/
 * pendingDecisions refs,避免 2 个独立连接 / 2 个独立 ref 漂移。
 *
 * Phase 9.16: 加 cascade.update event 分支 + latestCascadeUpdates ref +
 *   onCascadeUpdate(handler) API, RippleDrawer 调 onCascadeUpdate 静默 re-fetch.
 */

import { onBeforeUnmount, onMounted, ref } from 'vue';

const WS_PATH = '/api/ws/workflows';
const RECONNECT_DELAY_MS = 1000;

// ---- Module-level singleton state (Phase 8.11) ----
const status = ref(null);
const pendingDecisions = ref([]);
const connected = ref(false);
const lastError = ref(null);
// Phase 9.16: cascade.update event 累积 (slice -10 防内存)
const latestCascadeUpdates = ref([]);

let ws = null;
let reconnectTimer = null;
let manuallyClosed = false;
let mountedCount = 0;

// Phase 9.16: registered handlers registry (跟 Phase 6.4 / 8.11 模式 1:1)
// 供 onCascadeUpdate 等 API 注册 callback, 0 改 module-level 既有 status/pendingDecisions
const registeredHandlers = {
  cascade: new Set(),
};

function buildWsUrl() {
  // 同源,后端在 8765 端口 → ws://host:8765/api/ws/workflows
  if (typeof window === 'undefined') return WS_PATH;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${WS_PATH}`;
}

function connect() {
  manuallyClosed = false;
  try {
    ws = new WebSocket(buildWsUrl());
  } catch (e) {
    lastError.value = e?.message || String(e);
    scheduleReconnect();
    return;
  }

  ws.onopen = () => {
    connected.value = true;
    lastError.value = null;
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'connected') {
        if (data.snapshot) status.value = data.snapshot;
        if (Array.isArray(data.pending_decisions)) {
          pendingDecisions.value = data.pending_decisions;
        }
      } else if (data.type === 'workflow.status' && data.payload) {
        status.value = data.payload;
      } else if (data.type === 'decision.snapshot' && Array.isArray(data.payload)) {
        pendingDecisions.value = data.payload;
      } else if (data.type === 'cascade.update' && data.payload) {
        // Phase 9.16: append + slice -10 防内存累积 + 通知 cascade handlers
        latestCascadeUpdates.value = [...latestCascadeUpdates.value, data.payload].slice(-10);
        registeredHandlers.cascade.forEach((h) => {
          try { h(data.payload); } catch (_) { /* best-effort */ }
        });
      }
    } catch (e) {
      lastError.value = `parse error: ${e?.message || e}`;
    }
  };

  ws.onerror = () => {
    lastError.value = 'WebSocket error';
  };

  ws.onclose = () => {
    connected.value = false;
    ws = null;
    if (!manuallyClosed) {
      scheduleReconnect();
    }
  };
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, RECONNECT_DELAY_MS);
}

function disconnect() {
  manuallyClosed = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    try {
      ws.close();
    } catch {
      // ignore
    }
    ws = null;
  }
  connected.value = false;
}

function sendKeepAlive() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    try {
      ws.send('ping');
    } catch {
      // ignore
    }
  }
}

export function useWorkflowSocket() {
  onMounted(() => {
    if (mountedCount === 0) {
      connect();
    }
    mountedCount += 1;
  });

  onBeforeUnmount(() => {
    mountedCount = Math.max(0, mountedCount - 1);
    if (mountedCount === 0) {
      disconnect();
    }
  });

  return {
    status,
    pendingDecisions,
    connected,
    lastError,
    latestCascadeUpdates,  // Phase 9.16
    sendKeepAlive,
    reconnect: connect,
  };
}

// Phase 9.16: cascade handler 注册 API (Set 自动去重; onBeforeUnmount 自动 cleanup)
export function onCascadeUpdate(handler) {
  registeredHandlers.cascade.add(handler);
  // Phase 9.16: dev-only test affordance — 暴露 __cascadeHandlers 给 e2e page.evaluate
  // 仅在 dev mode 注入, prod build 0 影响 (import.meta.env.DEV=false 时 stub 掉).
  if (typeof window !== 'undefined' && import.meta.env && import.meta.env.DEV) {
    if (!window.__cascadeHandlers) window.__cascadeHandlers = [];
    if (!window.__cascadeHandlers.includes(handler)) window.__cascadeHandlers.push(handler);
  }
  onBeforeUnmount(() => {
    registeredHandlers.cascade.delete(handler);
    if (typeof window !== 'undefined' && window.__cascadeHandlers) {
      const i = window.__cascadeHandlers.indexOf(handler);
      if (i >= 0) window.__cascadeHandlers.splice(i, 1);
    }
  });
}
