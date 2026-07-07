import { describe, it, expect } from 'vitest';
import type { StructureVolumeNode } from '../helpers/strict-test-types.js';
import {
  buildStructureGraph,
  findVolumeSummary,
  worstDeviationSeverity,
} from '../../src/utils/creatorStructureGraphUtils.js';

describe('creatorStructureGraphUtils', () => {
  it('findVolumeSummary matches by chapter range when label differs', () => {
    const summary = findVolumeSummary(
      [{ start_chapter: 1, end_chapter: 5, excerpt: '范围匹配' }],
      { label: '卷一', startChapter: 1, endChapter: 5 },
    );
    expect((summary as { excerpt?: string } | null)?.excerpt).toBe('范围匹配');
    expect(findVolumeSummary([], { label: 'x', startChapter: 1, endChapter: 2 })).toBeNull();
  });

  it('worstDeviationSeverity treats unknown severity as warn rank', () => {
    const deviations = [{ chapter: 1, severity: 'unknown' }];
    expect(worstDeviationSeverity(deviations, 1)).toBe('unknown');
    expect(worstDeviationSeverity([{ chapter: 1, severity: 'info' }], 1)).toBe('info');
  });

  it('worstDeviationSeverity picks highest severity', () => {
    const deviations = [
      { chapter: 2, severity: 'warn' },
      { chapter: 2, severity: 'alert' },
    ];
    expect(worstDeviationSeverity(deviations, 2)).toBe('alert');
    expect(worstDeviationSeverity(deviations, 99)).toBe('ok');
  });

  it('buildStructureGraph uses volume_pulse when volumes omitted', () => {
    const graph = buildStructureGraph({
      overview: {
        volume_pulse: {
          volumes: [{ label: '脉冲卷', start_chapter: 1, end_chapter: 2, locked: true }],
        },
        chapters: [{ chapter: 1, has_body: true }],
      },
      deviations: [],
    });
    expect(graph.volumes[0].label).toBe('脉冲卷');
    expect(graph.volumes[0].locked).toBe(true);
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
    expect((graph.volumes[0] as StructureVolumeNode).summaryExcerpt).toContain('第一卷');
  });
});
