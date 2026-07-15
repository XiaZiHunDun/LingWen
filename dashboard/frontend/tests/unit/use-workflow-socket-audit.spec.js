/**
 * Phase 9.62 F53: useWorkflowSocket audit.created handler tests
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

class MockWebSocket {
  constructor(url) {
    this.url = url;
    MockWebSocket.instances.push(this);
    this.readyState = 0;
    this._onopen = null;
    this._onmessage = null;
  }
  set onopen(fn) {
    this._onopen = fn;
    setTimeout(() => {
      this.readyState = 1;
      if (this._onopen) this._onopen({});
    }, 0);
  }
  set onmessage(fn) { this._onmessage = fn; }
  set onerror(fn) {}
  set onclose(fn) {}
  close() {}
  send() {}
  simulateMessage(data) {
    if (this._onmessage) this._onmessage({ data: JSON.stringify(data) });
  }
}
MockWebSocket.instances = [];
globalThis.WebSocket = MockWebSocket;

function createHarness(setupExtras) {
  return defineComponent({
    setup() {
      const m = globalThis.__wsModule;
      const { useWorkflowSocket, onAuditCreated } = m;
      useWorkflowSocket();
      if (setupExtras) setupExtras({ onAuditCreated });
      return () => h('div');
    },
  });
}

describe('useWorkflowSocket audit.created (Phase 9.62 F53)', () => {
  let wrapper;

  beforeEach(async () => {
    vi.resetModules();
    MockWebSocket.instances = [];
    globalThis.__wsModule = await import('../../src/composables/useWorkflowSocket.js');
  });

  afterEach(() => {
    wrapper?.unmount();
  });

  it('onAuditCreated receives audit.created payload', async () => {
    const received = [];
    const Harness = createHarness(({ onAuditCreated }) => {
      onAuditCreated((payload) => received.push(payload));
    });
    wrapper = mount(Harness);
    await nextTick();
    await new Promise((r) => setTimeout(r, 5));
    const ws = MockWebSocket.instances[0];
    expect(ws).toBeTruthy();
    ws.simulateMessage({
      type: 'audit.created',
      payload: { ripple_id: 'rip-x', action: 'applied', id: 9 },
    });
    expect(received).toHaveLength(1);
    expect(received[0].ripple_id).toBe('rip-x');
  });

  it('ignores audit.created without payload', async () => {
    const received = [];
    const Harness = createHarness(({ onAuditCreated }) => {
      onAuditCreated((payload) => received.push(payload));
    });
    wrapper = mount(Harness);
    await nextTick();
    await new Promise((r) => setTimeout(r, 5));
    MockWebSocket.instances[0].simulateMessage({ type: 'audit.created' });
    expect(received).toHaveLength(0);
  });

  it('onAuditCreated cleans up on unmount', async () => {
    const received = [];
    const Harness = createHarness(({ onAuditCreated }) => {
      onAuditCreated((payload) => received.push(payload));
    });
    wrapper = mount(Harness);
    await nextTick();
    await new Promise((r) => setTimeout(r, 5));
    wrapper.unmount();
    await nextTick();
    MockWebSocket.instances[0].simulateMessage({
      type: 'audit.created',
      payload: { ripple_id: 'rip-y', action: 'created', id: 1 },
    });
    expect(received).toHaveLength(0);
  });
});
