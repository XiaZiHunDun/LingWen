// tests/unit/dashboard-error-loading.spec.ts — Phase 8.45.2
// OverviewPage e2e 加深: 5 tests 覆盖 error / loading / empty / refresh-recovery
// / partial data 5 态. 跟 Phase 8.30b dashboard.spec.ts 1:1 mirror, vi.mock
// api/index.js + vi.resetModules + dynamic import per test 保 singleton 隔离.
//
// Phase 8.30b 已覆盖 happy path 7 tests (page title / refresh / chapter table /
// 5 stat cards / hook-trend-chart / error banner not shown / StatCard testid).
// Phase 8.45.2 收尾 5 边界态: error / loading / empty / refresh-recovery / partial.
// 同步修复 Phase 8.34 漏改的 latent template binding bug (4 binding 引用 undefined),
// 5 边界态测试需 template binding 正确才能跑通 (error-banner 显需 'error' 绑定
// 真实值, refresh-btn disabled 需 'loading' 绑定 真实值, etc).
//
// Test 3 (empty state) 跟原 plan 不同: statCards computed 永远 render 5 (用 '0' /
// '-' fallback), 不返 [], 所以 5 stat-cards 显. Test 5 (partial data) 跟原 plan
// 不同: Step 3 加的 v-if 让 ChapterTable 在 chapters 空时不 render, 改显
// chapters-empty fallback. 这两处修正跟当前 OverviewPage.vue 实际行为对齐.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

const mocks = vi.hoisted(() => ({
  fetchOverview: vi.fn(),
  fetchChapters: vi.fn(),
}))

vi.mock('../../src/api/index.js', () => ({
  fetchOverview: mocks.fetchOverview,
  fetchChapters: mocks.fetchChapters,
}))

beforeEach(() => {
  mocks.fetchOverview.mockReset()
  mocks.fetchChapters.mockReset()
})

async function mountPage() {
  vi.resetModules()
  const { default: OverviewPage } = await import('../../src/pages/OverviewPage.vue')
  const wrapper = mount(OverviewPage)
  await flushPromises()
  return wrapper
}

describe('OverviewPage e2e 加深 (Phase 8.45.2)', () => {
  test('error state: api throws → error-banner testid visible + page-title 仍 visible', async () => {
    mocks.fetchOverview.mockRejectedValue(new Error('API 500'))
    mocks.fetchChapters.mockResolvedValue({ chapters: [] })

    const wrapper = await mountPage()

    const errorBanner = wrapper.find(byTestid('error-banner'))
    expect(errorBanner.exists()).toBe(true)
    expect(errorBanner.text()).toContain('API 500')
    expect(wrapper.find(byTestid('page-title')).exists()).toBe(true)
  })

  test('loading state: api slow → initial state (no error, refresh-btn disabled, 5 stat-card render with "0"/"-" fallback)', async () => {
    // mock 永 not resolve → store.loading 持续 true (mountPage flushPromises 已 flush
    // store 内部 microtask, 但实际 fetchOverview / fetchChapters 永 pending, store.loading
    // 不会从 true 翻 false). refresh-btn disabled 一直 hold.
    mocks.fetchOverview.mockReturnValue(new Promise(() => {}))
    mocks.fetchChapters.mockReturnValue(new Promise(() => {}))

    const wrapper = await mountPage()

    expect(wrapper.find(byTestid('error-banner')).exists()).toBe(false)
    const refreshBtn = wrapper.find(byTestid('refresh-btn'))
    expect(refreshBtn.exists()).toBe(true)
    expect(refreshBtn.attributes('disabled')).toBeDefined()
    // 跟 Test 3 一致: statCards computed 永远 render 5 (用 '0' / '-' fallback),
    // 即便 loading 期间 store.overview={}. 验证 5 stat-cards 显.
    expect(wrapper.findAll(byTestid('stat-card'))).toHaveLength(5)
  })

  test('empty state: api returns 0 chapters + 0 overview → page-title visible + 5 stat-card (with "0"/"-" fallback)', async () => {
    mocks.fetchOverview.mockResolvedValue({
      total_chapters: 0,
      total_hooks: 0,
      avg_hook_strength: null,
      total_coolpoints: 0,
      avg_coolpoint_density: null,
    })
    mocks.fetchChapters.mockResolvedValue({ chapters: [] })

    const wrapper = await mountPage()

    expect(wrapper.find(byTestid('page-title')).exists()).toBe(true)
    // 修正: statCards computed 永远 render 5 (Phase 8.34 store registry 0 改),
    // 用 '0' / '-' fallback. 验证 5 stat-cards 显 + fallback 文本出现.
    expect(wrapper.findAll(byTestid('stat-card'))).toHaveLength(5)
    // 验证 fallback 文本: total_chapters=0 → '0', avg_hook_strength=null → '-'
    expect(wrapper.text()).toContain('0')
    expect(wrapper.text()).toContain('-')
    expect(wrapper.find(byTestid('error-banner')).exists()).toBe(false)
  })

  test('refresh error recovery: initial throw + click refresh + mock re-fetch happy → error-banner hide + 5 stat-card 渲染', async () => {
    mocks.fetchOverview
      .mockRejectedValueOnce(new Error('网络错误'))
      .mockResolvedValueOnce({
        total_chapters: 359,
        total_hooks: 2845,
        avg_hook_strength: 0.78,
        total_coolpoints: 1823,
        avg_coolpoint_density: 5.1,
      })
    mocks.fetchChapters.mockResolvedValue({
      chapters: [
        { chapter: 1, hook_count: 8, hook_strength: 0.82, coolpoint_count: 5, coolpoint_density: 5.5 },
      ],
    })

    const wrapper = await mountPage()
    expect(wrapper.find(byTestid('error-banner')).exists()).toBe(true)
    await wrapper.find(byTestid('refresh-btn')).trigger('click')
    await flushPromises()
    expect(wrapper.find(byTestid('error-banner')).exists()).toBe(false)
    expect(wrapper.findAll(byTestid('stat-card'))).toHaveLength(5)
  })

  test('partial data: overview 有 + chapters 空 → 5 stat-card 渲染 + chapters-empty 显 (v-else fallback)', async () => {
    mocks.fetchOverview.mockResolvedValue({
      total_chapters: 359,
      total_hooks: 2845,
      avg_hook_strength: 0.78,
      total_coolpoints: 1823,
      avg_coolpoint_density: 5.1,
    })
    mocks.fetchChapters.mockResolvedValue({ chapters: [] })

    const wrapper = await mountPage()

    expect(wrapper.findAll(byTestid('stat-card'))).toHaveLength(5)
    // 修正: Step 3 加的 v-if/v-else 让 ChapterTable 在 chapters 空时不 render,
    // 改显 chapters-empty fallback. chapter-table / chapter-row 0 显.
    expect(wrapper.find(byTestid('chapters-empty')).exists()).toBe(true)
    expect(wrapper.find(byTestid('chapter-table')).exists()).toBe(false)
    // 注: chapter-row testid Phase 8.31 加在 ChapterTable.vue, 0 改 ChapterTable 在 8.45.2
    expect(wrapper.findAll(byTestid('chapter-row'))).toHaveLength(0)
  })
})
