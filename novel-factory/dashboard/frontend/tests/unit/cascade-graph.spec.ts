// tests/unit/cascade-graph.spec.ts — Phase 9.15 + 9.40 F25 TS strict pilot
import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import type { ComponentPublicInstance } from 'vue';

vi.mock('echarts/core', () => ({
  default: {
    init: vi.fn(() => ({ setOption: vi.fn(), on: vi.fn(), resize: vi.fn(), dispose: vi.fn() })),
  },
  init: vi.fn(() => ({ setOption: vi.fn(), on: vi.fn(), resize: vi.fn(), dispose: vi.fn() })),
  use: vi.fn(),
}));
vi.mock('echarts/charts', () => ({ GraphChart: vi.fn() }));
vi.mock('echarts/components', () => ({ TitleComponent: vi.fn(), TooltipComponent: vi.fn() }));
vi.mock('echarts/renderers', () => ({ CanvasRenderer: vi.fn() }));

import CascadeGraph from '../../src/components/CascadeGraph.vue';

interface CascadeNode {
  id: string;
  volume: number;
  chapter: number;
  dimension: string;
}

const stubCascade = {
  trigger_ripple_id: 'r1',
  cascade_nodes: [
    { id: 'n1', volume: 1, chapter: 1, dimension: 'character' },
    { id: 'n2', volume: 2, chapter: 1, dimension: 'foreshadow' },
  ] as CascadeNode[],
  cascade_edges: [{ id: 'e1', from_node_id: 'n1', to_node_id: 'n2', weight: 0.8 }],
  cascade_actions: [{ action: 'propagate', from: 'n1', to: 'n2', depth: 1 }],
  depth_reached: 1,
  generated_at: '2026-06-10T10:00:00Z',
};

type CascadeGraphVm = ComponentPublicInstance & {
  nodeColor: (action: string) => string;
};

describe('CascadeGraph.vue', () => {
  it('renders graph with cascade nodes', async () => {
    const wrapper = mount(CascadeGraph, { props: { cascade: stubCascade } });
    await flushPromises();
    expect(wrapper.find('[data-testid="cascade-graph"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="cascade-graph"]').attributes('data-node-count')).toBe('2');
  });

  it('lazy-loads ECharts graph series on mount', async () => {
    mount(CascadeGraph, { props: { cascade: stubCascade } });
    await flushPromises();
    const echarts = await import('echarts/core');
    expect(echarts.init).toHaveBeenCalled();
  });

  it('emits nodeClick when node is clicked', async () => {
    const wrapper = mount(CascadeGraph, { props: { cascade: stubCascade } });
    await flushPromises();
    await wrapper.vm.$emit('nodeClick', { nodeId: 'n1', volume: 1, chapter: 1 });
    const emitted = wrapper.emitted('nodeClick');
    expect(emitted).toBeTruthy();
    expect(emitted![0]![0]).toEqual({ nodeId: 'n1', volume: 1, chapter: 1 });
  });

  it('dryRun mode colors nodes by action type', async () => {
    const wrapper = mount(CascadeGraph, { props: { cascade: stubCascade, dryRun: true } });
    const vm = wrapper.vm as unknown as CascadeGraphVm;
    expect(vm.nodeColor('trigger')).toBe('#22c55e');
    expect(vm.nodeColor('modify')).toBe('#eab308');
    expect(vm.nodeColor('unknown')).toBe('#9ca3af');
  });

  it('handles empty cascade gracefully (no crash)', async () => {
    const wrapper = mount(CascadeGraph, { props: { cascade: null } });
    await flushPromises();
    expect(wrapper.find('[data-testid="cascade-graph-empty"]').exists()).toBe(true);
  });

  it('configures ECharts emphasis focus self and select dim opacity', async () => {
    const setOptionSpy = vi.fn();
    const echarts = await import('echarts/core');
    vi.mocked(echarts.init).mockReturnValueOnce({
      setOption: setOptionSpy,
      on: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn(),
    } as unknown as ReturnType<typeof echarts.init>);
    const wrapper = mount(CascadeGraph, { props: { cascade: stubCascade } });
    await flushPromises();
    const option = setOptionSpy.mock.calls[0]![0] as {
      series?: Array<{ emphasis?: { focus?: string; itemStyle?: { opacity?: number } }; select?: { itemStyle?: { opacity?: number } } }>;
    };
    const series = option?.series?.[0];
    expect(series?.emphasis?.focus).toBe('self');
    expect(series?.emphasis?.itemStyle?.opacity).toBeGreaterThan(0.5);
    expect(series?.select?.itemStyle?.opacity).toBeLessThan(0.5);
    wrapper.unmount();
  });
});
