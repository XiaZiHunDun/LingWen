// tests/unit/today-page.spec.ts — Phase A Today hub

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { computed } from 'vue'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  navigateTo: vi.fn(),
  copyDashboardShareUrl: vi.fn().mockResolvedValue({ ok: true }),
  fetchStudioSummary: vi.fn(),
  fetchCreatorOverview: vi.fn(),
  fetchPendingDecisions: vi.fn(),
  fetchRippleStats: vi.fn(),
  fetchStudioQuality: vi.fn(),
  fetchStudioQualityReport: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
  fetchCreatorOnboarding: vi.fn(),
  fetchCreatorChapterPreview: vi.fn(),
}))

vi.mock('../../src/utils/shareLink.js', () => ({
  copyDashboardShareUrl: mocks.copyDashboardShareUrl,
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
  fetchCreatorChapterPreview: mocks.fetchCreatorChapterPreview,
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
  mocks.fetchCreatorChapterPreview.mockResolvedValue({
    body_text: '字'.repeat(1500),
  })
}

describe('TodayPage (Phase A)', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    defaultApiMocks()
    const { useTodayHub } = await import('../../src/composables/useTodayHub.js')
    useTodayHub().snapshot.value = null
  })

  test('renders lead bar and primary CTA for companion mode', async () => {
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('page-lead-bar-today')).exists()).toBe(true)
    expect(wrapper.find(byTestid('today-primary-cta')).text()).toBe('继续创作')
    expect(wrapper.find(byTestid('today-project-line')).text()).toContain('暗夜信标')
  })

  test('primary CTA navigates to creator', async () => {
    const wrapper = mount(TodayPage)
    await flushPromises()
    await wrapper.find(byTestid('today-primary-cta')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('creator', expect.objectContaining({ clearFocus: true }))
  })

  test('companion micro task CTA when chapter below goal', async () => {
    mocks.fetchCreatorChapterPreview.mockResolvedValue({
      body_text: '字'.repeat(200),
    })
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('today-primary-cta')).text()).toMatch(/^再写 \d+ 字$/)
    expect(wrapper.find(byTestid('today-micro-task-stat')).exists()).toBe(true)
    await wrapper.find(byTestid('today-primary-cta')).trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('creator', expect.objectContaining({
      clearFocus: false,
      chapter: 3,
    }))
  })

  test('pending decisions take priority in primary CTA', async () => {
    mocks.fetchPendingDecisions.mockResolvedValue([{ id: 'd1' }, { id: 'd2' }])
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('today-primary-cta')).text()).toBe('处理 2 条待决策')
  })

  test('no todo grid; secondary links hidden when nothing pending', async () => {
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('today-todo-section')).exists()).toBe(false)
    expect(wrapper.find(byTestid('today-secondary-links')).exists()).toBe(false)
  })

  test('secondary link navigates for non-primary pending items', async () => {
    mocks.fetchPendingDecisions.mockResolvedValue([{ id: 'd1' }, { id: 'd2' }])
    mocks.fetchRippleStats.mockResolvedValue({ by_status: { pending: 1 } })
    const wrapper = mount(TodayPage)
    await flushPromises()
    expect(wrapper.find(byTestid('today-primary-cta')).text()).toBe('处理 2 条待决策')
    const rippleLink = wrapper.find(byTestid('today-secondary-ripples'))
    expect(rippleLink.exists()).toBe(true)
    expect(rippleLink.text()).toContain('一致性变更')
    await rippleLink.trigger('click')
    expect(mocks.navigateTo).toHaveBeenCalledWith('inbox', expect.objectContaining({ tab: 'ripples', clearFocus: true }))
  })

  test('reviewer mode shows banner without quick links section', async () => {
    const wrapper = mount(TodayPage, {
      global: {
        provide: { isReviewer: computed(() => true) },
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('today-reviewer-banner')).exists()).toBe(true)
    expect(wrapper.find(byTestid('today-quick-links')).exists()).toBe(false)
    expect(wrapper.find(byTestid('today-health-section')).exists()).toBe(true)
  })

  test('reviewer share link copies inbox URL', async () => {
    const wrapper = mount(TodayPage, {
      global: {
        provide: { isReviewer: computed(() => true) },
      },
    })
    await flushPromises()
    await wrapper.find(byTestid('today-share-link-btn')).trigger('click')
    await flushPromises()
    expect(mocks.copyDashboardShareUrl).toHaveBeenCalledWith(expect.objectContaining({
      nav: 'inbox',
      role: 'reviewer',
    }))
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
    expect(action.chapter).toBe(1)
  })

  test('companion micro task takes priority over generic write CTA', () => {
    const action = resolveTodayPrimaryAction({
      creationMode: 'companion',
      chaptersWritten: 3,
      microTask: { remaining: 120, current: 1380, goal: 1500 },
      activeChapter: 2,
    })
    expect(action.id).toBe('write-micro')
    expect(action.label).toBe('再写 120 字')
    expect(action.chapter).toBe(2)
  })

  test('reviewer prioritizes decisions then insight', () => {
    const withDecisions = resolveTodayPrimaryAction({
      isReviewer: true,
      pendingDecisions: 2,
    })
    expect(withDecisions.nav).toBe('inbox')
    const fallback = resolveTodayPrimaryAction({ isReviewer: true })
    expect(fallback.nav).toBe('insight')
  })
})
