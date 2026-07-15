// tests/unit/analytics-page.spec.ts — Phase 9.77 F67
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import AnalyticsPage from '../../src/pages/AnalyticsPage.vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchProductionRollup: vi.fn(),
  fetchProductionCostTrend: vi.fn(),
  overview: {
    overview: { value: { total_chapters: 10 } },
    chapters: {
      value: [{ chapter: 1, hook_count: 2, coolpoint_count: 1 }],
    },
    loading: { value: false },
    lastError: { value: null },
    refresh: vi.fn().mockResolvedValue(undefined),
  },
  ripple: {
    stats: { value: { total: 3, by_status: { open: 1, resolved: 2 } } },
    lastError: { value: null },
    refresh: vi.fn().mockResolvedValue(undefined),
  },
  status: {
    value: {
      is_active: true,
      workflow_name: 'novel_writing',
      paused: false,
      completed: 7,
      failed: 0,
      total_cost_usd: 0.05,
      pending_decisions: [],
      production_summary: {
        chapter_num: 12,
        memory_context_source: 'stub',
        emit_chapter_completed: true,
      },
    },
  },
}))

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...(actual as object),
    fetchProductionRollup: mocks.fetchProductionRollup,
    fetchProductionCostTrend: mocks.fetchProductionCostTrend,
  }
})

vi.mock('../../src/composables/useOverviewStore.js', () => ({
  useOverviewStore: () => mocks.overview,
}))

vi.mock('../../src/composables/useRippleStore.js', () => ({
  useRippleStore: () => mocks.ripple,
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: mocks.status,
    connected: { value: true },
    lastError: { value: null },
  }),
}))

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    activeSlug: { value: 'anye-xinbiao' },
    projectRevision: { value: 0 },
  }),
}))

vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    dispose: vi.fn(),
    resize: vi.fn(),
  })),
  use: vi.fn(),
}))

describe('AnalyticsPage (F67/F81/F87)', () => {
  beforeEach(() => {
    mocks.overview.lastError.value = null
    mocks.ripple.lastError.value = null
    mocks.fetchProductionCostTrend.mockResolvedValue({
      point_count: 2,
      total_cost_usd: 0.108,
      points: [
        {
          recorded_at: '2026-06-11T00:00:00Z',
          record_id: 'ch360',
          record_type: 'pilot',
          label: 'ch360',
          incremental_cost_usd: 0.025,
          cumulative_cost_usd: 0.025,
        },
        {
          recorded_at: '2026-06-11T01:00:00Z',
          record_id: 'batch-361-363',
          record_type: 'batch',
          label: 'ch361-363',
          incremental_cost_usd: 0.083,
          cumulative_cost_usd: 0.108,
        },
      ],
    })
    mocks.fetchProductionRollup.mockResolvedValue({
      records_dir: '/tmp/projects/anye-xinbiao/.state/pilot_records',
      record_count: 5,
      pilot_count: 4,
      batch_count: 1,
      total_cost_usd: 0.108,
      chapters_with_records: 4,
      latest_recorded_at: '2026-06-11T02:00:00Z',
      batches: [{
        record_id: 'batch-361-363',
        chapter_range: '361-363',
        total_cost_usd: 0.083,
        stopped_reason: 'completed',
        recorded_at: '2026-06-11T01:00:00Z',
        source_file: 'batch-361-363.json',
      }],
    })
  })

  test('renders title and KPI sections', async () => {
    const wrapper = mount(AnalyticsPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('数据分析')
    expect(wrapper.find(byTestid('production-kpi')).exists()).toBe(true)
    expect(wrapper.find(byTestid('production-rollup-kpi')).exists()).toBe(true)
    expect(wrapper.find(byTestid('production-cost-trend-kpi')).exists()).toBe(true)
    expect(wrapper.find(byTestid('production-cost-trend-chart')).exists()).toBe(true)
    expect(wrapper.find(byTestid('ripple-kpi')).exists()).toBe(true)
    expect(wrapper.text()).toContain('novel_writing')
    expect(wrapper.text()).toContain('章节 #12')
    expect(wrapper.text()).toContain('ch361-363')
    expect(wrapper.text()).toContain('0.1080')
    expect(wrapper.find(byTestid('production-records-dir')).text()).toContain(
      'anye-xinbiao/.state/pilot_records',
    )
  })

  test('refresh calls overview, ripple, rollup, and trend', async () => {
    const wrapper = mount(AnalyticsPage)
    await flushPromises()
    mocks.overview.refresh.mockClear()
    mocks.fetchProductionRollup.mockClear()
    mocks.fetchProductionCostTrend.mockClear()
    await wrapper.find(byTestid('refresh-btn')).trigger('click')
    await flushPromises()
    expect(mocks.overview.refresh).toHaveBeenCalled()
    expect(mocks.ripple.refresh).toHaveBeenCalled()
    expect(mocks.fetchProductionRollup).toHaveBeenCalled()
    expect(mocks.fetchProductionCostTrend).toHaveBeenCalled()
  })
})
