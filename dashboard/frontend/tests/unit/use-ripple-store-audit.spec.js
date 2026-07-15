// tests/unit/use-ripple-store-audit.spec.js — Phase 9.14
// useRippleStore 2 新 action 测试 (fetchAudit / rollback) + api 2 新 method 测试
//   (fetchRippleAudit / rollbackRipple)
// 镜像 use-ripple-store.spec.js Phase 9.13 模式: relative path import +
//   vi.mock + dynamic import (proven pattern, 避免 alias resolution 风险).
// 测试 6 case:
//   - store.fetchAudit returns entries on success
//   - store.fetchAudit sets lastError on failure (raw e.message, 跟 apply/reject wrap 风格不同)
//   - store.rollback updates ripple status optimistically (server response 覆盖, 跟 apply/reject 1:1)
//   - store.rollback sets lastError and does not mutate on failure (snapshot 回滚)
//   - api.fetchRippleAudit calls correct URL (GET /api/cvg/ripples/{id}/audit)
//   - api.rollbackRipple sends POST with reason (POST /api/cvg/ripples/{id}/rollback)
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/index.js', () => ({
  fetchRipples: vi.fn(),
  fetchRippleStats: vi.fn(),
  applyRipple: vi.fn(),
  rejectRipple: vi.fn(),
  fetchRippleAudit: vi.fn(),
  rollbackRipple: vi.fn(),
  fetchRippleCascade: vi.fn(),       // Phase 9.15
  fetchRipplePreview: vi.fn(),       // Phase 9.15
}));

describe('useRippleStore audit actions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchAudit returns entries on success', async () => {
    const api = await import('../../src/api/index.js');
    const entries = [{ id: 1, action: 'created', actor: 'sys', origin: 'system' }];
    api.fetchRippleAudit.mockResolvedValue(entries);
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    const result = await store.fetchAudit('rip-1');
    expect(result).toEqual(entries);
    expect(api.fetchRippleAudit).toHaveBeenCalledWith('rip-1');
  });

  it('fetchAudit sets lastError on failure', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRippleAudit.mockRejectedValue(new Error('network'));
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    await expect(store.fetchAudit('rip-1')).rejects.toThrow('network');
    expect(store.lastError.value).toBe('network');
  });

  it('rollback updates ripple status optimistically', async () => {
    const api = await import('../../src/api/index.js');
    const updated = { ripple_id: 'rip-1', status: 'pending', applied_at: null };
    api.rollbackRipple.mockResolvedValue(updated);
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    store.ripples.value = [
      { ripple_id: 'rip-1', status: 'applied', applied_at: '2026-06-10' },
      { ripple_id: 'rip-2', status: 'pending' },
    ];
    await store.rollback('rip-1', 'test reason');
    expect(store.ripples.value[0].status).toBe('pending');
    expect(store.ripples.value[0].applied_at).toBeNull();
    expect(store.ripples.value[1].status).toBe('pending');  // unchanged
  });

  it('rollback sets lastError and does not mutate on failure', async () => {
    const api = await import('../../src/api/index.js');
    api.rollbackRipple.mockRejectedValue(new Error('422'));
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    store.ripples.value = [{ ripple_id: 'rip-1', status: 'applied' }];
    await expect(store.rollback('rip-1', 'r')).rejects.toThrow('422');
    expect(store.ripples.value[0].status).toBe('applied');  // unchanged
    expect(store.lastError.value).toBe('422');
  });

  it('api.fetchRippleAudit calls correct URL', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve([]) });
    global.fetch = mockFetch;
    // vi.importActual: 拿真实 module (不取 mock) 来测 fetch URL/options
    const api = await vi.importActual('../../src/api/index.js');
    await api.fetchRippleAudit('rip-1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/cvg/ripples/rip-1/audit'),
      expect.any(Object)
    );
  });

  it('api.rollbackRipple sends POST with reason', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    global.fetch = mockFetch;
    // vi.importActual: 拿真实 module (不取 mock) 来测 fetch URL/options
    const api = await vi.importActual('../../src/api/index.js');
    await api.rollbackRipple('rip-1', 'reason text');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/cvg/ripples/rip-1/rollback'),
      expect.objectContaining({ method: 'POST' })
    );
    // 验证 body 包含 reason 字段
    const callArgs = mockFetch.mock.calls[0];
    const opts = callArgs[1];
    expect(JSON.parse(opts.body)).toEqual({ reason: 'reason text' });
  });

  // === Phase 9.15: cascade BFS + dry-run preview (cascade actions / preview) ===

  it('loadCascade fetches and caches cascade', async () => {
    const api = await import('../../src/api/index.js');
    const data = {
      trigger_ripple_id: 'rip-1',
      cascade_nodes: [{ id: 'n2', volume: 2, chapter: 1, dimension: 'character' }],
      cascade_edges: [],
      cascade_actions: [{ action: 'propagate', from: 'n1', to: 'n2', depth: 1, weight: 1.0 }],
      depth_reached: 1,
      generated_at: '2026-06-10T10:00:00Z',
      bfs_algorithm_version: 'v1',
    };
    api.fetchRippleCascade.mockResolvedValue(data);
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    const result = await store.loadCascade('rip-1');
    expect(result).toEqual(data);
    expect(api.fetchRippleCascade).toHaveBeenCalledWith('rip-1');
    expect(store.cascadeByRippleId.value.get('rip-1').depth_reached).toBe(1);
  });

  it('loadCascadePreview fetches and caches preview', async () => {
    const api = await import('../../src/api/index.js');
    const data = {
      ripple_id: 'rip-1',
      nodes_to_add: [],
      edges_to_add: [],
      actions_to_apply: [],
      totals: { nodes: 3, edges: 2, actions: 1 },
    };
    api.fetchRipplePreview.mockResolvedValue(data);
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    const result = await store.loadCascadePreview('rip-1');
    expect(result.totals.nodes).toBe(3);
    expect(api.fetchRipplePreview).toHaveBeenCalledWith('rip-1');
    expect(store.previewByRippleId.value.get('rip-1').totals.edges).toBe(2);
  });
});
