import { describe, it, expect } from 'vitest';
import { computeLineDiff, countDiffChanges } from '../../src/utils/textDiffUtils.js';

describe('textDiffUtils', () => {
  it('computeLineDiff marks added and removed lines', () => {
    const lines = computeLineDiff('a\nb\nc', 'a\nx\nc\nd');
    expect(lines.some((l) => l.type === 'remove' && l.text === 'b')).toBe(true);
    expect(lines.some((l) => l.type === 'add' && l.text === 'x')).toBe(true);
    expect(countDiffChanges(lines)).toBeGreaterThan(0);
  });

  it('computeLineDiff handles empty old text', () => {
    const lines = computeLineDiff('', 'new');
    expect(lines.some((l) => l.type === 'add' && l.text === 'new')).toBe(true);
    expect(countDiffChanges(computeLineDiff('only', ''))).toBeGreaterThan(0);
  });
});
