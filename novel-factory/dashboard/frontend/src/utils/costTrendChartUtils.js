/**
 * costTrendChartUtils.js — CostTrendChart helpers (Phase 9.29 F13)
 */

/** Running sum over daily USD values (same date order as input). */
export function computeCumulativeSeries(dailyValues) {
  let running = 0
  return dailyValues.map((value) => {
    running += Number(value)
    return Math.round(running * 1_000_000) / 1_000_000
  })
}
