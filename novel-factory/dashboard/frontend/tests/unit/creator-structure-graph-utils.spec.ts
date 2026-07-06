import { describe, it, expect } from 'vitest';
import { buildStructureGraph, worstDeviationSeverity } from '../../src/utils/creatorStructureGraphUtils.js';

describe('creatorStructureGraphUtils', () => {
  it('worstDeviationSeverity picks highest severity', () => {
    const deviations = [
      { chapter: 2, severity: 'warn' },
      { chapter: 2, severity: 'alert' },
    ];
    expect(worstDeviationSeverity(deviations, 2)).toBe('alert');
    expect(worstDeviationSeverity(deviations, 99)).toBe('ok');
  });

  it('buildStructureGraph maps volumes and chapter severity', () => {
    const graph = buildStructureGraph({
      volumes: [{ label: '一', start_chapter: 1, end_chapter: 2, locked: true }],
      overview: {
        chapters: [
          { chapter: 1, has_body: true, word_count: 100 },
          { chapter: 2, has_body: false, word_count: 0 },
        ],
      },
      deviations: [{ chapter: 2, severity: 'warn' }],
    });
    expect(graph.volumes).toHaveLength(1);
    expect(graph.volumes[0].chapters[0].severity).toBe('ok');
    expect(graph.volumes[0].chapters[1].severity).toBe('warn');
    expect(graph.volumes[0].locked).toBe(true);
  });

  it('falls back to single volume from max_chapter', () => {
    const graph = buildStructureGraph({
      overview: { max_chapter: 3, chapters: [] },
      deviations: [],
    });
    expect(graph.volumes[0].chapters).toHaveLength(3);
    expect(graph.timelineChapters).toHaveLength(3);
  });

  it('attaches volume summary excerpt', () => {
    const graph = buildStructureGraph({
      volumes: [{ label: '一', start_chapter: 1, end_chapter: 2, locked: false }],
      overview: {
        chapters: [{ chapter: 1, has_body: true }],
        volume_summaries: [{
          name: 'vol.md',
          volume_label: '一',
          start_chapter: 1,
          end_chapter: 2,
          excerpt: '第一卷摘要内容',
        }],
      },
      deviations: [],
    });
    expect(graph.volumes[0].summaryExcerpt).toContain('第一卷');
  });
});
