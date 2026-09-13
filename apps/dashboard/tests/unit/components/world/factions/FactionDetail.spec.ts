/**
 * Phase 67 — FactionDetail.vue unit tests.
 *
 * FactionDetail is the closeable sidebar on the World page that
 * displays a selected faction's name + description (Phase 117
 * Task 16). Pure presentational — takes a `faction` object prop,
 * emits `close` event. No composables.
 *
 * 5 tests covering render + close emission + null fallback.
 */

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import FactionDetail from '@/components/world/factions/FactionDetail.vue';

const sampleFaction = {
  id: 1,
  name: '金剑盟',
  description: '北方最大的武林门派',
};

// ---------------------------------------------------------------------------
// Render with valid faction
// ---------------------------------------------------------------------------

describe('FactionDetail — render', () => {
  it('renders the container testid for hub-level selectors', () => {
    const wrapper = mount(FactionDetail, {
      props: { faction: sampleFaction },
    });
    expect(wrapper.find('[data-testid="faction-detail"]').exists()).toBe(true);
  });

  it('renders faction name + description when faction prop is provided', () => {
    const wrapper = mount(FactionDetail, {
      props: { faction: sampleFaction },
    });
    expect(wrapper.text()).toContain('金剑盟');
    expect(wrapper.text()).toContain('北方最大的武林门派');
  });

  it('emits close event when the close button is clicked', async () => {
    const wrapper = mount(FactionDetail, {
      props: { faction: sampleFaction },
    });
    await wrapper.find('[data-testid="faction-detail-close"]').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
    expect(wrapper.emitted('close')).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// Null fallback (faction = null)
// ---------------------------------------------------------------------------

describe('FactionDetail — null faction', () => {
  it('still renders the container when faction is null', () => {
    const wrapper = mount(FactionDetail, {
      props: { faction: null },
    });
    expect(wrapper.find('[data-testid="faction-detail"]').exists()).toBe(true);
  });

  it('omits the description paragraph when faction is null', () => {
    const wrapper = mount(FactionDetail, {
      props: { faction: null },
    });
    expect(wrapper.find('.faction-detail__description').exists()).toBe(false);
  });

  it('renders the close button even when faction is null', async () => {
    const wrapper = mount(FactionDetail, {
      props: { faction: null },
    });
    await wrapper.find('[data-testid="faction-detail-close"]').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
