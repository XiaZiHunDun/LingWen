// tests/unit/production-records.spec.js — Phase 9.82 F74
import { describe, test, expect } from 'vitest'
import {
  formatProductionRecordRows,
  indexRecordsByChapter,
  chapterProductionBadge,
} from '../../src/utils/productionRecords.js'

describe('productionRecords (F74)', () => {
  test('formatProductionRecordRows', () => {
    const rows = formatProductionRecordRows([
      {
        record_id: 'p1',
        record_type: 'pilot',
        chapter_num: 360,
        chapter_range: null,
        operator: 'op',
        recorded_at: '2026-06-11T00:00:00Z',
        provider: 'minimax',
        total_cost_usd: 0.025,
        emit_chapter_completed: true,
        memory_context_source: 'stub',
        stopped_reason: null,
        source_file: 'ch360.json',
      },
    ])
    expect(rows[0].chapter).toBe('#360')
    expect(rows[0].cost).toBe('$0.0250')
    expect(rows[0].status).toBe('emit ok')
  })

  test('indexRecordsByChapter and badge', () => {
    const rec = {
      record_id: 'p1',
      record_type: 'pilot',
      chapter_num: 360,
      emit_chapter_completed: true,
    }
    const map = indexRecordsByChapter([rec])
    expect(chapterProductionBadge(360, map)).toBe('已生产')
    expect(chapterProductionBadge(361, map)).toBeNull()
  })
})
