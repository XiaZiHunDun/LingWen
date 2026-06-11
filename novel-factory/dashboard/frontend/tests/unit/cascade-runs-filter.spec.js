// dashboard/frontend/tests/unit/cascade-runs-filter.spec.js — Phase 9.23 T4
// Vitest unit tests for CascadeRunsFilter.vue (5 tests, 0 network, 0 LLM).
// Pattern matches ripple-drawer-cascade.spec.js (mount via @vue/test-utils +
// jsdom, dynamic await import in beforeEach). Emit capture via
// wrapper.emitted() (the @vue/test-utils v2+ API), since script-setup
// defineEmits 走 component instance 机制, wrapper.vm.$emit 覆盖无效.

import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

const DEFAULT = { status: 'all', minDepth: null, maxDepth: null, algorithm: 'all' };

describe('Phase 9.23: CascadeRunsFilter', () => {
  let wrapper;

  beforeEach(async () => {
    const { default: CascadeRunsFilter } = await import('../../src/components/CascadeRunsFilter.vue');
    wrapper = mount(CascadeRunsFilter, {
      props: { modelValue: { ...DEFAULT } },
      global: {
        config: { globalProperties: {} },
        mocks: {},
      },
      attachTo: document.body,
    });
  });

  it('renders 3 dropdowns + 2 number inputs + reset hidden by default', async () => {
    expect(wrapper.find('[data-testid="filter-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-algorithm"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-min-depth"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-max-depth"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-reset"]').exists()).toBe(false);
  });

  it('changing status dropdown emits update:modelValue with new status', async () => {
    const select = wrapper.find('[data-testid="filter-status"]');
    await select.setValue('cancelled');
    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0]).toEqual({
      status: 'cancelled',
      minDepth: null,
      maxDepth: null,
      algorithm: 'all',
    });
  });

  it('typing minDepth=2 emits update with numeric value', async () => {
    const input = wrapper.find('[data-testid="filter-min-depth"]');
    await input.setValue('2');
    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0]).toEqual({
      status: 'all',
      minDepth: 2,
      maxDepth: null,
      algorithm: 'all',
    });
  });

  it('typing invalid number (15) silently drops without emit', async () => {
    const input = wrapper.find('[data-testid="filter-min-depth"]');
    await input.setValue('15');
    expect(wrapper.emitted('update:modelValue')).toBeFalsy();
  });

  it('reset button only renders when any filter is active, emits defaults on click', async () => {
    // No active filter → reset hidden
    expect(wrapper.find('[data-testid="filter-reset"]').exists()).toBe(false);
    // Set active filter via prop change
    await wrapper.setProps({ modelValue: { status: 'cancelled', minDepth: null, maxDepth: null, algorithm: 'all' } });
    await nextTick();
    expect(wrapper.find('[data-testid="filter-reset"]').exists()).toBe(true);
    // Click reset
    await wrapper.find('[data-testid="filter-reset"]').trigger('click');
    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[events.length - 1][0]).toEqual({
      status: 'all',
      minDepth: null,
      maxDepth: null,
      algorithm: 'all',
    });
  });
});
