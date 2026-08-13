// tests/unit/cost-trend-chart-utils.spec.ts — Phase 9.57 F48
import { describe, test, expect } from 'vitest'
import { tierColor, computeCumulativeSeries, TIER_ORDER } from '../../src/utils/costTrendChartUtils.js'

describe('costTrendChartUtils (F48)', () => {
  test('tierColor known and fallback', () => {
    expect(tierColor('haiku')).toBe('#67c23a')
    expect(tierColor('unknown')).toBe('#ff6b6b')
  })

  test('computeCumulativeSeries running sum', () => {
    expect(computeCumulativeSeries([0.1, 0.2, 0.05])).toEqual([0.1, 0.3, 0.35])
  })

  test('TIER_ORDER length', () => {
    expect(TIER_ORDER).toHaveLength(3)
  })
})
