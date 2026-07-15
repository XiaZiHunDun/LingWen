import { describe, it, expect } from 'vitest';
import {
  buildInlineConflictMarkers,
  findParagraphRange,
} from '../../src/utils/creatorInlineConflictUtils.js';

describe('creatorInlineConflictUtils', () => {
  it('buildInlineConflictMarkers returns empty without chapter', () => {
    expect(buildInlineConflictMarkers({ deviations: [{ chapter: 1 }] })).toEqual([]);
  });

  it('buildInlineConflictMarkers merges deviation logic and light issues', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 2,
      deviations: [
        { chapter: 2, severity: 'alert', message: '偏离', paragraph: 1 },
        { chapter: 3, severity: 'warn', message: 'skip' },
      ],
      logicIssues: [
        { chapter: 2, severity: 'P0', title: 'P0 问题', paragraph: 2 },
        { chapter: 2, severity: 'P1', message: 'warn logic' },
      ],
      lightIssues: [
        { id: 'l1', level: 'warn', label: '引号', paragraph: 3, kind: 'quote', fixHint: '补引号' } as {
          id: string; level: string; label: string; paragraph: number; kind: string; fixHint: string;
        },
      ],
    });
    expect(markers).toHaveLength(4);
    expect(markers[0].level).toBe('error');
    expect(markers[1].level).toBe('error');
    expect(markers[2].level).toBe('warn');
    expect(markers[3].fixHint).toBe('补引号');
  });

  it('buildInlineConflictMarkers caps at ten markers', () => {
    const lightIssues = Array.from({ length: 12 }, (_, i) => ({
      id: `l${i}`,
      level: 'info',
      label: `提示${i}`,
    }));
    expect(buildInlineConflictMarkers({ chapter: 1, lightIssues })).toHaveLength(10);
  });

  it('findParagraphRange locates paragraph offsets', () => {
    const body = '第一段\n\n第二段内容';
    expect(findParagraphRange(body, 0)).toEqual({ offset: 0, length: 0, text: '' });
    expect(findParagraphRange(body, 2).text).toBe('第二段内容');
    expect(findParagraphRange(body, 9).text).toBe('');
  });
});
