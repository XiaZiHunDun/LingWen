// tests/unit/decisions-page.spec.ts — Phase 8.39
// DecisionsPage page-level mount spec (mirror Phase 8.30b dashboard.spec.ts pattern)
// 验证:
//   1. page-title 渲染 ("决策中心")
//   2. refresh-btn 渲染 + click 触发 store.refresh() (mock api 返 [] 不抛错)
//   3. error-banner 在 store.lastError 出现时显示 (mock fetchAllDecisions reject)
//   4. pending tab badge 渲染 WS pendingDecisions (mock WS 推 1 pending)
//
// 契约约束:
//   - Phase 9.30 F14: page 元素走 data-testid + byTestid (跟 OverviewPage 对齐)
//   - mock api/index.js + useWorkflowSocket 走 module mock 跟 use-decision-store.spec.ts
//     同 pattern (vi.mock at top + vi.resetModules in error/WS tests)
//
// Phase 8.34 状态:
//   - useDecisionStore 管 all (REST) + 4 mutations
//   - useWorkflowSocket 管 pendingDecisions (WS 权威) + connected + lastError
//   - 页面 UI state (activeTab / expanded) 仍 page-local

import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

// 顶层 mock api (跟 Phase 8.30b dashboard.spec.ts 同 pattern)
vi.mock('../../src/api/index.js', () => ({
  fetchAllDecisions: vi.fn().mockResolvedValue([]),
  resolveDecision: vi.fn().mockResolvedValue({}),
  deferDecision: vi.fn().mockResolvedValue({}),
  cancelDecision: vi.fn().mockResolvedValue({}),
  fetchWorkflows: vi.fn().mockResolvedValue([]),
  fetchOverview: vi.fn().mockResolvedValue({}),
  fetchChapters: vi.fn().mockResolvedValue({ chapters: [] }),
}))

// 顶层 mock WS composable: 默认 connected + 空 pending (happy path)
vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => ({
    status: { value: null },
    pendingDecisions: { value: [] },
    connected: { value: true },
    lastError: { value: null },
    sendKeepAlive: () => {},
    reconnect: () => {},
  }),
}))

import DecisionsPage from '../../src/pages/DecisionsPage.vue'

describe('DecisionsPage (page-level) — Phase 8.39', () => {
  test('page-title 渲染 ("决策中心")', async () => {
    const wrapper = mount(DecisionsPage)
    await flushPromises()
    const title = wrapper.find(byTestid('page-title'))
    expect(title.exists()).toBe(true)
    expect(title.text()).toBe('决策中心')
  })

  test('refresh-btn 渲染 + click 触发 store.refresh() (mock api 返 [] 不抛错)', async () => {
    const wrapper = mount(DecisionsPage)
    await flushPromises()
    // refresh-btn 0 data-testid, 沿用 .refresh-btn class selector
    const btn = wrapper.find(byTestid('refresh-btn'))
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('刷新')

    // click 触发 store.refresh(), store 内部 await fetchAllDecisions() (mock 返 [])
    await btn.trigger('click')
    await flushPromises()
    // 不抛错 + 仍渲染 (happy path 断言)
    expect(wrapper.find(byTestid('refresh-btn')).exists()).toBe(true)
  })

  test('error-banner 在 store.lastError 出现时显示 (mock fetchAllDecisions reject)', async () => {
    // 重新加载模块 + 重设 api mock, 让 useDecisionStore 内部 refresh() 走 reject
    // (module-level singleton: 顶层 vi.mock 是 default, 这里需要重置 mock 后重新 import)
    vi.resetModules()
    const api = await import('../../src/api/index.js')
    vi.mocked(api.fetchAllDecisions).mockReset()
    vi.mocked(api.fetchAllDecisions).mockRejectedValue(new Error('fetch fail'))

    // 重新 import DecisionsPage (走新的 module graph + 新的 store)
    const { default: FreshDecisionsPage } = await import('../../src/pages/DecisionsPage.vue')
    const wrapper = mount(FreshDecisionsPage)
    await flushPromises()
    // store.refresh 内部 fetchAllDecisions reject → lastError = "fetch fail" →
    // error computed 走 truthy → v-if="error" 显 .error-banner
    const banner = wrapper.find(byTestid('error-banner'))
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('fetch fail')
  })

  test('pending tab badge 渲染 WS pendingDecisions (mock 1 pending)', async () => {
    // vi.doMock 重新设 WS mock 返 1 个 pending, 然后动态 re-import 拿新 module graph
    // (顶层 vi.mock 是 default empty; vi.doMock 走 resetModules 后的 fresh module)
    vi.resetModules()
    vi.doMock('../../src/composables/useWorkflowSocket.js', () => ({
      useWorkflowSocket: () => ({
        status: { value: null },
        pendingDecisions: {
          value: [
            {
              decision_id: 'p1',
              status: 'pending',
              kind: 'outline-judgment',
              priority: 1,
              title: 'Pending 1',
            },
          ],
        },
        connected: { value: true },
        lastError: { value: null },
        sendKeepAlive: () => {},
        reconnect: () => {},
      }),
    }))

    const { default: FreshDecisionsPage } = await import('../../src/pages/DecisionsPage.vue')
    const wrapper = mount(FreshDecisionsPage)
    await flushPromises()
    // pending count 在 .count-badge 显示 "待处理: 1 / 总计: 0"
    const badge = wrapper.find(byTestid('count-badge'))
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toContain('待处理: 1')
  })

  test('resolved tab shows empty state then expand', async () => {
    const wrapper = mount(DecisionsPage)
    await flushPromises()
    const tabs = wrapper.findAll('.tab-btn')
    await tabs[1].trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('暂无已解决决策')
    const expandBtn = wrapper.find('.expand-toggle')
    await expandBtn.trigger('click')
    await flushPromises()
    expect(expandBtn.text()).toContain('折叠')
  })

  test('decision cards render from store data', async () => {
    vi.resetModules()
    const api = await import('../../src/api/index.js')
    vi.mocked(api.fetchAllDecisions).mockResolvedValue([
      {
        decision_id: 'd1',
        status: 'resolved',
        kind: 'outline-judgment',
        priority: 1,
        title: 'Done',
        resolved_at: '2026-06-11T00:00:00Z',
        created_at: '2026-06-10T00:00:00Z',
      },
    ])
    const { default: FreshDecisionsPage } = await import('../../src/pages/DecisionsPage.vue')
    const wrapper = mount(FreshDecisionsPage)
    await flushPromises()
    await wrapper.findAll('.tab-btn')[1].trigger('click')
    await flushPromises()
    await wrapper.find('.expand-toggle').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="decision-card"]').exists()).toBe(true)
  })

  test('closed tab expand shows cancelled decisions', async () => {
    vi.resetModules()
    const api = await import('../../src/api/index.js')
    vi.mocked(api.fetchAllDecisions).mockResolvedValue([
      {
        decision_id: 'd-c',
        status: 'cancelled',
        kind: 'outline-judgment',
        priority: 2,
        title: 'Cancelled',
        created_at: '2026-06-10T00:00:00Z',
        reason: 'no',
        node_id: 'n2',
        prompt: 'P',
        options: [],
      },
    ])
    const { default: FreshDecisionsPage } = await import('../../src/pages/DecisionsPage.vue')
    const wrapper = mount(FreshDecisionsPage)
    await flushPromises()
    await wrapper.findAll('.tab-btn')[2].trigger('click')
    await flushPromises()
    await wrapper.find('.expand-toggle').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="decision-card"]').exists()).toBe(true)
  })
})
