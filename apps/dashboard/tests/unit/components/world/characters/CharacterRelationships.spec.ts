/**
 * Phase 70 — CharacterRelationships.vue unit tests.
 *
 * CharacterRelationships is the embedded subcomponent on the World
 * page (Phase 117 Task 14). Loads relationships for a given
 * character via useWorldDb().listRelationships('character', id),
 * renders them as a list or shows an empty-state message.
 *
 * 5 tests covering load + empty + render + reload on prop change.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const listRelationshipsMock = vi.fn();
vi.mock('@/composables/world/useWorldDb.js', () => ({
  useWorldDb: () => ({
    listRelationships: listRelationshipsMock,
  }),
}));

import CharacterRelationships from '@/components/world/characters/CharacterRelationships.vue';

const sampleRelationships = [
  { id: 1, kind: 'mentor', target_kind: 'character', target_id: 5, notes: '授业恩师' },
  { id: 2, kind: 'rival', target_kind: 'character', target_id: 7, notes: '' },
];

beforeEach(() => {
  listRelationshipsMock.mockReset();
});

// ---------------------------------------------------------------------------
// Container + heading
// ---------------------------------------------------------------------------

describe('CharacterRelationships — container', () => {
  it('renders the testid container + heading', async () => {
    listRelationshipsMock.mockResolvedValue([]);
    const wrapper = mount(CharacterRelationships, { props: { characterId: 1 } });
    await flushPromises();
    expect(wrapper.find('[data-testid="character-relationships"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('关系');
  });
});

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

describe('CharacterRelationships — empty state', () => {
  it('shows the empty-state message when relationships array is empty', async () => {
    listRelationshipsMock.mockResolvedValue([]);
    const wrapper = mount(CharacterRelationships, { props: { characterId: 99 } });
    await flushPromises();
    expect(wrapper.text()).toContain('暂无关系');
    // No relationship items rendered.
    expect(wrapper.findAll('[data-testid^="relationship-"]')).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Render list
// ---------------------------------------------------------------------------

describe('CharacterRelationships — render', () => {
  it('renders one li per relationship with kind → target_kind #target_id', async () => {
    listRelationshipsMock.mockResolvedValue(sampleRelationships);
    const wrapper = mount(CharacterRelationships, { props: { characterId: 1 } });
    await flushPromises();
    const items = wrapper.findAll('[data-testid^="relationship-"]');
    expect(items).toHaveLength(2);
    expect(items[0].text()).toContain('mentor');
    expect(items[0].text()).toContain('character');
    expect(items[0].text()).toContain('#5');
    expect(items[1].text()).toContain('rival');
    expect(items[1].text()).toContain('#7');
  });

  it('includes notes in parentheses when present', async () => {
    listRelationshipsMock.mockResolvedValue(sampleRelationships);
    const wrapper = mount(CharacterRelationships, { props: { characterId: 1 } });
    await flushPromises();
    const items = wrapper.findAll('[data-testid^="relationship-"]');
    expect(items[0].text()).toContain('(授业恩师)');
  });

  it('omits the notes span when notes is empty', async () => {
    listRelationshipsMock.mockResolvedValue([sampleRelationships[1]]);
    const wrapper = mount(CharacterRelationships, { props: { characterId: 1 } });
    await flushPromises();
    const item = wrapper.find('[data-testid="relationship-2"]');
    expect(item.text()).toContain('rival');
    // No parenthetical notes block for empty notes.
    expect(item.text()).not.toContain('()');
  });
});

// ---------------------------------------------------------------------------
// Reload on characterId change
// ---------------------------------------------------------------------------

describe('CharacterRelationships — reload', () => {
  it('calls listRelationships with the current characterId on prop change', async () => {
    listRelationshipsMock.mockResolvedValue([]);
    const wrapper = mount(CharacterRelationships, { props: { characterId: 1 } });
    await flushPromises();
    expect(listRelationshipsMock).toHaveBeenCalledTimes(1);
    expect(listRelationshipsMock).toHaveBeenLastCalledWith('character', 1);

    // Phase 110 fix: cast — component declares characterId only via runtime
    // defineProps so vue-tsc cannot infer the prop type.
    await wrapper.setProps({ characterId: 2 } as Record<string, unknown>);
    await flushPromises();
    expect(listRelationshipsMock).toHaveBeenCalledTimes(2);
    expect(listRelationshipsMock).toHaveBeenLastCalledWith('character', 2);
  });
});
