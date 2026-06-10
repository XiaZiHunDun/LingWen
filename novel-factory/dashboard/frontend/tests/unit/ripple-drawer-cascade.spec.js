// dashboard/frontend/tests/unit/ripple-drawer-cascade.spec.js — Phase 9.16 T3
// RippleDrawer mount 时 onCascadeUpdate 注册 + ripple_id 匹配时静默 re-fetch 测试
// 镜像 ripple-drawer-audit.spec.js Phase 9.14 T5 模式: relative path import +
//   vi.mock + mockResolvedValue + flushPromises
// 验证 refetch 行为: spy 在 api level (fetchRippleCascade / fetchRipplePreview),
//   因为 useRippleStore 是 module singleton, 每次 useRippleStore() 返回新 object
//   (refs 是 module-level shared), spyOn return-object 的 method 不会传到
//   RippleDrawer 内的 store 实例. spy api 是更稳的 integration test 模式.
// 3 case:
//   - registers_on_cascade_update_handler_on_mount
//   - matching_ripple_id_triggers_silent_refetch
//   - non_matching_ripple_id_ignored_no_refetch

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

// 注入式 mock: capture registered cascade handlers to globalThis so tests can
// simulate WS push from outside. 镜像 use-workflow-socket-cascade.spec.js pattern
const registeredCascadeHandlers = new Set();
globalThis.__cascadeHandlers = registeredCascadeHandlers;

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: { value: null },
    pendingDecisions: { value: [] },
    connected: { value: true },
    lastError: { value: null },
    latestCascadeUpdates: { value: [] },
    sendKeepAlive: () => {},
    reconnect: () => {},
  }),
  onCascadeUpdate: vi.fn((handler) => {
    registeredCascadeHandlers.add(handler);
  }),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchRippleAudit: vi.fn(),
  rollbackRipple: vi.fn(),
  fetchRipples: vi.fn(),
  fetchRippleStats: vi.fn(),
  applyRipple: vi.fn(),
  rejectRipple: vi.fn(),
  fetchRippleCascade: vi.fn(),
  fetchRipplePreview: vi.fn(),
}));

const baseRipple = {
  ripple_id: 'rip-1',
  source_chapter: 1,
  target_chapter: 120,
  relationship_type: 'foreshadows',
  confidence: 4,
  status: 'pending',
  source_payload: {},
  target_payload: {},
  edge_payload: {},
  evidence: '...',
  created_at: '2026-06-10T12:00:00Z',
};

describe('RippleDrawer cascade auto-refresh (Phase 9.16)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    registeredCascadeHandlers.clear();
    // 镜像 ripple-drawer-audit.spec.js: 显式 import + mockResolvedValue before mount
    // (避免 useRippleStore 单例 mount 时 refresh() 拿到 undefined)
    const api = await import('../../src/api/index.js');
    api.fetchRipples.mockResolvedValue([]);
    api.fetchRippleStats.mockResolvedValue({ total: 0, by_status: {}, by_volume: {} });
    api.fetchRippleAudit.mockResolvedValue([]);
    api.fetchRippleCascade.mockResolvedValue({ cascade_nodes: [], cascade_edges: [], depth_reached: 0 });
    api.fetchRipplePreview.mockResolvedValue({ affected_chapter_count: 0 });
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('registers_on_cascade_update_handler_on_mount', async () => {
    const RippleDrawer = (await import('../../src/components/RippleDrawer.vue')).default;
    mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();
    // RippleDrawer mount 时 onCascadeUpdate 应被调 1+ 次
    expect(registeredCascadeHandlers.size).toBeGreaterThanOrEqual(1);
  });

  it('matching_ripple_id_triggers_silent_refetch', async () => {
    const RippleDrawer = (await import('../../src/components/RippleDrawer.vue')).default;
    const api = await import('../../src/api/index.js');

    mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();

    // mount 时已经调 1 次 fetchRippleCascade + fetchRipplePreview (eager load)
    const cascadeCallsAfterMount = api.fetchRippleCascade.mock.calls.length;
    const previewCallsAfterMount = api.fetchRipplePreview.mock.calls.length;
    // baseline sanity check
    expect(cascadeCallsAfterMount).toBeGreaterThanOrEqual(1);
    expect(previewCallsAfterMount).toBeGreaterThanOrEqual(1);

    // simulate cascade.update with matching ripple_id
    for (const h of registeredCascadeHandlers) {
      h({ ripple_id: 'rip-1', cascade_node_count: 3 });
    }
    await flushPromises();

    // 应比 mount 后多 1 次 (匹配 → 静默 re-fetch)
    expect(api.fetchRippleCascade).toHaveBeenCalledTimes(cascadeCallsAfterMount + 1);
    expect(api.fetchRippleCascade).toHaveBeenLastCalledWith('rip-1');
    expect(api.fetchRipplePreview).toHaveBeenCalledTimes(previewCallsAfterMount + 1);
    expect(api.fetchRipplePreview).toHaveBeenLastCalledWith('rip-1');
  });

  it('non_matching_ripple_id_ignored_no_refetch', async () => {
    const RippleDrawer = (await import('../../src/components/RippleDrawer.vue')).default;
    const api = await import('../../src/api/index.js');

    mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();

    const cascadeCallsAfterMount = api.fetchRippleCascade.mock.calls.length;
    const previewCallsAfterMount = api.fetchRipplePreview.mock.calls.length;

    // simulate cascade.update with non-matching ripple_id
    for (const h of registeredCascadeHandlers) {
      h({ ripple_id: 'rip-other', cascade_node_count: 5 });
    }
    await flushPromises();

    // 应仍是 mount 时的次数 (不匹配 → 不 re-fetch)
    expect(api.fetchRippleCascade).toHaveBeenCalledTimes(cascadeCallsAfterMount);
    expect(api.fetchRipplePreview).toHaveBeenCalledTimes(previewCallsAfterMount);
  });
});
