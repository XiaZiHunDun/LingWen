/**
 * useWorkflowSocket.js — Vue composable for WebSocket workflow subscription (Phase 6.4)
 *
 * 替换 WorkflowsPage 的 2s 轮询为实时推送。
 *
 * 用法:
 *   const { status, pendingDecisions, connected } = useWorkflowSocket();
 *
 * 自动:
 * - mount 时建立 WS 连接
 * - close 时 1s 后重连
 * - unmount 时断开
 *
 * 事件:
 * - connected (initial): { type, snapshot: <workflow>, pending_decisions: <list> }
 * - workflow.status: { type, payload: <workflow> }
 * - decision.snapshot: { type, payload: <pending list> }
 */

import { onBeforeUnmount, onMounted, ref } from 'vue';

const WS_PATH = '/api/ws/workflows';
const RECONNECT_DELAY_MS = 1000;

function buildWsUrl() {
  // 同源,后端在 8765 端口 → ws://host:8765/api/ws/workflows
  if (typeof window === 'undefined') return WS_PATH;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${WS_PATH}`;
}

export function useWorkflowSocket() {
  const status = ref(null);
  const pendingDecisions = ref([]);
  const connected = ref(false);
  const lastError = ref(null);

  let ws = null;
  let reconnectTimer = null;
  let manuallyClosed = false;

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

  onMounted(connect);
  onBeforeUnmount(disconnect);

  return {
    status,
    pendingDecisions,
    connected,
    lastError,
    sendKeepAlive,
    reconnect: connect,
  };
}
