// tests/unit/analytics-production-rollup.spec.js — Phase 9.89 F81
import { describe, test, expect } from 'vitest'
import {
  buildProductionRollupKpiCards,
  formatBatchRollupRows,
  productionRollupSummaryLines,
} from '../../src/utils/analyticsProductionRollup.js'

describe('analyticsProductionRollup (F81)', () => {
  test('buildProductionRollupKpiCards', () => {
    const cards = buildProductionRollupKpiCards({
      record_count: 5,
      pilot_count: 4,
      batch_count: 1,
      total_cost_usd: 0.108,
      chapters_with_records: 4,
    })
    expect(cards.find((c) => c.label === '累计成本 (USD)')?.value).toBe('0.1080')
    expect(cards.find((c) => c.label === '覆盖章节')?.value).toBe(4)
  })

  test('formatBatchRollupRows', () => {
    const rows = formatBatchRollupRows({
      batches: [{
        record_id: 'b1',
        chapter_range: '361-363',
        total_cost_usd: 0.083,
        stopped_reason: 'completed',
        recorded_at: '2026-06-11T01:00:00Z',
      }],
    })
    expect(rows).toHaveLength(1)
    expect(rows[0].range).toBe('ch361-363')
    expect(rows[0].cost).toBe('$0.0830')
  })

  test('productionRollupSummaryLines', () => {
    const lines = productionRollupSummaryLines({
      latest_recorded_at: '2026-06-11T02:00:00Z',
      batch_count: 1,
    })
    expect(lines[0]).toContain('最近记录')
    expect(lines[1]).toContain('Batch 汇总')
  })
})
