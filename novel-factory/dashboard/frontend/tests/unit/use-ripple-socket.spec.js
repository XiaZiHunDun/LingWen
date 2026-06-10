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
    // Verify timer is scheduled with 1000ms delay (first attempt)
    expect(vi.getTimerCount()).toBe(1);
    // Advance exactly the expected first-attempt delay (1000ms)
    vi.advanceTimersByTime(1000);
    // After first reconnect attempt fires, ws is a new socket instance
    expect(socket.ws.value).toBeInstanceOf(MockWebSocket);
    // MockWebSocket does not auto-fire onopen, so reconnectAttempts stays at 1
    // until the next onclose triggers another scheduleReconnect.
    expect(socket.reconnectAttempts.value).toBe(1);
    // Simulate second close: scheduleReconnect increments to 2 with 2000ms delay
    socket.ws.value.onclose({});
    expect(socket.reconnectAttempts.value).toBe(2);
    vi.advanceTimersByTime(2000);
    // After second timer fires, ws is again a new instance
    expect(socket.ws.value).toBeInstanceOf(MockWebSocket);
    // Third close: scheduleReconnect increments to 3 with 4000ms delay
    socket.ws.value.onclose({});
    expect(socket.reconnectAttempts.value).toBe(3);
    vi.advanceTimersByTime(4000);
    // Third reconnect fires, ws is a new instance
    expect(socket.ws.value).toBeInstanceOf(MockWebSocket);
    // Fourth close: cap kicks in (3 >= MAX_RECONNECT_ATTEMPTS=3),
    // no further reconnect timer should be scheduled
    socket.ws.value.onclose({});
    expect(socket.reconnectAttempts.value).toBe(3);
    expect(vi.getTimerCount()).toBe(0);
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
