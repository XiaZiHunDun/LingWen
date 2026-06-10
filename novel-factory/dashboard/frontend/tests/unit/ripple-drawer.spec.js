// dashboard/frontend/tests/unit/ripple-drawer.spec.js
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RippleDrawer from '../../src/components/RippleDrawer.vue';

const sample = {
  ripple_id: 'r1',
  dimension: 'character',
  relationship_type: 'mentions',
  source_chapter: 5,
  target_chapter: 20,
  status: 'pending',
  confidence: 4,
  evidence: 'test evidence text',
  source_payload: { name: 'Source' },
  target_payload: { name: 'Target' },
  edge_payload: { weight: 0.8 },
  created_at: '2026-06-10T12:00:00Z',
};

describe('RippleDrawer', () => {
  it('renders source / target / evidence when open', () => {
    const wrapper = mount(RippleDrawer, {
      props: { ripple: sample, open: true },
    });
    expect(wrapper.find('[data-testid="ripple-drawer"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('test evidence text');
    expect(wrapper.text()).toContain('Source');
  });

  it('does not render drawer content when closed', () => {
    const wrapper = mount(RippleDrawer, {
      props: { ripple: sample, open: false },
    });
    expect(wrapper.find('[data-testid="ripple-drawer-content"]').exists()).toBe(false);
  });

  it('emits apply and reject events', async () => {
    const wrapper = mount(RippleDrawer, {
      props: { ripple: sample, open: true },
    });
    await wrapper.find('[data-testid="ripple-drawer-apply"]').trigger('click');
    expect(wrapper.emitted('apply')).toBeTruthy();
    await wrapper.find('[data-testid="ripple-drawer-reject"]').trigger('click');
    expect(wrapper.emitted('reject')).toBeTruthy();
  });
});
