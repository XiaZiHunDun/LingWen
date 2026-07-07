// tests/unit/analytics-kpi.spec.js — Phase 9.77 F67
import { describe, test, expect } from 'vitest'
import {
  buildProductionKpiCards,
  buildRippleKpiCards,
} from '../../src/utils/analyticsKpi.js'

describe('analyticsKpi (F67)', () => {
  test('buildProductionKpiCards idle workflow', () => {
    const cards = buildProductionKpiCards({ is_active: false })
    expect(cards.find((c) => c.label === '工作流状态')?.value).toBe('空闲')
  })

  test('buildProductionKpiCards paused workflow', () => {
    const cards = buildProductionKpiCards({
      is_active: true,
      paused: true,
      workflow_name: 'novel_writing',
    })
    expect(cards.find((c) => c.label === '工作流状态')?.value).toContain('暂停')
  })

  test('buildProductionKpiCards active with summary', () => {
    const cards = buildProductionKpiCards({
      is_active: true,
      workflow_name: 'novel_writing',
      paused: false,
      completed: 5,
      failed: 0,
      total_cost_usd: 0.0123,
      pending_decisions: [{ decision_id: 'd1' }],
      production_summary: { chapter_num: 360 },
    })
    expect(cards.find((c) => c.label === '生产章节')?.value).toBe('#360')
    expect(cards.find((c) => c.label === 'LLM 成本 (USD)')?.value).toBe('0.0123')
  })

  test('buildRippleKpiCards', () => {
    const cards = buildRippleKpiCards({
      total: 4,
      by_status: { open: 2, resolved: 1 },
    })
    expect(cards.find((c) => c.label === '涟漪总数')?.value).toBe(4)
    expect(cards.find((c) => c.label === 'OPEN')?.value).toBe(2)
  })
})
