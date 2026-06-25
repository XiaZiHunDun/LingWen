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
  fetchStudioProjects: vi.fn().mockResolvedValue({
    projects: [{ slug: 'anye-xinbiao', name: '暗夜信标', role: 'production' }],
    active_slug: 'anye-xinbiao',
  }),
  fetchStudioSummary: vi.fn(),
  fetchCreatorOverview: vi.fn(),
  fetchPendingDecisions: vi.fn(),
  fetchStudioQuality: vi.fn(),
  fetchStudioQualityReport: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
  fetchCreatorOnboarding: vi.fn(),
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
  fetchStudioProjects: mocks.fetchStudioProjects,
  fetchStudioSummary: mocks.fetchStudioSummary,
  fetchCreatorOverview: mocks.fetchCreatorOverview,
  fetchPendingDecisions: mocks.fetchPendingDecisions,
  fetchStudioQuality: mocks.fetchStudioQuality,
  fetchStudioQualityReport: mocks.fetchStudioQualityReport,
  fetchStudioActiveBatchJob: mocks.fetchStudioActiveBatchJob,
  fetchCreatorOnboarding: mocks.fetchCreatorOnboarding,
  setStudioActive: vi.fn(),
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
    window.history.replaceState(null, '', '/')
    mocks.connected.value = true
    mocks.fetchStudioSummary.mockResolvedValue({
      name: '暗夜信标',
      slug: 'anye-xinbiao',
      creation_mode: 'companion',
    })
    mocks.fetchCreatorOverview.mockResolvedValue({
      name: '暗夜信标',
      creation_mode: 'companion',
      chapters_written: 3,
      max_chapter: 100,
      coverage_pct: 3,
      alert_count: 0,
      p0_count: 0,
    })
    mocks.fetchPendingDecisions.mockResolvedValue([])
    mocks.fetchStudioQuality.mockResolvedValue({
      chapters_written: 3,
      max_chapter: 100,
      coverage_pct: 3,
    })
    mocks.fetchStudioQualityReport.mockResolvedValue({ available: true, p0: 0 })
    mocks.fetchStudioActiveBatchJob.mockResolvedValue({ active: false })
    mocks.fetchCreatorOnboarding.mockResolvedValue({ progress_pct: 100 })
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

  test('app-root renders today by default', async () => {
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('app-root')).exists()).toBe(true)
    expect(wrapper.find(byTestid('page-title')).text()).toBe('今日')
    expect(wrapper.find(byTestid('creation-mode-hint')).text()).toContain('陪伴模式')
  })

  test('click 工作流 nav shows WorkflowsPage inside produce hub', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.find(byTestid('nav-produce')).trigger('click')
    await flushPromises()
    await wrapper.find(byTestid('produce-tabs-workflows')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('生产')
    expect(wrapper.find(byTestid('page-title')).text()).not.toBe('工作流')
    expect(wrapper.text()).toContain('工作流')
  })

  test('click 章节 via produce tab shows ChaptersPage', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.find(byTestid('nav-produce')).trigger('click')
    await flushPromises()
    await wrapper.find(byTestid('produce-tabs-chapters')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('生产')
    expect(wrapper.text()).toContain('章节管理')
  })

  test('click 分析 via insight tab shows analytics inside hub', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.find(byTestid('nav-insight')).trigger('click')
    await flushPromises()
    await wrapper.find(byTestid('insight-tabs-analytics')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('洞察')
    expect(wrapper.text()).toContain('数据分析')
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

  test('reviewer mode shows limited nav and badge', async () => {
    window.history.replaceState(null, '', '/?role=reviewer')
    vi.resetModules()
    const { default: FreshApp } = await import('../../src/App.vue')
    const wrapper = mount(FreshApp)
    await flushPromises()
    expect(wrapper.find(byTestid('reviewer-mode-badge')).exists()).toBe(true)
    expect(wrapper.find(byTestid('nav-produce')).exists()).toBe(false)
    expect(wrapper.find(byTestid('nav-inbox')).exists()).toBe(true)
    expect(wrapper.find(byTestid('nav-insight')).exists()).toBe(true)
  })

  test('overview error banner on API failure', async () => {
    window.history.replaceState(null, '', '/?nav=insight&tab=overview')
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
