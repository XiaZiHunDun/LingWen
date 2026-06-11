// dashboard/frontend/tests/unit/cascade-runs-panel.spec.js — Phase 9.22 T2 + Phase 9.23 T5
// CascadeRunsPanel vitest: list historical cascade_runs + Replay + Cancel + WS handler
// Mirror cascade-graph.spec.js pattern: vi.mock('../../src/api/index.js') + vi.mock
//   useWorkflowSocket + globalThis.__cascadeHandlers for WS push injection.
// 3 case (Phase 9.22 T2):
//   - renders_table_with_status_badges_and_cancel_only_for_running
//   - click_replay_fetches_cascade_with_same_max_depth_and_renders_graph
//   - ws_cascade_cancel_event_updates_row_status_to_cancelled
// 3 case (Phase 9.23 T5): filter URL sync
//   - reads filter from route.query on mount and passes to fetchCascadeRuns
//   - changing status filter updates URL via router.replace
//   - watch on route.query reloads runs when query changes (browser back/forward)

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { nextTick, reactive } from 'vue';

// Phase 9.23 T5: vue-router mock (hoisted, so cascade-runs-panel.vue's
// useRoute()/useRouter() return our local refs that tests can mutate).
// mockRoute is reactive so watch(() => route.query) fires on inner-property mutation,
// mirroring how vue-router exposes a reactive RouteLocationNormalized.
const mockRoute = reactive({ query: {} });
const mockRouter = { replace: vi.fn() };
vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter,
}));

// 注入式 mock: capture registered cascade handlers (mirror use-workflow-socket-cascade.spec.js)
const registeredCascadeHandlers = new Set();
globalThis.__cascadeHandlers = registeredCascadeHandlers;

// 局部 mock echarts/core 避免 jsdom "canvas not supported" 错误
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

// 镜像 ripple-drawer-cascade.spec.js: 在 vi.mock factory 内联 vi.fn(),
// 避免 hoisting 撞 top-level const (vi.mock 被提升到 import 之前)
vi.mock('../../src/api/index.js', () => ({
  fetchCascadeRuns: vi.fn(),
  cancelCascadeRun: vi.fn(),
  fetchCascadeWithDepth: vi.fn(),
}));

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  onCascadeUpdate: vi.fn((handler) => {
    registeredCascadeHandlers.add(handler);
  }),
}));

const FAKE_RUNS = [
  { id: 1, ripple_id: 'rip-1', started_at: '2026-06-11T10:00:00Z', completed_at: '2026-06-11T10:00:05Z',
    max_depth: 3, depth_reached: 2, status: 'completed', algorithm_version: 'v2_weighted',
    cascade_nodes: [], cascade_edges: [], cascade_actions: [] },
  { id: 2, ripple_id: 'rip-1', started_at: '2026-06-11T11:00:00Z', completed_at: null,
    max_depth: 5, depth_reached: 0, status: 'running', algorithm_version: 'v2_weighted',
    cascade_nodes: [], cascade_edges: [], cascade_actions: [] },
  { id: 3, ripple_id: 'rip-1', started_at: '2026-06-11T09:00:00Z', completed_at: '2026-06-11T09:00:02Z',
    max_depth: 2, depth_reached: 1, status: 'cancelled', algorithm_version: 'v2_weighted',
    cascade_nodes: [], cascade_edges: [], cascade_actions: [] },
];

const FAKE_REPLAY_CASCADE = {
  trigger_ripple_id: 'rip-1',
  cascade_nodes: [{ id: 'n1', dimension: 'character', volume: 1, chapter: 1, title: 't', description: '', payload: {} }],
  cascade_edges: [],
  cascade_actions: [],
  depth_reached: 1,
  generated_at: '2026-06-11T12:00:00Z',
  bfs_algorithm_version: 'v2_weighted',
};

let mockFetchCascadeRuns;
let mockCancelCascadeRun;
let mockFetchCascadeWithDepth;
let CascadeRunsPanel;

beforeEach(async () => {
  // 动态 import 获取已 mock 的模块引用 (镜像 ripple-drawer-cascade.spec.js 模式)
  const api = await import('../../src/api/index.js');
  mockFetchCascadeRuns = api.fetchCascadeRuns;
  mockCancelCascadeRun = api.cancelCascadeRun;
  mockFetchCascadeWithDepth = api.fetchCascadeWithDepth;

  // 动态 import component (避免 top-level import 跟 vi.mock hoist 冲突)
  const mod = await import('../../src/components/CascadeRunsPanel.vue');
  CascadeRunsPanel = mod.default;

  mockFetchCascadeRuns.mockReset();
  mockCancelCascadeRun.mockReset();
  mockFetchCascadeWithDepth.mockReset();
  registeredCascadeHandlers.clear();
  mockFetchCascadeRuns.mockResolvedValue(FAKE_RUNS);
  mockCancelCascadeRun.mockResolvedValue({ ...FAKE_RUNS[1], status: 'cancelled', completed_at: '2026-06-11T11:30:00Z' });
  mockFetchCascadeWithDepth.mockResolvedValue(FAKE_REPLAY_CASCADE);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('CascadeRunsPanel.vue', () => {
  it('renders_table_with_status_badges_and_cancel_only_for_running', async () => {
    const wrapper = mount(CascadeRunsPanel, { props: { rippleId: 'rip-1' } });
    await flushPromises();
    const rows = wrapper.findAll('[data-testid="cascade-run-row"]');
    expect(rows).toHaveLength(3);
    // 2nd row (id=2) is running → should have cancel button
    expect(rows[1].find('[data-testid="cancel-btn"]').exists()).toBe(true);
    // 1st row (id=1) is completed → no cancel button
    expect(rows[0].find('[data-testid="cancel-btn"]').exists()).toBe(false);
    // 3rd row (id=3) is cancelled → no cancel button
    expect(rows[2].find('[data-testid="cancel-btn"]').exists()).toBe(false);
    // All rows have status badges
    expect(rows[0].find('[data-testid="status-badge-completed"]').exists()).toBe(true);
    expect(rows[1].find('[data-testid="status-badge-running"]').exists()).toBe(true);
    expect(rows[2].find('[data-testid="status-badge-cancelled"]').exists()).toBe(true);
  });

  it('click_replay_fetches_cascade_with_same_max_depth_and_renders_graph', async () => {
    const wrapper = mount(CascadeRunsPanel, { props: { rippleId: 'rip-1' } });
    await flushPromises();
    // Click Replay on run id=2 (max_depth=5, running)
    const rows = wrapper.findAll('[data-testid="cascade-run-row"]');
    await rows[1].find('[data-testid="replay-btn"]').trigger('click');
    await flushPromises();
    // fetchCascadeWithDepth called with (rip-1, 5) — same max_depth as run
    expect(mockFetchCascadeWithDepth).toHaveBeenCalledWith('rip-1', 5);
    // Replay panel + cascade-graph visible
    expect(wrapper.find('[data-testid="cascade-runs-replay"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="replay-graph"]').exists()).toBe(true);
    // Replay note shows run #2
    expect(wrapper.find('[data-testid="replay-note"]').text()).toContain('#2');
  });

  it('ws_cascade_cancel_event_updates_row_status_to_cancelled', async () => {
    const wrapper = mount(CascadeRunsPanel, { props: { rippleId: 'rip-1' } });
    await flushPromises();
    // Simulate WS cascade.cancel event for run id=2 (Phase 9.21 payload)
    for (const h of registeredCascadeHandlers) {
      h({ type: 'cascade.cancel', payload: { run_id: 2, ripple_id: 'rip-1', status: 'cancelled', reason: '' } });
    }
    await flushPromises();
    // 2nd row status badge should be cancelled now
    const rows = wrapper.findAll('[data-testid="cascade-run-row"]');
    expect(rows[1].find('[data-testid="status-badge-cancelled"]').exists()).toBe(true);
    // Cancel button should be gone (no longer running)
    expect(rows[1].find('[data-testid="cancel-btn"]').exists()).toBe(false);
  });
});

// Phase 9.23 T5: CascadeRunsPanel URL sync (vue-router mock + filter propagation)
describe('Phase 9.23: CascadeRunsPanel filter URL sync', () => {
  // Mocked fetchCascadeRuns in this describe uses 1-row FAKE_RUNS to keep
  // assertions deterministic; existing top-level vi.mock('../../src/api/index.js')
  // factory is shared with the Phase 9.22 suite, so we still reference
  // mockFetchCascadeRuns via the same beforeEach dynamic-import pattern.

  beforeEach(() => {
    // Reset URL mock state per test
    mockRoute.query = {};
    mockRouter.replace.mockClear();
    registeredCascadeHandlers.clear();
  });

  it('reads filter from route.query on mount and passes to fetchCascadeRuns', async () => {
    mockRoute.query = { status: 'cancelled', min_depth: '2' };
    const { default: Panel } = await import('../../src/components/CascadeRunsPanel.vue');
    mount(Panel, { props: { rippleId: 'rip-1' } });
    // onMounted → loadRuns is async; wait for fetchCascadeRuns to fire
    await new Promise((r) => setTimeout(r, 50));
    expect(mockFetchCascadeRuns).toHaveBeenCalledWith(
      'rip-1',
      expect.objectContaining({ status: 'cancelled', minDepth: 2 }),
    );
  });

  it('changing status filter updates URL via router.replace', async () => {
    const { default: Panel } = await import('../../src/components/CascadeRunsPanel.vue');
    const wrapper = mount(Panel, { props: { rippleId: 'rip-1' } });
    await new Promise((r) => setTimeout(r, 50));
    // Simulate filter change by emitting update:modelValue on the child
    const filter = wrapper.findComponent({ name: 'CascadeRunsFilter' });
    expect(filter.exists()).toBe(true);
    await filter.vm.$emit('update:modelValue', {
      status: 'cancelled', minDepth: null, maxDepth: null, algorithm: 'all',
    });
    await nextTick();
    expect(mockRouter.replace).toHaveBeenCalledWith({ query: { status: 'cancelled' } });
  });

  it('watch on route.query reloads runs when query changes (browser back/forward)', async () => {
    // Reset query to empty (initial mount sees no filter → loads all runs)
    mockRoute.query = {};
    const { default: Panel } = await import('../../src/components/CascadeRunsPanel.vue');
    mount(Panel, { props: { rippleId: 'rip-1' } });
    await new Promise((r) => setTimeout(r, 50));
    mockFetchCascadeRuns.mockClear();
    // Simulate browser back/forward: vue-router reassigns the reactive route.query
    // ref to a new object on URL change, mirroring real production behavior.
    mockRoute.query = { status: 'running' };
    await nextTick();
    await new Promise((r) => setTimeout(r, 50));
    expect(mockFetchCascadeRuns.mock.calls.length).toBeGreaterThan(0);
    const lastCall = mockFetchCascadeRuns.mock.calls[mockFetchCascadeRuns.mock.calls.length - 1];
    expect(lastCall[1]).toEqual(expect.objectContaining({ status: 'running' }));
  });
});
