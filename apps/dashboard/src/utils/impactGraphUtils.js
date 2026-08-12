/**
 * impactGraphUtils.js — ImpactGraph dimension palette (Phase 9.41 F30)
 */

export const IMPACT_DIMENSION_COLORS = {
  character: '#3b82f6',
  foreshadow: '#8b5cf6',
  setting: '#10b981',
  plot_point: '#f59e0b',
}

export const IMPACT_DIMENSION_ORDER = ['character', 'foreshadow', 'setting', 'plot_point']

export function impactNodeColor(dimension) {
  return IMPACT_DIMENSION_COLORS[dimension] ?? '#9ca3af'
}
