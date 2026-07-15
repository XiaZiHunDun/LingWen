// tests/unit/ripple-card.spec.ts — Phase 9.40 F25 TS strict pilot
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RippleCard from '../../src/components/RippleCard.vue';

interface RippleSample {
  ripple_id: string;
  dimension: string;
  relationship_type: string;
  source_chapter: number;
  target_chapter: number;
  status: string;
  confidence: number;
  created_at: string;
}

const sample: RippleSample = {
  ripple_id: 'r1',
  dimension: 'character',
  relationship_type: 'mentions',
  source_chapter: 5,
  target_chapter: 20,
  status: 'pending',
  confidence: 4,
  created_at: '2026-06-10T12:00:00Z',
};

describe('RippleCard', () => {
  it('renders dimension and chapter refs', () => {
    const wrapper = mount(RippleCard, { props: { ripple: sample } });
    expect(wrapper.text()).toContain('character');
    expect(wrapper.text()).toContain('ch5');
    expect(wrapper.text()).toContain('ch20');
  });

  it('renders status badge with data-testid', () => {
    const wrapper = mount(RippleCard, { props: { ripple: sample } });
    expect(wrapper.find('[data-testid="ripple-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="ripple-status"]').text()).toBe('pending');
  });

  it('renders confidence badge (4/5)', () => {
    const wrapper = mount(RippleCard, { props: { ripple: sample } });
    expect(wrapper.find('[data-testid="ripple-confidence"]').text()).toContain('4/5');
  });

  it('emits select event on click', async () => {
    const wrapper = mount(RippleCard, { props: { ripple: sample } });
    await wrapper.find('[data-testid="ripple-card"]').trigger('click');
    const emitted = wrapper.emitted('select');
    expect(emitted).toBeTruthy();
    expect(emitted![0]![0]).toEqual(sample);
  });
});
