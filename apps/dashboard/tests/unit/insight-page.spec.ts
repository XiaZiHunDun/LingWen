// tests/unit/insight-page.spec.ts — Task C-3
// InsightPage function coverage lift: 37.5% funcs → 70%+.
// Exercises: readonly banner, subtitle variants, hubLoading, tab change, refresh.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, type Ref } from 'vue'
import InsightPage from '../../src/pages/InsightPage.vue'
import { byTestid } from '../helpers/by-testid'

// Mock fns in hoisted (only `vi` is captured).
const setup = vi.hoisted(() => ({
  nav: {
    setInsightTab: vi.fn(),
  },
  overview: {
    refresh: vi.fn().mockResolvedValue(undefined),
  },
  ripple: {
    refresh: vi.fn().mockResolvedValue(undefined),
  },
}))

// Reactive state at top-level (vi.hoisted only captures `vi`).
const insightTabRef: Ref<string> = ref('overview')
const overviewLoadingRef: Ref<boolean> = ref(false)
const rippleLoadingRef: Ref<boolean> = ref(false)
const isReadonlyInsightRef: Ref<boolean> = ref(false)

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    insightTab: insightTabRef,
    setInsightTab: setup.nav.setInsightTab,
  }),
}))

vi.mock('../../src/composables/useOverviewStore.js', () => ({
  useOverviewStore: () => ({
    loading: overviewLoadingRef,
    refresh: setup.overview.refresh,
  }),
}))

vi.mock('../../src/composables/useRippleStore.js', () => ({
  useRippleStore: () => ({
    loading: rippleLoadingRef,
    refresh: setup.ripple.refresh,
  }),
}))

// Stub child pages — they have deep dependency trees (charts, widgets, fetches)
// that aren't relevant to InsightPage's own logic.
const StubOverview = { template: '<div data-testid="overview-page" />' }
const StubAnalytics = { template: '<div data-testid="analytics-page" />' }

function mountInsightPage() {
  return mount(InsightPage, {
    global: {
      provide: {
        isReadonlyInsight: isReadonlyInsightRef,
      },
      stubs: {
        OverviewPage: StubOverview,
        AnalyticsPage: StubAnalytics,
      },
    },
  })
}

describe('InsightPage (Task C-3)', () => {
  beforeEach(() => {
    insightTabRef.value = 'overview'
    setup.nav.setInsightTab.mockClear()
    overviewLoadingRef.value = false
    setup.overview.refresh.mockClear().mockResolvedValue(undefined)
    rippleLoadingRef.value = false
    setup.ripple.refresh.mockClear().mockResolvedValue(undefined)
    isReadonlyInsightRef.value = false
  })

  test('renders page testid', async () => {
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.find(byTestid('insight-page')).exists()).toBe(true)
  })

  test('does NOT render readonly banner when isReadonlyInsight is false', async () => {
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.find(byTestid('insight-readonly-banner')).exists()).toBe(false)
  })

  test('renders readonly banner when isReadonlyInsight is true', async () => {
    isReadonlyInsightRef.value = true
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.find(byTestid('insight-readonly-banner')).exists()).toBe(true)
  })

  test('subtitle for overview tab in non-readonly mode', async () => {
    insightTabRef.value = 'overview'
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.text()).toContain('追读力趋势')
  })

  test('subtitle for analytics tab in non-readonly mode', async () => {
    insightTabRef.value = 'analytics'
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.text()).toContain('生产 KPI')
  })

  test('subtitle for overview tab in readonly mode', async () => {
    isReadonlyInsightRef.value = true
    insightTabRef.value = 'overview'
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.text()).toContain('审阅视图 · 追读力只读')
  })

  test('subtitle for analytics tab in readonly mode', async () => {
    isReadonlyInsightRef.value = true
    insightTabRef.value = 'analytics'
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.text()).toContain('审阅视图 · 生产 KPI 只读')
  })

  test('renders OverviewPage when activeTab is overview', async () => {
    insightTabRef.value = 'overview'
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.find('[data-testid="overview-page"]').exists()).toBe(true)
  })

  test('renders AnalyticsPage when activeTab is analytics', async () => {
    insightTabRef.value = 'analytics'
    const wrapper = mountInsightPage()
    await flushPromises()
    expect(wrapper.find('[data-testid="analytics-page"]').exists()).toBe(true)
  })

  test('hubLoading reflects overviewStore.loading on overview tab', async () => {
    insightTabRef.value = 'overview'
    overviewLoadingRef.value = true
    const wrapper = mountInsightPage()
    await flushPromises()

    const header = wrapper.findComponent({ name: 'HubPageHeader' })
    expect(header.props('loading')).toBe(true)
  })

  test('hubLoading reflects rippleStore.loading on analytics tab', async () => {
    insightTabRef.value = 'analytics'
    rippleLoadingRef.value = true
    const wrapper = mountInsightPage()
    await flushPromises()

    const header = wrapper.findComponent({ name: 'HubPageHeader' })
    expect(header.props('loading')).toBe(true)
  })

  test('refresh on overview tab calls overviewStore.refresh only', async () => {
    insightTabRef.value = 'overview'
    const wrapper = mountInsightPage()
    await flushPromises()

    await wrapper.findComponent({ name: 'HubPageHeader' }).vm.$emit('refresh')
    await flushPromises()

    expect(setup.overview.refresh).toHaveBeenCalledTimes(1)
    expect(setup.ripple.refresh).not.toHaveBeenCalled()
  })

  test('refresh on analytics tab calls both stores in parallel', async () => {
    insightTabRef.value = 'analytics'
    const wrapper = mountInsightPage()
    await flushPromises()

    await wrapper.findComponent({ name: 'HubPageHeader' }).vm.$emit('refresh')
    await flushPromises()

    expect(setup.overview.refresh).toHaveBeenCalledTimes(1)
    expect(setup.ripple.refresh).toHaveBeenCalledTimes(1)
  })

  test('v-model activeTab setter routes through setInsightTab', async () => {
    const wrapper = mountInsightPage()
    await flushPromises()

    const tabBar = wrapper.findComponent({ name: 'HubTabBar' })
    await tabBar.vm.$emit('update:model-value', 'analytics')
    await flushPromises()

    expect(setup.nav.setInsightTab).toHaveBeenCalledWith('analytics')
  })

  test('onTabChange also routes through setInsightTab (update:model-value)', async () => {
    const wrapper = mountInsightPage()
    await flushPromises()

    // HubTabBar emits update:model-value which triggers activeTab.set (via v-model)
    // AND fires onTabChange (via @update:model-value). Both call setInsightTab.
    setup.nav.setInsightTab.mockClear()
    const tabBar = wrapper.findComponent({ name: 'HubTabBar' })
    await tabBar.vm.$emit('update:model-value', 'overview')
    await flushPromises()

    // setInsightTab should be called — at least once via the v-model setter
    expect(setup.nav.setInsightTab).toHaveBeenCalled()
    expect(setup.nav.setInsightTab.mock.calls.some((c) => c[0] === 'overview')).toBe(true)
  })
})
