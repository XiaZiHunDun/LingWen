/**
 * costTrendChartUtils.js — Cost chart shared helpers (Phase 9.29 F13 + F26)
 */

/** Tier palette shared by CostTrendChart + CostBarChart (F26). */
export const TIER_COLORS = {
  haiku: '#67c23a',
  sonnet: '#ff6b6b',
  opus: '#9b59b6',
}

export const TIER_ORDER = ['haiku', 'sonnet', 'opus']

export function tierColor(tierName) {
  return TIER_COLORS[tierName] ?? '#ff6b6b'
}

/** Running sum over daily USD values (same date order as input). */
export function computeCumulativeSeries(dailyValues) {
  let running = 0
  return dailyValues.map((value) => {
    running += Number(value)
    return Math.round(running * 1_000_000) / 1_000_000
  })
}
