// tests/unit/cost-bar-chart-scenario.spec.ts — Phase 9.57 F48
import { describe, test, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import CostBarChart from '../../src/components/CostBarChart.vue'
import { byTestid } from '../helpers/by-testid'

describe('CostBarChart scenario mode (F48)', () => {
  test('scenario mode renders chart without tier legend', async () => {
    const wrapper = mount(CostBarChart, {
      props: {
        costByScenario: { writing: 0.02, review: 0.01 },
        costByTier: {},
        mode: 'scenario',
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-bar-chart')).exists()).toBe(true)
  })

  test('empty scenario shows empty state', async () => {
    const wrapper = mount(CostBarChart, {
      props: { costByScenario: {}, costByTier: {}, mode: 'scenario' },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('暂无')
  })

  test('tier mode still renders with tier data', async () => {
    const wrapper = mount(CostBarChart, {
      props: {
        costByScenario: {},
        costByTier: { haiku: 0.01, sonnet: 0.02, opus: 0.03 },
        mode: 'tier',
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-bar-chart')).exists()).toBe(true)
  })
})
