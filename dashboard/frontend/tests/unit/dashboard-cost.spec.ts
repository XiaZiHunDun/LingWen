// tests/unit/dashboard-cost.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — Dashboard 成本柱状图 (cost_by_scenario render)
// 跟 ceremonial Playwright spec (tests/e2e/dashboard_cost.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test.
//
// 契约 (跟 ceremonial 同步):
//   - cost-section 可见 when cost_by_scenario 有 entry
//   - cost-bar-chart 组件 render 内部 (ECharts canvas stub by setup.ts)
//   - cost-total-usd 文本含 $0.0450 格式

import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowStatus from '../../src/components/WorkflowStatus.vue'
import { byTestid } from '../helpers/by-testid'

const makeStatus = (costByScenario: Record<string, number>, totalUsd: number) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  completed: 7,
  failed: 0,
  paused: false,
  paused_nodes: [],
  node_count: 7,
  steps: 7,
  total_cost_usd: totalUsd,
  pending_decisions: [],
  executions: {
    write_chapter: 'COMPLETED',
    review_chapter: 'COMPLETED',
    polish_emotional_pacing: 'COMPLETED',
    polish_ai_trace_removal: 'COMPLETED',
    polish_merge: 'COMPLETED',
    emit_chapter: 'COMPLETED',
  },
  score_data: {},
  cost_by_scenario: costByScenario,
})

// Phase 8.30b: 隔离 useCostWindow fetch 副作用
vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => ({
    timeWindow: { value: 'all' },
    windowedCost: { value: null },
    setTimeWindow: vi.fn(),
  }),
}))

describe('Dashboard Cost Bar Chart (Phase 8.7)', () => {
  test('renders cost bar chart from workflow status when cost_by_scenario present', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus(
          {
            chapter_writing: 0.015,
            chapter_review: 0.008,
            polish_emotional_pacing: 0.012,
            polish_ai_trace_removal: 0.006,
            polish_merge: 0.004,
          },
          0.045,
        ),
      },
    })
    await flushPromises()

    // cost-section visible
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(true)
    // CostBarChart 组件 render
    expect(wrapper.find(byTestid('cost-bar-chart')).exists()).toBe(true)
    // total USD 文本断言
    const totalUsd = wrapper.get(byTestid('cost-total-usd'))
    expect(totalUsd.text()).toContain('$0.0450')
  })
})
