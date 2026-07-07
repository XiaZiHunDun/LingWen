import { describe, expect, it, vi } from 'vitest';
import { ref, computed, nextTick } from 'vue';
import {
  runLightValidation,
  summarizeLightValidation,
  splitBodyParagraphs,
} from '../../src/utils/creatorLightValidationUtils.js';
import { buildInlineConflictMarkers } from '../../src/utils/creatorInlineConflictUtils.js';
import { isWriteWorkbenchPanelVisible } from '../../src/config/creatorPanelMatrix.js';
import { useCreatorWriteWorkbench } from '../../src/composables/useCreatorWriteWorkbench.js';

describe('creatorLightValidationUtils', () => {
  it('flags duplicate paragraphs and long blocks', () => {
    const body = '同一段\n\n同一段\n\n' + '很长'.repeat(220);
    const issues = runLightValidation({ body, chapter: 1 });
    expect(issues.some((i) => i.rule === 'duplicate_paragraph')).toBe(true);
    expect(issues.some((i) => i.rule === 'long_paragraph')).toBe(true);
  });

  it('detects unclosed quotes', () => {
    const issues = runLightValidation({ body: '他说"未完', chapter: 2 });
    expect(issues.some((i) => i.rule === 'unclosed_quote')).toBe(true);
  });

  it('summarizes ok when no issues', () => {
    const summary = summarizeLightValidation([]);
    expect(summary.status).toBe('ok');
    expect(summary.label).toContain('通过');
  });

  it('splits paragraphs for indexing', () => {
    expect(splitBodyParagraphs('a\n\nb')).toEqual(['a', 'b']);
  });
});

describe('light validation workbench integration', () => {
  it('exposes light validation bar in companion matrix', () => {
    expect(isWriteWorkbenchPanelVisible('companion', 'lightValidationBar')).toBe(true);
    expect(isWriteWorkbenchPanelVisible('studio', 'lightValidationBar')).toBe(false);
  });

  it('merges light issues into inline conflict markers', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 1,
      lightIssues: [{
        id: 'light-dup-2',
        kind: 'light',
        level: 'warn',
        label: '重复段',
        paragraph: 2,
      }],
    });
    expect(markers[0].kind).toBe('light');
  });

  it('runs debounced light validation on draft change', async () => {
    vi.useFakeTimers();
    const uiProfile = computed(() => ({ creator_write_workbench: true }));
    const overview = ref({ creation_mode: 'companion' });
    const chapterBodyDraft = ref('初稿');
    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft,
      selectedChapter: ref(1),
      saveMessage: ref(''),
    });

    chapterBodyDraft.value = '他说"未完';
    await nextTick();
    await vi.advanceTimersByTimeAsync(1300);
    expect(wb.lightValidationIssues.value.some((i: { rule: string }) => i.rule === 'unclosed_quote')).toBe(true);
    vi.useRealTimers();
  });
});
