/**
 * useNavUrlUtils 独立测试（Phase 63.1）
 *
 * 17 helpers 从 useNavStore.js 抽出后独立可测。
 * 使用 vi.stubGlobal('window', ...) 模拟 URL 参数；
 * vi.unstubAllGlobals() 在每个测试后清理。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNavUrlUtils } from '../../src/stores/useNavUrlUtils';

type WindowStub = {
  location: {
    href: string;
    search: string;
    pathname: string;
    hash: string;
  };
};

function stubWindowUrl(search: string, href?: string): void {
  const base = 'http://test/';
  const fullHref = href ?? `${base}${search}`;
  vi.stubGlobal('window', {
    location: {
      href: fullHref,
      search,
      pathname: '/',
      hash: '',
    },
  } as unknown as WindowStub);
}

function stubWindowUndefined(): void {
  // vitest stubGlobal accepts undefined as value
  vi.stubGlobal('window', undefined as unknown as WindowStub);
}

describe('useNavUrlUtils', () => {
  let utils: ReturnType<typeof useNavUrlUtils>;

  beforeEach(() => {
    utils = useNavUrlUtils();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // ───────────────────────────────────────────────────────────────────────
  // 1. canonicalNav — 5 legacy-id collapses + identity + empty fallback
  // ───────────────────────────────────────────────────────────────────────
  describe('canonicalNav', () => {
    it('returns "ask" for empty/falsy nav', () => {
      expect(utils.canonicalNav('')).toBe('ask');
      expect(utils.canonicalNav(undefined as unknown as string)).toBe('ask');
      expect(utils.canonicalNav(null as unknown as string)).toBe('ask');
    });

    it('collapses write/creator to creator', () => {
      expect(utils.canonicalNav('write')).toBe('creator');
      expect(utils.canonicalNav('creator')).toBe('creator');
    });

    it('collapses legacy produce ids to produce', () => {
      expect(utils.canonicalNav('studio')).toBe('produce');
      expect(utils.canonicalNav('chapters')).toBe('produce');
      expect(utils.canonicalNav('workflows')).toBe('produce');
    });

    it('collapses legacy inbox ids to inbox', () => {
      expect(utils.canonicalNav('decisions')).toBe('inbox');
      expect(utils.canonicalNav('ripples')).toBe('inbox');
    });

    it('collapses legacy insight ids to insight', () => {
      expect(utils.canonicalNav('overview')).toBe('insight');
      expect(utils.canonicalNav('analytics')).toBe('insight');
    });

    it('returns identity for non-legacy nav', () => {
      expect(utils.canonicalNav('ask')).toBe('ask');
      expect(utils.canonicalNav('inbox')).toBe('inbox');
      expect(utils.canonicalNav('library')).toBe('library');
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 2. readRawNavFromUrl — direct nav query param
  // ───────────────────────────────────────────────────────────────────────
  describe('readRawNavFromUrl', () => {
    it('reads nav query param', () => {
      stubWindowUrl('?nav=write');
      expect(utils.readRawNavFromUrl()).toBe('write');
    });

    it('returns null when nav missing', () => {
      stubWindowUrl('');
      expect(utils.readRawNavFromUrl()).toBe(null);
    });

    it('returns null on SSR (window undefined)', () => {
      stubWindowUndefined();
      expect(utils.readRawNavFromUrl()).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 3. isReviewerUrl — role=reviewer or review=1
  // ───────────────────────────────────────────────────────────────────────
  describe('isReviewerUrl', () => {
    it('returns true for role=reviewer', () => {
      stubWindowUrl('?role=reviewer');
      expect(utils.isReviewerUrl()).toBe(true);
    });

    it('returns true for review=1', () => {
      stubWindowUrl('?review=1');
      expect(utils.isReviewerUrl()).toBe(true);
    });

    it('returns false when both params absent', () => {
      stubWindowUrl('?nav=inbox');
      expect(utils.isReviewerUrl()).toBe(false);
    });

    it('returns false on SSR', () => {
      stubWindowUndefined();
      expect(utils.isReviewerUrl()).toBe(false);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 4. readProduceTab — tab id resolve + rawNav fallback
  // ───────────────────────────────────────────────────────────────────────
  describe('readProduceTab', () => {
    it('reads valid tab param', () => {
      stubWindowUrl('?tab=chapters');
      expect(utils.readProduceTab(null)).toBe('chapters');
    });

    it('falls back to rawNav legacy when tab invalid', () => {
      stubWindowUrl('?tab=invalid');
      expect(utils.readProduceTab('workflows')).toBe('workflows');
    });

    it('returns "studio" default when no signal', () => {
      stubWindowUrl('');
      expect(utils.readProduceTab(null)).toBe('studio');
    });

    it('returns "studio" default on SSR', () => {
      stubWindowUndefined();
      expect(utils.readProduceTab(null)).toBe('studio');
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 5. readInboxTab — inbox tab resolution
  // ───────────────────────────────────────────────────────────────────────
  describe('readInboxTab', () => {
    it('reads valid tab param', () => {
      stubWindowUrl('?tab=ripples');
      expect(utils.readInboxTab(null)).toBe('ripples');
    });

    it('falls back to rawNav legacy when tab invalid', () => {
      stubWindowUrl('?tab=invalid');
      expect(utils.readInboxTab('decisions')).toBe('decisions');
    });

    it('returns "decisions" default', () => {
      stubWindowUrl('');
      expect(utils.readInboxTab(null)).toBe('decisions');
    });

    it('returns "decisions" default on SSR', () => {
      stubWindowUndefined();
      expect(utils.readInboxTab(null)).toBe('decisions');
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 6. readInsightTab — insight tab resolution
  // ───────────────────────────────────────────────────────────────────────
  describe('readInsightTab', () => {
    it('reads valid tab param', () => {
      stubWindowUrl('?tab=analytics');
      expect(utils.readInsightTab(null)).toBe('analytics');
    });

    it('falls back to rawNav legacy when tab invalid', () => {
      stubWindowUrl('?tab=invalid');
      expect(utils.readInsightTab('overview')).toBe('overview');
    });

    it('returns "overview" default', () => {
      stubWindowUrl('');
      expect(utils.readInsightTab(null)).toBe('overview');
    });

    it('returns "overview" default on SSR', () => {
      stubWindowUndefined();
      expect(utils.readInsightTab(null)).toBe('overview');
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 7. readCreatorWorkspaceFromUrl — workspace param with 'write' exclusion
  // ───────────────────────────────────────────────────────────────────────
  describe('readCreatorWorkspaceFromUrl', () => {
    it('returns valid non-write workspace', () => {
      stubWindowUrl('?workspace=pulse');
      expect(utils.readCreatorWorkspaceFromUrl()).toBe('pulse');
    });

    it('returns null for "write" workspace (excluded)', () => {
      stubWindowUrl('?workspace=write');
      expect(utils.readCreatorWorkspaceFromUrl()).toBe(null);
    });

    it('returns null for invalid workspace', () => {
      stubWindowUrl('?workspace=invalid');
      expect(utils.readCreatorWorkspaceFromUrl()).toBe(null);
    });

    it('returns null when workspace missing', () => {
      stubWindowUrl('');
      expect(utils.readCreatorWorkspaceFromUrl()).toBe(null);
    });

    it('returns null on SSR', () => {
      stubWindowUndefined();
      expect(utils.readCreatorWorkspaceFromUrl()).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 8. normalizeCreatorWorkspace — pure helper (no window)
  // ───────────────────────────────────────────────────────────────────────
  describe('normalizeCreatorWorkspace', () => {
    it('returns workspace for valid id', () => {
      expect(utils.normalizeCreatorWorkspace('pulse')).toBe('pulse');
      expect(utils.normalizeCreatorWorkspace('settings')).toBe('settings');
    });

    it('returns null for "write" (excluded)', () => {
      expect(utils.normalizeCreatorWorkspace('write')).toBe(null);
    });

    it('returns null for invalid id', () => {
      expect(utils.normalizeCreatorWorkspace('invalid')).toBe(null);
    });

    it('returns null for empty/null/undefined', () => {
      expect(utils.normalizeCreatorWorkspace('')).toBe(null);
      expect(utils.normalizeCreatorWorkspace(null)).toBe(null);
      expect(utils.normalizeCreatorWorkspace(undefined)).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 9. readNavFromUrl — combined reviewer-aware resolution
  // ───────────────────────────────────────────────────────────────────────
  describe('readNavFromUrl', () => {
    it('returns canonical nav for valid input', () => {
      stubWindowUrl('?nav=write');
      expect(utils.readNavFromUrl()).toBe('creator');
    });

    it('returns null when no nav and not reviewer', () => {
      stubWindowUrl('');
      expect(utils.readNavFromUrl()).toBe(null);
    });

    it('returns "inbox" when reviewer with no nav', () => {
      stubWindowUrl('?role=reviewer');
      expect(utils.readNavFromUrl()).toBe('inbox');
    });

    it('returns "inbox" for reviewer blocked nav (canonical)', () => {
      stubWindowUrl('?role=reviewer&nav=write');
      // write is in REVIEWER_BLOCKED_NAV → reviewer falls back to inbox
      expect(utils.readNavFromUrl()).toBe('inbox');
    });

    it('returns "ask" for invalid non-reviewer nav', () => {
      stubWindowUrl('?nav=invalid_xyz');
      expect(utils.readNavFromUrl()).toBe('ask');
    });

    it('returns "inbox" for reviewer with invalid nav', () => {
      stubWindowUrl('?role=reviewer&nav=invalid_xyz');
      expect(utils.readNavFromUrl()).toBe('inbox');
    });

    it('returns "ask" on SSR', () => {
      stubWindowUndefined();
      expect(utils.readNavFromUrl()).toBe('ask');
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 10. readChapterFromUrl — numeric chapter param
  // ───────────────────────────────────────────────────────────────────────
  describe('readChapterFromUrl', () => {
    it('reads positive chapter number', () => {
      stubWindowUrl('?chapter=42');
      expect(utils.readChapterFromUrl()).toBe(42);
    });

    it('returns null for chapter=0 (below threshold)', () => {
      stubWindowUrl('?chapter=0');
      expect(utils.readChapterFromUrl()).toBe(null);
    });

    it('returns null for negative chapter', () => {
      stubWindowUrl('?chapter=-5');
      expect(utils.readChapterFromUrl()).toBe(null);
    });

    it('returns null for non-numeric chapter', () => {
      stubWindowUrl('?chapter=abc');
      expect(utils.readChapterFromUrl()).toBe(null);
    });

    it('returns null for empty chapter', () => {
      stubWindowUrl('?chapter=');
      expect(utils.readChapterFromUrl()).toBe(null);
    });

    it('returns null when chapter missing', () => {
      stubWindowUrl('');
      expect(utils.readChapterFromUrl()).toBe(null);
    });

    it('returns null on SSR', () => {
      stubWindowUndefined();
      expect(utils.readChapterFromUrl()).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 11. readDecisionFromUrl — trimmed decision id
  // ───────────────────────────────────────────────────────────────────────
  describe('readDecisionFromUrl', () => {
    it('reads decision id', () => {
      stubWindowUrl('?decision=dec-123');
      expect(utils.readDecisionFromUrl()).toBe('dec-123');
    });

    it('trims whitespace', () => {
      stubWindowUrl('?decision=%20%20dec-9%20%20');
      expect(utils.readDecisionFromUrl()).toBe('dec-9');
    });

    it('returns null for empty decision', () => {
      stubWindowUrl('?decision=');
      expect(utils.readDecisionFromUrl()).toBe(null);
    });

    it('returns null for whitespace-only decision', () => {
      stubWindowUrl('?decision=%20%20%20');
      expect(utils.readDecisionFromUrl()).toBe(null);
    });

    it('returns null when decision missing', () => {
      stubWindowUrl('');
      expect(utils.readDecisionFromUrl()).toBe(null);
    });

    it('returns null on SSR', () => {
      stubWindowUndefined();
      expect(utils.readDecisionFromUrl()).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 12. encodeWizardNotes — base64 of UTF-8 JSON (pure helper)
  // ───────────────────────────────────────────────────────────────────────
  describe('encodeWizardNotes', () => {
    it('encodes notes to base64', () => {
      const encoded = utils.encodeWizardNotes({ a: '1', b: 'two' });
      expect(encoded).not.toBe(null);
      // Round-trip decode
      const decoded = JSON.parse(decodeURIComponent(escape(atob(encoded!))));
      expect(decoded).toEqual({ a: '1', b: 'two' });
    });

    it('handles unicode characters (encodeURIComponent before btoa)', () => {
      const encoded = utils.encodeWizardNotes({ note: '灵文笔记 ✓' });
      expect(encoded).not.toBe(null);
      const decoded = JSON.parse(decodeURIComponent(escape(atob(encoded!))));
      expect(decoded).toEqual({ note: '灵文笔记 ✓' });
    });

    it('returns null for empty notes object', () => {
      expect(utils.encodeWizardNotes({})).toBe(null);
    });

    it('returns null for null/undefined input', () => {
      expect(utils.encodeWizardNotes(null)).toBe(null);
      expect(utils.encodeWizardNotes(undefined)).toBe(null);
    });

    it('filters out entries whose stringified value is empty', () => {
      // Object.fromEntries + filter: only entries with non-empty stringified value remain
      const encoded = utils.encodeWizardNotes({ a: '1', b: '', c: '   ', d: '4' });
      expect(encoded).not.toBe(null);
      const decoded = JSON.parse(decodeURIComponent(escape(atob(encoded!))));
      expect(decoded).toEqual({ a: '1', d: '4' });
    });

    it('returns null when all entries filter out', () => {
      expect(utils.encodeWizardNotes({ a: '', b: '   ' })).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 13. readWizardNotesFromUrl — base64 decode + JSON parse
  // ───────────────────────────────────────────────────────────────────────
  describe('readWizardNotesFromUrl', () => {
    it('reads base64-encoded notes from URL', () => {
      const notes = { x: 'one', y: 'two' };
      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(notes))));
      stubWindowUrl(`?notes=${encodeURIComponent(encoded)}`);
      expect(utils.readWizardNotesFromUrl()).toEqual(notes);
    });

    it('handles unicode round-trip', () => {
      const notes = { title: '灵文测试' };
      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(notes))));
      stubWindowUrl(`?notes=${encodeURIComponent(encoded)}`);
      expect(utils.readWizardNotesFromUrl()).toEqual(notes);
    });

    it('returns empty object when notes missing', () => {
      stubWindowUrl('');
      expect(utils.readWizardNotesFromUrl()).toEqual({});
    });

    it('returns empty object for malformed base64 (decode fails)', () => {
      stubWindowUrl('?notes=!!!not-valid-base64!!!');
      expect(utils.readWizardNotesFromUrl()).toEqual({});
    });

    it('returns empty object when JSON is not an object', () => {
      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify('a string'))));
      stubWindowUrl(`?notes=${encodeURIComponent(encoded)}`);
      expect(utils.readWizardNotesFromUrl()).toEqual({});
    });

    it('returns empty object on SSR', () => {
      stubWindowUndefined();
      expect(utils.readWizardNotesFromUrl()).toEqual({});
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 14. readWizardFromUrl — boolean: wizard=1 OR any of step/done/notes set
  // ───────────────────────────────────────────────────────────────────────
  describe('readWizardFromUrl', () => {
    it('returns true for wizard=1', () => {
      stubWindowUrl('?wizard=1');
      expect(utils.readWizardFromUrl()).toBe(true);
    });

    it('returns true for step set', () => {
      stubWindowUrl('?step=intro');
      expect(utils.readWizardFromUrl()).toBe(true);
    });

    it('returns true for done set', () => {
      stubWindowUrl('?done=step1');
      expect(utils.readWizardFromUrl()).toBe(true);
    });

    it('returns true for notes set', () => {
      stubWindowUrl('?notes=abc');
      expect(utils.readWizardFromUrl()).toBe(true);
    });

    it('returns false when none set', () => {
      stubWindowUrl('?nav=inbox');
      expect(utils.readWizardFromUrl()).toBe(false);
    });

    it('returns false on SSR', () => {
      stubWindowUndefined();
      expect(utils.readWizardFromUrl()).toBe(false);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 15. readWizardStepFromUrl — trimmed step
  // ───────────────────────────────────────────────────────────────────────
  describe('readWizardStepFromUrl', () => {
    it('reads step value', () => {
      stubWindowUrl('?step=intro');
      expect(utils.readWizardStepFromUrl()).toBe('intro');
    });

    it('trims whitespace', () => {
      stubWindowUrl('?step=%20%20intro%20%20');
      expect(utils.readWizardStepFromUrl()).toBe('intro');
    });

    it('returns null for empty step', () => {
      stubWindowUrl('?step=');
      expect(utils.readWizardStepFromUrl()).toBe(null);
    });

    it('returns null when step missing', () => {
      stubWindowUrl('');
      expect(utils.readWizardStepFromUrl()).toBe(null);
    });

    it('returns null on SSR', () => {
      stubWindowUndefined();
      expect(utils.readWizardStepFromUrl()).toBe(null);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 16. readWizardDoneFromUrl — comma-separated trimmed steps
  // ───────────────────────────────────────────────────────────────────────
  describe('readWizardDoneFromUrl', () => {
    it('reads comma-separated done steps', () => {
      stubWindowUrl('?done=step1,step2,step3');
      expect(utils.readWizardDoneFromUrl()).toEqual(['step1', 'step2', 'step3']);
    });

    it('trims whitespace around each step', () => {
      stubWindowUrl('?done=%20step1%20,%20step2%20');
      expect(utils.readWizardDoneFromUrl()).toEqual(['step1', 'step2']);
    });

    it('filters out empty entries from trailing commas', () => {
      stubWindowUrl('?done=step1,,step2,');
      expect(utils.readWizardDoneFromUrl()).toEqual(['step1', 'step2']);
    });

    it('returns empty array when done missing', () => {
      stubWindowUrl('');
      expect(utils.readWizardDoneFromUrl()).toEqual([]);
    });

    it('returns empty array for whitespace-only done', () => {
      stubWindowUrl('?done=%20%20%20');
      expect(utils.readWizardDoneFromUrl()).toEqual([]);
    });

    it('returns empty array on SSR', () => {
      stubWindowUndefined();
      expect(utils.readWizardDoneFromUrl()).toEqual([]);
    });
  });

  // ───────────────────────────────────────────────────────────────────────
  // 17. preserveRoleParams — role/review propagation to new URL
  // ───────────────────────────────────────────────────────────────────────
  describe('preserveRoleParams', () => {
    it('copies role param from current URL', () => {
      stubWindowUrl('?role=reviewer');
      const url = new URL('http://test/page?foo=bar');
      utils.preserveRoleParams(url);
      expect(url.searchParams.get('role')).toBe('reviewer');
      expect(url.searchParams.get('foo')).toBe('bar');
      expect(url.searchParams.get('review')).toBe(null);
    });

    it('copies review=1 when no role', () => {
      stubWindowUrl('?review=1');
      const url = new URL('http://test/page');
      utils.preserveRoleParams(url);
      expect(url.searchParams.get('review')).toBe('1');
      expect(url.searchParams.get('role')).toBe(null);
    });

    it('role wins over review (review not copied when role present)', () => {
      stubWindowUrl('?role=admin&review=1');
      const url = new URL('http://test/page');
      utils.preserveRoleParams(url);
      expect(url.searchParams.get('role')).toBe('admin');
      expect(url.searchParams.get('review')).toBe(null);
    });

    it('deletes role and review when neither set in current URL', () => {
      stubWindowUrl('');
      const url = new URL('http://test/page?role=stale&review=1');
      utils.preserveRoleParams(url);
      expect(url.searchParams.get('role')).toBe(null);
      expect(url.searchParams.get('review')).toBe(null);
    });

    it('does nothing on SSR', () => {
      stubWindowUndefined();
      const url = new URL('http://test/page');
      expect(() => utils.preserveRoleParams(url)).not.toThrow();
      // URL object unchanged since function early-returns
      expect(url.searchParams.toString()).toBe('');
    });
  });
});
