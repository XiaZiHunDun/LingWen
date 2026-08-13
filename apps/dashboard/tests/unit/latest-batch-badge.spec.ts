import { describe, it, expect } from 'vitest';
import {
  formatLatestBatchBadge,
  hasLatestBatchBadge,
  latestBatchFromRollup,
  pickLatestBatch,
} from '../../src/utils/latestBatchBadge.js';

describe('latestBatchBadge', () => {
  const batches = [
    { chapter_range: '1-2', recorded_at: '2026-06-01T10:00:00Z', source_file: 'a.json', total_cost_usd: 0.1 },
    { chapter_range: '3-4', recorded_at: '2026-06-02T10:00:00Z', source_file: 'b.json', stopped_reason: 'paused' },
  ];

  it('pickLatestBatch sorts by recorded_at then source_file', () => {
    expect(pickLatestBatch(null)).toBeNull();
    expect(pickLatestBatch([])).toBeNull();
    expect(pickLatestBatch(batches)?.chapter_range).toBe('3-4');
  });

  it('latestBatchFromRollup reads batches array', () => {
    expect(latestBatchFromRollup({ batches })?.chapter_range).toBe('3-4');
    expect(latestBatchFromRollup({})).toBeNull();
  });

  it('formatLatestBatchBadge joins range reason date and cost', () => {
    expect(hasLatestBatchBadge({})).toBe(false);
    const text = formatLatestBatchBadge(batches[1]);
    expect(text).toContain('ch3-4');
    expect(text).toContain('paused');
    expect(text).toContain('2026-06-02');
    expect(formatLatestBatchBadge({ chapter_range: null })).toBe('');
  });
});
