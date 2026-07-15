// dashboard/frontend/tests/unit/use-workflow-socket-cascade.spec.js — Phase 9.16 T3
// useWorkflowSocket cascade.update event 分支 + onCascadeUpdate API 测试
// 镜像 use-ripple-store.spec.js Phase 9.13 模式: dynamic import + vi.resetModules
//   隔离 module-level singleton state (latestCascadeUpdates / registeredHandlers)
// useWorkflowSocket 内 onMounted hook 必须 mount 在 Vue component context 内
//   才会触发 connect(), 走 mount(TestHarness, { props: { ... } }) 包一层
// latestCascadeUpdates 走 useWorkflowSocket() return value 暴露 (不是 named export,
//   跟 status / pendingDecisions 1:1 模式)
// 4 case:
//   - handler_registers_and_receives_cascade_update_event
//   - latest_cascade_updates_ref_slices_to_10
//   - backward_compat_old_3_events_still_work
//   - handler_unregisters_on_unmount

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

// Mock WebSocket at module level (跟 Phase 8.11 + 9.15 既有 test 风格 1:1)
class MockWebSocket {
  constructor(url) {
    this.url = url;
    MockWebSocket.instances.push(this);
    this.readyState = 0; // CONNECTING
    this._onopen = null;
    this._onmessage = null;
    this._onerror = null;
    this._onclose = null;
  }
  set onopen(fn) {
    this._onopen = fn;
    setTimeout(() => {
      this.readyState = 1;
      if (this._onopen) this._onopen({});
    }, 0);
  }
  set onmessage(fn) { this._onmessage = fn; }
  set onerror(fn) { this._onerror = fn; }
  set onclose(fn) { this._onclose = fn; }
  close() {
    this.readyState = 3;
    if (this._onclose) this._onclose({});
  }
  send() {}
  // test helper
  simulateMessage(data) {
    if (this._onmessage) this._onmessage({ data: JSON.stringify(data) });
  }
}
MockWebSocket.instances = [];
MockWebSocket.OPEN = 1;
globalThis.WebSocket = MockWebSocket;

// Test harness component: invokes useWorkflowSocket() in setup context, exposes
// all needed APIs (including latestCascadeUpdates ref) to tests via test extras
function createHarness(setupExtras) {
  return defineComponent({
    setup() {
      const m = globalThis.__wsModule;
      const { useWorkflowSocket, onCascadeUpdate } = m;
      const ctx = useWorkflowSocket();
      if (setupExtras) {
        setupExtras({
          onCascadeUpdate,
          status: ctx.status,
          pendingDecisions: ctx.pendingDecisions,
          latestCascadeUpdates: ctx.latestCascadeUpdates,
        });
      }
      return () => h('div');
    },
  });
}

describe('useWorkflowSocket cascade event (Phase 9.16)', () => {
  let wrapper;
  let testModule;
  // Each test sets these to grab the refs from inside the harness setup()
  const ctxRefs = { onCascadeUpdate: null, status: null, pendingDecisions: null, latestCascadeUpdates: null };

  beforeEach(async () => {
    MockWebSocket.instances = [];
    // Reset module-level singleton state between tests (跟 use-ripple-store 1:1)
    vi.resetModules();
    testModule = await import('../../src/composables/useWorkflowSocket.js');
    globalThis.__wsModule = testModule;
    // Reset ctx refs
    ctxRefs.onCascadeUpdate = null;
    ctxRefs.status = null;
    ctxRefs.pendingDecisions = null;
    ctxRefs.latestCascadeUpdates = null;
  });
  afterEach(async () => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
    vi.restoreAllMocks();
  });

  async function mountHarness(extraCapture) {
    const captureFn = (refs) => {
      ctxRefs.onCascadeUpdate = refs.onCascadeUpdate;
      ctxRefs.status = refs.status;
      ctxRefs.pendingDecisions = refs.pendingDecisions;
      ctxRefs.latestCascadeUpdates = refs.latestCascadeUpdates;
      if (extraCapture) extraCapture(refs);
    };
    const Comp = createHarness(captureFn);
    wrapper = mount(Comp);
    // wait for ws.onopen to fire (setTimeout 0 inside MockWebSocket setter)
    await new Promise((r) => setTimeout(r, 10));
    await nextTick();
  }

  it('handler_registers_and_receives_cascade_update_event', async () => {
    await mountHarness();
    const handler = vi.fn();
    ctxRefs.onCascadeUpdate(handler);
    MockWebSocket.instances[0].simulateMessage({
      type: 'cascade.update',
      payload: {
        ripple_id: 'rip-1',
        cascade_node_count: 3,
        cascade_edge_count: 2,
        depth_reached: 1,
        bfs_algorithm_version: 'v2_weighted',
      },
    });
    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({
      ripple_id: 'rip-1',
      cascade_node_count: 3,
      bfs_algorithm_version: 'v2_weighted',
    }));
    // module-level ref 也 append 了 (via useWorkflowSocket return)
    expect(ctxRefs.latestCascadeUpdates.value.length).toBe(1);
    expect(ctxRefs.latestCascadeUpdates.value[0].ripple_id).toBe('rip-1');
  });

  it('latest_cascade_updates_ref_slices_to_10', async () => {
    await mountHarness();
    for (let i = 0; i < 15; i++) {
      MockWebSocket.instances[0].simulateMessage({
        type: 'cascade.update',
        payload: { ripple_id: `rip-${i}`, cascade_node_count: i },
      });
    }
    expect(ctxRefs.latestCascadeUpdates.value.length).toBe(10);
    // 最早的 5 个 (rip-0..rip-4) 被裁掉
    expect(ctxRefs.latestCascadeUpdates.value[0].ripple_id).toBe('rip-5');
    expect(ctxRefs.latestCascadeUpdates.value[9].ripple_id).toBe('rip-14');
  });

  it('backward_compat_old_3_events_still_work', async () => {
    await mountHarness();
    // workflow.status
    MockWebSocket.instances[0].simulateMessage({
      type: 'workflow.status',
      payload: { id: 'wf-1', status: 'running' },
    });
    expect(ctxRefs.status.value).toEqual({ id: 'wf-1', status: 'running' });
    // decision.snapshot
    MockWebSocket.instances[0].simulateMessage({
      type: 'decision.snapshot',
      payload: [{ decision_id: 'd-1' }],
    });
    expect(ctxRefs.pendingDecisions.value).toEqual([{ decision_id: 'd-1' }]);
    // connected snapshot
    MockWebSocket.instances[0].simulateMessage({
      type: 'connected',
      snapshot: { id: 'wf-2', status: 'pending' },
      pending_decisions: [],
    });
    expect(ctxRefs.status.value).toEqual({ id: 'wf-2', status: 'pending' });
  });

  it('handler_unregisters_on_unmount', async () => {
    await mountHarness();
    const handler = vi.fn();
    ctxRefs.onCascadeUpdate(handler);
    ctxRefs.onCascadeUpdate(handler);  // 重复 register → Set 自动去重
    MockWebSocket.instances[0].simulateMessage({
      type: 'cascade.update',
      payload: { ripple_id: 'rip-1' },
    });
    // Set 去重保证 handler 只调 1 次
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
