/**
 * Phase 64 — WorldTabs.vue unit tests.
 *
 * WorldTabs is the top-level tab navigation strip on the World page
 * (Phase 117 Task 12 / F). It renders 4 hardcoded tabs (characters,
 * factions, timeline, lore), highlights the active one, and emits
 * `switch` events on click.
 *
 * 4 tabs × active class + emit behavior = 6 tests.
 */

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import WorldTabs from '@/components/world/WorldTabs.vue';

const TAB_IDS = ['characters', 'factions', 'timeline', 'lore'] as const;
const TAB_LABELS = ['人物卡', '势力图', '时间线', '世界书'];

// ---------------------------------------------------------------------------
// Render structure
// ---------------------------------------------------------------------------

describe('WorldTabs — render', () => {
  it('renders all 4 tabs in stable order with correct labels', () => {
    const wrapper = mount(WorldTabs, {
      props: { activeTab: 'characters' },
    });

    const buttons = wrapper.findAll('[data-testid^="world-tab-"]');
    expect(buttons).toHaveLength(4);

    TAB_IDS.forEach((id, i) => {
      expect(buttons[i].attributes('data-testid')).toBe(`world-tab-${id}`);
      expect(buttons[i].text()).toBe(TAB_LABELS[i]);
    });
  });

  it('renders the container with world-tabs testid for hub-level selectors', () => {
    const wrapper = mount(WorldTabs, {
      props: { activeTab: 'lore' },
    });
    expect(wrapper.find('[data-testid="world-tabs"]').exists()).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Active tab highlighting
// ---------------------------------------------------------------------------

describe('WorldTabs — active tab', () => {
  it('applies world-tab--active class only to the active tab', () => {
    const wrapper = mount(WorldTabs, {
      props: { activeTab: 'factions' },
    });

    const buttons = wrapper.findAll('[data-testid^="world-tab-"]');
    buttons.forEach((btn, i) => {
      const id = TAB_IDS[i];
      const isActive = id === 'factions';
      if (isActive) {
        expect(btn.classes()).toContain('world-tab--active');
      } else {
        expect(btn.classes()).not.toContain('world-tab--active');
      }
    });
  });

  it('updates the active class when activeTab prop changes', async () => {
    const wrapper = mount(WorldTabs, {
      props: { activeTab: 'characters' },
    });

    // Initially characters is active.
    let activeBtn = wrapper.find('[data-testid="world-tab-characters"]');
    expect(activeBtn.classes()).toContain('world-tab--active');

    // Switch to lore.
    await wrapper.setProps({ activeTab: 'lore' });
    activeBtn = wrapper.find('[data-testid="world-tab-lore"]');
    expect(activeBtn.classes()).toContain('world-tab--active');

    const charactersBtn = wrapper.find('[data-testid="world-tab-characters"]');
    expect(charactersBtn.classes()).not.toContain('world-tab--active');
  });
});

// ---------------------------------------------------------------------------
// Click → emit('switch', tabId)
// ---------------------------------------------------------------------------

describe('WorldTabs — switch emission', () => {
  it('emits switch event with the clicked tab id', async () => {
    const wrapper = mount(WorldTabs, {
      props: { activeTab: 'characters' },
    });

    await wrapper.find('[data-testid="world-tab-timeline"]').trigger('click');

    expect(wrapper.emitted('switch')).toBeTruthy();
    expect(wrapper.emitted('switch')).toHaveLength(1);
    expect(wrapper.emitted('switch')![0]).toEqual(['timeline']);
  });

  it('emits distinct switch events when different tabs are clicked', async () => {
    const wrapper = mount(WorldTabs, {
      props: { activeTab: 'characters' },
    });

    await wrapper.find('[data-testid="world-tab-factions"]').trigger('click');
    await wrapper.find('[data-testid="world-tab-lore"]').trigger('click');

    const events = wrapper.emitted('switch');
    expect(events).toHaveLength(2);
    expect(events![0]).toEqual(['factions']);
    expect(events![1]).toEqual(['lore']);
  });
});
