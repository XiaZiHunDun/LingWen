// tests/unit/ripple-filter.spec.ts — Phase 9.40 F25 TS strict pilot
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RippleFilter from '../../src/components/RippleFilter.vue';

describe('RippleFilter', () => {
  it('renders 4 dropdowns with default values', () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' },
    });
    expect(wrapper.findAll('select')).toHaveLength(4);
  });

  it('emits update:status on status change', async () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' },
    });
    await wrapper.find('[data-testid="ripple-filter-status"]').setValue('pending');
    const emitted = wrapper.emitted('update:status');
    expect(emitted![0]![0]).toBe('pending');
  });

  it('emits update:volume on volume change', async () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all', sortBy: 'created_at', minScore: '' },
    });
    await wrapper.find('[data-testid="ripple-filter-volume"]').setValue('2');
    const emitted = wrapper.emitted('update:volume');
    expect(emitted![0]![0]).toBe('2');
  });
});
