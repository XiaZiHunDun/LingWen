import { describe, expect, it } from 'vitest';
import {
  buildMicroTaskProgress,
  countDraftChars,
  resolveChapterWordGoal,
} from '../../src/utils/creatorMicroTaskUtils.js';

describe('creatorMicroTaskUtils', () => {
  it('counts draft chars without whitespace', () => {
    expect(countDraftChars('你好 世界')).toBe(4);
    expect(countDraftChars('')).toBe(0);
  });

  it('resolves chapter word goals by mode', () => {
    expect(resolveChapterWordGoal({ creationMode: 'companion' })).toBe(1500);
    expect(resolveChapterWordGoal({ creationMode: 'advance' })).toBe(2000);
    expect(resolveChapterWordGoal({ goal: 800 })).toBe(800);
  });

  it('builds remaining progress for micro task bar', () => {
    const draft = '字'.repeat(1400);
    const progress = buildMicroTaskProgress({ draft, creationMode: 'companion' });
    expect(progress.current).toBe(1400);
    expect(progress.remaining).toBe(100);
    expect(progress.met).toBe(false);
    expect(progress.progress).toBe(93);
  });

  it('marks goal met when draft reaches target', () => {
    const draft = '字'.repeat(1500);
    const progress = buildMicroTaskProgress({ draft, creationMode: 'companion' });
    expect(progress.met).toBe(true);
    expect(progress.remaining).toBe(0);
    expect(progress.progress).toBe(100);
  });
});
