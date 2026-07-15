// tests/unit/latest-batch-badge.spec.js — Phase 9.97 F88
import { describe, test, expect } from 'vitest'
import {
  formatLatestBatchBadge,
  hasLatestBatchBadge,
  latestBatchFromRollup,
  pickLatestBatch,
} from '../../src/utils/latestBatchBadge.js'

describe('latestBatchBadge (F88)', () => {
  test('pickLatestBatch sorts by recorded_at desc', () => {
    const latest = pickLatestBatch([
      {
        record_id: 'b-old',
        chapter_range: '350-352',
        recorded_at: '2026-06-10T00:00:00Z',
        stopped_reason: 'completed',
      },
      {
        record_id: 'b-new',
        chapter_range: '361-363',
        recorded_at: '2026-06-11T01:00:00Z',
        stopped_reason: 'completed',
        total_cost_usd: 0.083,
      },
    ])
    expect(latest?.record_id).toBe('b-new')
    expect(latest?.chapter_range).toBe('361-363')
  })

  test('formatLatestBatchBadge', () => {
    const text = formatLatestBatchBadge({
      chapter_range: '361-363',
      stopped_reason: 'completed',
      recorded_at: '2026-06-11T01:00:00Z',
      total_cost_usd: 0.083,
    })
    expect(text).toBe('ch361-363 · completed · 2026-06-11 · $0.0830')
  })

  test('latestBatchFromRollup', () => {
    const batch = latestBatchFromRollup({
      batches: [{
        chapter_range: '364-366',
        recorded_at: '2026-06-12T00:00:00Z',
        stopped_reason: 'completed',
      }],
    })
    expect(hasLatestBatchBadge(batch)).toBe(true)
    expect(formatLatestBatchBadge(batch)).toContain('ch364-366')
  })

  test('hasLatestBatchBadge false when no range', () => {
    expect(hasLatestBatchBadge({ record_id: 'x' })).toBe(false)
    expect(formatLatestBatchBadge(null)).toBe('')
  })
})
