/**
 * Phase 66 — CharacterCard.vue unit tests.
 *
 * CharacterCard is the clickable character summary on the World page
 * (Phase 117 Task 13). Renders name + canon_level + optional status,
 * applies a CSS variant class per canon_level, and emits 'click' for
 * the parent to open the detail panel.
 *
 * 5 tests covering render + variant class + click emission.
 */

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import CharacterCard from '@/components/world/characters/CharacterCard.vue';

const baseCharacter = {
  slug: 'lin-yuan',
  name: '林远',
  canon_level: 'ESTABLISHED',
  status: '主角',
};

describe('CharacterCard — render', () => {
  it('renders name, canon_level, and optional status', () => {
    const wrapper = mount(CharacterCard, {
      props: { character: baseCharacter },
    });
    expect(wrapper.text()).toContain('林远');
    expect(wrapper.text()).toContain('ESTABLISHED');
    expect(wrapper.text()).toContain('主角');
  });

  it('omits the status span when character.status is falsy', () => {
    const { status, ...rest } = baseCharacter;
    void status;
    const wrapper = mount(CharacterCard, {
      props: { character: rest },
    });
    expect(wrapper.find('.character-card__status').exists()).toBe(false);
  });

  it('applies the slug-derived testid for hub-level selectors', () => {
    const wrapper = mount(CharacterCard, {
      props: { character: baseCharacter },
    });
    expect(wrapper.find('[data-testid="character-card-lin-yuan"]').exists()).toBe(true);
  });
});

describe('CharacterCard — canon_level variant', () => {
  it.each([
    ['draft', 'draft'],
    ['provisional', 'provisional'],
    ['established', 'established'],
  ])('applies character-card--%s class for canon_level=%s', (level, _) => {
    const wrapper = mount(CharacterCard, {
      props: { character: { ...baseCharacter, canon_level: level.toUpperCase() } },
    });
    expect(wrapper.classes()).toContain(`character-card--${level}`);
  });
});

describe('CharacterCard — click emission', () => {
  it('emits click event when the card is clicked', async () => {
    const wrapper = mount(CharacterCard, {
      props: { character: baseCharacter },
    });
    await wrapper.trigger('click');
    expect(wrapper.emitted('click')).toBeTruthy();
    expect(wrapper.emitted('click')).toHaveLength(1);
  });
});
