// tests/unit/production-summary.spec.js — Phase 9.74 F66
import { describe, test, expect } from 'vitest'
import {
  formatIncrementalBackfill,
  productionSummaryLines,
  resolveProductionSummary,
  hasProductionSummary,
} from '../../src/utils/productionSummary.js'

describe('productionSummary utils (F66)', () => {
  test('formatIncrementalBackfill builds label', () => {
    const label = formatIncrementalBackfill({
      nodes_written: 2,
      nodes_skipped: 1,
      total_count: 3,
      elapsed_s: 0.12,
    })
    expect(label).toContain('写入 2 节点')
    expect(label).toContain('跳过 1')
  })

  test('productionSummaryLines from nested summary', () => {
    const lines = productionSummaryLines({
      chapter_num: 360,
      memory_context_source: 'stub',
      emit_chapter_completed: true,
      incremental_backfill: { nodes_written: 1 },
    })
    expect(lines.some((l) => l.includes('360'))).toBe(true)
    expect(lines.some((l) => l.includes('Memory: stub'))).toBe(true)
    expect(lines.some((l) => l.includes('emit_chapter'))).toBe(true)
  })

  test('resolveProductionSummary prefers nested object', () => {
    const status = {
      production_summary: { chapter_num: 5 },
      incremental_backfill: { nodes_written: 9 },
    }
    expect(resolveProductionSummary(status)?.chapter_num).toBe(5)
  })

  test('resolveProductionSummary falls back to incremental_backfill', () => {
    const status = { incremental_backfill: { nodes_written: 1 } }
    expect(hasProductionSummary(status)).toBe(true)
  })
})
