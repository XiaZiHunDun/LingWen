// tests/unit/app-smoke.spec.ts — Phase 9.31 F15
// 替代 tests/e2e-smoke/smoke.spec.js (4 tests, @vue/test-utils + jsdom)

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchOverview: vi.fn(),
  fetchChapters: vi.fn(),
  fetchAllDecisions: vi.fn(),
  fetchWorkflows: vi.fn(),
  fetchBudgets: vi.fn(),
  fetchBudgetsByTier: vi.fn(),
  connected: { value: true },
  status: {
    value: {
      total_cost_usd: 0.42,
      cost_by_scenario: { chapter_writing: 0.42 },
      cost_by_tier: {},
      cost_budget_status: {},
    },
  },
}))

vi.mock('../../src/api/index.js', () => ({
  fetchOverview: mocks.fetchOverview,
  fetchChapters: mocks.fetchChapters,
  fetchAllDecisions: mocks.fetchAllDecisions,
  resolveDecision: vi.fn(),
  deferDecision: vi.fn(),
  cancelDecision: vi.fn(),
  fetchWorkflows: mocks.fetchWorkflows,
  fetchWorkflowGraph: vi.fn(),
  runWorkflow: vi.fn(),
  resumeWorkflow: vi.fn(),
  fetchRipples: vi.fn().mockResolvedValue([]),
  fetchRippleStats: vi.fn().mockResolvedValue({ total: 0, by_status: {}, by_volume: {} }),
  fetchBudgets: mocks.fetchBudgets,
  fetchBudgetsByTier: mocks.fetchBudgetsByTier,
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: mocks.status,
    pendingDecisions: { value: [] },
    connected: mocks.connected,
    lastError: { value: null },
    sendKeepAlive: vi.fn(),
    reconnect: vi.fn(),
  }),
}))

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => ({
    timeWindow: ref('all'),
    windowedCost: ref(null),
    setTimeWindow: vi.fn(),
  }),
}))

import App from '../../src/App.vue'

describe('App smoke (Phase 9.31 F15)', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  beforeEach(() => {
    mocks.connected.value = true
    mocks.fetchOverview.mockResolvedValue({
      total_chapters: 10,
      total_hooks: 100,
      avg_hook_strength: 0.7,
      total_coolpoints: 50,
      avg_coolpoint_density: 5,
    })
    mocks.fetchChapters.mockResolvedValue({ chapters: [] })
    mocks.fetchAllDecisions.mockResolvedValue([])
    mocks.fetchWorkflows.mockResolvedValue([])
    mocks.fetchBudgets.mockResolvedValue({
      per_run: { budget_usd: 1, used_usd: 0, used_pct: 0, status: 'ok' },
      per_day: {},
      per_week: {},
    })
    mocks.fetchBudgetsByTier.mockResolvedValue({ haiku: null, sonnet: null, opus: null })
  })

  test('app-root renders overview by default', async () => {
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('app-root')).exists()).toBe(true)
    expect(wrapper.find(byTestid('page-title')).text()).toBe('追读力总览')
  })

  test('click 工作流 nav shows WorkflowsPage', async () => {
    const wrapper = mount(App)
    await flushPromises()
    const nav = wrapper.findAll('.nav-item').find((n) => n.text().includes('工作流'))
    expect(nav).toBeTruthy()
    await nav!.trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('工作流')
  })

  test('click 章节 nav shows ChaptersPage', async () => {
    const wrapper = mount(App)
    await flushPromises()
    const nav = wrapper.findAll('.nav-item').find((n) => n.text().includes('章节'))
    expect(nav).toBeTruthy()
    await nav!.trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('章节管理')
  })

  test('click 分析 nav shows AnalyticsPage', async () => {
    const wrapper = mount(App)
    await flushPromises()
    const nav = wrapper.findAll('.nav-item').find((n) => n.text().includes('分析'))
    expect(nav).toBeTruthy()
    await nav!.trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('数据分析')
    expect(wrapper.find(byTestid('production-kpi')).exists()).toBe(true)
  })

  test('click 设置 nav shows SettingsPage', async () => {
    const wrapper = mount(App)
    await flushPromises()
    const nav = wrapper.findAll('.nav-item').find((n) => n.text().includes('设置'))
    expect(nav).toBeTruthy()
    await nav!.trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('系统设置')
    expect(wrapper.find(byTestid('budget-panel')).exists()).toBe(true)
  })

  test('WS connected hides disconnected banner (realtime indicator ok)', async () => {
    vi.useFakeTimers()
    const wrapper = mount(App)
    await flushPromises()
    vi.advanceTimersByTime(200)
    await flushPromises()
    expect(wrapper.find(byTestid('ws-disconnected-banner')).exists()).toBe(false)
    vi.useRealTimers()
  })

  test('overview error banner on API failure', async () => {
    window.history.replaceState(null, '', '/')
    vi.resetModules()
    mocks.fetchOverview.mockRejectedValue(new Error('api down'))
    mocks.fetchChapters.mockRejectedValue(new Error('api down'))
    const { default: FreshApp } = await import('../../src/App.vue')
    const wrapper = mount(FreshApp)
    await flushPromises()
    expect(wrapper.find(byTestid('error-banner')).exists()).toBe(true)
    expect(wrapper.find(byTestid('error-banner')).text()).toContain('api down')
  })
})
