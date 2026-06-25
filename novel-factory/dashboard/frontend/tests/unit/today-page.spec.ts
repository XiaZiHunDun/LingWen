// tests/unit/today-page.spec.ts — Phase A Today hub

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  navigateTo: vi.fn(),
  fetchStudioSummary: vi.fn(),
  fetchCreatorOverview: vi.fn(),
  fetchPendingDecisions: vi.fn(),
  fetchRippleStats: vi.fn(),
  fetchStudioQuality: vi.fn(),
  fetchStudioQualityReport: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
  fetchCreatorOnboarding: vi.fn(),
}))

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    navigateTo: mocks.navigateTo,
  }),
}))

vi.mock('../../src/api/index.js', () => ({
  fetchStudioSummary: mocks.fetchStudioSummary,
  fetchCreatorOverview: mocks.fetchCreatorOverview,
  fetchPendingDecisions: mocks.fetchPendingDecisions,
  fetchRippleStats: mocks.fetchRippleStats,
  fetchStudioQuality: mocks.fetchStudioQuality,
  fetchStudioQualityReport: mocks.fetchStudioQualityReport,
  fetchStudioActiveBatchJob: mocks.fetchStudioActiveBatchJob,
  fetchCreatorOnboarding: mocks.fetchCreatorOnboarding,
}))

import TodayPage from '../../src/pages/TodayPage.vue'
import { resolveTodayPrimaryAction } from '../../src/utils/creationModeHint.js'

function defaultApiMocks() {
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
  mocks.fetchRippleStats.mockResolvedValue({ by_status: { pending: 0 } })
  mocks.fetchStudioQuality.mockResolvedValue({
    chapters_written: 3,
    max_chapter: 100,
    coverage_pct: 3,
  })
  mocks.fetchStudioQualityReport.mockResolvedValue({ available: true, p0: 0 })
  mocks.fetchStudioActiveBatchJob.mockResolvedValue({ active: false })
  mocks.fetchCreatorOnboarding.mockResolvedValue({ progress_pct: 100 })
}

describe('TodayPage (Phase A)', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    defaultApiMocks()
    const { useTodayHub } = await import('../../src/composables/useTodayHub.js')
    useTodayHub().snapshot.value = null
  })

  test('renders title and primary CTA for companion mode', async () => {
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('今日')
    expect(wrapper.find(byTestid('today-primary-cta')).text()).toBe('继续创作')
    expect(wrapper.find(byTestid('today-project-line')).text()).toContain('暗夜信标')
  })

  test('primary CTA navigates to creator', async () => {
    const wrapper = mount(TodayPage)
    await flushPromises()
    await wrapper.find(byTestid('today-primary-cta')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('creator', expect.objectContaining({ clearFocus: true }))
  })

  test('pending decisions take priority in primary CTA', async () => {
    mocks.fetchPendingDecisions.mockResolvedValue([{ id: 'd1' }, { id: 'd2' }])
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('today-primary-cta')).text()).toBe('处理 2 条待决策')
  })

  test('todo card click navigates', async () => {
    const wrapper = mount(TodayPage)
    await flushPromises()
    await wrapper.find(byTestid('today-todo-decisions')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('inbox', expect.objectContaining({ tab: 'decisions', clearFocus: true }))
  })
})

describe('resolveTodayPrimaryAction', () => {
  test('decisions before ripples', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      pendingDecisions: 1,
      pendingRipples: 2,
    })
    expect(action.nav).toBe('inbox')
    expect(action.tab).toBe('decisions')
  })

  test('companion with zero chapters suggests ch001', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      chaptersWritten: 0,
    })
    expect(action.label).toContain('ch001')
  })
})
