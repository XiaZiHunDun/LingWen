// tests/unit/analytics-production-cost-trend.spec.js — Phase 9.96 F87
import { describe, test, expect } from 'vitest'
import {
  buildCostTrendChartOption,
  formatTrendAxisLabel,
  hasCostTrendData,
  productionCostTrendSummaryLines,
} from '../../src/utils/analyticsProductionCostTrend.js'

const sampleTrend = {
  point_count: 2,
  total_cost_usd: 0.108,
  points: [
    {
      recorded_at: '2026-06-11T00:00:00Z',
      record_id: 'ch360',
      record_type: 'pilot',
      label: 'ch360',
      cost_usd: 0.025,
      incremental_cost_usd: 0.025,
      cumulative_cost_usd: 0.025,
    },
    {
      recorded_at: '2026-06-11T01:00:00Z',
      record_id: 'batch-361-363',
      record_type: 'batch',
      label: 'ch361-363',
      cost_usd: 0.083,
      incremental_cost_usd: 0.083,
      cumulative_cost_usd: 0.108,
    },
  ],
}

describe('analyticsProductionCostTrend (F87)', () => {
  test('hasCostTrendData', () => {
    expect(hasCostTrendData(sampleTrend)).toBe(true)
    expect(hasCostTrendData({ points: [] })).toBe(false)
    expect(hasCostTrendData(null)).toBe(false)
  })

  test('formatTrendAxisLabel', () => {
    expect(formatTrendAxisLabel(sampleTrend.points[0])).toBe('2026-06-11')
    expect(formatTrendAxisLabel({ label: 'ch361-363' })).toBe('ch361-363')
  })

  test('buildCostTrendChartOption', () => {
    const option = buildCostTrendChartOption(sampleTrend)
    expect(option.series).toHaveLength(2)
    expect(option.series[0].data).toEqual([0.025, 0.083])
    expect(option.series[1].data).toEqual([0.025, 0.108])
    expect(option.xAxis.data).toEqual(['2026-06-11', '2026-06-11'])
  })

  test('productionCostTrendSummaryLines', () => {
    const lines = productionCostTrendSummaryLines(sampleTrend)
    expect(lines[0]).toContain('2 点')
    expect(lines[0]).toContain('0.1080')
    expect(lines[1]).toContain('ch361-363')
  })
})
