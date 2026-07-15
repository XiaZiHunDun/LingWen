// tests/unit/soft-warning-state.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — SidebarCostBanner soft warning 三态
// 跟 ceremonial Playwright spec (tests/e2e/soft-warning-state.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test.
//
// 契约 (跟 ceremonial 同步):
//   - activeBudget progress-bar-fill class 跟 used_pct 自动切三态:
//     < 80% → .ok (绿) / 80-100% → .warning (黄) / >= 100% → .exceeded (红)
//   - BUDGET_OK_PCT 阈值 = 80 (跟 Phase 8.21 TIER_ALARM_WARNING_PCT 对齐)
//   - 0 改 backend cost_budget_status (二态保留, 单纯前端 UI 升级)

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
  total_cost_usd: 0.085,
  cost_budget_status: costBudgetStatus,
})

// Phase 8.30b: mock useCostWindow 走 vue ref 保 reactivity
vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => {
    const timeWindow = ref('all')
    const windowedCost = ref(null)
    const setTimeWindow = vi.fn()
    return { timeWindow, windowedCost, setTimeWindow }
  },
}))

// Phase 8.30b: mock useWorkflowSocket 避免真 WS 建连
vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => {
    const connected = ref(true)
    return { connected }
  },
}))

describe('Sidebar Soft Warning Three-State (Phase 8.28)', () => {
  test('progress bar shows ok class when used_pct < 80%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.012, chapter_review: 0.008 },
          { status: 'ok', budget_usd: 0.10, used_usd: 0.020, used_pct: 20.0 },
        ),
      },
    })
    await flushPromises()

    // activeBudget fill class: ok (绿) (20% < 80%)
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('ok')
    expect(fill.classes()).not.toContain('warning')
    expect(fill.classes()).not.toContain('exceeded')
  })

  test('progress bar shows warning class when 80% <= used_pct < 100%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.050, chapter_review: 0.035 },
          { status: 'ok', budget_usd: 0.10, used_usd: 0.085, used_pct: 85.0 },
        ),
      },
    })
    await flushPromises()

    // 80% ≤ 85% < 100% → warning (黄, 前端从 ok 升级)
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('warning')
    expect(fill.classes()).not.toContain('ok')
    expect(fill.classes()).not.toContain('exceeded')
  })

  test('progress bar shows exceeded class when used_pct >= 100%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.070, chapter_review: 0.050 },
          { status: 'exceeded', budget_usd: 0.10, used_usd: 0.120, used_pct: 120.0 },
        ),
      },
    })
    await flushPromises()

    // >= 100% → exceeded (红)
    const fill = wrapper.find(byTestid('progress-bar-fill'))
    expect(fill.exists()).toBe(true)
    expect(fill.classes()).toContain('exceeded')
    expect(fill.classes()).not.toContain('ok')
    expect(fill.classes()).not.toContain('warning')
  })
})
