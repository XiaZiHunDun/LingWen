// Phase 9.46 F35: CascadeRunsPage global view vitest
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

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

vi.mock('../../src/api/index.js', () => ({
  fetchAllCascadeRuns: vi.fn(),
  fetchCascadeRuns: vi.fn(),
  cancelCascadeRun: vi.fn(),
  fetchCascadeWithDepth: vi.fn(),
}));

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  onCascadeUpdate: vi.fn(() => () => {}),
}));

const FAKE_RUNS = [
  {
    id: 10,
    ripple_id: 'rip-a',
    started_at: '2026-06-11T10:00:00Z',
    completed_at: '2026-06-11T10:00:05Z',
    max_depth: 3,
    depth_reached: 2,
    status: 'completed',
    algorithm: 'v2_weighted',
    cascade_nodes: [],
    cascade_edges: [],
    cascade_actions: [],
  },
  {
    id: 11,
    ripple_id: 'rip-b',
    started_at: '2026-06-11T11:00:00Z',
    completed_at: null,
    max_depth: 5,
    depth_reached: 0,
    status: 'running',
    algorithm: 'v1',
    cascade_nodes: [],
    cascade_edges: [],
    cascade_actions: [],
  },
];

let mockFetchAllCascadeRuns;
let CascadeRunsPage;

beforeEach(async () => {
  const api = await import('../../src/api/index.js');
  mockFetchAllCascadeRuns = api.fetchAllCascadeRuns;
  mockFetchAllCascadeRuns.mockReset();
  mockFetchAllCascadeRuns.mockResolvedValue(FAKE_RUNS);
  const mod = await import('../../src/pages/CascadeRunsPage.vue');
  CascadeRunsPage = mod.default;
  window.history.replaceState(window.history.state, '', window.location.pathname);
});

describe('CascadeRunsPage.vue', () => {
  it('renders_page_and_global_table_with_ripple_column', async () => {
    const wrapper = mount(CascadeRunsPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="cascade-runs-page"]').exists()).toBe(true);
    expect(mockFetchAllCascadeRuns).toHaveBeenCalled();
    const rippleCells = wrapper.findAll('[data-testid="cascade-run-ripple"]');
    expect(rippleCells).toHaveLength(2);
    expect(rippleCells[0].text()).toBe('rip-a');
  });

  it('shows_global_filter_controls', async () => {
    const wrapper = mount(CascadeRunsPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="filter-ripple-id"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="filter-since-days"]').exists()).toBe(true);
  });

  it('passes_status_filter_to_fetch_all_cascade_runs', async () => {
    window.history.replaceState(window.history.state, '', '?status=completed');
    mount(CascadeRunsPage);
    await flushPromises();
    expect(mockFetchAllCascadeRuns).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'completed' }),
    );
  });
});
