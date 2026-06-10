// dashboard/frontend/tests/unit/ripple-list.spec.js
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RippleList from '../../src/components/RippleList.vue';
import RippleCard from '../../src/components/RippleCard.vue';

const samples = [
  { ripple_id: 'r1', dimension: 'character', relationship_type: 'mentions', source_chapter: 5, target_chapter: 20, status: 'pending', confidence: 4, created_at: '2026-06-10T12:00:00Z' },
  { ripple_id: 'r2', dimension: 'foreshadow', relationship_type: 'foreshadows', source_chapter: 3, target_chapter: 50, status: 'applied', confidence: 5, created_at: '2026-06-10T11:00:00Z' },
];

describe('RippleList', () => {
  it('renders RippleCard for each ripple', () => {
    const wrapper = mount(RippleList, { props: { ripples: samples, loading: false } });
    expect(wrapper.findAllComponents(RippleCard)).toHaveLength(2);
  });

  it('shows empty state when ripples is empty', () => {
    const wrapper = mount(RippleList, { props: { ripples: [], loading: false } });
    expect(wrapper.text()).toContain('No ripples');
  });

  it('shows loading skeleton when loading is true', () => {
    const wrapper = mount(RippleList, { props: { ripples: [], loading: true } });
    expect(wrapper.find('[data-testid="ripple-list-loading"]').exists()).toBe(true);
  });
});
