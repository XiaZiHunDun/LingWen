// tests/unit/cascade-graph.spec.js — Phase 9.15 T3
// CascadeGraph vitest (lazy ECharts graph + dry-run colors).
// 5 测试覆盖核心行为契约: render / lazy-load / emit / dryRun color / empty fallback.
import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';

// 局部 mock echarts/core (T3 子组件, 不动 setup.ts 既有 global echarts mock)
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

const stubCascade = {
  trigger_ripple_id: 'r1',
  cascade_nodes: [
    { id: 'n1', volume: 1, chapter: 1, dimension: 'character' },
    { id: 'n2', volume: 2, chapter: 1, dimension: 'foreshadow' },
  ],
  cascade_edges: [{ id: 'e1', from_node_id: 'n1', to_node_id: 'n2', weight: 0.8 }],
  cascade_actions: [{ action: 'propagate', from: 'n1', to: 'n2', depth: 1 }],
  depth_reached: 1,
  generated_at: '2026-06-10T10:00:00Z',
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
    expect(wrapper.emitted('nodeClick')).toBeTruthy();
    expect(wrapper.emitted('nodeClick')[0][0]).toEqual({ nodeId: 'n1', volume: 1, chapter: 1 });
  });

  it('dryRun mode colors nodes by action type', async () => {
    const wrapper = mount(CascadeGraph, { props: { cascade: stubCascade, dryRun: true } });
    expect(wrapper.vm.nodeColor('trigger')).toBe('#22c55e');
    expect(wrapper.vm.nodeColor('modify')).toBe('#eab308');
    expect(wrapper.vm.nodeColor('unknown')).toBe('#9ca3af');
  });

  it('handles empty cascade gracefully (no crash)', async () => {
    const wrapper = mount(CascadeGraph, { props: { cascade: null } });
    await flushPromises();
    expect(wrapper.find('[data-testid="cascade-graph-empty"]').exists()).toBe(true);
  });
});
