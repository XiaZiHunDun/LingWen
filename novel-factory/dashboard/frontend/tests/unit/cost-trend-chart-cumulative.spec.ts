// tests/unit/cost-trend-chart-cumulative.spec.ts — Phase 9.29 F13
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import * as echarts from 'echarts'
import CostTrendChart from '../../src/components/CostTrendChart.vue'
import { computeCumulativeSeries } from '../../src/utils/costTrendChartUtils.js'
import { byTestid } from '../helpers/by-testid'

const dayData = {
  '2026-06-01': 0.010,
  '2026-06-02': 0.005,
  '2026-06-03': 0.015,
}

describe('computeCumulativeSeries (Phase 9.29 F13)', () => {
  test('returns running sum over daily values', () => {
    expect(computeCumulativeSeries([0.01, 0.005, 0.015])).toEqual([
      0.01, 0.015, 0.03,
    ])
  })

  test('empty input returns empty array', () => {
    expect(computeCumulativeSeries([])).toEqual([])
  })
})

describe('CostTrendChart cumulative line (Phase 9.29 F13)', () => {
  beforeEach(() => {
    vi.mocked(echarts.init).mockClear()
  })

  test('single-line path renders daily + cumulative series with legend', async () => {
    const setOptionSpy = vi.fn()
    vi.mocked(echarts.init).mockReturnValueOnce({
      setOption: setOptionSpy,
      clear: vi.fn(),
      dispose: vi.fn(),
      resize: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
    })

    const wrapper = mount(CostTrendChart, {
      props: { costByDay: dayData, costByDayPerTier: null },
    })
    await flushPromises()

    expect(setOptionSpy).toHaveBeenCalled()
    const option = setOptionSpy.mock.calls[0][0]
    expect(option.series).toHaveLength(2)
    expect(option.series.map((s) => s.name)).toEqual(['每日', '累计'])
    expect(option.series[1].data).toEqual([0.01, 0.015, 0.03])
    expect(option.legend.data).toEqual(['每日', '累计'])
    expect(wrapper.find(byTestid('cost-trend-chart-title')).text()).toContain('累计')
  })

  test('per-tier path unchanged (no cumulative series mixed in)', async () => {
    const setOptionSpy = vi.fn()
    vi.mocked(echarts.init).mockReturnValueOnce({
      setOption: setOptionSpy,
      clear: vi.fn(),
      dispose: vi.fn(),
      resize: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
    })

    mount(CostTrendChart, {
      props: {
        costByDay: dayData,
        costByDayPerTier: {
          '2026-06-01': { haiku: 0.005, sonnet: 0.005, opus: 0.0 },
          '2026-06-02': { haiku: 0.002, sonnet: 0.003, opus: 0.0 },
          '2026-06-03': { haiku: 0.005, sonnet: 0.010, opus: 0.0 },
        },
      },
    })
    await flushPromises()

    const option = setOptionSpy.mock.calls[0][0]
    expect(option.series).toHaveLength(2)
    expect(option.series.every((s) => ['haiku', 'sonnet'].includes(s.name))).toBe(true)
    expect(option.legend.data).not.toContain('累计')
  })
})
