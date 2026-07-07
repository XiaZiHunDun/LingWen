// tests/unit/share-link.spec.js
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { buildDashboardShareUrl, copyDashboardShareUrl } from '../../src/utils/shareLink.js';

describe('shareLink', () => {
  beforeEach(() => {
    vi.stubGlobal('window', {
      location: {
        origin: 'http://localhost:5173',
        pathname: '/',
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test('buildDashboardShareUrl returns empty without window', () => {
    vi.stubGlobal('window', undefined);
    expect(buildDashboardShareUrl({ nav: 'creator' })).toBe('');
  });

  test('buildDashboardShareUrl adds nav/tab/chapter params', () => {
    const url = buildDashboardShareUrl({
      nav: 'inbox',
      tab: 'decisions',
      chapter: 3,
      role: 'reviewer',
    });
    expect(url).toContain('nav=inbox');
    expect(url).toContain('tab=decisions');
    expect(url).toContain('chapter=3');
    expect(url).toContain('role=reviewer');
  });

  test('buildDashboardShareUrl omits nav when today', () => {
    const url = buildDashboardShareUrl({ nav: 'today', tab: 'decisions' });
    expect(url).not.toContain('nav=today');
    expect(url).toContain('tab=decisions');
  });

  test('buildDashboardShareUrl includes decision deep link', () => {
    const url = buildDashboardShareUrl({ nav: 'inbox', decision: 'd-42' });
    expect(url).toContain('decision=d-42');
  });

  test('copyDashboardShareUrl writes clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });
    const result = await copyDashboardShareUrl({ nav: 'creator', chapter: 1 });
    expect(result.ok).toBe(true);
    expect(writeText).toHaveBeenCalled();
  });

  test('copyDashboardShareUrl empty when url missing', async () => {
    vi.stubGlobal('window', undefined);
    const result = await copyDashboardShareUrl({ nav: 'creator' });
    expect(result.ok).toBe(false);
    expect(result.url).toBe('');
  });

  test('copyDashboardShareUrl handles clipboard failure', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('denied'));
    vi.stubGlobal('navigator', { clipboard: { writeText } });
    const result = await copyDashboardShareUrl({ nav: 'creator' });
    expect(result.ok).toBe(false);
    expect(result.url).toContain('nav=creator');
  });
});
