/**
 * Phase 9.64 F55: RippleCard parent/child badge tests
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RippleCard from '../../src/components/RippleCard.vue';

const baseRipple = {
  ripple_id: 'rip-1',
  dimension: 'character',
  relationship_type: 'mentions',
  source_chapter: 1,
  target_chapter: 2,
  status: 'pending',
  confidence: 3,
  impact_score: 1.5,
  parent_ripple_id: null,
  child_count: 0,
};

describe('RippleCard parent/child badges', () => {
  it('shows parent badge when parent_ripple_id set', () => {
    const wrapper = mount(RippleCard, {
      props: {
        ripple: { ...baseRipple, parent_ripple_id: 'parent-abc-123' },
      },
    });
    expect(wrapper.find('[data-testid="ripple-parent-badge"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('child of parent-a');
  });

  it('shows child count badge when child_count > 0', () => {
    const wrapper = mount(RippleCard, {
      props: {
        ripple: { ...baseRipple, child_count: 2 },
      },
    });
    expect(wrapper.find('[data-testid="ripple-child-count"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('2 children');
  });

  it('hides badges when no parent or children', () => {
    const wrapper = mount(RippleCard, { props: { ripple: baseRipple } });
    expect(wrapper.find('[data-testid="ripple-parent-badge"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="ripple-child-count"]').exists()).toBe(false);
  });
});
