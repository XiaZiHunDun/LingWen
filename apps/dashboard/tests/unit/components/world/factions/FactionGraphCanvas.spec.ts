/**
 * Phase 73 — FactionGraphCanvas.vue unit tests.
 *
 * FactionGraphCanvas wraps vis-network/standalone's Network class
 * (Phase 117 Task 17). Filters relationships to enemy/ally only,
 * assigns red/green colors, updates via setData on prop change,
 * destroys on unmount.
 *
 * Per MEMORY Phase 118 lesson, vis-network requires install +
 * canvas rendering. We mock the dynamic import to isolate
 * FactionGraphCanvas's data-shape + lifecycle behavior.
 *
 * 6 tests covering mount + data update + unmount.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

// Stub the vis-network/standalone dynamic import.
const setDataMock = vi.fn();
const destroyMock = vi.fn();
const NetworkMock = vi.fn(function () {
  return { setData: setDataMock, destroy: destroyMock };
});

vi.mock('vis-network/standalone', () => ({
  Network: NetworkMock,
}));

// Import after vi.mock so mocks are in place.
import FactionGraphCanvas from '@/components/world/factions/FactionGraphCanvas.vue';

const sampleFactions = [
  { id: 10, slug: 'golden-sword', name: '金剑盟' },
  { id: 11, slug: 'azure-dragon', name: '青龙帮' },
  { id: 12, slug: 'shadow', name: '暗影楼' },
];

beforeEach(() => {
  NetworkMock.mockClear();
  setDataMock.mockClear();
  destroyMock.mockClear();
});

// ---------------------------------------------------------------------------
// Mount
// ---------------------------------------------------------------------------

describe('FactionGraphCanvas — mount', () => {
  it('renders the container testid for hub-level selectors', async () => {
    const wrapper = mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships: [] },
    });
    await flushPromises();
    expect(wrapper.find('[data-testid="faction-graph-canvas"]').exists()).toBe(true);
  });

  it('dynamically imports vis-network and instantiates Network on mount', async () => {
    mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships: [] },
    });
    await flushPromises();
    expect(NetworkMock).toHaveBeenCalledTimes(1);
    // Network receives the container DOM element + data + options.
    // Phase 110 fix: cast — vi.fn() with no explicit signature gives `Mock<[], []>`,
    // so indexed access returns `never`. Cast keeps the test body intact.
    const callArgs = NetworkMock.mock.calls[0] as unknown as [
      HTMLElement,
      { nodes: unknown[]; edges: unknown[] },
      { physics: unknown },
    ];
    expect(callArgs[0]).toBeTruthy(); // container DOM element
    expect(callArgs[1]).toHaveProperty('nodes');
    expect(callArgs[1]).toHaveProperty('edges');
    expect(callArgs[2]).toHaveProperty('physics');
  });

  it('builds nodes from factions (one per faction, prefixed "faction-")', async () => {
    mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships: [] },
    });
    await flushPromises();
    const nodes = (NetworkMock.mock.calls[0] as unknown as [unknown, { nodes: unknown[] }])[1].nodes;
    expect(nodes).toHaveLength(3);
    expect(nodes[0]).toMatchObject({
      id: 'faction-10',
      label: '金剑盟',
      shape: 'box',
    });
  });
});

// ---------------------------------------------------------------------------
// Data updates
// ---------------------------------------------------------------------------

describe('FactionGraphCanvas — data updates', () => {
  it('calls setData when factions prop changes', async () => {
    const wrapper = mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships: [] },
    });
    await flushPromises();
    setDataMock.mockClear();

    const newFactions = [...sampleFactions, { id: 13, slug: 'new', name: '新' }];
    await wrapper.setProps({ factions: newFactions } as Record<string, unknown>);
    await flushPromises();

    expect(setDataMock).toHaveBeenCalledTimes(1);
    expect(setDataMock.mock.calls[0][0].nodes).toHaveLength(4);
  });

  it('filters relationships to enemy/ally only', async () => {
    const relationships = [
      { source_kind: 'faction', source_id: 10, target_kind: 'faction', target_id: 11, kind: 'enemy' },
      { source_kind: 'faction', source_id: 10, target_kind: 'faction', target_id: 12, kind: 'trade' },
      { source_kind: 'faction', source_id: 11, target_kind: 'faction', target_id: 12, kind: 'ally' },
      { source_kind: 'faction', source_id: 10, target_kind: 'faction', target_id: 13, kind: 'rival' },
    ];
    const wrapper = mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships },
    });
    await flushPromises();

    const edges = (NetworkMock.mock.calls[0] as unknown as [unknown, { edges: { color: string }[] }])[1].edges;
    // 4 relationships provided, but only enemy + ally = 2 edges.
    expect(edges).toHaveLength(2);
    expect(edges.map((e: { color: string }) => e.color)).toEqual(
      expect.arrayContaining(['#ef4444', '#10b981']),
    );
  });

  it('assigns red color to enemy edges and green to ally edges', async () => {
    const relationships = [
      { source_kind: 'faction', source_id: 10, target_kind: 'faction', target_id: 11, kind: 'enemy' },
      { source_kind: 'faction', source_id: 11, target_kind: 'faction', target_id: 12, kind: 'ally' },
    ];
    mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships },
    });
    await flushPromises();

    const edges = (NetworkMock.mock.calls[0] as unknown as [unknown, { edges: { color: string; from: string; to: string }[] }])[1].edges;
    const enemyEdge = edges.find((e) => e.color === '#ef4444');
    const allyEdge = edges.find((e) => e.color === '#10b981');
    expect(enemyEdge).toBeDefined();
    expect(enemyEdge!.from).toBe('faction-10');
    expect(enemyEdge!.to).toBe('faction-11');
    expect(allyEdge).toBeDefined();
    expect(allyEdge!.from).toBe('faction-11');
    expect(allyEdge!.to).toBe('faction-12');
  });
});

// ---------------------------------------------------------------------------
// Unmount
// ---------------------------------------------------------------------------

describe('FactionGraphCanvas — unmount', () => {
  it('calls Network.destroy on unmount', async () => {
    const wrapper = mount(FactionGraphCanvas, {
      props: { factions: sampleFactions, relationships: [] },
    });
    await flushPromises();
    expect(destroyMock).not.toHaveBeenCalled();
    wrapper.unmount();
    expect(destroyMock).toHaveBeenCalledTimes(1);
  });
});
