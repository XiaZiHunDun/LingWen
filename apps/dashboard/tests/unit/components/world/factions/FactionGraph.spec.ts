/**
 * Phase 72 — FactionGraph.vue unit tests.
 *
 * FactionGraph is the faction page view-mode toggle (Phase 117
 * Task 16). Renders toolbar with 2 toggle buttons (list / graph)
 * + the corresponding view body. list mode shows faction cards;
 * graph mode renders FactionGraphCanvas stub. Selection state
 * reuses store.selectedCharacterId (intentional, per source comment).
 *
 * 7 tests covering view toggle + list rendering + selection.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';

// Stub composable.
const listFactionsMock = vi.fn();
const listRelationshipsMock = vi.fn();
vi.mock('@/composables/world/useWorldDb.js', () => ({
  useWorldDb: () => ({
    listFactions: listFactionsMock,
    listRelationships: listRelationshipsMock,
  }),
}));

// Stub child components.
vi.mock('@/components/world/factions/FactionGraphCanvas.vue', () => ({
  default: {
    name: 'FactionGraphCanvas',
    props: ['factions', 'relationships'],
    template: '<div data-testid="stub-faction-graph-canvas" :data-factions-count="(factions || []).length" :data-relationships-count="(relationships || []).length"></div>',
  },
}));
vi.mock('@/components/world/factions/FactionDetail.vue', () => ({
  default: {
    name: 'FactionDetail',
    props: ['faction'],
    emits: ['close'],
    template: '<aside v-if="faction" data-testid="stub-faction-detail" :data-faction-id="faction.id"></aside>',
  },
}));

// Import after vi.mock so mocks are in place.
import FactionGraph from '@/components/world/factions/FactionGraph.vue';
import { useWorldStore } from '@/stores/useWorldStore';

const sampleFactions = [
  { id: 10, slug: 'golden-sword', name: '金剑盟' },
  { id: 11, slug: 'azure-dragon', name: '青龙帮' },
];

beforeEach(() => {
  setActivePinia(createPinia());
  listFactionsMock.mockReset();
  listRelationshipsMock.mockReset();
  listFactionsMock.mockResolvedValue(sampleFactions);
  listRelationshipsMock.mockResolvedValue([]);
});

// ---------------------------------------------------------------------------
// Render defaults
// ---------------------------------------------------------------------------

describe('FactionGraph — render defaults', () => {
  it('renders the page container testid', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    expect(wrapper.find('[data-testid="faction-graph-page"]').exists()).toBe(true);
  });

  it('renders toolbar with list + graph toggle buttons', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    expect(wrapper.find('[data-testid="faction-graph-view-list"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="faction-graph-view-graph"]').exists()).toBe(true);
  });

  it('defaults to list view (renders faction list, hides graph canvas)', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    expect(wrapper.find('[data-testid="faction-list"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="stub-faction-graph-canvas"]').exists()).toBe(false);
    // List toggle has is-active class.
    expect(wrapper.find('[data-testid="faction-graph-view-list"]').classes()).toContain('is-active');
  });
});

// ---------------------------------------------------------------------------
// View toggle
// ---------------------------------------------------------------------------

describe('FactionGraph — view toggle', () => {
  it('switches to graph view on 关系图 click (renders canvas stub)', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    await wrapper.find('[data-testid="faction-graph-view-graph"]').trigger('click');
    expect(wrapper.find('[data-testid="stub-faction-graph-canvas"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="faction-list"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="faction-graph-view-graph"]').classes()).toContain('is-active');
  });

  it('switches back to list view on 列表 click', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    await wrapper.find('[data-testid="faction-graph-view-graph"]').trigger('click');
    await wrapper.find('[data-testid="faction-graph-view-list"]').trigger('click');
    expect(wrapper.find('[data-testid="faction-list"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="stub-faction-graph-canvas"]').exists()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Selection state
// ---------------------------------------------------------------------------

describe('FactionGraph — selection', () => {
  it('renders faction cards with slug-based testids', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    expect(wrapper.find('[data-testid="faction-card-golden-sword"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="faction-card-azure-dragon"]').exists()).toBe(true);
  });

  it('clicking a faction card sets store.selectedCharacterId (reused for faction)', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    await wrapper.find('[data-testid="faction-card-golden-sword"]').trigger('click');

    const store = useWorldStore();
    // Source intentionally reuses selectedCharacterId for faction selection.
    expect(store.selectedCharacterId).toBe(10);
  });

  it('renders FactionDetail when a faction is selected via store', async () => {
    const wrapper = mount(FactionGraph);
    await flushPromises();
    const store = useWorldStore();
    store.selectedCharacterId = 10;
    await flushPromises();
    expect(wrapper.find('[data-testid="stub-faction-detail"]').exists()).toBe(true);
  });
});
