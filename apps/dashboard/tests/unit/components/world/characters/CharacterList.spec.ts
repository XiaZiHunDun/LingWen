/**
 * Phase 68 — CharacterList.vue unit tests.
 *
 * CharacterList is the World page character grid (Phase 117 Task 13).
 * Lists characters from useWorldDb().listCharacters(), filtered by
 * useWorldStore().canonLevelFilter, and emits selection via the
 * store's selectedCharacterId. 3 filter buttons (Draft/Provisional/
 * Established) toggle the active filter on click.
 *
 * Test setup:
 *  - vi.mock useWorldDb → listCharacters returns test fixtures
 *  - vi.mock CharacterCard + CharacterDetail (stub components)
 *  - useWorldStore is real (Pinia globally set up in tests/unit/setup.ts)
 *
 * 6 tests covering filter UI + selection state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';

// Stub composable.
const listCharactersMock = vi.fn();
vi.mock('@/composables/world/useWorldDb.js', () => ({
  useWorldDb: () => ({
    listCharacters: listCharactersMock,
  }),
}));

// Stub child components (CharacterCard + CharacterDetail) to isolate
// CharacterList behavior from the (already-tested) child component logic.
vi.mock('@/components/world/characters/CharacterCard.vue', () => ({
  default: {
    name: 'CharacterCard',
    props: ['character'],
    emits: ['click'],
    template: '<button class="stub-character-card" :data-testid="`stub-card-${character.slug}`" @click="$emit(\'click\')">{{ character.name }}</button>',
  },
}));

vi.mock('@/components/world/characters/CharacterDetail.vue', () => ({
  default: {
    name: 'CharacterDetail',
    props: ['characterId'],
    emits: ['close'],
    template: '<div v-if="characterId" class="stub-character-detail" :data-testid="`stub-detail-${characterId}`"></div>',
  },
}));

// Import after vi.mock so mocks are in place.
import CharacterList from '@/components/world/characters/CharacterList.vue';
import { useWorldStore } from '@/stores/useWorldStore';

const sampleCharacters = [
  { id: 1, slug: 'lin-yuan', name: '林远', canon_level: 'ESTABLISHED' },
  { id: 2, slug: 'su-wan', name: '苏婉', canon_level: 'DRAFT' },
];

beforeEach(() => {
  setActivePinia(createPinia());
  listCharactersMock.mockReset();
  listCharactersMock.mockResolvedValue(sampleCharacters);
});

// ---------------------------------------------------------------------------
// Filter buttons
// ---------------------------------------------------------------------------

describe('CharacterList — filter buttons', () => {
  it('renders 3 filter buttons (Draft/Provisional/Established)', () => {
    const wrapper = mount(CharacterList);
    const buttons = wrapper.findAll('[data-testid^="character-filter-"]');
    expect(buttons).toHaveLength(3);
    expect(wrapper.find('[data-testid="character-filter-Draft"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-filter-Provisional"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="character-filter-Established"]').exists()).toBe(true);
  });

  it('applies character-filter--active class only to the active filter', async () => {
    const wrapper = mount(CharacterList);
    await flushPromises();
    const store = useWorldStore();
    store.setCanonLevelFilter('Draft');
    await flushPromises();

    const draftBtn = wrapper.find('[data-testid="character-filter-Draft"]');
    expect(draftBtn.classes()).toContain('character-filter--active');

    const provisionalBtn = wrapper.find('[data-testid="character-filter-Provisional"]');
    expect(provisionalBtn.classes()).not.toContain('character-filter--active');
  });

  it('clicking an inactive filter activates it', async () => {
    const wrapper = mount(CharacterList);
    await flushPromises();
    await wrapper.find('[data-testid="character-filter-Provisional"]').trigger('click');

    const store = useWorldStore();
    expect(store.canonLevelFilter).toBe('Provisional');
  });

  it('clicking the active filter clears it (toggles to null)', async () => {
    const wrapper = mount(CharacterList);
    await flushPromises();
    const store = useWorldStore();
    store.setCanonLevelFilter('Established');
    await flushPromises();

    await wrapper.find('[data-testid="character-filter-Established"]').trigger('click');
    expect(store.canonLevelFilter).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Character load + selection
// ---------------------------------------------------------------------------

describe('CharacterList — characters + selection', () => {
  it('loads characters on mount via listCharacters composable', async () => {
    mount(CharacterList);
    await flushPromises();
    expect(listCharactersMock).toHaveBeenCalledTimes(1);
  });

  it('clicking a character card sets store.selectedCharacterId', async () => {
    const wrapper = mount(CharacterList);
    await flushPromises();
    await wrapper.find('[data-testid="stub-card-lin-yuan"]').trigger('click');

    const store = useWorldStore();
    expect(store.selectedCharacterId).toBe(1);
  });
});
