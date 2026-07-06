import { describe, expect, it } from 'vitest';
import { ref, computed } from 'vue';
import {
  resolveChapterEntities,
  extractMentionedEntityNames,
} from '../../src/utils/creatorChapterEntityUtils.js';
import {
  buildInlineConflictMarkers,
  findParagraphRange,
} from '../../src/utils/creatorInlineConflictUtils.js';
import { isWriteWorkbenchPanelVisible } from '../../src/config/creatorPanelMatrix.js';
import { useCreatorWriteWorkbench } from '../../src/composables/useCreatorWriteWorkbench.js';

describe('creatorChapterEntityUtils', () => {
  const assets = [
    { id: 'c1', kind: 'character', name: '林默', chapters: [1], excerpt: '主角' },
    { id: 'c2', kind: 'character', name: '苏晚', chapters: [3], excerpt: '配角' },
    { id: 'fp1', kind: 'foreshadow', name: '伏笔：玉佩', chapters: [1], excerpt: '待回收' },
  ];

  it('resolves entities by chapter and body mention', () => {
    const entities = resolveChapterEntities({
      memoryAssets: assets,
      chapter: 1,
      bodyText: '林默走进雨里，苏晚在远处望着。',
    });
    expect(entities.map((e) => e.name)).toContain('林默');
    expect(entities.map((e) => e.name)).toContain('苏晚');
    expect(entities.find((e) => e.name === '苏晚')?.relevance).toBe('mention');
  });

  it('extracts mentioned character names on save', () => {
    const names = extractMentionedEntityNames('林默与苏晚对话', assets);
    expect(names).toEqual(['林默', '苏晚']);
  });
});

describe('creatorInlineConflictUtils', () => {
  it('builds markers for chapter deviations and logic issues', () => {
    const markers = buildInlineConflictMarkers({
      chapter: 2,
      deviations: [{ chapter: 2, severity: 'alert', message: '武器材质矛盾', paragraph: 2 }],
      logicIssues: [{ chapter: 2, severity: 'P0', title: '时间线冲突', paragraph: 3 }],
    });
    expect(markers).toHaveLength(2);
    expect(markers[0].kind).toBe('deviation');
    expect(markers[1].level).toBe('error');
  });

  it('finds paragraph range in body', () => {
    const body = '第一段\n\n第二段内容\n\n第三段';
    const range = findParagraphRange(body, 2);
    expect(range.text).toBe('第二段内容');
    expect(range.offset).toBeGreaterThan(0);
  });
});

describe('write workbench P1 panels', () => {
  it('exposes chapter entity rail and conflict gutter in matrix', () => {
    expect(isWriteWorkbenchPanelVisible('companion', 'chapterEntityRail')).toBe(true);
    expect(isWriteWorkbenchPanelVisible('companion', 'inlineConflictGutter')).toBe(true);
  });

  it('computes chapter entities from memory cache', () => {
    const wb = useCreatorWriteWorkbench({
      uiProfile: computed(() => ({ write_chapter_entity_rail: true })),
      overview: ref({ creation_mode: 'companion' }),
      chapterBodyDraft: ref('林默抬头'),
      selectedChapter: ref(1),
      saveMessage: ref(''),
      getMemoryAssets: () => [
        { id: 'c1', kind: 'character', name: '林默', chapters: [1], excerpt: '主角' },
      ],
    });
    expect(wb.chapterEntities.value[0]?.name).toBe('林默');
  });

  it('focuses inline conflict when paragraph present', () => {
    let focused = null;
    const wb = useCreatorWriteWorkbench({
      uiProfile: computed(() => ({})),
      overview: ref({
        creation_mode: 'companion',
        deviations: [{ chapter: 1, message: '偏离', paragraph: 1 }],
      }),
      chapterBodyDraft: ref('段一\n\n段二'),
      selectedChapter: ref(1),
      saveMessage: ref(''),
      focusParagraphByIndex: (p) => { focused = p; },
    });
    const marker = wb.inlineConflictMarkers.value[0];
    wb.focusInlineConflict(marker);
    expect(wb.activeInlineConflictId.value).toBe(marker.id);
    expect(focused).toBe(1);
  });
});
