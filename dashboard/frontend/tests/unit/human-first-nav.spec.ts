import { describe, expect, it } from 'vitest';
import {
  buildVisibleNavGroups,
  buildMorePageLinks,
  isNavItemAllowedForMode,
  suggestNavFallback,
} from '../../src/config/dashboardNavByMode.js';
import { isHumanNavItemActive } from '../../src/config/humanFirstNav.js';
import { resolveDefaultLandingNav, resolveDefaultLandingNavAsync } from '../../src/utils/resolveDefaultLanding.js';
import { saveWriteResume } from '../../src/utils/writeResumeStorage.js';

describe('dashboardNavByMode (human-first)', () => {
  it('companion shows ask/write/library/more/settings', () => {
    const ids = buildVisibleNavGroups('companion').flatMap((g) => g.items.map((i) => i.id));
    expect(ids).toEqual(['ask', 'write', 'library', 'more', 'settings']);
  });

  it('studio hides write', () => {
    const ids = buildVisibleNavGroups('studio').flatMap((g) => g.items.map((i) => i.id));
    expect(ids).not.toContain('write');
    expect(ids).toContain('ask');
  });

  it('companion more page hides produce and settings', () => {
    const ids = buildMorePageLinks('companion').map((l) => l.id);
    expect(ids).not.toContain('produce');
    expect(ids).not.toContain('settings');
    expect(ids).toContain('inbox');
  });

  it('advance more page includes produce', () => {
    const ids = buildMorePageLinks('advance').map((l) => l.id);
    expect(ids).toContain('produce');
  });

  it('suggestNavFallback studio on write', () => {
    expect(suggestNavFallback('creator', 'studio')).toBe('produce');
    expect(suggestNavFallback('write', 'studio')).toBe('produce');
  });

  it('isHumanNavItemActive maps write to creator', () => {
    expect(isHumanNavItemActive('write', 'creator')).toBe(true);
    expect(isHumanNavItemActive('ask', 'creator')).toBe(false);
  });
});

describe('resolveDefaultLandingNav', () => {
  it('returns ask for empty project', () => {
    expect(resolveDefaultLandingNav({ chaptersWritten: 0 })).toBe('ask');
  });

  it('returns write when chapters exist', () => {
    expect(resolveDefaultLandingNav({ chaptersWritten: 3 })).toBe('write');
  });

  it('returns write when resume exists', () => {
    saveWriteResume('demo', { chapter: 2 });
    expect(resolveDefaultLandingNav({ slug: 'demo', chaptersWritten: 0 })).toBe('write');
  });

  it('returns inbox for reviewer regardless of progress', () => {
    expect(resolveDefaultLandingNav({ isReviewer: true, chaptersWritten: 5 })).toBe('inbox');
    expect(resolveDefaultLandingNav({ isReviewer: true, slug: 'demo', chaptersWritten: 0 })).toBe('inbox');
  });
});

describe('resolveDefaultLandingNavAsync', () => {
  it('returns inbox for reviewer without fetching', async () => {
    const nav = await resolveDefaultLandingNavAsync({
      isReviewer: true,
      fetchSummary: async () => ({ slug: 'x', chapter_count: 9 }),
    });
    expect(nav).toBe('inbox');
  });

  it('merges summary and overview chapter counts', async () => {
    const nav = await resolveDefaultLandingNavAsync({
      fetchSummary: async () => ({ slug: 'demo', chapter_count: 0 }),
      fetchOverview: async () => ({ slug: 'demo', chapters_written: 2 }),
    });
    expect(nav).toBe('write');
  });

  it('ignores rejected fetches', async () => {
    const nav = await resolveDefaultLandingNavAsync({
      fetchSummary: async () => { throw new Error('down'); },
      fetchOverview: async () => { throw new Error('down'); },
    });
    expect(nav).toBe('ask');
  });
});
