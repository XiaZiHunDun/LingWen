import { describe, it, expect } from 'vitest';
import {
  chapterProductionBadge,
  formatProductionRecordRows,
  formatRecordChapterLabel,
  formatRecordCost,
  formatRecordStatus,
  formatRecordSummaryLine,
  indexRecordsByChapter,
} from '../../src/utils/productionRecords.js';

const pilot = (overrides: Record<string, unknown> = {}) => ({
  record_id: 'p1',
  record_type: 'pilot' as const,
  chapter_num: 3,
  chapter_range: null,
  operator: 'ops',
  recorded_at: '2026-06-01T12:00:00Z',
  provider: 'mock',
  total_cost_usd: 0.0123,
  emit_chapter_completed: true,
  memory_context_source: 'rag',
  stopped_reason: null,
  source_file: 'p1.json',
  ...overrides,
});

const batch = (overrides: Record<string, unknown> = {}) => ({
  record_id: 'b1',
  record_type: 'batch' as const,
  chapter_num: null,
  chapter_range: '2-4',
  operator: null,
  recorded_at: null,
  provider: null,
  total_cost_usd: null,
  emit_chapter_completed: null,
  memory_context_source: null,
  stopped_reason: 'paused',
  source_file: 'b1.json',
  ...overrides,
});

describe('productionRecords', () => {
  it('formatRecordCost handles null and numbers', () => {
    expect(formatRecordCost(pilot({ total_cost_usd: null }))).toBe('-');
    expect(formatRecordCost(pilot({ total_cost_usd: 0.1 }))).toBe('$0.1000');
  });

  it('formatRecordChapterLabel prefers batch range', () => {
    expect(formatRecordChapterLabel(batch())).toBe('ch2-4');
    expect(formatRecordChapterLabel(pilot())).toBe('#3');
    expect(formatRecordChapterLabel(pilot({ chapter_num: null }))).toBe('-');
  });

  it('formatRecordStatus covers batch and emit branches', () => {
    expect(formatRecordStatus(batch())).toBe('paused');
    expect(formatRecordStatus(batch({ stopped_reason: null }))).toBe('batch');
    expect(formatRecordStatus(pilot({ emit_chapter_completed: true }))).toBe('emit ok');
    expect(formatRecordStatus(pilot({ emit_chapter_completed: false }))).toBe('emit fail');
    expect(formatRecordStatus(pilot({ emit_chapter_completed: null }))).toBe('-');
  });

  it('formatRecordSummaryLine joins provider and memory', () => {
    const line = formatRecordSummaryLine(pilot());
    expect(line).toContain('mock');
    expect(line).toContain('mem:rag');
    expect(line).toContain('emit ok');
  });

  it('indexRecordsByChapter maps pilot and batch ranges', () => {
    const map = indexRecordsByChapter([
      pilot({ chapter_num: 1 }),
      batch({ chapter_range: '2-3' }),
      batch({ chapter_range: 'bad' }),
    ]);
    expect(map[1].record_id).toBe('p1');
    expect(map[2].record_id).toBe('b1');
    expect(map[3].record_id).toBe('b1');
    expect(map[99]).toBeUndefined();
  });

  it('chapterProductionBadge returns labels per record type', () => {
    const byChapter = indexRecordsByChapter([pilot({ chapter_num: 5, emit_chapter_completed: false })]);
    expect(chapterProductionBadge(5, byChapter)).toBe('生产异常');
    const batchMap = indexRecordsByChapter([batch({ chapter_range: '6-6' })]);
    expect(chapterProductionBadge(6, batchMap)).toBe('batch');
    expect(chapterProductionBadge(1, {})).toBeNull();
  });

  it('formatProductionRecordRows normalizes table fields', () => {
    const rows = formatProductionRecordRows([pilot(), batch()]);
    expect(rows[0].key).toBe('p1');
    expect(rows[0].at).toBe('2026-06-01T12:00:00');
    expect(rows[1].operator).toBe('-');
    expect(rows[1].cost).toBe('-');
  });
});
