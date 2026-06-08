// tests/unit/cost-trend-chart.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — CostTrendChart trend line (cost by day)
// 跟 ceremonial Playwright spec (tests/e2e/cost-trend-chart.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test. echarts 已
// 在 tests/unit/setup.ts 顶层 stub (canvas getContext 限制绕过).
//
// 契约 (跟 ceremonial 同步):
//   - CostTrendChart 在 cost-section 内 (跟 CostBarChart 串联, 后面)
//   - canvas .cost-trend-chart 渲染 (line type, 走 echarts stub)
//   - hasData gate: costByDay Object.keys > 0 + values > 0
//   - hasCost gate additive OR: scenarioHas || tierHas || dayHas (Phase 8.24)
//   - empty data → "暂无 trend 数据" 显示 (data-testid="cost-trend-chart-empty")
//   - cost-section 整体隐藏: 3 维度都空 (all-empty path)

import { describe, test, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowStatus from '../../src/components/WorkflowStatus.vue'
import { byTestid } from '../helpers/by-testid'

const makeStatus = (
  costByScenario: Record<string, number> = {},
  costByTier: Record<string, number> = {},
  costByDay: Record<string, number> = {},
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
  cost_by_day: costByDay,
  total_cost_usd: 0.025,
})

// Phase 8.30b: vi.mock useCostWindow 隔离 fetch 副作用, 走 vue ref 保 reactivity
vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => {
    const timeWindow = ref('all')
    const windowedCost = ref(null)
    const setTimeWindow = vi.fn()
    return { timeWindow, windowedCost, setTimeWindow }
  },
}))

describe('CostTrendChart trend line (Phase 8.24)', () => {
  test('renders cost-trend-chart canvas when cost_by_day has data', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.015, chapter_review: 0.010 },
          { sonnet: 0.020, haiku: 0.005 },
          { '2026-06-05': 0.010, '2026-06-06': 0.008, '2026-06-07': 0.007 },
        ),
      },
    })
    await flushPromises()

    // cost-section 渲染 (3 维度都非空)
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(true)
    // CostTrendChart wrapper + canvas 渲染 (echarts stub 走空壳)
    expect(wrapper.find(byTestid('cost-trend-chart-wrapper')).exists()).toBe(true)
    expect(wrapper.find(byTestid('cost-trend-chart')).exists()).toBe(true)
    // hasData=true → empty msg 不显示
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })

  test('shows empty fallback when cost_by_day is empty (但 scenario/tier 仍非空)', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.01 },
          { sonnet: 0.01 },
          {},  // empty day → hasData=false → empty msg 显示
        ),
      },
    })
    await flushPromises()

    // hasCost=true (scenario OR tier 触发) → cost-section 仍渲染
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(true)
    // CostTrendChart wrapper 仍渲染
    expect(wrapper.find(byTestid('cost-trend-chart-wrapper')).exists()).toBe(true)
    // empty msg 显示
    const emptyMsg = wrapper.find(byTestid('cost-trend-chart-empty'))
    expect(emptyMsg.exists()).toBe(true)
    expect(emptyMsg.text()).toContain('暂无 trend 数据')
  })

  test('hasCost gate includes dayHas (day-only data shows cost section)', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus(
          {},  // scenario empty
          {},  // tier empty
          { '2026-06-07': 0.02 },  // ONLY day data
        ),
      },
    })
    await flushPromises()

    // hasCost 走 (false || false || true) = true → cost-section 渲染
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(true)
    // CostTrendChart canvas 渲染 (day data → hasData=true)
    expect(wrapper.find(byTestid('cost-trend-chart')).exists()).toBe(true)
    // empty msg 不显示
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })

  test('cost-section hidden when no scenario/tier/day data (all empty)', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus({}, {}, {}),  // 3 维度都空
      },
    })
    await flushPromises()

    // hasCost=false → cost-section 隐藏
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(false)
    // CostTrendChart wrapper 也隐藏 (v-if hasCost)
    expect(wrapper.find(byTestid('cost-trend-chart-wrapper')).exists()).toBe(false)
  })
})
