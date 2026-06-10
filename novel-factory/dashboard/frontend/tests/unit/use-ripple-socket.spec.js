// dashboard/frontend/tests/unit/use-ripple-socket.spec.js — Phase 9.13
import { describe, it, expect, beforeEach, vi } from 'vitest';

class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this.sent = [];
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
  }
  send(data) { this.sent.push(data); }
  close() {
    this.readyState = 3;
    if (this.onclose) this.onclose({});
  }
}

global.WebSocket = MockWebSocket;

describe('useRippleSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('connect opens WebSocket to /api/ws/cvg', async () => {
    const { useRippleSocket } = await import('../../src/composables/useRippleSocket.js');
    const socket = useRippleSocket();
    socket.connect();
    expect(socket.ws.value).toBeInstanceOf(MockWebSocket);
    expect(socket.ws.value.url).toContain('/api/ws/cvg');
  });

  it('onmessage pushes update to pendingUpdates', async () => {
    const { useRippleSocket } = await import('../../src/composables/useRippleSocket.js');
    const socket = useRippleSocket();
    socket.connect();
    socket.ws.value.onmessage({ data: JSON.stringify({ type: 'ripple_created', data: { ripple_id: 'r1' } }) });
    expect(socket.pendingUpdates.value).toHaveLength(1);
    expect(socket.pendingUpdates.value[0].type).toBe('ripple_created');
  });

  it('onmessage handles ping → reply pong', async () => {
    const { useRippleSocket } = await import('../../src/composables/useRippleSocket.js');
    const socket = useRippleSocket();
    socket.connect();
    socket.ws.value.onmessage({ data: JSON.stringify({ type: 'ping' }) });
    expect(socket.ws.value.sent).toContain(JSON.stringify({ type: 'pong' }));
  });

  it('onclose schedules exponential backoff reconnect (max 3 attempts)', async () => {
    const { useRippleSocket } = await import('../../src/composables/useRippleSocket.js');
    const socket = useRippleSocket();
    socket.connect();
    socket.ws.value.onclose({});
    expect(socket.connected.value).toBe(false);
    expect(socket.reconnectAttempts.value).toBe(1);
  });

  it('disconnect closes the WebSocket', async () => {
    const { useRippleSocket } = await import('../../src/composables/useRippleSocket.js');
    const socket = useRippleSocket();
    socket.connect();
    const ws = socket.ws.value;
    socket.disconnect();
    expect(ws.readyState).toBe(3);
  });
});
