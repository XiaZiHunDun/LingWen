// tests/unit/use-ripple-store.spec.js — Phase 9.13
// useRippleStore module-level singleton test (跟 useDecisionStore 1:1 mirror pattern)
// 测试 6 case: refresh / apply / reject / applySocketUpdate ripple_created /
//   applySocketUpdate ripple_status_changed / lastError on failure
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/index.js', () => ({
  fetchRipples: vi.fn(),
  fetchRippleStats: vi.fn(),
  applyRipple: vi.fn(),
  rejectRipple: vi.fn(),
}));

describe('useRippleStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('refresh fetches ripples and stats', async () => {
    const mockRipples = [{ ripple_id: 'r1', status: 'pending' }];
    const mockStats = { total: 1, by_status: { pending: 1 }, by_volume: { '1': 1 } };
    const api = await import('../../src/api/index.js');
    api.fetchRipples.mockResolvedValue(mockRipples);
    api.fetchRippleStats.mockResolvedValue(mockStats);
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    await store.refresh();
    await Promise.resolve();
    expect(store.ripples.value).toEqual(mockRipples);
    expect(store.stats.value).toEqual(mockStats);
    expect(store.loading.value).toBe(false);
  });

  it('apply updates ripple status optimistically', async () => {
    const api = await import('../../src/api/index.js');
    api.applyRipple.mockResolvedValue({ ripple_id: 'r1', status: 'applied' });
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    store.ripples.value = [{ ripple_id: 'r1', status: 'pending' }];
    await store.apply('r1');
    expect(store.ripples.value[0].status).toBe('applied');
  });

  it('reject updates ripple status', async () => {
    const api = await import('../../src/api/index.js');
    api.rejectRipple.mockResolvedValue({ ripple_id: 'r1', status: 'rejected' });
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    store.ripples.value = [{ ripple_id: 'r1', status: 'pending' }];
    await store.reject('r1', '测试 reason');
    expect(store.ripples.value[0].status).toBe('rejected');
  });

  it('applySocketUpdate handles ripple_created', async () => {
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    store.ripples.value = [];
    store.applySocketUpdate({
      type: 'ripple_created',
      data: { ripple_id: 'r-new', status: 'pending' },
    });
    expect(store.ripples.value).toHaveLength(1);
    expect(store.ripples.value[0].ripple_id).toBe('r-new');
  });

  it('applySocketUpdate handles ripple_status_changed', async () => {
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    store.ripples.value = [{ ripple_id: 'r1', status: 'pending' }];
    store.applySocketUpdate({
      type: 'ripple_status_changed',
      data: { ripple_id: 'r1', new_status: 'applied' },
    });
    expect(store.ripples.value[0].status).toBe('applied');
  });

  it('lastError is set on refresh failure', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRipples.mockRejectedValue(new Error('network error'));
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    await store.refresh();
    expect(store.lastError.value).toBe('network error');
    expect(store.loading.value).toBe(false);
  });

  it('refresh passes sort_by and min_score filters', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRipples.mockResolvedValue([]);
    api.fetchRippleStats.mockResolvedValue({ total: 0, by_status: {}, by_volume: {} });
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    await store.refresh({ sort_by: 'impact_score', min_score: 3, status: 'pending', volume: 2 });
    const params = api.fetchRipples.mock.calls[0][0];
    expect(params.get('sort_by')).toBe('impact_score');
    expect(params.get('min_score')).toBe('3');
    expect(params.get('status')).toBe('pending');
    expect(params.get('volume')).toBe('2');
  });

  it('apply failure sets lastError', async () => {
    const api = await import('../../src/api/index.js');
    api.applyRipple.mockRejectedValue(new Error('apply fail'));
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    await expect(store.apply('r1')).rejects.toThrow('apply fail');
    expect(store.lastError.value).toContain('apply 失败');
  });

  it('reject failure sets lastError', async () => {
    const api = await import('../../src/api/index.js');
    api.rejectRipple.mockRejectedValue(new Error('reject fail'));
    const { useRippleStore } = await import('../../src/composables/useRippleStore.js');
    const store = useRippleStore();
    await expect(store.reject('r1')).rejects.toThrow('reject fail');
    expect(store.lastError.value).toContain('reject 失败');
  });
});
