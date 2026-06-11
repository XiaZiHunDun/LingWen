// tests/unit/workflow-status-branches.spec.ts — Phase 9.57 F48
import { describe, test, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowStatus from '../../src/components/WorkflowStatus.vue'
import { byTestid } from '../helpers/by-testid'

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => ({
    timeWindow: { value: 'all' },
    windowedCost: { value: null },
    setTimeWindow: vi.fn(),
  }),
}))

const baseStatus = {
  workflow_name: 'novel_writing',
  is_active: true,
  completed: 2,
  failed: 1,
  paused: false,
  paused_nodes: [],
  node_count: 5,
  steps: 3,
  total_cost_usd: 0.05,
  pending_decisions: [],
  cost_by_scenario: { write: 0.03 },
  cost_by_tier: { sonnet: 0.02 },
  score_data: {},
}

describe('WorkflowStatus branches (F48)', () => {
  test('unknown workflow name fallback', () => {
    const wrapper = mount(WorkflowStatus, {
      props: { status: { ...baseStatus, workflow_name: '' } },
    })
    expect(wrapper.text()).toContain('未知工作流')
  })

  test('paused section when paused_nodes present', () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: { ...baseStatus, paused: true, paused_nodes: ['node-a'] },
      },
    })
    expect(wrapper.text()).toContain('node-a')
  })

  test('pending decisions render resume buttons', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: {
          ...baseStatus,
          pending_decisions: [{
            decision_id: 'd1',
            kind: 'outline',
            node_id: 'n1',
            priority: 1,
            prompt: 'Pick',
            options: ['A', 'B'],
          }],
        },
      },
    })
    expect(wrapper.text()).toContain('待审核决策')
    await wrapper.find('.resume-btn').trigger('click')
    expect(wrapper.emitted('resume')?.[0]?.[0]).toMatchObject({ decisionId: 'd1', option: 'A' })
  })

  test('cost section visible when scenario cost present', async () => {
    const wrapper = mount(WorkflowStatus, { props: { status: baseStatus } })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(true)
  })

  test('score radar when score_data populated', () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: {
          ...baseStatus,
          score_data: {
            n1: {
              scores_a: { s1: 1 },
              scores_b: { s1: 2 },
              label_a: 'A',
              label_b: 'B',
              winner: 'A',
            },
          },
        },
      },
    })
    expect(wrapper.find('[data-testid="score-radar-chart"]').exists()).toBe(true)
  })

  test('status labels for idle paused running', () => {
    const idle = mount(WorkflowStatus, { props: { status: { ...baseStatus, is_active: false } } })
    expect(idle.text()).toContain('未运行')
    const paused = mount(WorkflowStatus, { props: { status: { ...baseStatus, is_active: true, paused: true } } })
    expect(paused.text()).toContain('已暂停')
    const running = mount(WorkflowStatus, { props: { status: { ...baseStatus, is_active: true, paused: false } } })
    expect(running.text()).toContain('运行中')
  })

  test('cost section with day-only data', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: {
          ...baseStatus,
          cost_by_scenario: {},
          cost_by_tier: {},
          cost_by_day: { '2026-06-01': 0.02 },
        },
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-section')).exists()).toBe(true)
  })
})
