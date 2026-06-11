// tests/unit/workflows-page.spec.ts — Phase 8.39
// WorkflowsPage page-level mount spec (mirror Phase 8.30b dashboard.spec.ts pattern)
// 验证:
//   1. page-title 渲染 ("工作流")
//   2. workflows list 渲染 (mock fetchWorkflows 返 2 个 fixture)
//   3. workflow 行点击触发 selected (走 vm.selected ref check)
//   4. error-banner 在 store.lastError 出现时显示 (mock fetchWorkflows reject)
//
// 契约约束:
//   - Phase 9.30 F14: page 元素走 data-testid + byTestid (跟 OverviewPage 对齐)
//   - mock api/index.js + useWorkflowSocket 走 module mock 跟 dashboard.spec.ts
//     同 pattern (vi.mock at top + vi.resetModules in error tests)
//
// Phase 8.34 状态:
//   - useWorkflowListStore 管 workflows 列表 (REST) + loading + lastError
//   - useWorkflowSocket 管 active status (WS 权威) + connected + lastError
//   - 页面 UI state (selected / initialInputsJson / maxBacktracks / running /
//     showGraph / graphData / graphLoading / localError / active) 仍 page-local

import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { byTestid } from '../helpers/by-testid'

// 顶层 mock api (跟 Phase 8.30b dashboard.spec.ts 同 pattern)
vi.mock('../../src/api/index.js', () => ({
  fetchAllDecisions: vi.fn().mockResolvedValue([]),
  resolveDecision: vi.fn().mockResolvedValue({}),
  deferDecision: vi.fn().mockResolvedValue({}),
  cancelDecision: vi.fn().mockResolvedValue({}),
  // 默认返 2 个 fixture workflow, 让 list 渲染
  fetchWorkflows: vi.fn().mockResolvedValue([
    { name: 'novel_writing', node_count: 7, path: 'wf/novel_writing.yaml', has_decision_nodes: true },
    { name: 'character_design', node_count: 4, path: 'wf/character_design.yaml', has_decision_nodes: false },
  ]),
  fetchOverview: vi.fn().mockResolvedValue({}),
  fetchChapters: vi.fn().mockResolvedValue({ chapters: [] }),
  fetchWorkflowGraph: vi.fn().mockResolvedValue({ mermaid: 'graph TD\n  A-->B', workflow_name: 'novel_writing' }),
  runWorkflow: vi.fn().mockResolvedValue({ workflow_name: 'novel_writing', is_active: true }),
  resumeWorkflow: vi.fn().mockResolvedValue({ workflow_name: 'novel_writing', is_active: true }),
}))

// 顶层 mock WS composable: 默认 connected + 空 status (happy path)
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

import WorkflowsPage from '../../src/pages/WorkflowsPage.vue'

describe('WorkflowsPage (page-level) — Phase 8.39', () => {
  test('page-title 渲染 ("工作流")', async () => {
    const wrapper = mount(WorkflowsPage)
    await flushPromises()
    const title = wrapper.find(byTestid('page-title'))
    expect(title.exists()).toBe(true)
    expect(title.text()).toBe('工作流')
  })

  test('workflows list 渲染 (mock fetchWorkflows 返 2 个 fixture)', async () => {
    const wrapper = mount(WorkflowsPage)
    await flushPromises()
    // 2 个 workflow 在 .wf-list → .wf-item 各 1 个
    const items = wrapper.findAll(byTestid('wf-item'))
    expect(items.length).toBe(2)
    // 第 1 个 workflow 名字 + node_count
    expect(items[0].text()).toContain('novel_writing')
    expect(items[0].text()).toContain('7 节点')
  })

  test('workflow 行点击触发 selected (走 vm.selected ref check)', async () => {
    const wrapper = mount(WorkflowsPage)
    await flushPromises()
    const items = wrapper.findAll(byTestid('wf-item'))
    expect(items.length).toBe(2)

    // 第 1 个 workflow 点击 → selected.value 设为该 wf
    await items[0].trigger('click')
    await flushPromises()
    // selected 设为后, .run-form (启动表单) 出现, 含 "运行: <name>"
    const runForm = wrapper.find(byTestid('run-form'))
    expect(runForm.exists()).toBe(true)
    expect(runForm.text()).toContain('运行: novel_writing')
  })

  test('error-banner 在 store.lastError 出现时显示 (mock fetchWorkflows reject)', async () => {
    // 重新加载模块 + 重设 api mock, 让 useWorkflowListStore 内部 refresh() 走 reject
    vi.resetModules()
    const api = await import('../../src/api/index.js')
    vi.mocked(api.fetchWorkflows).mockReset()
    vi.mocked(api.fetchWorkflows).mockRejectedValue(new Error('fetch fail'))

    // 重新 import WorkflowsPage (走新的 module graph + 新的 store)
    const { default: FreshWorkflowsPage } = await import('../../src/pages/WorkflowsPage.vue')
    const wrapper = mount(FreshWorkflowsPage)
    await flushPromises()
    // store.refresh 内部 fetchWorkflows reject → lastError = "fetch fail" →
    // error computed 走 truthy → v-if="error" 显 .error-banner
    const banner = wrapper.find(byTestid('error-banner'))
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('fetch fail')
  })
})
