// tests/unit/dashboard-budget.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — Cost budget 告警 banner
// 跟 ceremonial Playwright spec (tests/e2e/dashboard_budget.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test.
//
// 契约发现: 原 ceremonial spec 期望 .cost-budget-section 在 WorkflowStatus
// 渲染. 但实际 cost_budget_status 处理在 Phase 8.11+ 已经落到 SidebarCostBanner
// 组件 (activeBudget computed cascade), 没在 WorkflowStatus 实现. WorkflowStatus
// 0 改:
//   - 0 .cost-budget-section DOM
//   - 0 cost_budget_status 字段处理
//   - 0 红色/绿色 border-left 视觉
//
// 本 spec 文档当前契约: cost_budget_status 行为在 SidebarCostBanner, 通过
// activeBudget computed (Phase 8.12 cascade) 渲染. 测试契约对齐 Sidebar
// 现有测试 (sidebar-banner-priority-cascade / soft-warning-state), 不引新
// WorkflowStatus 依赖. 等价覆盖 dashboard_budget ceremonial 3 个 case:
//   - cost_budget_status.exceeded → Sidebar 显 "今日" 档 (exceeded 优先)
//   - cost_budget_status.ok → Sidebar 显 progress-bar ok fill
//   - cost_budget_status === {} → Sidebar 不显 activeBudget (v-if gate)

import { describe, test, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'
import { byTestid } from '../helpers/by-testid'

const makeStatus = (
  costByScenario: Record<string, number> = {},
  costBudgetStatus: object | null = null,
) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario: costByScenario,
  cost_by_tier: {},
  total_cost_usd: 0.045,
  cost_budget_status: costBudgetStatus,
})

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => {
    const timeWindow = ref('all')
    const windowedCost = ref(null)
    const setTimeWindow = vi.fn()
    return { timeWindow, windowedCost, setTimeWindow }
  },
}))

vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => {
    const connected = ref(true)
    return { connected }
  },
}))

describe('Dashboard cost budget banner (Phase 8.8, 实际落在 Sidebar 8.11+)', () => {
  test('cost_budget_status.exceeded → Sidebar 显 budget block (exceeded fill)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.025, chapter_review: 0.020 },
          { status: 'exceeded', budget_usd: 0.04, used_usd: 0.045, used_pct: 112.5 },
        ),
      },
    })
    await flushPromises()

    // Sidebar budget text 渲染 (中文 "本次" 标签 + $used/$budget + pct)
    // 注: activePct 走 Math.min(100, used_pct) clip, 112.5% → 100.0% 显示
    const budgetText = wrapper.find(byTestid('sidebar-cost-budget-text'))
    expect(budgetText.exists()).toBe(true)
    expect(budgetText.text()).toContain('本次')
    expect(budgetText.text()).toContain('$0.0450')  // used_usd
    expect(budgetText.text()).toContain('$0.0400')  // budget_usd
    expect(budgetText.text()).toContain('100.0')   // clipped from 112.5%

    // progress-bar-fill class 含 "exceeded" (跟 ceremonial 契约对齐)
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('exceeded')
    // width clip 100% (112.5% → 100%)
    expect(fill.attributes('style')).toContain('width: 100%')
  })

  test('cost_budget_status.ok → Sidebar 显 budget block (ok fill)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.012, chapter_review: 0.008 },
          { status: 'ok', budget_usd: 0.10, used_usd: 0.02, used_pct: 20.0 },
        ),
      },
    })
    await flushPromises()

    // Sidebar budget text 渲染
    const budgetText = wrapper.find(byTestid('sidebar-cost-budget-text'))
    expect(budgetText.exists()).toBe(true)
    expect(budgetText.text()).toContain('本次')
    expect(budgetText.text()).toContain('$0.0200')
    expect(budgetText.text()).toContain('$0.1000')
    expect(budgetText.text()).toContain('20.0')

    // ok fill (Phase 8.28 soft warning: < 80% → ok 绿)
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('ok')
    expect(fill.classes()).not.toContain('exceeded')
  })

  test('cost_budget_status === {} (no budget) → Sidebar 不显 activeBudget block', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.005 },
          {},  // empty → activeBudget cascade 空, 显 total 但不显 budget block
        ),
      },
    })
    await flushPromises()

    // banner 仍渲染 (hasCost=true, cost_by_scenario 非空)
    expect(wrapper.find(byTestid('sidebar-cost-banner')).exists()).toBe(true)
    // total text 显
    expect(wrapper.find(byTestid('sidebar-cost-total-text')).exists()).toBe(true)
    // budget text 不显 (v-if=activeBudget 锁 false, 0 误渲染空 banner)
    expect(wrapper.find(byTestid('sidebar-cost-budget-text')).exists()).toBe(false)
    expect(wrapper.find(byTestid('progress-bar-fill')).exists()).toBe(false)
  })
})
