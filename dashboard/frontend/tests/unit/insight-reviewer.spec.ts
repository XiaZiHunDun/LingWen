// tests/unit/insight-reviewer.spec.ts — Phase D insight hub + reviewer mode

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, computed } from 'vue'
import { byTestid } from '../helpers/by-testid'

const navMocks = vi.hoisted(() => {
  // ref must be created inside hoisted callback (vitest init order)
  const { ref: vueRef } = require('vue') as typeof import('vue')
  return {
    insightTab: vueRef('overview'),
    setInsightTab: vi.fn(),
  }
})

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    insightTab: navMocks.insightTab,
    setInsightTab: navMocks.setInsightTab,
  }),
}))

vi.mock('../../src/pages/OverviewPage.vue', () => ({
  default: { template: '<div data-testid="overview-embed">overview</div>' },
}))
vi.mock('../../src/pages/AnalyticsPage.vue', () => ({
  default: { template: '<div data-testid="analytics-embed">analytics</div>' },
}))

import InsightPage from '../../src/pages/InsightPage.vue'
import { buildDashboardShareUrl } from '../../src/utils/shareLink.js'

describe('InsightPage (Phase D)', () => {
  beforeEach(() => {
    navMocks.insightTab.value = 'overview'
    vi.clearAllMocks()
  })

  test('renders insight hub with overview tab', async () => {
    const wrapper = mount(InsightPage, {
      global: {
        provide: { isReadonlyInsight: computed(() => false) },
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('page-title')).text()).toBe('洞察')
    expect(wrapper.find(byTestid('overview-embed')).exists()).toBe(true)
  })

  test('shows readonly banner in reviewer mode', async () => {
    const wrapper = mount(InsightPage, {
      global: {
        provide: { isReadonlyInsight: computed(() => true) },
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('insight-readonly-banner')).exists()).toBe(true)
  })

  test('subtitle reflects active insight tab', async () => {
    navMocks.insightTab.value = 'analytics'
    const wrapper = mount(InsightPage, {
      global: {
        provide: { isReadonlyInsight: computed(() => false) },
      },
    })
    await flushPromises()
    expect(wrapper.find('.hub-subtitle').text()).toContain('生产 KPI')
  })
})

describe('shareLink utils', () => {
  test('buildDashboardShareUrl includes nav tab decision role', () => {
    const url = buildDashboardShareUrl({
      nav: 'inbox',
      tab: 'decisions',
      decision: 'd-1',
      chapter: 5,
      role: 'reviewer',
    })
    expect(url).toContain('nav=inbox')
    expect(url).toContain('tab=decisions')
    expect(url).toContain('decision=d-1')
    expect(url).toContain('chapter=5')
    expect(url).toContain('role=reviewer')
  })
})
