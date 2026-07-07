// tests/unit/cost-trend-chart-branches.spec.ts — Phase 9.57 F48
import { describe, test, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import CostTrendChart from '../../src/components/CostTrendChart.vue'
import { byTestid } from '../helpers/by-testid'

describe('CostTrendChart branches (F48)', () => {
  test('empty data shows empty hint', async () => {
    const wrapper = mount(CostTrendChart, { props: { costByDay: {} } })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(true)
  })

  test('single series with daily data', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: { '2026-06-01': 0.01, '2026-06-02': 0.02 } },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart')).exists()).toBe(true)
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })

  test('multi-tier series path', async () => {
    const wrapper = mount(CostTrendChart, {
      props: {
        costByDay: { '2026-06-01': 0.03 },
        costByDayPerTier: {
          '2026-06-01': { haiku: 0.01, sonnet: 0.01, opus: 0.01 },
          '2026-06-02': { haiku: 0, sonnet: 0.02, opus: 0 },
        },
      },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })

  test('prop update clears empty state', async () => {
    const wrapper = mount(CostTrendChart, { props: { costByDay: {} } })
    await flushPromises()
    await wrapper.setProps({ costByDay: { '2026-06-03': 0.05 } } as never)
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })
})
