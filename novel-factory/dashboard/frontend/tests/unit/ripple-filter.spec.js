// dashboard/frontend/tests/unit/ripple-filter.spec.js
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RippleFilter from '../../src/components/RippleFilter.vue';

describe('RippleFilter', () => {
  it('renders 3 dropdowns with default values', () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all' },
    });
    expect(wrapper.findAll('select')).toHaveLength(3);
  });

  it('emits update:status on status change', async () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all' },
    });
    await wrapper.find('[data-testid="ripple-filter-status"]').setValue('pending');
    expect(wrapper.emitted('update:status')[0][0]).toBe('pending');
  });

  it('emits update:volume on volume change', async () => {
    const wrapper = mount(RippleFilter, {
      props: { status: 'all', dimension: 'all', volume: 'all' },
    });
    await wrapper.find('[data-testid="ripple-filter-volume"]').setValue('2');
    expect(wrapper.emitted('update:volume')[0][0]).toBe('2');
  });
});
