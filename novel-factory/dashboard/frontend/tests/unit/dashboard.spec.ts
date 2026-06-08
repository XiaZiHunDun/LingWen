// tests/unit/dashboard.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — OverviewPage 页面级 (page-level)
// 跟 ceremonial Playwright spec (tests/e2e/dashboard.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 page-level test (mount 整 page + mock
// fetch api).
//
// 契约 (跟 ceremonial 同步):
//   - page-title "追读力总览" 渲染
//   - refresh-btn "刷新" 渲染 + click 不报错
//   - chapter-table 渲染 + 5 列 header (章节/钩子数/钩子强度/爽点数/爽点密度)
//   - 5 stat-card 渲染 (总章节数/总钩子数/平均钩子强度/总爽点数/平均爽点密度)
//   - hook-trend-chart canvas 渲染
//   - error-banner happy path 不显
//
// 注: StatCard 没 data-testid, 改用 .stat-card class 选 (跟 ceremonial 契约对齐).
// HookTrendChart canvas 走 echarts stub (tests/unit/setup.ts 已设).

import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import OverviewPage from '../../src/pages/OverviewPage.vue'

// Phase 8.30b: mock api/index.js 模块 (fetchOverview + fetchChapters)
// 返 fixture 让页面 mount 后 loadData() 不抛错. 后续 5 stat-card + chapter
// table 都能 render.
vi.mock('../../src/api/index.js', () => ({
  fetchOverview: vi.fn().mockResolvedValue({
    total_chapters: 359,
    total_hooks: 2845,
    avg_hook_strength: 0.78,
    total_coolpoints: 1823,
    avg_coolpoint_density: 5.1,
  }),
  fetchChapters: vi.fn().mockResolvedValue({
    chapters: [
      { chapter: 1, hook_count: 8, hook_strength: 0.82, coolpoint_count: 5, coolpoint_density: 5.5 },
      { chapter: 2, hook_count: 7, hook_strength: 0.76, coolpoint_count: 4, coolpoint_density: 4.8 },
    ],
  }),
}))

describe('OverviewPage (page-level) — Phase 8.30b dashboard', () => {
  test('page title "追读力总览" renders', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()
    const title = wrapper.find('[data-testid="page-title"]')
    expect(title.exists()).toBe(true)
    expect(title.text()).toBe('追读力总览')
  })

  test('refresh button renders + click triggers load', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()
    const refreshBtn = wrapper.find('[data-testid="refresh-btn"]')
    expect(refreshBtn.exists()).toBe(true)
    expect(refreshBtn.text()).toContain('刷新')

    // click refresh 触发 loadData (mock api 已就位, 不报错)
    await refreshBtn.trigger('click')
    await flushPromises()
    // error banner 不显 (api 返 fixture, loadData 成功)
    expect(wrapper.find('[data-testid="error-banner"]').exists()).toBe(false)
  })

  test('chapter table renders with 5 columns (章节/钩子数/钩子强度/爽点数/爽点密度)', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()
    const table = wrapper.find('[data-testid="chapter-table"]')
    expect(table.exists()).toBe(true)

    // 5 column headers
    const expectedHeaders = ['章节', '钩子数', '钩子强度', '爽点数', '爽点密度']
    for (const headerText of expectedHeaders) {
      expect(table.text()).toContain(headerText)
    }
  })

  test('5 stat cards render with correct labels (总章节数/总钩子数/平均钩子强度/总爽点数/平均爽点密度)', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()

    // .stat-card 5 个 (StatCard 组件无 data-testid, 用 class 选)
    const statCards = wrapper.findAll('[data-testid="stat-card"]')
    expect(statCards.length).toBe(5)

    // labels
    const expectedLabels = ['总章节数', '总钩子数', '平均钩子强度', '总爽点数', '平均爽点密度']
    for (const label of expectedLabels) {
      expect(wrapper.text()).toContain(label)
    }
  })

  test('hook-trend-chart canvas renders (ECharts stub → empty init)', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()
    const chartContainer = wrapper.find('[data-testid="hook-trend-chart"]')
    expect(chartContainer.exists()).toBe(true)
  })

  test('error banner not shown in happy path (api mock 返 fixture)', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()
    // loadData 成功 → error=null → v-if="error" 不显
    expect(wrapper.find('[data-testid="error-banner"]').exists()).toBe(false)
  })

  test('StatCard renders with data-testid="stat-card" (Phase 8.31 unification)', async () => {
    const wrapper = mount(OverviewPage)
    await flushPromises()
    const statCards = wrapper.findAll('[data-testid="stat-card"]')
    expect(statCards.length).toBe(5)  // OverviewPage mount 5 个 StatCard (跟已有 test 一致)
  })
})
