import { describe, it, expect } from 'vitest';
import {
  chapterDecisionLinkEnabled,
  extractChapterFromDecision,
  findPendingDecisionForChapter,
  resolveFocusedDecisionId,
} from '../../src/utils/chapterDecisionLink.js';

describe('chapterDecisionLink', () => {
  it('extractChapterFromDecision reads chapter fields', () => {
    expect(extractChapterFromDecision({ context: { chapter_num: 3 } })).toBe(3);
    expect(extractChapterFromDecision({ context: { chapter: 4 } })).toBe(4);
    expect(extractChapterFromDecision({ context: {} })).toBeNull();
    expect(extractChapterFromDecision(null)).toBeNull();
  });

  it('findPendingDecisionForChapter matches chapter or paused workflow', () => {
    const pending = [
      { decision_id: 'd1', status: 'pending', context: { chapter_num: 2 } },
      { decision_id: 'd2', status: 'resolved', context: { chapter_num: 2 } },
    ];
    expect(findPendingDecisionForChapter(2, pending, null)?.decision_id).toBe('d1');
    const status = { paused: true, production_summary: { chapter_num: 5 } };
    expect(findPendingDecisionForChapter(5, pending, status)?.decision_id).toBe('d1');
    expect(findPendingDecisionForChapter(9, pending, status)).toBeNull();
  });

  it('chapterDecisionLinkEnabled mirrors finder', () => {
    const pending = [{ decision_id: 'd1', status: 'pending', context: { chapter: 1 } }];
    expect(chapterDecisionLinkEnabled(1, pending, null)).toBe(true);
    expect(chapterDecisionLinkEnabled(2, pending, null)).toBe(false);
  });

  it('resolveFocusedDecisionId prefers explicit id then chapter', () => {
    const decisions = [
      { decision_id: 'd1', status: 'pending', context: { chapter_num: 1 } },
      { decision_id: 'd2', status: 'pending', context: { chapter_num: 2 } },
    ];
    expect(resolveFocusedDecisionId(1, 'd2', decisions)).toBe('d2');
    expect(resolveFocusedDecisionId(2, null, decisions)).toBe('d2');
    expect(resolveFocusedDecisionId(null, 'missing', decisions)).toBe('missing');
  });
});
