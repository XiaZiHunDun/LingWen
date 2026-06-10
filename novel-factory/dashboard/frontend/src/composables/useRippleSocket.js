// dashboard/frontend/src/composables/useRippleSocket.js — Phase 9.13
// Vue composable for CVG WebSocket subscription (跟 useWorkflowSocket 1:1 mirror)
// Module-level singleton state (Phase 8.11 baseline)

import { onBeforeUnmount, onMounted, ref } from 'vue';

const WS_PATH = '/api/ws/cvg';
const RECONNECT_BASE_MS = 1000;
const RECONNECT_FACTOR = 2;
const RECONNECT_MAX_MS = 8000;
const MAX_RECONNECT_ATTEMPTS = 3;

// ---- Module-level singleton state (跟 useWorkflowSocket 1:1) ----
const ws = ref(null);
const connected = ref(false);
const lastError = ref(null);
const pendingUpdates = ref([]);
const reconnectAttempts = ref(0);

let reconnectTimer = null;
let manuallyClosed = false;
let mountedCount = 0;

function buildWsUrl() {
  if (typeof window === 'undefined') return WS_PATH;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${WS_PATH}`;
}

function connect() {
  manuallyClosed = false;
  try {
    ws.value = new WebSocket(buildWsUrl());
  } catch (e) {
    lastError.value = e?.message || String(e);
    scheduleReconnect();
    return;
  }
  ws.value.onopen = () => {
    connected.value = true;
    lastError.value = null;
    reconnectAttempts.value = 0;
  };
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'ping') {
        ws.value.send(JSON.stringify({ type: 'pong' }));
        return;
      }
      pendingUpdates.value.push(data);
    } catch (e) {
      lastError.value = `parse error: ${e?.message || e}`;
    }
  };
  ws.value.onerror = () => { lastError.value = 'WebSocket error'; };
  ws.value.onclose = () => {
    connected.value = false;
    if (!manuallyClosed) scheduleReconnect();
  };
}

function scheduleReconnect() {
  if (reconnectTimer || reconnectAttempts.value >= MAX_RECONNECT_ATTEMPTS) return;
  const delay = Math.min(
    RECONNECT_BASE_MS * (RECONNECT_FACTOR ** reconnectAttempts.value),
    RECONNECT_MAX_MS,
  );
  reconnectAttempts.value += 1;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, delay);
}

function disconnect() {
  manuallyClosed = true;
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
  if (ws.value) {
    try { ws.value.close(); } catch { /* ignore */ }
    ws.value = null;
  }
  connected.value = false;
}

export function useRippleSocket() {
  onMounted(() => {
    if (mountedCount === 0) connect();
    mountedCount += 1;
  });
  onBeforeUnmount(() => {
    mountedCount = Math.max(0, mountedCount - 1);
    if (mountedCount === 0) disconnect();
  });
  return { ws, connected, lastError, pendingUpdates, reconnectAttempts, connect, disconnect };
}
