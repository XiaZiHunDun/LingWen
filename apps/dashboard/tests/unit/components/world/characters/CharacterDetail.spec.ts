/**
 * Phase 69 — CharacterDetail.vue unit tests.
 *
 * CharacterDetail is the closeable character sidebar on the World
 * page (Phase 117 Task 14). Loads character via useWorldDb().getCharacter
 * when characterId prop changes, renders name/slug/canon_level/
 * attributes, embeds CharacterRelationships, and has an edit toggle
 * that conditionally renders CharacterEditor.
 *
 * Test setup:
 *  - vi.mock useWorldDb → getCharacter fixture
 *  - vi.mock CharacterRelationships + CharacterEditor (stub components)
 *
 * 7 tests covering render states + close emit + edit toggle.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

// Stub composable.
const getCharacterMock = vi.fn();
vi.mock('@/composables/world/useWorldDb.js', () => ({
  useWorldDb: () => ({
    getCharacter: getCharacterMock,
  }),
}));

// Stub child components (CharacterRelationships + CharacterEditor).
// CharacterRelationships receives :character-id; CharacterEditor receives
// nothing. We add data-testids so the tests can verify their conditional
// rendering driven by CharacterDetail's state.
vi.mock('@/components/world/characters/CharacterRelationships.vue', () => ({
  default: {
    name: 'CharacterRelationships',
    props: ['characterId'],
    template: '<div v-if="characterId" data-testid="stub-character-relationships" :data-character-id="characterId"></div>',
  },
}));
vi.mock('@/components/world/characters/CharacterEditor.vue', () => ({
  default: {
    name: 'CharacterEditor',
    template: '<div data-testid="stub-character-editor"></div>',
  },
}));

// Import after vi.mock so mocks are in place.
import CharacterDetail from '@/components/world/characters/CharacterDetail.vue';

const sampleCharacter = {
  id: 1,
  slug: 'lin-yuan',
  name: '林远',
  canon_level: 'ESTABLISHED',
  attributes: { age: 30, role: '主角' },
};

beforeEach(() => {
  getCharacterMock.mockReset();
});

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

describe('CharacterDetail — render', () => {
  it('renders the container testid for hub-level selectors', async () => {
    getCharacterMock.mockResolvedValue(sampleCharacter);
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();
    expect(wrapper.find('[data-testid="character-detail"]').exists()).toBe(true);
  });

  it('renders character name, slug, canon_level when loaded', async () => {
    getCharacterMock.mockResolvedValue(sampleCharacter);
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();
    expect(wrapper.text()).toContain('林远');
    expect(wrapper.text()).toContain('lin-yuan');
    expect(wrapper.text()).toContain('ESTABLISHED');
    // Loading indicator should be gone after data resolves.
    expect(wrapper.text()).not.toContain('加载中');
  });

  it('renders JSON-stringified attributes when present', async () => {
    getCharacterMock.mockResolvedValue(sampleCharacter);
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();
    expect(wrapper.text()).toContain('age');
    expect(wrapper.text()).toContain('30');
    expect(wrapper.text()).toContain('主角');
  });

  it('renders the embedded CharacterRelationships stub when character loads', async () => {
    getCharacterMock.mockResolvedValue(sampleCharacter);
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();
    const rels = wrapper.find('[data-testid="stub-character-relationships"]');
    expect(rels.exists()).toBe(true);
    expect(rels.attributes('data-character-id')).toBe('1');
  });
});

// ---------------------------------------------------------------------------
// States
// ---------------------------------------------------------------------------

describe('CharacterDetail — states', () => {
  it('renders loading indicator while getCharacter is pending', async () => {
    // Never-resolving promise → component stays in loading state.
    getCharacterMock.mockReturnValue(new Promise(() => {}));
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();
    expect(wrapper.text()).toContain('加载中');
    // No character section should be rendered.
    expect(wrapper.find('.character-detail__name').exists()).toBe(false);
  });

  it('renders no character section when getCharacter resolves to null', async () => {
    getCharacterMock.mockResolvedValue(null);
    const wrapper = mount(CharacterDetail, { props: { characterId: 99 } });
    await flushPromises();
    expect(wrapper.find('.character-detail__name').exists()).toBe(false);
    // No CharacterRelationships either.
    expect(wrapper.find('[data-testid="stub-character-relationships"]').exists()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Close + edit toggle
// ---------------------------------------------------------------------------

describe('CharacterDetail — interactions', () => {
  it('emits close event when close button clicked', async () => {
    getCharacterMock.mockResolvedValue(sampleCharacter);
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();
    await wrapper.find('[data-testid="character-detail-close"]').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
    expect(wrapper.emitted('close')).toHaveLength(1);
  });

  it('toggles CharacterEditor stub on edit-button click', async () => {
    getCharacterMock.mockResolvedValue(sampleCharacter);
    const wrapper = mount(CharacterDetail, { props: { characterId: 1 } });
    await flushPromises();

    // Initially no CharacterEditor (editing=false).
    expect(wrapper.find('[data-testid="stub-character-editor"]').exists()).toBe(false);

    // Click edit toggle → editing=true → CharacterEditor mounts.
    await wrapper.find('[data-testid="character-detail-edit-toggle"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="stub-character-editor"]').exists()).toBe(true);

    // Click toggle again → editing=false → CharacterEditor unmounts.
    await wrapper.find('[data-testid="character-detail-edit-toggle"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="stub-character-editor"]').exists()).toBe(false);
  });
});
