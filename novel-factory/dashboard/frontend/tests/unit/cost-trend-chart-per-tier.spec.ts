// tests/unit/cost-trend-chart-per-tier.spec.ts — Phase 8.30
// vitest 真 e2e 改造 — CostTrendChart per-tier multi-series (Phase 8.29)
// 跟 ceremonial spec (cost-trend-chart-per-tier.spec.js) 同契约:
//   - costByDayPerTier=null → 单线 baseline (Phase 8.24)
//   - costByDayPerTier={...non-zero} → multi-series 3 lines (haiku/sonnet/opus) + legend
//   - costByDayPerTier={...all zero} → multi-series 但 0 data
//   - 0 改 baseline: costByDay prop 仍 required, 单线 path 保留 (additive 升级)
//
// ECharts canvas 渲染 stub 走 tests/unit/setup.ts (Phase 8.30 setup file).
// 测试只关 component 行为契约 (data-testid 渲染 / render() 调用), 不需真实 pixel.

import { describe, test, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import * as echarts from 'echarts'
import CostTrendChart from '../../src/components/CostTrendChart.vue'
import { byTestid } from '../helpers/by-testid'

const dayData = {
  '2026-06-01': 0.020,
  '2026-06-02': 0.020,
  '2026-06-03': 0.020,
}

const dayDataPerTier = {
  '2026-06-01': { haiku: 0.005, sonnet: 0.010, opus: 0.005 },
  '2026-06-02': { haiku: 0.008, sonnet: 0.015, opus: 0.005 },
  '2026-06-03': { haiku: 0.005, sonnet: 0.020, opus: 0.010 },
}

const dayDataAllZero = {
  '2026-06-01': { haiku: 0, sonnet: 0, opus: 0 },
  '2026-06-02': { haiku: 0, sonnet: 0, opus: 0 },
}

describe('CostTrendChart: single-line baseline (Phase 8.24)', () => {
  test('renders chart wrapper with data-testid when costByDay has data', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: dayData },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart')).exists()).toBe(true)
    expect(wrapper.find(byTestid('cost-trend-chart-wrapper')).exists()).toBe(true)
  })

  test('hides empty state when costByDay has values', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: dayData },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })

  test('shows empty state when costByDay is empty', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: {} },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(true)
  })

  test('costByDayPerTier=null falls back to single-line baseline (no regression)', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: dayData, costByDayPerTier: null },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart')).exists()).toBe(true)
  })
})

describe('CostTrendChart: per-tier multi-series (Phase 8.29)', () => {
  beforeEach(() => {
    // 每次 init/setOption 调用都会入账, 重置 mock 以便精准断言 per-tier path
    vi.mocked(echarts.init).mockClear()
  })

  test('renders multi-series with 3 lines when costByDayPerTier has non-zero data', async () => {
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
      props: { costByDay: dayData, costByDayPerTier: dayDataPerTier },
    })
    await flushPromises()

    expect(setOptionSpy).toHaveBeenCalled()
    const option = setOptionSpy.mock.calls[0][0]
    // Phase 8.29: per-tier 多线 path → series 数组 length=3 (haiku/sonnet/opus)
    expect(option.series.length).toBe(3)
    // legend data 应包含 3 tier name
    expect(option.legend.data).toEqual(expect.arrayContaining(['haiku', 'sonnet', 'opus']))
    // series name 应跟 TIER_ORDER 一致
    expect(option.series.map((s) => s.name).sort()).toEqual(['haiku', 'opus', 'sonnet'])
  })

  test('shows empty state when both costByDay and costByDayPerTier empty', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: {}, costByDayPerTier: {} },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(true)
  })

  test('hides empty state when only costByDayPerTier has data (Phase 9.28 F12)', async () => {
    const wrapper = mount(CostTrendChart, {
      props: { costByDay: {}, costByDayPerTier: dayDataPerTier },
    })
    await flushPromises()
    expect(wrapper.find(byTestid('cost-trend-chart-empty')).exists()).toBe(false)
  })

  test('uses single-line baseline when costByDayPerTier is empty dict', async () => {
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
      props: { costByDay: dayData, costByDayPerTier: {} },
    })
    await flushPromises()

    expect(setOptionSpy).toHaveBeenCalled()
    const option = setOptionSpy.mock.calls[0][0]
    // Phase 8.29: empty dict → hasMultiSeries=false → 单线 path
    expect(option.series.length).toBe(1)
  })

  test('uses single-line baseline when costByDayPerTier all-zero', async () => {
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
      props: { costByDay: dayData, costByDayPerTier: dayDataAllZero },
    })
    await flushPromises()

    expect(setOptionSpy).toHaveBeenCalled()
    const option = setOptionSpy.mock.calls[0][0]
    // Phase 8.29: 全 0 → hasMultiSeries=false (some > 0 检查失败) → 单线
    expect(option.series.length).toBe(1)
  })
})
