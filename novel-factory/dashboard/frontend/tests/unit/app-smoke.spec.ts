// tests/unit/app-smoke.spec.ts — Phase 9.31 F15
// 替代 tests/e2e-smoke/smoke.spec.js (4 tests, @vue/test-utils + jsdom)

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'
import { apiConnectivity } from '../../src/api/connectivity.js'
import { useStudioProject } from '../../src/composables/useStudioProject.js'

const studioSingleton = useStudioProject()

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
  fetchStudioProseDiff: vi.fn().mockResolvedValue(null),
  fetchStudioProseJudge: vi.fn().mockResolvedValue(null),
  fetchCreatorOnboarding: vi.fn(),
  fetchHealth: vi.fn().mockResolvedValue({ status: 'healthy', service: 'reading-power-dashboard' }),
  fetchProductionRollup: vi.fn().mockResolvedValue(null),
  fetchProductionRecords: vi.fn().mockResolvedValue({ records: [] }),
  fetchProductionRecordsTrend: vi.fn().mockResolvedValue(null),
  queryCreatorMemory: vi.fn().mockResolvedValue({ hits: [] }),
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
  fetchStudioProseDiff: mocks.fetchStudioProseDiff,
  fetchStudioProseJudge: mocks.fetchStudioProseJudge,
  fetchCreatorOnboarding: mocks.fetchCreatorOnboarding,
  fetchHealth: mocks.fetchHealth,
  fetchProductionRollup: mocks.fetchProductionRollup,
  fetchProductionRecords: mocks.fetchProductionRecords,
  fetchProductionRecordsTrend: mocks.fetchProductionRecordsTrend,
  queryCreatorMemory: mocks.queryCreatorMemory,
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
    studioSingleton.projects.value = []
    studioSingleton.activeSlug.value = null
    studioSingleton.summary.value = null
    mocks.connected.value = true
    apiConnectivity.value = { offline: false, message: '', checking: false }
    mocks.fetchHealth.mockResolvedValue({ status: 'healthy', service: 'reading-power-dashboard' })
    mocks.fetchStudioProjects.mockResolvedValue({
      projects: [{ slug: 'anye-xinbiao', name: '暗夜信标', role: 'production' }],
      active_slug: 'anye-xinbiao',
    })
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
      outlines_present: 0,
      missing_outlines: [],
      missing_bodies: [],
      pillars_ok: true,
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

  test('human-first shell shows header project switcher and settings nav', async () => {
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('nav-settings')).exists()).toBe(true)
    expect(wrapper.find(byTestid('sidebar-system-panel')).exists()).toBe(false)
    expect(wrapper.find(byTestid('project-switcher')).exists()).toBe(true)
    await wrapper.find(byTestid('nav-ask')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('header-l1-page-name')).exists()).toBe(false)
    expect(wrapper.find(byTestid('ask-page-tabs')).exists()).toBe(true)
    expect(wrapper.find(byTestid('ask-tab-chat')).exists()).toBe(true)
  })

  test('app-root smart lands on write when project has chapters', async () => {
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('app-root')).exists()).toBe(true)
    expect(wrapper.find(byTestid('header-l1-page-name')).text()).toBe('书桌')
    expect(wrapper.find(byTestid('header-context-title')).exists()).toBe(false)
    expect(wrapper.find(byTestid('creation-mode-hint')).exists()).toBe(false)
    expect(wrapper.find(byTestid('sidebar-mode-hint')).exists()).toBe(false)
  })

  test('app-root lands on ask for new project', async () => {
    mocks.fetchCreatorOverview.mockResolvedValue({
      name: '新书',
      creation_mode: 'companion',
      chapters_written: 0,
      max_chapter: 0,
      coverage_pct: 0,
      alert_count: 0,
      p0_count: 0,
    })
    window.history.replaceState(null, '', '/')
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('ask-page')).exists()).toBe(true)
  })

  async function openMoreLink(wrapper, linkId) {
    await wrapper.find(byTestid('nav-more')).trigger('click')
    await flushPromises()
    await wrapper.find(byTestid(`more-link-${linkId}`)).trigger('click')
    await flushPromises()
  }

  test('more → produce → workflows shows WorkflowsPage', async () => {
    mocks.fetchStudioSummary.mockResolvedValue({
      name: '暗夜信标',
      slug: 'anye-xinbiao',
      creation_mode: 'advance',
    })
    const wrapper = mount(App)
    await flushPromises()
    await openMoreLink(wrapper, 'produce')
    await wrapper.find(byTestid('produce-tabs-workflows')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('header-l1-page-name')).text()).toBe('生产')
    expect(wrapper.text()).toContain('工作流')
  })

  test('more → produce → chapters shows ChaptersPage', async () => {
    mocks.fetchStudioSummary.mockResolvedValue({
      name: '暗夜信标',
      slug: 'anye-xinbiao',
      creation_mode: 'advance',
    })
    const wrapper = mount(App)
    await flushPromises()
    await openMoreLink(wrapper, 'produce')
    await wrapper.find(byTestid('produce-tabs-chapters')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('header-l1-page-name')).text()).toBe('生产')
    expect(wrapper.find(byTestid('chapter-range-select')).exists()).toBe(true)
  })

  test('more → insight → analytics shows analytics hub', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await openMoreLink(wrapper, 'insight')
    await wrapper.find(byTestid('insight-tabs-analytics')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('header-l1-page-name')).text()).toBe('洞察')
    expect(wrapper.text()).toContain('正文生产 KPI')
  })

  test('settings nav shows SettingsPage', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.find(byTestid('nav-settings')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('header-l1-page-name')).text()).toBe('设置')
    expect(wrapper.find(byTestid('system-status-panel')).exists()).toBe(true)
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

  test('companion branded project hides advance toolbox links when backend is advance', async () => {
    mocks.fetchStudioProjects.mockResolvedValue({
      projects: [{ slug: 'demo-companion', name: '创作伴侣', role: 'production' }],
      active_slug: 'demo-companion',
    })
    mocks.fetchStudioSummary.mockResolvedValue({
      name: '创作伴侣',
      slug: 'demo-companion',
      creation_mode: 'advance',
    })
    mocks.fetchCreatorOverview.mockResolvedValue({
      name: '创作伴侣',
      creation_mode: 'advance',
      chapters_written: 0,
      max_chapter: 0,
      coverage_pct: 0,
      alert_count: 0,
      p0_count: 0,
    })
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.find(byTestid('nav-more')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('more-link-produce')).exists()).toBe(false)
    expect(wrapper.find(byTestid('more-link-cascade-runs')).exists()).toBe(false)
    expect(wrapper.find(byTestid('more-link-today')).exists()).toBe(true)
  })

  test('companion mode hides produce nav', async () => {
    mocks.fetchStudioSummary.mockResolvedValue({
      name: '暗夜信标',
      slug: 'anye-xinbiao',
      creation_mode: 'companion',
    })
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('nav-write')).exists()).toBe(true)
    expect(wrapper.find(byTestid('nav-ask')).exists()).toBe(true)
    expect(wrapper.find(byTestid('nav-produce')).exists()).toBe(false)
    expect(wrapper.find(byTestid('sidebar-mode-hint')).exists()).toBe(false)
  })

  test('studio mode hides write nav', async () => {
    mocks.fetchStudioSummary.mockResolvedValue({
      name: '暗夜信标',
      slug: 'anye-xinbiao',
      creation_mode: 'studio',
    })
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.find(byTestid('nav-write')).exists()).toBe(false)
    expect(wrapper.find(byTestid('nav-ask')).exists()).toBe(true)
    expect(wrapper.find(byTestid('nav-more')).exists()).toBe(true)
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

  test('network offline shows global banner and hides page duplicate', async () => {
    window.history.replaceState(null, '', '/?nav=produce&tab=studio')
    vi.resetModules()
    const networkMsg = 'Network error: Unable to connect to /api. Is the server running?'
    mocks.fetchHealth.mockRejectedValue(new Error(networkMsg))
    mocks.fetchStudioSummary.mockRejectedValue(new Error(networkMsg))
    mocks.fetchStudioQuality.mockRejectedValue(new Error(networkMsg))
    mocks.fetchStudioQualityReport.mockRejectedValue(new Error(networkMsg))
    apiConnectivity.value = { offline: true, message: networkMsg, checking: false }
    const { default: FreshApp } = await import('../../src/App.vue')
    const wrapper = mount(FreshApp)
    await flushPromises()
    expect(wrapper.find(byTestid('api-offline-banner')).exists()).toBe(true)
    expect(wrapper.find(byTestid('api-offline-banner')).text()).toContain('Unable to connect')
    const pageErrors = wrapper.findAll(byTestid('error-banner'))
    expect(pageErrors.some((el) => el.text().includes('Unable to connect'))).toBe(false)
  })
})
