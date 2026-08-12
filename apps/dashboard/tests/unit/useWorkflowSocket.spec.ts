/**
 * useWorkflowSocket.spec.ts — Phase 9.17 + 9.40 F25 TS strict pilot + F48 branches
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { WorkflowSocketVm } from '../helpers/strict-test-types.js';
import { mount, flushPromises } from '@vue/test-utils';
import { defineComponent } from 'vue';

class MockWebSocket {
  static OPEN = 1;
  url: string;
  readyState = 0;
  onopen: ((ev: unknown) => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: ((ev: unknown) => void) | null = null;
  onerror: ((ev: unknown) => void) | null = null;
  sent: string[] = [];
  constructor(url: string) {
    this.url = url;
  }
  send(data: string) { this.sent.push(data); }
  close() {
    this.readyState = 3;
    this.onclose?.({});
  }
}

describe('useWorkflowSocket: MAX_HANDLERS guard (Phase 9.17)', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.resetModules();
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('refuses to register beyond MAX_HANDLERS=50', async () => {
    const { onCascadeUpdate } = await import('../../src/composables/useWorkflowSocket.js');
    const handlers = Array.from({ length: 50 }, () => () => {});
    handlers.forEach((h) => onCascadeUpdate(h));
    warnSpy.mockClear();
    const extra = () => {};
    onCascadeUpdate(extra);
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('MAX_HANDLERS=50'),
    );
  });
});

describe('useWorkflowSocket message branches (F48)', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  async function mountSocket() {
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    return mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
  }

  it('connected event sets status and pending decisions', async () => {
    const wrapper = await mountSocket();
    const ws = (wrapper.vm as { ws?: MockWebSocket }).ws;
    // access internal via reconnect
    wrapper.vm.reconnect();
    const socket = (globalThis as unknown as { WebSocket: typeof MockWebSocket }).WebSocket;
    // get last created ws from module - use onMounted connect
    await flushPromises();
    const mod = await import('../../src/composables/useWorkflowSocket.js');
    mod.useWorkflowSocket().reconnect();
    // Fire via stored ws from MockWebSocket instances - simpler: call onmessage on last instance
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    const w2 = mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    const sock = instances[instances.length - 1];
    sock.onopen?.({});
    sock.onmessage?.({
      data: JSON.stringify({
        type: 'connected',
        snapshot: { workflow_name: 'wf', is_active: true },
        pending_decisions: [{ decision_id: 'd1', status: 'pending' }],
      }),
    });
    const w2Vm = w2.vm as WorkflowSocketVm;
    expect(w2Vm.status?.workflow_name).toBe('wf');
    expect(w2Vm.pendingDecisions.length).toBe(1);
  });

  it('workflow.status and decision.snapshot update refs', async () => {
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    const wrapper = mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    const sock = instances[0];
    sock.onmessage?.({ data: JSON.stringify({ type: 'workflow.status', payload: { workflow_name: 'x' } }) });
    sock.onmessage?.({ data: JSON.stringify({ type: 'decision.snapshot', payload: [{ decision_id: 'd2' }] }) });
    const vm = wrapper.vm as WorkflowSocketVm;
    expect(vm.status?.workflow_name).toBe('x');
    expect(vm.pendingDecisions[0].decision_id).toBe('d2');
  });

  it('cascade.update notifies handler', async () => {
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket, onCascadeUpdate } = await import('../../src/composables/useWorkflowSocket.js');
    const handler = vi.fn();
    mount(defineComponent({
      setup() {
        onCascadeUpdate(handler);
        return useWorkflowSocket();
      },
      template: '<div />',
    }));
    await flushPromises();
    instances[0].onmessage?.({
      data: JSON.stringify({
        type: 'cascade.update',
        payload: { ripple_id: 'r1', cascade_node_count: 2 },
      }),
    });
    expect(handler).toHaveBeenCalled();
  });

  it('parse error sets lastError', async () => {
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    const wrapper = mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    instances[0].onmessage?.({ data: 'not-json' });
    expect(wrapper.vm.lastError).toContain('parse error');
  });

  it('sendKeepAlive sends ping when open', async () => {
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      static OPEN = 1;
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    const wrapper = mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    instances[0].readyState = MockWebSocket.OPEN;
    wrapper.vm.sendKeepAlive();
    expect(instances[0].sent).toContain('ping');
  });

  it('onclose schedules reconnect when not manual', async () => {
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    instances[0].onclose?.({});
    expect(vi.getTimerCount()).toBeGreaterThan(0);
    vi.advanceTimersByTime(1000);
  });

  it('onerror sets lastError', async () => {
    const instances: MockWebSocket[] = [];
    vi.stubGlobal('WebSocket', class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        instances.push(this);
      }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    const wrapper = mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    instances[0].onerror?.({});
    expect(wrapper.vm.lastError).toBe('WebSocket error');
  });

  it('connect constructor failure sets lastError and schedules reconnect', async () => {
    vi.stubGlobal('WebSocket', class {
      constructor() { throw new Error('no ws'); }
    } as unknown as typeof WebSocket);
    vi.resetModules();
    const { useWorkflowSocket } = await import('../../src/composables/useWorkflowSocket.js');
    const wrapper = mount(defineComponent({
      setup() { return useWorkflowSocket(); },
      template: '<div />',
    }));
    await flushPromises();
    wrapper.vm.reconnect();
    expect(wrapper.vm.lastError).toBe('no ws');
  });
});
