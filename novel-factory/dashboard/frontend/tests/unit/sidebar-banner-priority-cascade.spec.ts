// tests/unit/sidebar-banner-priority-cascade.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — Sidebar Cost Banner priority cascade (3 档 budget)
// 跟 ceremonial Playwright spec (tests/e2e/sidebar_banner_priority_cascade.spec.js)
// 同契约. 但用 @vue/test-utils + jsdom 真跑 component-level test.
//
// 契约 (跟 ceremonial 同步):
//   - 3 档 budget (per-run/per-day/per-week) 同时暴露, banner 只显最紧急档
//   - cascade 规则: exceeded 优先, 同状态按 used_pct desc
//   - 测试场景: per-run ok 50% + per-day exceeded 120% + per-week ok 80%
//     → 期望 banner 显 "今日" (per-day, exceeded 优先)
//   - active 只 1 个 budget block, 其他档 label (本次/本周) 不显
//   - progress bar width = min(100, used_pct)%, fill class "exceeded"

import { describe, test, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'

const makeStatus = (
  costBudgetStatus: object | null,
  budgetPerDay: object | null,
  budgetPerWeek: object | null,
) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario: { chapter_writing: 0.06 },
  cost_by_tier: {},
  total_cost_usd: 0.06,
  cost_budget_status: costBudgetStatus,
  budget_per_day: budgetPerDay,
  budget_per_week: budgetPerWeek,
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

describe('Sidebar Cost Banner Priority Cascade (Phase 8.12)', () => {
  test('shows most urgent budget (exceeded priority over ok)', async () => {
    // 3 档 budget: per-run ok 50% / per-day exceeded 120% / per-week ok 80%
    // → 期望 banner 显 "今日" (per-day, exceeded 优先)
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { status: 'ok', budget_usd: 0.1, used_usd: 0.05, used_pct: 50.0 },
          { status: 'exceeded', budget_usd: 0.05, used_usd: 0.06, used_pct: 120.0 },
          { status: 'ok', budget_usd: 0.2, used_usd: 0.16, used_pct: 80.0 },
        ),
      },
    })
    await flushPromises()

    // Sidebar banner 可见
    expect(wrapper.find('[data-testid="sidebar-cost-banner"]').exists()).toBe(true)

    // Total USD 正常显 (cost_by_scenario has entry)
    const totalText = wrapper.find('[data-testid="sidebar-cost-total-text"]')
    expect(totalText.text()).toContain('💰')
    expect(totalText.text()).toContain('$0.0600')

    // Banner 文本含 "今日" (per-day, exceeded 优先)
    const budgetText = wrapper.find('[data-testid="sidebar-cost-budget-text"]')
    expect(budgetText.text()).toContain('今日')
    expect(budgetText.text()).toContain('$0.0600')  // active.used_usd (per-day)
    expect(budgetText.text()).toContain('$0.0500')  // active.budget_usd (per-day)
    expect(budgetText.text()).toContain('100.0')   // clipped from 120% to 100%

    // Per-run "本次" / per-week "本周" label 不显示 (active 只 1 个 budget block)
    expect(budgetText.text()).not.toContain('本次')
    expect(budgetText.text()).not.toContain('本周')

    // Progress bar fill width = 100% (exceeded clip), class "exceeded"
    const fill = wrapper.find('[data-testid="progress-bar-fill"]')
    expect(fill.exists()).toBe(true)
    expect(fill.attributes('style')).toContain('width: 100%')
    expect(fill.classes()).toContain('exceeded')
  })
})
