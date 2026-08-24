import { onBeforeUnmount, onMounted, ref } from 'vue';
import { logger } from '../utils/logger.js';

const MAX_HANDLERS = 50;
const RECONNECT_DELAY_MS = 1000;
const HEARTBEAT_INTERVAL_MS = 30000;
const HEARTBEAT_TIMEOUT_MS = 45000;

const eventTypes = {
  WORKFLOW_STATUS: 'workflow.status',
  DECISION_SNAPSHOT: 'decision.snapshot',
  CASCADE_UPDATE: 'cascade.update',
  AUDIT_CREATED: 'audit.created',
  RIPPLE_UPDATE: 'ripple.update',
  WS_CONNECTED: 'ws.connected',
  WS_DISCONNECTED: 'ws.disconnected',
};

const registeredHandlers = {
  [eventTypes.WORKFLOW_STATUS]: new Set(),
  [eventTypes.DECISION_SNAPSHOT]: new Set(),
  [eventTypes.CASCADE_UPDATE]: new Set(),
  [eventTypes.AUDIT_CREATED]: new Set(),
  [eventTypes.RIPPLE_UPDATE]: new Set(),
  [eventTypes.WS_CONNECTED]: new Set(),
  [eventTypes.WS_DISCONNECTED]: new Set(),
};

const connections = {
  workflows: ref(false),
  cvg: ref(false),
};

const lastErrors = {
  workflows: ref(null),
  cvg: ref(null),
};

const workflowStatus = ref(null);
const pendingDecisions = ref([]);
const pendingUpdates = ref([]);
const latestCascadeUpdates = ref([]);

let wsWorkflows = null;
let wsCvg = null;
let reconnectTimerWorkflows = null;
let reconnectTimerCvg = null;
let heartbeatTimer = null;
let heartbeatTimeoutTimer = null;
let mountedCount = 0;

function buildWsUrl(path) {
  if (typeof window === 'undefined') return path;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${path}`;
}

function notifyHandlers(eventType, payload) {
  const handlers = registeredHandlers[eventType];
  if (!handlers) return;
  handlers.forEach((handler) => {
    try {
      handler(payload);
    } catch (e) {
      logger.warn(`[useEventBus] Handler error for ${eventType}:`, e);
    }
  });
}

function connectWorkflows() {
  if (wsWorkflows) return;
  try {
    wsWorkflows = new WebSocket(buildWsUrl('/api/ws/workflows'));
  } catch (e) {
    lastErrors.workflows.value = e?.message || String(e);
    scheduleReconnect('workflows');
    return;
  }

  wsWorkflows.onopen = () => {
    connections.workflows.value = true;
    lastErrors.workflows.value = null;
    notifyHandlers(eventTypes.WS_CONNECTED, { connection: 'workflows' });
    startHeartbeat();
  };

  wsWorkflows.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'connected') {
        if (data.snapshot) {
          workflowStatus.value = data.snapshot;
          notifyHandlers(eventTypes.WORKFLOW_STATUS, data.snapshot);
        }
        if (Array.isArray(data.pending_decisions)) {
          pendingDecisions.value = data.pending_decisions;
          notifyHandlers(eventTypes.DECISION_SNAPSHOT, data.pending_decisions);
        }
      } else if (data.type === 'workflow.status' && data.payload) {
        workflowStatus.value = data.payload;
        notifyHandlers(eventTypes.WORKFLOW_STATUS, data.payload);
      } else if (data.type === 'decision.snapshot' && Array.isArray(data.payload)) {
        pendingDecisions.value = data.payload;
        notifyHandlers(eventTypes.DECISION_SNAPSHOT, data.payload);
      } else if (data.type === 'cascade.update' && data.payload) {
        latestCascadeUpdates.value = [...latestCascadeUpdates.value, data.payload].slice(-10);
        notifyHandlers(eventTypes.CASCADE_UPDATE, data.payload);
      } else if (data.type === 'audit.created' && data.payload) {
        notifyHandlers(eventTypes.AUDIT_CREATED, data.payload);
      } else if (data.type === 'heartbeat') {
        resetHeartbeatTimeout();
      }
    } catch (e) {
      lastErrors.workflows.value = `parse error: ${e?.message || e}`;
    }
  };

  wsWorkflows.onerror = () => {
    lastErrors.workflows.value = 'WebSocket error';
  };

  wsWorkflows.onclose = () => {
    connections.workflows.value = false;
    wsWorkflows = null;
    notifyHandlers(eventTypes.WS_DISCONNECTED, { connection: 'workflows' });
    scheduleReconnect('workflows');
  };
}

function connectCvg() {
  if (wsCvg) return;
  try {
    wsCvg = new WebSocket(buildWsUrl('/api/ws/cvg'));
  } catch (e) {
    lastErrors.cvg.value = e?.message || String(e);
    scheduleReconnect('cvg');
    return;
  }

  wsCvg.onopen = () => {
    connections.cvg.value = true;
    lastErrors.cvg.value = null;
    notifyHandlers(eventTypes.WS_CONNECTED, { connection: 'cvg' });
  };

  wsCvg.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'ping') {
        wsCvg.send(JSON.stringify({ type: 'pong' }));
        return;
      }
      pendingUpdates.value.push(data);
      notifyHandlers(eventTypes.RIPPLE_UPDATE, data);
    } catch (e) {
      lastErrors.cvg.value = `parse error: ${e?.message || e}`;
    }
  };

  wsCvg.onerror = () => {
    lastErrors.cvg.value = 'WebSocket error';
  };

  wsCvg.onclose = () => {
    connections.cvg.value = false;
    wsCvg = null;
    notifyHandlers(eventTypes.WS_DISCONNECTED, { connection: 'cvg' });
    scheduleReconnect('cvg');
  };
}

function scheduleReconnect(connectionType) {
  if (connectionType === 'workflows') {
    if (reconnectTimerWorkflows) return;
    reconnectTimerWorkflows = setTimeout(() => {
      reconnectTimerWorkflows = null;
      connectWorkflows();
    }, RECONNECT_DELAY_MS);
  } else {
    if (reconnectTimerCvg) return;
    reconnectTimerCvg = setTimeout(() => {
      reconnectTimerCvg = null;
      connectCvg();
    }, RECONNECT_DELAY_MS);
  }
}

function disconnectWorkflows() {
  if (reconnectTimerWorkflows) {
    clearTimeout(reconnectTimerWorkflows);
    reconnectTimerWorkflows = null;
  }
  if (wsWorkflows) {
    try {
      wsWorkflows.close();
    } catch {
      // ignore
    }
    wsWorkflows = null;
  }
  connections.workflows.value = false;
}

function disconnectCvg() {
  if (reconnectTimerCvg) {
    clearTimeout(reconnectTimerCvg);
    reconnectTimerCvg = null;
  }
  if (wsCvg) {
    try {
      wsCvg.close();
    } catch {
      // ignore
    }
    wsCvg = null;
  }
  connections.cvg.value = false;
}

function startHeartbeat() {
  stopHeartbeat();
  heartbeatTimer = setInterval(() => {
    if (wsWorkflows && wsWorkflows.readyState === WebSocket.OPEN) {
      try {
        wsWorkflows.send('ping');
      } catch (e) {
        logger.warn('[useEventBus] Failed to send heartbeat:', e);
        stopHeartbeat();
        scheduleReconnect('workflows');
      }
    }
  }, HEARTBEAT_INTERVAL_MS);
  resetHeartbeatTimeout();
}

function resetHeartbeatTimeout() {
  if (heartbeatTimeoutTimer) {
    clearTimeout(heartbeatTimeoutTimer);
  }
  heartbeatTimeoutTimer = setTimeout(() => {
    logger.warn('[useEventBus] Heartbeat timeout, reconnecting');
    stopHeartbeat();
    disconnectWorkflows();
    scheduleReconnect('workflows');
  }, HEARTBEAT_TIMEOUT_MS);
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
  if (heartbeatTimeoutTimer) {
    clearTimeout(heartbeatTimeoutTimer);
    heartbeatTimeoutTimer = null;
  }
}

function subscribe(eventType, handler) {
  const handlers = registeredHandlers[eventType];
  if (!handlers) {
    logger.warn(`[useEventBus] Unknown event type: ${eventType}`);
    return;
  }
  if (handlers.size >= MAX_HANDLERS) {
    logger.warn(`[useEventBus] MAX_HANDLERS=${MAX_HANDLERS} reached for ${eventType}`);
    return;
  }
  handlers.add(handler);
  return () => {
    handlers.delete(handler);
  };
}

function unsubscribe(eventType, handler) {
  const handlers = registeredHandlers[eventType];
  if (handlers) {
    handlers.delete(handler);
  }
}

export function useEventBus() {
  onMounted(() => {
    if (mountedCount === 0) {
      connectWorkflows();
      connectCvg();
    }
    mountedCount += 1;
  });

  onBeforeUnmount(() => {
    mountedCount = Math.max(0, mountedCount - 1);
    if (mountedCount === 0) {
      stopHeartbeat();
      disconnectWorkflows();
      disconnectCvg();
    }
  });

  return {
    connections,
    lastErrors,
    workflowStatus,
    pendingDecisions,
    pendingUpdates,
    latestCascadeUpdates,
    subscribe,
    unsubscribe,
    eventTypes,
    reconnectWorkflows: connectWorkflows,
    reconnectCvg: connectCvg,
  };
}

export function onCascadeUpdate(handler) {
  const unsubscribeFn = subscribe(eventTypes.CASCADE_UPDATE, handler);
  onBeforeUnmount(() => {
    unsubscribeFn();
  });
}

export function onAuditCreated(handler) {
  const unsubscribeFn = subscribe(eventTypes.AUDIT_CREATED, handler);
  onBeforeUnmount(() => {
    unsubscribeFn();
  });
}

export function onRippleUpdate(handler) {
  const unsubscribeFn = subscribe(eventTypes.RIPPLE_UPDATE, handler);
  onBeforeUnmount(() => {
    unsubscribeFn();
  });
}
