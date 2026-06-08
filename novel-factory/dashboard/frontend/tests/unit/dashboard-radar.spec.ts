// tests/unit/dashboard-radar.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — Dashboard S1-S8 评分雷达图
// 跟 ceremonial Playwright spec (tests/e2e/dashboard_radar.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test.
//
// 契约 (跟 ceremonial 同步):
//   - WorkflowStatus 含 score_data 时渲染 ScoreRadarChart
//   - score-radar-chart canvas 渲染 (ECharts 走 setup.ts stub)
//   - winner-badge 显 (label 含 "polish_emotional_pacing")
//   - score_data 含 fallback reason → score-radar-fallback-warning 显 ("LLM 评分未生效")

import { describe, test, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowStatus from '../../src/components/WorkflowStatus.vue'

const makeStatus = (scoreData: Record<string, any> = {}, costByScenario: Record<string, number> = {}) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 7,
  failed: 0,
  node_count: 7,
  steps: 7,
  cost_by_scenario: costByScenario,
  cost_by_tier: {},
  total_cost_usd: 0.0,
  score_data: scoreData,
})

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => {
    const timeWindow = ref('all')
    const windowedCost = ref(null)
    const setTimeWindow = vi.fn()
    return { timeWindow, windowedCost, setTimeWindow }
  },
}))

describe('Dashboard Score Radar (Phase 7.6)', () => {
  test('radar chart renders when score_data has S1-S8 scores + winner badge visible', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus({
          polish_merge: {
            scores_a: { S1: 8, S2: 7, S3: 9, S4: 8, S5: 7, S6: 8, S7: 9, S8: 8 },
            scores_b: { S1: 5, S2: 5, S3: 5, S4: 5, S5: 5, S6: 5, S7: 5, S8: 5 },
            scores_total_a: 8.0,
            scores_total_b: 5.0,
            scores_delta: 3.0,
            winner: 'polish_emotional_pacing',
            label_a: 'polish_emotional_pacing',
            label_b: 'polish_ai_trace_removal',
            fallback: null,
          },
        }),
      },
    })
    await flushPromises()

    // 雷达图容器 渲染 (data-testid 来自 ScoreRadarChart 内部)
    const radar = wrapper.find('[data-testid="score-radar-chart"]')
    expect(radar.exists()).toBe(true)

    // winner badge 显 (label_a "polish_emotional_pacing")
    const winnerBadge = wrapper.find('[data-testid="winner-badge"]')
    expect(winnerBadge.exists()).toBe(true)
    expect(winnerBadge.text()).toContain('polish_emotional_pacing')

    // fallback warning NOT shown (fallback=null)
    expect(wrapper.find('[data-testid="score-radar-fallback-warning"]').exists()).toBe(false)
  })

  test('fallback warning shown when score_data has fallback reason', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus({
          polish_merge: {
            scores_a: {},
            scores_b: {},
            scores_total_a: 0,
            scores_total_b: 0,
            scores_delta: 0,
            winner: '',
            label_a: 'A',
            label_b: 'B',
            fallback: 'llm_fail',
          },
        }),
      },
    })
    await flushPromises()

    // 警告横幅 可见 (含 "LLM 评分未生效")
    const warning = wrapper.find('[data-testid="score-radar-fallback-warning"]')
    expect(warning.exists()).toBe(true)
    expect(warning.text()).toContain('LLM 评分未生效')
  })
})
