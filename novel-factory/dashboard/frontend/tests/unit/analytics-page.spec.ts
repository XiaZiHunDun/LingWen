// tests/unit/analytics-page.spec.ts — Phase 9.77 F67
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import AnalyticsPage from '../../src/pages/AnalyticsPage.vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
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

vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    dispose: vi.fn(),
    resize: vi.fn(),
  })),
  use: vi.fn(),
}))

describe('AnalyticsPage (F67)', () => {
  beforeEach(() => {
    mocks.overview.lastError.value = null
    mocks.ripple.lastError.value = null
  })

  test('renders title and KPI sections', async () => {
    const wrapper = mount(AnalyticsPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('数据分析')
    expect(wrapper.find(byTestid('production-kpi')).exists()).toBe(true)
    expect(wrapper.find(byTestid('ripple-kpi')).exists()).toBe(true)
    expect(wrapper.text()).toContain('novel_writing')
    expect(wrapper.text()).toContain('章节 #12')
  })

  test('refresh calls overview and ripple stores', async () => {
    const wrapper = mount(AnalyticsPage)
    await flushPromises()
    await wrapper.find(byTestid('refresh-btn')).trigger('click')
    await flushPromises()
    expect(mocks.overview.refresh).toHaveBeenCalled()
    expect(mocks.ripple.refresh).toHaveBeenCalled()
  })
})
