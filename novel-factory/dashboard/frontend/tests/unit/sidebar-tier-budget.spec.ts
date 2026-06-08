// tests/unit/sidebar-tier-budget.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — SidebarCostBanner per-tier budget rows (3 row)
// 跟 ceremonial Playwright spec (tests/e2e/sidebar-tier-budget.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test. useCostWindow +
// useWorkflowSocket 双 mock (跟 pilot echarts mock 同模式).
//
// 契约 (跟 ceremonial 同步):
//   - 3 个 .sidebar-cost-tier-row (haiku/sonnet/opus) 渲染, 顺序 hardcode
//     haiku → sonnet → opus (TIER_ORDER 跟 ModelTier 枚举一致)
//   - 每 row 含 tier label + "$used/$budget (pct%)" + progress-bar + fill
//   - status="exceeded" → fill class 含 "exceeded" + width clip 100%
//   - status="ok" → fill class 含 "ok" + width 跟 pct 同步
//   - 未设 tier (空 dict {}) → row 隐藏 (tierBudgets computed filter)
//   - Phase 8.12 activeBudget cascade 仍工作 (per-run cost_budget_status +
//     Phase 8.15 tier row 共存, 0 互破)

import { describe, test, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SidebarCostBanner from '../../src/components/SidebarCostBanner.vue'

interface TierBudget {
  status?: string
  budget_usd?: number
  used_usd?: number
  used_pct?: number
}

const makeStatus = (
  costByScenario: Record<string, number> = {},
  costByTier: Record<string, number> = {},
  budgetByTier: Record<string, TierBudget> = {},
  costBudgetStatus: TierBudget | null = null,
) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario: costByScenario,
  cost_by_tier: costByTier,
  total_cost_usd: 0.1234,
  budget_by_tier: budgetByTier,
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

// Phase 8.30b: mock useWorkflowSocket 避免真 WS 建连 (用 connected=true 隐藏断线 banner)
vi.mock('../../src/composables/useWorkflowSocket.js', () => ({
  useWorkflowSocket: () => {
    const connected = ref(true)
    return { connected }
  },
}))

describe('SidebarCostBanner per-tier budget rows (Phase 8.15)', () => {
  test('renders 3 tier rows when all budgets set (haiku/sonnet/opus)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.1234 },
          { haiku: 0.0, sonnet: 0.0, opus: 0.1234 },
          {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.0, used_pct: 0.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.0, used_pct: 0.0 },
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.1234, used_pct: 12.34 },
          },
        ),
      },
    })
    await flushPromises()

    // banner 渲染
    expect(wrapper.find('[data-testid="sidebar-cost-banner"]').exists()).toBe(true)
    // 3 tier rows
    const rows = wrapper.findAll('[data-testid="sidebar-cost-tier-row"]')
    expect(rows.length).toBe(3)
  })

  test('hides row when budget unset (empty dict)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.5 },
          { haiku: 0.0, sonnet: 0.5, opus: 0.0 },
          {
            haiku: {},  // empty → 隐藏
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.0, used_pct: 0.0 },
            opus: {},  // empty → 隐藏
          },
        ),
      },
    })
    await flushPromises()

    // 只 sonnet 可见
    const rows = wrapper.findAll('[data-testid="sidebar-cost-tier-row"]')
    expect(rows.length).toBe(1)
    // 验证 sonnet tier text 包含 "sonnet"
    const tierText = rows[0].find('.sidebar-cost-tier-text')
    expect(tierText.text()).toContain('sonnet')
  })

  test('progress bar shows exceeded class + width clip 100%', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 1.5 },
          { haiku: 0.0, sonnet: 0.0, opus: 1.5 },
          {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.0, used_pct: 0.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.0, used_pct: 0.0 },
            opus: { status: 'exceeded', budget_usd: 1.00, used_usd: 1.20, used_pct: 120.0 },
          },
        ),
      },
    })
    await flushPromises()

    // opus row 找
    const rows = wrapper.findAll('[data-testid="sidebar-cost-tier-row"]')
    const opusRow = rows.find((r) => r.text().includes('opus'))
    expect(opusRow).toBeTruthy()

    // opus fill class 含 "exceeded"
    const fill = opusRow.find('.progress-bar-fill')
    expect(fill.classes()).toContain('exceeded')
    // width style clip 100% (120% → clipped)
    expect(fill.attributes('style')).toContain('width: 100%')
  })

  test('progress bar shows ok class when status=ok', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.05 },
          { haiku: 0.0, sonnet: 0.05, opus: 0.0 },
          {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.0, used_pct: 0.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.05, used_pct: 10.0 },
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.0, used_pct: 0.0 },
          },
        ),
      },
    })
    await flushPromises()

    // sonnet row
    const rows = wrapper.findAll('[data-testid="sidebar-cost-tier-row"]')
    const sonnetRow = rows.find((r) => r.text().includes('sonnet'))
    expect(sonnetRow).toBeTruthy()

    // sonnet fill class 含 "ok" + width 10%
    const fill = sonnetRow.find('.progress-bar-fill')
    expect(fill.classes()).toContain('ok')
    expect(fill.attributes('style')).toContain('width: 10%')
  })

  test('order is haiku → sonnet → opus (TIER_ORDER deterministic)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.5 },
          { haiku: 0.1, sonnet: 0.2, opus: 0.2 },
          {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.05, used_pct: 50.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.2, used_pct: 40.0 },
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.5, used_pct: 50.0 },
          },
        ),
      },
    })
    await flushPromises()

    // 顺序 haiku → sonnet → opus (跟 TierOrder 枚举一致)
    const rows = wrapper.findAll('[data-testid="sidebar-cost-tier-row"]')
    expect(rows.length).toBe(3)
    expect(rows[0].text()).toContain('haiku')
    expect(rows[1].text()).toContain('sonnet')
    expect(rows[2].text()).toContain('opus')
  })

  test('Phase 8.12 active budget cascade unchanged (tier rows coexist)', async () => {
    const wrapper = mount(SidebarCostBanner, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.075 },
          { haiku: 0.0, sonnet: 0.0, opus: 0.075 },
          {
            haiku: {},
            sonnet: {},
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.075, used_pct: 7.5 },
          },
          { status: 'exceeded', budget_usd: 0.10, used_usd: 0.075, used_pct: 75.0 },
        ),
      },
    })
    await flushPromises()

    // Phase 8.12 activeBudget cascade 仍显 (per-run cost_budget_status)
    const activeBudgetText = wrapper.find('[data-testid="sidebar-cost-budget-text"]')
    expect(activeBudgetText.exists()).toBe(true)
    expect(activeBudgetText.text()).toContain('本次')
    expect(activeBudgetText.text()).toContain('75.0')

    // Phase 8.15 tier row 也可见 (opus only)
    const tierRows = wrapper.findAll('[data-testid="sidebar-cost-tier-row"]')
    expect(tierRows.length).toBe(1)
    expect(tierRows[0].text()).toContain('opus')
  })
})
