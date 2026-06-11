// tests/unit/impact-graph.spec.ts — Phase 9.41 F30
import { describe, it, expect, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import type { ComponentPublicInstance } from 'vue';

vi.mock('echarts/core', () => ({
  default: {
    init: vi.fn(() => ({ setOption: vi.fn(), on: vi.fn(), clear: vi.fn(), dispose: vi.fn() })),
  },
  init: vi.fn(() => ({ setOption: vi.fn(), on: vi.fn(), clear: vi.fn(), dispose: vi.fn() })),
  use: vi.fn(),
}));
vi.mock('echarts/charts', () => ({ GraphChart: vi.fn() }));
vi.mock('echarts/components', () => ({
  TitleComponent: vi.fn(),
  TooltipComponent: vi.fn(),
  LegendComponent: vi.fn(),
}));
vi.mock('echarts/renderers', () => ({ CanvasRenderer: vi.fn() }));

import ImpactGraph from '../../src/components/ImpactGraph.vue';
import { IMPACT_DIMENSION_COLORS } from '../../src/utils/impactGraphUtils.js';

const sampleGraph = {
  nodes: [
    {
      id: 'n1',
      dimension: 'character',
      volume: 1,
      chapter: 2,
      title: 'Hero',
      description: 'lead',
      payload: {},
    },
    {
      id: 'n2',
      dimension: 'plot_point',
      volume: 2,
      chapter: 4,
      title: 'Climax',
      description: '',
      payload: {},
    },
  ],
  edges: [
    {
      id: 'e1',
      from_node_id: 'n1',
      to_node_id: 'n2',
      relationship_type: 'causes',
      weight: 0.7,
      payload: {},
    },
  ],
  total_node_count: 2,
  total_edge_count: 1,
  truncated: false,
};

type ImpactGraphVm = ComponentPublicInstance & {
  impactNodeColor: (dimension: string) => string;
};

describe('ImpactGraph (Phase 9.41 F30)', () => {
  it('renders title and chart when graph has nodes', async () => {
    const wrapper = mount(ImpactGraph, { props: { graph: sampleGraph } });
    await flushPromises();
    expect(wrapper.find('[data-testid="impact-graph-wrapper"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="impact-graph-title"]').text()).toContain('reference graph');
    expect(wrapper.find('[data-testid="impact-graph"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="impact-graph"]').attributes('data-node-count')).toBe('2');
  });

  it('shows empty state when graph has no nodes', async () => {
    const wrapper = mount(ImpactGraph, {
      props: {
        graph: { nodes: [], edges: [], total_node_count: 0, total_edge_count: 0, truncated: false },
      },
    });
    await flushPromises();
    expect(wrapper.find('[data-testid="impact-graph-empty"]').exists()).toBe(true);
  });

  it('impactNodeColor maps dimensions to palette', () => {
    const wrapper = mount(ImpactGraph, { props: { graph: sampleGraph } });
    const vm = wrapper.vm as unknown as ImpactGraphVm;
    expect(vm.impactNodeColor('character')).toBe(IMPACT_DIMENSION_COLORS.character);
    expect(vm.impactNodeColor('plot_point')).toBe(IMPACT_DIMENSION_COLORS.plot_point);
    expect(vm.impactNodeColor('unknown')).toBe('#9ca3af');
  });

  it('lazy-loads ECharts graph on mount', async () => {
    mount(ImpactGraph, { props: { graph: sampleGraph } });
    await flushPromises();
    const echarts = await import('echarts/core');
    expect(echarts.init).toHaveBeenCalled();
  });

  it('shows truncation warning when graph.truncated', async () => {
    const wrapper = mount(ImpactGraph, {
      props: {
        graph: { ...sampleGraph, truncated: true, total_node_count: 500 },
      },
    });
    await flushPromises();
    expect(wrapper.find('[data-testid="impact-graph-warning"]').exists()).toBe(true);
  });

  it('setOption uses per-dimension colors', async () => {
    const setOptionSpy = vi.fn();
    const echarts = await import('echarts/core');
    vi.mocked(echarts.init).mockReturnValueOnce({
      setOption: setOptionSpy,
      on: vi.fn(),
      clear: vi.fn(),
      dispose: vi.fn(),
    } as unknown as ReturnType<typeof echarts.init>);

    mount(ImpactGraph, { props: { graph: sampleGraph } });
    await flushPromises();

    expect(setOptionSpy).toHaveBeenCalled();
    const option = setOptionSpy.mock.calls[0]![0] as {
      series?: Array<{ data?: Array<{ itemStyle?: { color?: string } }> }>;
      legend?: { data?: string[] };
    };
    const colors = option.series?.[0]?.data?.map((d) => d.itemStyle?.color) ?? [];
    expect(colors).toContain(IMPACT_DIMENSION_COLORS.character);
    expect(colors).toContain(IMPACT_DIMENSION_COLORS.plot_point);
    expect(option.legend?.data).toEqual(expect.arrayContaining(['character', 'plot_point']));
  });
});
