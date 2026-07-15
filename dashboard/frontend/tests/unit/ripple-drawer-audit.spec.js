// dashboard/frontend/tests/unit/ripple-drawer-audit.spec.js — Phase 9.14 T5
// RippleDrawer audit timeline + Rollback button 测试 6 case.
// 镜像 use-ripple-store-audit.spec.js Phase 9.14 T4 + ripple-drawer.spec.js
//   Phase 9.13 模式: relative path import + vi.mock (proven pattern).
// 测试 6 case:
//   - drawer_calls_fetch_audit_on_mount
//   - drawer_renders_audit_entries_with_action_actor_timestamp
//   - rollback_button_hidden_for_pending
//   - rollback_button_shown_for_applied
//   - rollback_click_prompts_and_calls_store_rollback
//   - empty_audit_shows_no_history
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import RippleDrawer from '../../src/components/RippleDrawer.vue';

vi.mock('../../src/api/index.js', () => ({
  fetchRippleAudit: vi.fn(),
  rollbackRipple: vi.fn(),
  fetchRipples: vi.fn(),
  fetchRippleStats: vi.fn(),
  applyRipple: vi.fn(),
  rejectRipple: vi.fn(),
}));

const baseRipple = {
  ripple_id: 'rip-1',
  source_chapter: 1,
  target_chapter: 120,
  relationship_type: 'foreshadows',
  confidence: 4,
  status: 'applied',
  applied_at: '2026-06-10T10:00:00',
  source_payload: {},
  target_payload: {},
  edge_payload: {},
  evidence: '...',
};

describe('RippleDrawer audit timeline', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    // 镜像 use-ripple-store-audit.spec.js 模式: 显式 import + mockResolvedValue
    // 必须在 useRippleStore() 调用之前设置, 否则 singleton store 第一个 mount
    // 时 refresh() 会拿到 undefined, 把 ripples.value 覆盖成 undefined,
    // 后续 store.rollback() findIndex() 报 TypeError
    const api = await import('../../src/api/index.js');
    api.fetchRipples.mockResolvedValue([]);
    api.fetchRippleStats.mockResolvedValue({ total: 0, by_status: {}, by_volume: {} });
  });

  afterEach(() => {
    // 防止 test 5 (rollback_click_prompts_and_calls_store_rollback) 中
    //   window.prompt = vi.fn(...) mock 泄漏到后续 test (e.g. 跨 describe 共享)
    vi.restoreAllMocks();
  });

  it('drawer_calls_fetch_audit_on_mount', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRippleAudit.mockResolvedValue([]);
    mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();
    expect(api.fetchRippleAudit).toHaveBeenCalledWith('rip-1');
  });

  it('drawer_renders_audit_entries_with_action_actor_timestamp', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRippleAudit.mockResolvedValue([
      { id: 1, action: 'applied', actor: 'user', origin: 'ui', created_at: '2026-06-10T10:00:00', reason: null },
      { id: 2, action: 'created', actor: 'system', origin: 'system', created_at: '2026-06-10T09:00:00', reason: null },
    ]);
    const wrapper = mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();
    expect(wrapper.text()).toContain('applied');
    expect(wrapper.text()).toContain('user');
    expect(wrapper.text()).toContain('2026-06-10T10:00:00');
    expect(wrapper.text()).toContain('created');
  });

  it('rollback_button_hidden_for_pending', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRippleAudit.mockResolvedValue([]);
    const pending = { ...baseRipple, status: 'pending' };
    const wrapper = mount(RippleDrawer, { props: { ripple: pending, open: true } });
    await flushPromises();
    expect(wrapper.find('[data-testid="ripple-rollback-btn"]').exists()).toBe(false);
  });

  it('rollback_button_shown_for_applied', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRippleAudit.mockResolvedValue([]);
    const wrapper = mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();
    expect(wrapper.find('[data-testid="ripple-rollback-btn"]').exists()).toBe(true);
  });

  it('rollback_click_prompts_and_calls_store_rollback', async () => {
    const api = await import('../../src/api/index.js');
    // fetchRipples 返回包含 baseRipple 的列表 — 这样 component mount 时的
    // refresh() 不会把 ripples.value 覆盖成空数组 (store.rollback 需要 ripple 在 list)
    api.fetchRipples.mockResolvedValue([{ ...baseRipple }]);
    api.fetchRippleAudit.mockResolvedValue([]);
    api.rollbackRipple.mockResolvedValue({ ripple_id: 'rip-1', status: 'pending' });
    window.prompt = vi.fn(() => 'user reason');
    const wrapper = mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();
    await wrapper.find('[data-testid="ripple-rollback-btn"]').trigger('click');
    await flushPromises();
    // 验证链: prompt 被调 + store.rollback → api.rollbackRipple('rip-1', reason)
    expect(window.prompt).toHaveBeenCalled();
    expect(api.rollbackRipple).toHaveBeenCalledWith('rip-1', 'user reason');
  });

  it('empty_audit_shows_no_history', async () => {
    const api = await import('../../src/api/index.js');
    api.fetchRippleAudit.mockResolvedValue([]);
    const wrapper = mount(RippleDrawer, { props: { ripple: baseRipple, open: true } });
    await flushPromises();
    expect(wrapper.text()).toContain('No history yet');
  });
});
